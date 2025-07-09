from typing import Optional
from uuid import UUID
from datetime import datetime

from src.domain.entities.role import Role
from src.domain.repositories.role_repository import RoleRepository
from src.domain.repositories.permission_repository import PermissionRepository


class UpdateRoleUseCase:
    def __init__(self, role_repository: RoleRepository, permission_repository: PermissionRepository):
        self.role_repository = role_repository
        self.permission_repository = permission_repository
    
    async def execute(
        self, 
        role_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permission_codes: Optional[list[str]] = None,
        is_active: Optional[bool] = None
    ) -> Role:
        """Update an existing role"""
        
        # Get existing role
        role = await self.role_repository.get_with_permissions(role_id)
        if not role:
            raise ValueError(f"Role with id '{role_id}' not found")
        
        # Check if new name conflicts with another role
        if name and name != role.name:
            existing_role = await self.role_repository.get_by_name(name)
            if existing_role and existing_role.id != role_id:
                raise ValueError(f"Role with name '{name}' already exists")
        
        # Update fields if provided
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if is_active is not None:
            role.is_active = is_active
        
        role.updated_at = datetime.utcnow()
        
        # Update permissions if provided
        if permission_codes is not None:
            if permission_codes:
                # Get permissions by codes
                permissions = await self.permission_repository.get_by_codes(permission_codes)
                if len(permissions) != len(permission_codes):
                    found_codes = {p.code for p in permissions}
                    missing_codes = set(permission_codes) - found_codes
                    raise ValueError(f"Permissions not found: {', '.join(missing_codes)}")
                
                permission_ids = [p.id for p in permissions]
            else:
                # Empty list means remove all permissions
                permission_ids = []
            
            await self.role_repository.set_permissions(role_id, permission_ids)
        
        # Update role
        updated_role = await self.role_repository.update(role)
        
        # Reload to get latest permissions
        return await self.role_repository.get_with_permissions(updated_role.id)