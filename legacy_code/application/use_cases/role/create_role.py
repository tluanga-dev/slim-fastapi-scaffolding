from typing import Optional
from uuid import uuid4
from datetime import datetime

from src.domain.entities.role import Role
from src.domain.repositories.role_repository import RoleRepository
from src.domain.repositories.permission_repository import PermissionRepository


class CreateRoleUseCase:
    def __init__(self, role_repository: RoleRepository, permission_repository: PermissionRepository):
        self.role_repository = role_repository
        self.permission_repository = permission_repository
    
    async def execute(self, name: str, description: Optional[str] = None, permission_codes: Optional[list[str]] = None) -> Role:
        """Create a new role with optional permissions"""
        
        # Check if role with same name already exists
        existing_role = await self.role_repository.get_by_name(name)
        if existing_role:
            raise ValueError(f"Role with name '{name}' already exists")
        
        # Get permissions if codes provided
        permissions = []
        if permission_codes:
            permissions = await self.permission_repository.get_by_codes(permission_codes)
            if len(permissions) != len(permission_codes):
                found_codes = {p.code for p in permissions}
                missing_codes = set(permission_codes) - found_codes
                raise ValueError(f"Permissions not found: {', '.join(missing_codes)}")
        
        # Create role entity
        role = Role(
            id=uuid4(),
            name=name,
            description=description,
            permissions=permissions,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        # Save role
        created_role = await self.role_repository.create(role)
        
        # Set permissions if any
        if permissions:
            permission_ids = [p.id for p in permissions]
            await self.role_repository.set_permissions(created_role.id, permission_ids)
            # Reload to get permissions
            created_role = await self.role_repository.get_with_permissions(created_role.id)
        
        return created_role