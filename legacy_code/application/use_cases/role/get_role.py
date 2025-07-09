from uuid import UUID

from src.domain.entities.role import Role
from src.domain.repositories.role_repository import RoleRepository


class GetRoleUseCase:
    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository
    
    async def execute(self, role_id: UUID) -> Role:
        """Get a role by ID with its permissions"""
        
        role = await self.role_repository.get_with_permissions(role_id)
        if not role:
            raise ValueError(f"Role with id '{role_id}' not found")
        
        return role