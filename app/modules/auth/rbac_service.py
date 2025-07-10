"""
Enhanced RBAC Service with dependency validation and user type management.

This service provides advanced RBAC functionality including:
- Permission dependency validation
- User type hierarchy management
- Risk-based permission checking
- Audit logging for RBAC operations
"""

from typing import Optional, List, Dict, Set, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from .models import (
    User, Role, Permission, PermissionCategory, PermissionDependency,
    RBACauditlog, user_roles_table, role_permissions_table, user_permissions_table
)
from .constants import (
    UserType, PermissionRiskLevel, RoleTemplate, PermissionCategory as PermissionCategoryEnum,
    get_permission_risk_level, get_permission_dependencies, 
    can_user_type_manage, validate_permission_dependencies
)
from .repository import AuthRepository
from app.core.errors import ValidationError, NotFoundError, ConflictError, AuthenticationError
from .rbac_cache import rbac_cache
# from app.core.security import get_current_user_id  # Not needed for this implementation


class RBACService:
    """Enhanced RBAC service with dependency validation and user type management."""
    
    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.repository = AuthRepository(session)
    
    # Permission dependency validation
    async def validate_permission_dependencies(self, user_id: UUID, permission_codes: List[str]) -> Dict[str, List[str]]:
        """
        Validate that user has all required dependencies for the given permissions.
        
        Args:
            user_id: User ID to check permissions for
            permission_codes: List of permission codes to validate
            
        Returns:
            Dict with 'missing_dependencies' key containing list of missing permission codes
        """
        # Get user's current permissions
        user_permissions = await self.get_user_all_permissions(user_id)
        user_permission_codes = {perm.code for perm in user_permissions}
        
        missing_dependencies = []
        
        for permission_code in permission_codes:
            # Get dependencies for this permission
            dependencies = get_permission_dependencies(permission_code)
            
            # Check if user has all required dependencies
            for dependency in dependencies:
                if dependency not in user_permission_codes:
                    missing_dependencies.append(dependency)
        
        return {
            'missing_dependencies': list(set(missing_dependencies))
        }
    
    async def can_grant_permission(self, granter_id: UUID, grantee_id: UUID, permission_code: str) -> Dict[str, Any]:
        """
        Check if a user can grant a permission to another user.
        
        Args:
            granter_id: ID of user trying to grant permission
            grantee_id: ID of user receiving permission
            permission_code: Permission code to grant
            
        Returns:
            Dict with 'can_grant', 'reason', and 'missing_dependencies' keys
        """
        # Get granter and grantee
        granter = await self.repository.get_user_by_id(granter_id)
        grantee = await self.repository.get_user_by_id(grantee_id)
        
        if not granter or not grantee:
            return {
                'can_grant': False,
                'reason': 'User not found',
                'missing_dependencies': []
            }
        
        # Check user type hierarchy - can granter manage grantee?
        if not can_user_type_manage(
            UserType(granter.user_type),
            UserType(grantee.user_type)
        ):
            return {
                'can_grant': False,
                'reason': f'Insufficient user type level. {granter.user_type} cannot manage {grantee.user_type}',
                'missing_dependencies': []
            }
        
        # Check if granter has the permission they're trying to grant
        granter_permissions = await self.get_user_all_permissions(granter_id)
        granter_permission_codes = {perm.code for perm in granter_permissions}
        
        if permission_code not in granter_permission_codes:
            return {
                'can_grant': False,
                'reason': f'Granter does not have permission {permission_code}',
                'missing_dependencies': []
            }
        
        # Check if grantee has all required dependencies
        dependency_check = await self.validate_permission_dependencies(grantee_id, [permission_code])
        
        if dependency_check['missing_dependencies']:
            return {
                'can_grant': False,
                'reason': 'Grantee is missing required dependencies',
                'missing_dependencies': dependency_check['missing_dependencies']
            }
        
        # Check permission risk level - high/critical permissions may need additional approval
        risk_level = get_permission_risk_level(permission_code)
        if risk_level in [PermissionRiskLevel.HIGH, PermissionRiskLevel.CRITICAL]:
            # Check if granter is superuser or admin
            if granter.user_type not in [UserType.SUPERADMIN.value, UserType.ADMIN.value]:
                return {
                    'can_grant': False,
                    'reason': f'Permission {permission_code} has {risk_level.value} risk level and requires admin approval',
                    'missing_dependencies': []
                }
        
        return {
            'can_grant': True,
            'reason': 'Grant approved',
            'missing_dependencies': []
        }
    
    async def grant_permission_to_user(
        self, 
        granter_id: UUID, 
        grantee_id: UUID, 
        permission_code: str,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Grant a permission to a user with validation.
        
        Args:
            granter_id: ID of user granting permission
            grantee_id: ID of user receiving permission
            permission_code: Permission code to grant
            expires_at: Optional expiration time for temporary permissions
            
        Returns:
            Dict with 'success', 'message', and 'permission_id' keys
        """
        # Validate if permission can be granted
        validation_result = await self.can_grant_permission(granter_id, grantee_id, permission_code)
        
        if not validation_result['can_grant']:
            await self.log_rbac_action(
                user_id=granter_id,
                action='GRANT_PERMISSION_FAILED',
                entity_type='USER_PERMISSION',
                entity_id=grantee_id,
                changes={'permission_code': permission_code, 'reason': validation_result['reason']},
                success=False,
                error_message=validation_result['reason']
            )
            return {
                'success': False,
                'message': validation_result['reason'],
                'permission_id': None
            }
        
        # Get permission by code
        permission = await self.get_permission_by_code(permission_code)
        if not permission:
            return {
                'success': False,
                'message': f'Permission {permission_code} not found',
                'permission_id': None
            }
        
        # Check if user already has this permission
        existing_permission = await self.session.execute(
            select(user_permissions_table).where(
                and_(
                    user_permissions_table.c.user_id == grantee_id,
                    user_permissions_table.c.permission_id == permission.id
                )
            )
        )
        
        if existing_permission.first():
            return {
                'success': False,
                'message': f'User already has permission {permission_code}',
                'permission_id': permission.id
            }
        
        # Grant permission
        insert_stmt = user_permissions_table.insert().values(
            user_id=grantee_id,
            permission_id=permission.id,
            granted_by=granter_id,
            granted_at=datetime.utcnow(),
            expires_at=expires_at
        )
        
        await self.session.execute(insert_stmt)
        await self.session.commit()
        
        # Invalidate user permissions cache
        await rbac_cache.invalidate_user_permissions(grantee_id)
        
        # Log the action
        await self.log_rbac_action(
            user_id=granter_id,
            action='GRANT_PERMISSION',
            entity_type='USER_PERMISSION',
            entity_id=grantee_id,
            changes={
                'permission_code': permission_code,
                'permission_id': str(permission.id),
                'expires_at': expires_at.isoformat() if expires_at else None
            },
            success=True
        )
        
        return {
            'success': True,
            'message': f'Permission {permission_code} granted successfully',
            'permission_id': permission.id
        }
    
    async def revoke_permission_from_user(
        self, 
        revoker_id: UUID, 
        user_id: UUID, 
        permission_code: str
    ) -> Dict[str, Any]:
        """
        Revoke a permission from a user with validation.
        
        Args:
            revoker_id: ID of user revoking permission
            user_id: ID of user to revoke permission from
            permission_code: Permission code to revoke
            
        Returns:
            Dict with 'success' and 'message' keys
        """
        # Basic validation
        revoker = await self.repository.get_user_by_id(revoker_id)
        target_user = await self.repository.get_user_by_id(user_id)
        
        if not revoker or not target_user:
            return {
                'success': False,
                'message': 'User not found'
            }
        
        # Check user type hierarchy
        if not can_user_type_manage(
            UserType(revoker.user_type),
            UserType(target_user.user_type)
        ):
            return {
                'success': False,
                'message': f'Insufficient user type level. {revoker.user_type} cannot manage {target_user.user_type}'
            }
        
        # Get permission by code
        permission = await self.get_permission_by_code(permission_code)
        if not permission:
            return {
                'success': False,
                'message': f'Permission {permission_code} not found'
            }
        
        # Check if user has this direct permission
        result = await self.session.execute(
            select(user_permissions_table).where(
                and_(
                    user_permissions_table.c.user_id == user_id,
                    user_permissions_table.c.permission_id == permission.id
                )
            )
        )
        
        if not result.first():
            return {
                'success': False,
                'message': f'User does not have direct permission {permission_code}'
            }
        
        # Remove permission
        delete_stmt = user_permissions_table.delete().where(
            and_(
                user_permissions_table.c.user_id == user_id,
                user_permissions_table.c.permission_id == permission.id
            )
        )
        
        await self.session.execute(delete_stmt)
        await self.session.commit()
        
        # Invalidate user permissions cache
        await rbac_cache.invalidate_user_permissions(user_id)
        
        # Log the action
        await self.log_rbac_action(
            user_id=revoker_id,
            action='REVOKE_PERMISSION',
            entity_type='USER_PERMISSION',
            entity_id=user_id,
            changes={
                'permission_code': permission_code,
                'permission_id': str(permission.id)
            },
            success=True
        )
        
        return {
            'success': True,
            'message': f'Permission {permission_code} revoked successfully'
        }
    
    # Enhanced permission checking
    async def check_permission_with_risk_level(
        self, 
        user_id: UUID, 
        permission_code: str,
        require_dependencies: bool = True
    ) -> Dict[str, Any]:
        """
        Check if user has permission with risk level validation.
        
        Args:
            user_id: User ID to check
            permission_code: Permission code to check
            require_dependencies: Whether to validate dependencies
            
        Returns:
            Dict with 'has_permission', 'risk_level', 'requires_approval', and 'missing_dependencies' keys
        """
        # Get user permissions
        user_permissions = await self.get_user_all_permissions(user_id)
        user_permission_codes = {perm.code for perm in user_permissions}
        
        # Check if user has the permission
        has_permission = permission_code in user_permission_codes
        
        # Get permission details
        permission = await self.get_permission_by_code(permission_code)
        if not permission:
            return {
                'has_permission': False,
                'risk_level': None,
                'requires_approval': False,
                'missing_dependencies': []
            }
        
        missing_dependencies = []
        if require_dependencies and has_permission:
            # Check dependencies
            dependency_check = await self.validate_permission_dependencies(user_id, [permission_code])
            missing_dependencies = dependency_check['missing_dependencies']
            
            # If dependencies are missing, permission is effectively not granted
            if missing_dependencies:
                has_permission = False
        
        return {
            'has_permission': has_permission,
            'risk_level': permission.risk_level,
            'requires_approval': permission.requires_approval,
            'missing_dependencies': missing_dependencies
        }
    
    async def get_user_all_permissions(self, user_id: UUID, use_cache: bool = True) -> List[Permission]:
        """
        Get all permissions for a user (from roles and direct assignments).
        
        Args:
            user_id: User ID
            use_cache: Whether to use cached results
            
        Returns:
            List of Permission objects
        """
        # Try to get from cache first
        if use_cache:
            cached_permissions = await rbac_cache.get_user_permissions(user_id)
            if cached_permissions:
                # Convert cached data back to Permission objects
                permissions = []
                for perm_data in cached_permissions:
                    # Create a mock Permission object from cached data
                    perm = Permission()
                    perm.id = UUID(perm_data['id'])
                    perm.code = perm_data['code']
                    perm.name = perm_data['name']
                    perm.description = perm_data['description']
                    perm.resource = perm_data['resource']
                    perm.action = perm_data['action']
                    perm.risk_level = perm_data['risk_level']
                    perm.requires_approval = perm_data['requires_approval']
                    permissions.append(perm)
                return permissions
        
        # Get permissions from roles
        role_permissions_query = select(Permission).select_from(
            Permission.__table__.join(role_permissions_table, Permission.id == role_permissions_table.c.permission_id)
            .join(user_roles_table, role_permissions_table.c.role_id == user_roles_table.c.role_id)
        ).where(
            and_(
                user_roles_table.c.user_id == user_id,
                Permission.is_active == True
            )
        )
        
        role_permissions_result = await self.session.execute(role_permissions_query)
        role_permissions = role_permissions_result.scalars().all()
        
        # Get direct permissions
        direct_permissions_query = select(Permission).select_from(
            Permission.__table__.join(user_permissions_table, Permission.id == user_permissions_table.c.permission_id)
        ).where(
            and_(
                user_permissions_table.c.user_id == user_id,
                Permission.is_active == True,
                or_(
                    user_permissions_table.c.expires_at.is_(None),
                    user_permissions_table.c.expires_at > datetime.utcnow()
                )
            )
        )
        
        direct_permissions_result = await self.session.execute(direct_permissions_query)
        direct_permissions = direct_permissions_result.scalars().all()
        
        # Combine and deduplicate
        all_permissions = {}
        for perm in role_permissions + direct_permissions:
            all_permissions[perm.id] = perm
        
        permissions_list = list(all_permissions.values())
        
        # Cache the result if caching is enabled
        if use_cache:
            await rbac_cache.set_user_permissions(user_id, permissions_list)
        
        return permissions_list
    
    async def get_permission_by_code(self, permission_code: str, use_cache: bool = True) -> Optional[Permission]:
        """Get permission by code."""
        # Try to get from cache first
        if use_cache:
            cached_permission = await rbac_cache.get_permission_by_code(permission_code)
            if cached_permission:
                # Convert cached data back to Permission object
                perm = Permission()
                perm.id = UUID(cached_permission['id'])
                perm.code = cached_permission['code']
                perm.name = cached_permission['name']
                perm.description = cached_permission['description']
                perm.resource = cached_permission['resource']
                perm.action = cached_permission['action']
                perm.risk_level = cached_permission['risk_level']
                perm.requires_approval = cached_permission['requires_approval']
                return perm
        
        result = await self.session.execute(
            select(Permission).where(
                and_(
                    Permission.code == permission_code,
                    Permission.is_active == True
                )
            )
        )
        permission = result.scalar_one_or_none()
        
        # Cache the result if found and caching is enabled
        if permission and use_cache:
            await rbac_cache.set_permission_by_code(permission_code, permission)
        
        return permission
    
    # User type management
    async def can_user_manage_user_type(self, manager_id: UUID, target_user_type: UserType) -> bool:
        """Check if a user can manage another user type."""
        manager = await self.repository.get_user_by_id(manager_id)
        if not manager:
            return False
        
        return can_user_type_manage(UserType(manager.user_type), target_user_type)
    
    async def elevate_user_type(
        self, 
        elevator_id: UUID, 
        target_user_id: UUID, 
        new_user_type: UserType
    ) -> Dict[str, Any]:
        """
        Elevate user type with validation.
        
        Args:
            elevator_id: ID of user performing elevation
            target_user_id: ID of user being elevated
            new_user_type: New user type to assign
            
        Returns:
            Dict with 'success', 'message', and 'previous_type' keys
        """
        # Get users
        elevator = await self.repository.get_user_by_id(elevator_id)
        target_user = await self.repository.get_user_by_id(target_user_id)
        
        if not elevator or not target_user:
            return {
                'success': False,
                'message': 'User not found',
                'previous_type': None
            }
        
        previous_type = target_user.user_type
        
        # Check if elevator can manage this user type
        if not can_user_type_manage(UserType(elevator.user_type), new_user_type):
            await self.log_rbac_action(
                user_id=elevator_id,
                action='ELEVATE_USER_TYPE_FAILED',
                entity_type='USER',
                entity_id=target_user_id,
                changes={
                    'target_user_type': new_user_type.value,
                    'previous_type': previous_type,
                    'reason': 'Insufficient user type level'
                },
                success=False,
                error_message='Insufficient user type level'
            )
            return {
                'success': False,
                'message': f'Insufficient user type level. {elevator.user_type} cannot elevate to {new_user_type.value}',
                'previous_type': previous_type
            }
        
        # Update user type
        await self.repository.update_user(target_user_id, {'user_type': new_user_type.value})
        
        # Log the action
        await self.log_rbac_action(
            user_id=elevator_id,
            action='ELEVATE_USER_TYPE',
            entity_type='USER',
            entity_id=target_user_id,
            changes={
                'new_user_type': new_user_type.value,
                'previous_type': previous_type
            },
            success=True
        )
        
        return {
            'success': True,
            'message': f'User type elevated from {previous_type} to {new_user_type.value}',
            'previous_type': previous_type
        }
    
    # Audit logging
    async def log_rbac_action(
        self,
        user_id: Optional[UUID],
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log RBAC action for audit trail."""
        import json
        
        audit_log = RBACauditlog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=json.dumps(changes) if changes else None,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            success=success,
            error_message=error_message,
            session_id=session_id
        )
        
        self.session.add(audit_log)
        await self.session.commit()
    
    async def get_rbac_audit_logs(
        self,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RBACauditlog]:
        """Get RBAC audit logs with filtering."""
        query = select(RBACauditlog)
        
        conditions = []
        if user_id:
            conditions.append(RBACauditlog.user_id == user_id)
        if action:
            conditions.append(RBACauditlog.action == action)
        if entity_type:
            conditions.append(RBACauditlog.entity_type == entity_type)
        if start_time:
            conditions.append(RBACauditlog.timestamp >= start_time)
        if end_time:
            conditions.append(RBACauditlog.timestamp <= end_time)
        if success is not None:
            conditions.append(RBACauditlog.success == success)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(RBACauditlog.timestamp.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    # Permission categories
    async def get_permission_categories(self) -> List[PermissionCategory]:
        """Get all permission categories."""
        result = await self.session.execute(
            select(PermissionCategory)
            .where(PermissionCategory.is_active == True)
            .order_by(PermissionCategory.display_order)
        )
        return result.scalars().all()
    
    async def get_permissions_by_category(self, category_code: str) -> List[Permission]:
        """Get permissions by category code."""
        result = await self.session.execute(
            select(Permission)
            .join(PermissionCategory)
            .where(
                and_(
                    PermissionCategory.code == category_code,
                    Permission.is_active == True,
                    PermissionCategory.is_active == True
                )
            )
            .order_by(Permission.name)
        )
        return result.scalars().all()
    
    # Permission dependencies
    async def get_permission_dependencies(self, permission_id: UUID) -> List[Permission]:
        """Get dependencies for a permission."""
        result = await self.session.execute(
            select(Permission)
            .join(PermissionDependency, Permission.id == PermissionDependency.depends_on_id)
            .where(
                and_(
                    PermissionDependency.permission_id == permission_id,
                    PermissionDependency.is_active == True,
                    Permission.is_active == True
                )
            )
        )
        return result.scalars().all()
    
    async def get_permission_dependents(self, permission_id: UUID) -> List[Permission]:
        """Get permissions that depend on the given permission."""
        result = await self.session.execute(
            select(Permission)
            .join(PermissionDependency, Permission.id == PermissionDependency.permission_id)
            .where(
                and_(
                    PermissionDependency.depends_on_id == permission_id,
                    PermissionDependency.is_active == True,
                    Permission.is_active == True
                )
            )
        )
        return result.scalars().all()
    
    # Role hierarchy support
    async def get_role_hierarchy(self, role_id: UUID) -> Dict[str, Any]:
        """Get role hierarchy information including parent and child roles."""
        from .models import role_hierarchy_table
        
        # Get parent roles
        parent_query = select(Role).join(
            role_hierarchy_table,
            Role.id == role_hierarchy_table.c.parent_role_id
        ).where(
            role_hierarchy_table.c.child_role_id == role_id
        )
        
        parent_result = await self.session.execute(parent_query)
        parent_roles = parent_result.scalars().all()
        
        # Get child roles
        child_query = select(Role).join(
            role_hierarchy_table,
            Role.id == role_hierarchy_table.c.child_role_id
        ).where(
            role_hierarchy_table.c.parent_role_id == role_id
        )
        
        child_result = await self.session.execute(child_query)
        child_roles = child_result.scalars().all()
        
        # Get current role
        current_role = await self.repository.get_role_by_id(role_id)
        
        return {
            'current_role': current_role,
            'parent_roles': parent_roles,
            'child_roles': child_roles
        }
    
    async def add_role_hierarchy(self, parent_role_id: UUID, child_role_id: UUID, inherit_permissions: bool = True) -> Dict[str, Any]:
        """Add a parent-child relationship between roles."""
        from .models import role_hierarchy_table
        
        # Validate roles exist
        parent_role = await self.repository.get_role_by_id(parent_role_id)
        child_role = await self.repository.get_role_by_id(child_role_id)
        
        if not parent_role or not child_role:
            return {
                'success': False,
                'message': 'Parent or child role not found'
            }
        
        # Check for circular dependency
        if await self._check_circular_dependency(parent_role_id, child_role_id):
            return {
                'success': False,
                'message': 'Circular dependency detected in role hierarchy'
            }
        
        # Check if relationship already exists
        existing_query = select(role_hierarchy_table).where(
            and_(
                role_hierarchy_table.c.parent_role_id == parent_role_id,
                role_hierarchy_table.c.child_role_id == child_role_id
            )
        )
        
        existing_result = await self.session.execute(existing_query)
        if existing_result.first():
            return {
                'success': False,
                'message': 'Role hierarchy relationship already exists'
            }
        
        # Add relationship
        insert_stmt = role_hierarchy_table.insert().values(
            parent_role_id=parent_role_id,
            child_role_id=child_role_id,
            inherit_permissions=inherit_permissions
        )
        
        await self.session.execute(insert_stmt)
        await self.session.commit()
        
        return {
            'success': True,
            'message': f'Role hierarchy created: {parent_role.name} -> {child_role.name}'
        }
    
    async def remove_role_hierarchy(self, parent_role_id: UUID, child_role_id: UUID) -> Dict[str, Any]:
        """Remove a parent-child relationship between roles."""
        from .models import role_hierarchy_table
        
        # Check if relationship exists
        existing_query = select(role_hierarchy_table).where(
            and_(
                role_hierarchy_table.c.parent_role_id == parent_role_id,
                role_hierarchy_table.c.child_role_id == child_role_id
            )
        )
        
        existing_result = await self.session.execute(existing_query)
        if not existing_result.first():
            return {
                'success': False,
                'message': 'Role hierarchy relationship not found'
            }
        
        # Remove relationship
        delete_stmt = role_hierarchy_table.delete().where(
            and_(
                role_hierarchy_table.c.parent_role_id == parent_role_id,
                role_hierarchy_table.c.child_role_id == child_role_id
            )
        )
        
        await self.session.execute(delete_stmt)
        await self.session.commit()
        
        return {
            'success': True,
            'message': 'Role hierarchy relationship removed'
        }
    
    async def _check_circular_dependency(self, parent_role_id: UUID, child_role_id: UUID) -> bool:
        """Check if adding this hierarchy would create a circular dependency."""
        from .models import role_hierarchy_table
        
        # Check if child_role_id is already a parent of parent_role_id (direct or indirect)
        visited = set()
        return await self._has_path_to_role(child_role_id, parent_role_id, visited)
    
    async def _has_path_to_role(self, start_role_id: UUID, target_role_id: UUID, visited: set) -> bool:
        """Check if there's a path from start_role to target_role through hierarchy."""
        from .models import role_hierarchy_table
        
        if start_role_id == target_role_id:
            return True
        
        if start_role_id in visited:
            return False
        
        visited.add(start_role_id)
        
        # Get all child roles of start_role
        child_query = select(role_hierarchy_table.c.child_role_id).where(
            role_hierarchy_table.c.parent_role_id == start_role_id
        )
        
        child_result = await self.session.execute(child_query)
        child_role_ids = [row[0] for row in child_result.fetchall()]
        
        # Recursively check each child
        for child_role_id in child_role_ids:
            if await self._has_path_to_role(child_role_id, target_role_id, visited):
                return True
        
        return False
    
    async def get_role_inherited_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions for a role including inherited permissions from parent roles."""
        from .models import role_hierarchy_table
        
        # Get direct permissions
        direct_permissions = await self.repository.get_role_permissions(role_id)
        permission_map = {perm.id: perm for perm in direct_permissions}
        
        # Get inherited permissions from parent roles
        await self._collect_inherited_permissions(role_id, permission_map, set())
        
        return list(permission_map.values())
    
    async def _collect_inherited_permissions(self, role_id: UUID, permission_map: Dict[UUID, Permission], visited: set):
        """Recursively collect inherited permissions from parent roles."""
        from .models import role_hierarchy_table
        
        if role_id in visited:
            return
        
        visited.add(role_id)
        
        # Get parent roles that allow permission inheritance
        parent_query = select(
            role_hierarchy_table.c.parent_role_id,
            role_hierarchy_table.c.inherit_permissions
        ).where(
            role_hierarchy_table.c.child_role_id == role_id
        )
        
        parent_result = await self.session.execute(parent_query)
        parent_data = parent_result.fetchall()
        
        for parent_role_id, inherit_permissions in parent_data:
            if inherit_permissions:
                # Get permissions from parent role
                parent_permissions = await self.repository.get_role_permissions(parent_role_id)
                
                # Add to permission map
                for perm in parent_permissions:
                    permission_map[perm.id] = perm
                
                # Recursively get permissions from parent's parents
                await self._collect_inherited_permissions(parent_role_id, permission_map, visited)
    
    async def get_user_all_permissions_with_hierarchy(self, user_id: UUID) -> Dict[str, Any]:
        """Get all permissions for a user including role hierarchy inheritance."""
        # Get user's direct permissions
        direct_permissions_query = select(Permission).join(
            user_permissions_table
        ).where(
            and_(
                user_permissions_table.c.user_id == user_id,
                Permission.is_active == True,
                or_(
                    user_permissions_table.c.expires_at.is_(None),
                    user_permissions_table.c.expires_at > datetime.utcnow()
                )
            )
        )
        
        direct_permissions_result = await self.session.execute(direct_permissions_query)
        direct_permissions = direct_permissions_result.scalars().all()
        
        # Get user's roles
        user_roles = await self.repository.get_user_roles(user_id)
        
        # Get permissions from roles (including inherited)
        role_permissions = {}
        for role in user_roles:
            role_perms = await self.get_role_inherited_permissions(role.id)
            role_permissions[role.name] = role_perms
        
        # Combine all permissions
        all_permissions = {}
        
        # Add direct permissions
        for perm in direct_permissions:
            all_permissions[perm.id] = {
                'permission': perm,
                'source': 'direct',
                'source_details': None
            }
        
        # Add role permissions
        for role_name, perms in role_permissions.items():
            for perm in perms:
                if perm.id not in all_permissions:
                    all_permissions[perm.id] = {
                        'permission': perm,
                        'source': 'role',
                        'source_details': role_name
                    }
                else:
                    # Permission exists from multiple sources
                    existing = all_permissions[perm.id]
                    if existing['source'] == 'role':
                        existing['source_details'] = f"{existing['source_details']}, {role_name}"
        
        return {
            'user_id': user_id,
            'direct_permissions': direct_permissions,
            'role_permissions': role_permissions,
            'all_permissions': list(all_permissions.values())
        }
    
    # Temporary permissions support
    async def grant_temporary_permission(
        self,
        granter_id: UUID,
        grantee_id: UUID,
        permission_code: str,
        expires_at: datetime,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Grant a temporary permission to a user with expiration."""
        # Use the existing grant_permission_to_user method with expiration
        result = await self.grant_permission_to_user(
            granter_id=granter_id,
            grantee_id=grantee_id,
            permission_code=permission_code,
            expires_at=expires_at
        )
        
        # If successful, log the temporary permission grant with reason
        if result['success']:
            await self.log_rbac_action(
                user_id=granter_id,
                action='GRANT_TEMPORARY_PERMISSION',
                entity_type='USER_PERMISSION',
                entity_id=grantee_id,
                changes={
                    'permission_code': permission_code,
                    'permission_id': str(result['permission_id']),
                    'expires_at': expires_at.isoformat(),
                    'reason': reason
                },
                success=True
            )
        
        return {
            'success': result['success'],
            'message': result['message'],
            'permission_id': result['permission_id'],
            'expires_at': expires_at if result['success'] else None
        }
    
    async def get_user_temporary_permissions(self, user_id: UUID) -> Dict[str, Any]:
        """Get all temporary permissions for a user."""
        # Get all direct permissions with expiration info
        query = select(
            Permission,
            user_permissions_table.c.granted_by,
            user_permissions_table.c.granted_at,
            user_permissions_table.c.expires_at
        ).join(
            user_permissions_table,
            Permission.id == user_permissions_table.c.permission_id
        ).where(
            and_(
                user_permissions_table.c.user_id == user_id,
                user_permissions_table.c.expires_at.is_not(None),
                Permission.is_active == True
            )
        ).order_by(user_permissions_table.c.expires_at.asc())
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        temporary_permissions = []
        active_count = 0
        expired_count = 0
        current_time = datetime.utcnow()
        
        for row in rows:
            permission, granted_by, granted_at, expires_at = row
            is_active = expires_at > current_time
            
            if is_active:
                active_count += 1
            else:
                expired_count += 1
            
            temporary_permissions.append({
                'permission': permission,
                'granted_by': granted_by,
                'granted_at': granted_at,
                'expires_at': expires_at,
                'is_active': is_active,
                'reason': None  # Could be stored in a separate table if needed
            })
        
        return {
            'user_id': user_id,
            'temporary_permissions': temporary_permissions,
            'active_count': active_count,
            'expired_count': expired_count
        }
    
    async def revoke_temporary_permission(
        self,
        revoker_id: UUID,
        user_id: UUID,
        permission_code: str
    ) -> Dict[str, Any]:
        """Revoke a temporary permission from a user."""
        # Use the existing revoke_permission_from_user method
        result = await self.revoke_permission_from_user(
            revoker_id=revoker_id,
            user_id=user_id,
            permission_code=permission_code
        )
        
        # If successful, log the temporary permission revocation
        if result['success']:
            await self.log_rbac_action(
                user_id=revoker_id,
                action='REVOKE_TEMPORARY_PERMISSION',
                entity_type='USER_PERMISSION',
                entity_id=user_id,
                changes={
                    'permission_code': permission_code
                },
                success=True
            )
        
        return result
    
    async def cleanup_expired_permissions(self) -> Dict[str, Any]:
        """Clean up expired temporary permissions."""
        current_time = datetime.utcnow()
        
        # Get expired permissions
        expired_query = select(
            user_permissions_table.c.user_id,
            user_permissions_table.c.permission_id,
            user_permissions_table.c.expires_at
        ).where(
            and_(
                user_permissions_table.c.expires_at.is_not(None),
                user_permissions_table.c.expires_at <= current_time
            )
        )
        
        expired_result = await self.session.execute(expired_query)
        expired_permissions = expired_result.fetchall()
        
        if not expired_permissions:
            return {
                'success': True,
                'message': 'No expired permissions to clean up',
                'cleaned_count': 0
            }
        
        # Delete expired permissions
        delete_stmt = user_permissions_table.delete().where(
            and_(
                user_permissions_table.c.expires_at.is_not(None),
                user_permissions_table.c.expires_at <= current_time
            )
        )
        
        await self.session.execute(delete_stmt)
        await self.session.commit()
        
        # Log the cleanup
        await self.log_rbac_action(
            user_id=None,  # System action
            action='CLEANUP_EXPIRED_PERMISSIONS',
            entity_type='SYSTEM',
            entity_id=None,
            changes={
                'cleaned_count': len(expired_permissions),
                'cleanup_time': current_time.isoformat()
            },
            success=True
        )
        
        return {
            'success': True,
            'message': f'Cleaned up {len(expired_permissions)} expired permissions',
            'cleaned_count': len(expired_permissions)
        }
    
    async def extend_temporary_permission(
        self,
        extender_id: UUID,
        user_id: UUID,
        permission_code: str,
        new_expires_at: datetime
    ) -> Dict[str, Any]:
        """Extend the expiration time of a temporary permission."""
        # Get permission by code
        permission = await self.get_permission_by_code(permission_code)
        if not permission:
            return {
                'success': False,
                'message': f'Permission {permission_code} not found'
            }
        
        # Check if user has this temporary permission
        existing_query = select(
            user_permissions_table.c.expires_at
        ).where(
            and_(
                user_permissions_table.c.user_id == user_id,
                user_permissions_table.c.permission_id == permission.id,
                user_permissions_table.c.expires_at.is_not(None)
            )
        )
        
        existing_result = await self.session.execute(existing_query)
        existing_row = existing_result.first()
        
        if not existing_row:
            return {
                'success': False,
                'message': f'User does not have temporary permission {permission_code}'
            }
        
        old_expires_at = existing_row[0]
        
        # Check if user can extend this permission
        extender = await self.repository.get_user_by_id(extender_id)
        target_user = await self.repository.get_user_by_id(user_id)
        
        if not extender or not target_user:
            return {
                'success': False,
                'message': 'User not found'
            }
        
        # Check user type hierarchy
        if not can_user_type_manage(
            UserType(extender.user_type),
            UserType(target_user.user_type)
        ):
            return {
                'success': False,
                'message': f'Insufficient user type level. {extender.user_type} cannot manage {target_user.user_type}'
            }
        
        # Update expiration time
        update_stmt = user_permissions_table.update().where(
            and_(
                user_permissions_table.c.user_id == user_id,
                user_permissions_table.c.permission_id == permission.id
            )
        ).values(expires_at=new_expires_at)
        
        await self.session.execute(update_stmt)
        await self.session.commit()
        
        # Log the extension
        await self.log_rbac_action(
            user_id=extender_id,
            action='EXTEND_TEMPORARY_PERMISSION',
            entity_type='USER_PERMISSION',
            entity_id=user_id,
            changes={
                'permission_code': permission_code,
                'permission_id': str(permission.id),
                'old_expires_at': old_expires_at.isoformat(),
                'new_expires_at': new_expires_at.isoformat()
            },
            success=True
        )
        
        return {
            'success': True,
            'message': f'Extended temporary permission {permission_code} until {new_expires_at.isoformat()}',
            'old_expires_at': old_expires_at,
            'new_expires_at': new_expires_at
        }
    
    # Bulk operations for efficiency
    async def bulk_grant_permissions(
        self,
        granter_id: UUID,
        grantee_id: UUID,
        permission_codes: List[str],
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Grant multiple permissions to a user at once."""
        results = {
            'success': True,
            'granted': [],
            'failed': [],
            'total': len(permission_codes),
            'granted_count': 0,
            'failed_count': 0
        }
        
        for permission_code in permission_codes:
            try:
                result = await self.grant_permission_to_user(
                    granter_id=granter_id,
                    grantee_id=grantee_id,
                    permission_code=permission_code,
                    expires_at=expires_at
                )
                
                if result['success']:
                    results['granted'].append({
                        'permission_code': permission_code,
                        'permission_id': result['permission_id'],
                        'message': result['message']
                    })
                    results['granted_count'] += 1
                else:
                    results['failed'].append({
                        'permission_code': permission_code,
                        'error': result['message']
                    })
                    results['failed_count'] += 1
                    
            except Exception as e:
                results['failed'].append({
                    'permission_code': permission_code,
                    'error': str(e)
                })
                results['failed_count'] += 1
        
        # If any failed, mark overall as failed
        if results['failed_count'] > 0:
            results['success'] = False
        
        # Log bulk operation
        await self.log_rbac_action(
            user_id=granter_id,
            action='BULK_GRANT_PERMISSIONS',
            entity_type='USER_PERMISSION',
            entity_id=grantee_id,
            changes={
                'permission_codes': permission_codes,
                'granted_count': results['granted_count'],
                'failed_count': results['failed_count'],
                'expires_at': expires_at.isoformat() if expires_at else None
            },
            success=results['success']
        )
        
        return results
    
    async def bulk_revoke_permissions(
        self,
        revoker_id: UUID,
        user_id: UUID,
        permission_codes: List[str]
    ) -> Dict[str, Any]:
        """Revoke multiple permissions from a user at once."""
        results = {
            'success': True,
            'revoked': [],
            'failed': [],
            'total': len(permission_codes),
            'revoked_count': 0,
            'failed_count': 0
        }
        
        for permission_code in permission_codes:
            try:
                result = await self.revoke_permission_from_user(
                    revoker_id=revoker_id,
                    user_id=user_id,
                    permission_code=permission_code
                )
                
                if result['success']:
                    results['revoked'].append({
                        'permission_code': permission_code,
                        'message': result['message']
                    })
                    results['revoked_count'] += 1
                else:
                    results['failed'].append({
                        'permission_code': permission_code,
                        'error': result['message']
                    })
                    results['failed_count'] += 1
                    
            except Exception as e:
                results['failed'].append({
                    'permission_code': permission_code,
                    'error': str(e)
                })
                results['failed_count'] += 1
        
        # If any failed, mark overall as failed
        if results['failed_count'] > 0:
            results['success'] = False
        
        # Log bulk operation
        await self.log_rbac_action(
            user_id=revoker_id,
            action='BULK_REVOKE_PERMISSIONS',
            entity_type='USER_PERMISSION',
            entity_id=user_id,
            changes={
                'permission_codes': permission_codes,
                'revoked_count': results['revoked_count'],
                'failed_count': results['failed_count']
            },
            success=results['success']
        )
        
        return results
    
    async def bulk_assign_roles_to_user(
        self,
        assigner_id: UUID,
        user_id: UUID,
        role_ids: List[UUID]
    ) -> Dict[str, Any]:
        """Assign multiple roles to a user at once."""
        results = {
            'success': True,
            'assigned': [],
            'failed': [],
            'total': len(role_ids),
            'assigned_count': 0,
            'failed_count': 0
        }
        
        for role_id in role_ids:
            try:
                success = await self.repository.assign_role_to_user(user_id, role_id)
                
                if success:
                    role = await self.repository.get_role_by_id(role_id)
                    results['assigned'].append({
                        'role_id': str(role_id),
                        'role_name': role.name if role else 'Unknown',
                        'message': f'Role {role.name if role else role_id} assigned successfully'
                    })
                    results['assigned_count'] += 1
                else:
                    results['failed'].append({
                        'role_id': str(role_id),
                        'error': 'Role assignment failed (possibly already assigned)'
                    })
                    results['failed_count'] += 1
                    
            except Exception as e:
                results['failed'].append({
                    'role_id': str(role_id),
                    'error': str(e)
                })
                results['failed_count'] += 1
        
        # If any failed, mark overall as failed
        if results['failed_count'] > 0:
            results['success'] = False
        
        # Invalidate user cache after bulk role assignment
        await rbac_cache.invalidate_user_permissions(user_id)
        
        # Log bulk operation
        await self.log_rbac_action(
            user_id=assigner_id,
            action='BULK_ASSIGN_ROLES',
            entity_type='USER_ROLE',
            entity_id=user_id,
            changes={
                'role_ids': [str(role_id) for role_id in role_ids],
                'assigned_count': results['assigned_count'],
                'failed_count': results['failed_count']
            },
            success=results['success']
        )
        
        return results
    
    async def bulk_remove_roles_from_user(
        self,
        remover_id: UUID,
        user_id: UUID,
        role_ids: List[UUID]
    ) -> Dict[str, Any]:
        """Remove multiple roles from a user at once."""
        results = {
            'success': True,
            'removed': [],
            'failed': [],
            'total': len(role_ids),
            'removed_count': 0,
            'failed_count': 0
        }
        
        for role_id in role_ids:
            try:
                success = await self.repository.remove_role_from_user(user_id, role_id)
                
                if success:
                    role = await self.repository.get_role_by_id(role_id)
                    results['removed'].append({
                        'role_id': str(role_id),
                        'role_name': role.name if role else 'Unknown',
                        'message': f'Role {role.name if role else role_id} removed successfully'
                    })
                    results['removed_count'] += 1
                else:
                    results['failed'].append({
                        'role_id': str(role_id),
                        'error': 'Role removal failed (possibly not assigned)'
                    })
                    results['failed_count'] += 1
                    
            except Exception as e:
                results['failed'].append({
                    'role_id': str(role_id),
                    'error': str(e)
                })
                results['failed_count'] += 1
        
        # If any failed, mark overall as failed
        if results['failed_count'] > 0:
            results['success'] = False
        
        # Invalidate user cache after bulk role removal
        await rbac_cache.invalidate_user_permissions(user_id)
        
        # Log bulk operation
        await self.log_rbac_action(
            user_id=remover_id,
            action='BULK_REMOVE_ROLES',
            entity_type='USER_ROLE',
            entity_id=user_id,
            changes={
                'role_ids': [str(role_id) for role_id in role_ids],
                'removed_count': results['removed_count'],
                'failed_count': results['failed_count']
            },
            success=results['success']
        )
        
        return results
    
    async def bulk_assign_permissions_to_role(
        self,
        assigner_id: UUID,
        role_id: UUID,
        permission_codes: List[str]
    ) -> Dict[str, Any]:
        """Assign multiple permissions to a role at once."""
        results = {
            'success': True,
            'assigned': [],
            'failed': [],
            'total': len(permission_codes),
            'assigned_count': 0,
            'failed_count': 0
        }
        
        for permission_code in permission_codes:
            try:
                # Get permission by code
                permission = await self.get_permission_by_code(permission_code)
                if not permission:
                    results['failed'].append({
                        'permission_code': permission_code,
                        'error': f'Permission {permission_code} not found'
                    })
                    results['failed_count'] += 1
                    continue
                
                success = await self.repository.assign_permission_to_role(role_id, permission.id)
                
                if success:
                    results['assigned'].append({
                        'permission_code': permission_code,
                        'permission_id': str(permission.id),
                        'message': f'Permission {permission_code} assigned successfully'
                    })
                    results['assigned_count'] += 1
                else:
                    results['failed'].append({
                        'permission_code': permission_code,
                        'error': 'Permission assignment failed (possibly already assigned)'
                    })
                    results['failed_count'] += 1
                    
            except Exception as e:
                results['failed'].append({
                    'permission_code': permission_code,
                    'error': str(e)
                })
                results['failed_count'] += 1
        
        # If any failed, mark overall as failed
        if results['failed_count'] > 0:
            results['success'] = False
        
        # Invalidate role cache after bulk permission assignment
        await rbac_cache.invalidate_role_permissions(role_id)
        
        # Log bulk operation
        await self.log_rbac_action(
            user_id=assigner_id,
            action='BULK_ASSIGN_PERMISSIONS_TO_ROLE',
            entity_type='ROLE_PERMISSION',
            entity_id=role_id,
            changes={
                'permission_codes': permission_codes,
                'assigned_count': results['assigned_count'],
                'failed_count': results['failed_count']
            },
            success=results['success']
        )
        
        return results