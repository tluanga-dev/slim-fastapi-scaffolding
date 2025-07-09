from typing import List

from src.domain.entities.role import Role
from src.domain.repositories.role_repository import RoleRepository


class ListRolesUseCase:
    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository
    
    async def execute(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Role]:
        """List all roles with their permissions"""
        
        if active_only:
            # Get all roles and filter active ones
            all_roles = await self.role_repository.list_with_permissions(skip, limit)
            return [role for role in all_roles if role.is_active]
        else:
            return await self.role_repository.list_with_permissions(skip, limit)