from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.role import Role
from src.domain.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Repository interface for Role entities"""
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get a role by its name"""
        pass
    
    @abstractmethod
    async def get_with_permissions(self, id: UUID) -> Optional[Role]:
        """Get a role with its permissions loaded"""
        pass
    
    @abstractmethod
    async def list_with_permissions(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """List all roles with their permissions loaded"""
        pass
    
    @abstractmethod
    async def add_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        """Add a permission to a role"""
        pass
    
    @abstractmethod
    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        """Remove a permission from a role"""
        pass
    
    @abstractmethod
    async def set_permissions(self, role_id: UUID, permission_ids: List[UUID]) -> bool:
        """Set the complete list of permissions for a role"""
        pass