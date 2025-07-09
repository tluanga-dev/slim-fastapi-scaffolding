from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from .models import User, Role, Permission, user_roles_table, role_permissions_table
# from app.shared.pagination import Page


class AuthRepository:
    """Repository for authentication data access operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    # User operations
    async def create_user(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_username_or_email(self, username_or_email: str) -> Optional[User]:
        """Get user by username or email."""
        query = select(User).where(
            or_(
                User.username == username_or_email,
                User.email == username_or_email
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_with_roles(self, user_id: UUID) -> Optional[User]:
        """Get user with their roles."""
        query = select(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_inactive: bool = False
    ) -> List[User]:
        """List users with optional filters and sorting."""
        query = select(User)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(User.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_user_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(User, sort_by)))
        else:
            query = query.order_by(asc(getattr(User, sort_by)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_paginated_users(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_inactive: bool = False
    ) -> List[User]:
        """Get paginated users."""
        query = select(User)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(User.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_user_filters(query, filters)
        
        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order_by(desc(getattr(User, sort_by)))
        else:
            query = query.order_by(asc(getattr(User, sort_by)))
        
        # Calculate pagination
        skip = (page - 1) * page_size
        limit = page_size
        
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update_user(self, user_id: UUID, update_data: dict) -> Optional[User]:
        """Update existing user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Soft delete user by setting is_active to False."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        await self.session.commit()
        
        return True
    
    async def count_users(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_inactive: bool = False
    ) -> int:
        """Count users matching filters."""
        query = select(func.count()).select_from(User)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(User.is_active == True)
        
        # Apply additional filters
        if filters:
            query = self._apply_user_filters(query, filters)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def exists_by_username(self, username: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a user with the given username exists."""
        query = select(func.count()).select_from(User).where(
            User.username == username
        )
        
        if exclude_id:
            query = query.where(User.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_email(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a user with the given email exists."""
        query = select(func.count()).select_from(User).where(
            User.email == email
        )
        
        if exclude_id:
            query = query.where(User.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    # Role operations
    async def create_role(self, role_data: dict) -> Role:
        """Create a new role."""
        role = Role(**role_data)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role
    
    async def get_role_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID."""
        query = select(Role).where(Role.id == role_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        query = select(Role).where(Role.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_role_with_permissions(self, role_id: UUID) -> Optional[Role]:
        """Get role with its permissions."""
        query = select(Role).options(
            selectinload(Role.permissions)
        ).where(Role.id == role_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Role]:
        """List roles."""
        query = select(Role)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Role.is_active == True)
        
        # Apply sorting
        query = query.order_by(Role.name)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_role(self, role_id: UUID, update_data: dict) -> Optional[Role]:
        """Update existing role."""
        role = await self.get_role_by_id(role_id)
        if not role:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(role, key):
                setattr(role, key, value)
        
        await self.session.commit()
        await self.session.refresh(role)
        
        return role
    
    async def delete_role(self, role_id: UUID) -> bool:
        """Soft delete role by setting is_active to False."""
        role = await self.get_role_by_id(role_id)
        if not role:
            return False
        
        role.is_active = False
        await self.session.commit()
        
        return True
    
    # Permission operations
    async def create_permission(self, permission_data: dict) -> Permission:
        """Create a new permission."""
        permission = Permission(**permission_data)
        self.session.add(permission)
        await self.session.commit()
        await self.session.refresh(permission)
        return permission
    
    async def get_permission_by_id(self, permission_id: UUID) -> Optional[Permission]:
        """Get permission by ID."""
        query = select(Permission).where(Permission.id == permission_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_permission_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name."""
        query = select(Permission).where(Permission.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_permission_by_resource_action(self, resource: str, action: str) -> Optional[Permission]:
        """Get permission by resource and action."""
        query = select(Permission).where(
            and_(
                Permission.resource == resource,
                Permission.action == action
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Permission]:
        """List permissions."""
        query = select(Permission)
        
        # Apply base filters
        if not include_inactive:
            query = query.where(Permission.is_active == True)
        
        # Apply sorting
        query = query.order_by(Permission.resource, Permission.action)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_permission(self, permission_id: UUID, update_data: dict) -> Optional[Permission]:
        """Update existing permission."""
        permission = await self.get_permission_by_id(permission_id)
        if not permission:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(permission, key):
                setattr(permission, key, value)
        
        await self.session.commit()
        await self.session.refresh(permission)
        
        return permission
    
    async def delete_permission(self, permission_id: UUID) -> bool:
        """Soft delete permission by setting is_active to False."""
        permission = await self.get_permission_by_id(permission_id)
        if not permission:
            return False
        
        permission.is_active = False
        await self.session.commit()
        
        return True
    
    # User-Role operations
    async def assign_role_to_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Assign a role to a user."""
        # Check if assignment already exists
        query = select(user_roles_table).where(
            and_(
                user_roles_table.c.user_id == user_id,
                user_roles_table.c.role_id == role_id
            )
        )
        result = await self.session.execute(query)
        existing = result.fetchone()
        
        if existing:
            return False  # Already assigned
        
        # Create new assignment
        insert_stmt = user_roles_table.insert().values(user_id=user_id, role_id=role_id)
        await self.session.execute(insert_stmt)
        await self.session.commit()
        
        return True
    
    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Remove a role from a user."""
        # Check if assignment exists
        query = select(user_roles_table).where(
            and_(
                user_roles_table.c.user_id == user_id,
                user_roles_table.c.role_id == role_id
            )
        )
        result = await self.session.execute(query)
        existing = result.fetchone()
        
        if not existing:
            return False  # Assignment doesn't exist
        
        # Delete assignment
        delete_stmt = user_roles_table.delete().where(
            and_(
                user_roles_table.c.user_id == user_id,
                user_roles_table.c.role_id == role_id
            )
        )
        await self.session.execute(delete_stmt)
        await self.session.commit()
        
        return True
    
    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """Get all roles for a user."""
        query = select(Role).join(user_roles_table).where(user_roles_table.c.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_user_permissions(self, user_id: UUID) -> List[Permission]:
        """Get all permissions for a user through their roles."""
        query = select(Permission).join(role_permissions_table).join(user_roles_table).where(
            user_roles_table.c.user_id == user_id
        ).distinct()
        result = await self.session.execute(query)
        return result.scalars().all()
    
    # Role-Permission operations
    async def assign_permission_to_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Assign a permission to a role."""
        # Check if assignment already exists
        query = select(role_permissions_table).where(
            and_(
                role_permissions_table.c.role_id == role_id,
                role_permissions_table.c.permission_id == permission_id
            )
        )
        result = await self.session.execute(query)
        existing = result.fetchone()
        
        if existing:
            return False  # Already assigned
        
        # Create new assignment
        insert_stmt = role_permissions_table.insert().values(role_id=role_id, permission_id=permission_id)
        await self.session.execute(insert_stmt)
        await self.session.commit()
        
        return True
    
    async def remove_permission_from_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Remove a permission from a role."""
        # Check if assignment exists
        query = select(role_permissions_table).where(
            and_(
                role_permissions_table.c.role_id == role_id,
                role_permissions_table.c.permission_id == permission_id
            )
        )
        result = await self.session.execute(query)
        existing = result.fetchone()
        
        if not existing:
            return False  # Assignment doesn't exist
        
        # Delete assignment
        delete_stmt = role_permissions_table.delete().where(
            and_(
                role_permissions_table.c.role_id == role_id,
                role_permissions_table.c.permission_id == permission_id
            )
        )
        await self.session.execute(delete_stmt)
        await self.session.commit()
        
        return True
    
    async def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions for a role."""
        query = select(Permission).join(role_permissions_table).where(role_permissions_table.c.role_id == role_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    def _apply_user_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to user query."""
        for key, value in filters.items():
            if value is None:
                continue
            
            if key == "username":
                query = query.where(User.username.ilike(f"%{value}%"))
            elif key == "email":
                query = query.where(User.email.ilike(f"%{value}%"))
            elif key == "first_name":
                query = query.where(User.first_name.ilike(f"%{value}%"))
            elif key == "last_name":
                query = query.where(User.last_name.ilike(f"%{value}%"))
            elif key == "status":
                query = query.where(User.status == value)
            elif key == "role":
                query = query.where(User.role == value)
            elif key == "is_verified":
                query = query.where(User.is_verified == value)
            elif key == "is_active":
                query = query.where(User.is_active == value)
            elif key == "created_after":
                query = query.where(User.created_at >= value)
            elif key == "created_before":
                query = query.where(User.created_at <= value)
            elif key == "last_login_after":
                query = query.where(User.last_login >= value)
            elif key == "last_login_before":
                query = query.where(User.last_login <= value)
            elif key == "search":
                search_pattern = f"%{value}%"
                query = query.where(
                    or_(
                        User.username.ilike(search_pattern),
                        User.email.ilike(search_pattern),
                        User.first_name.ilike(search_pattern),
                        User.last_name.ilike(search_pattern)
                    )
                )
        
        return query