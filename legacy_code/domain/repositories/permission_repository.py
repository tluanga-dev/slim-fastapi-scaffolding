from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.role import Permission
from src.domain.repositories.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    """Repository interface for Permission entities"""
    
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Permission]:
        """Get a permission by its code"""
        pass
    
    @abstractmethod
    async def get_by_codes(self, codes: List[str]) -> List[Permission]:
        """Get multiple permissions by their codes"""
        pass
    
    @abstractmethod
    async def list_by_role(self, role_id: UUID) -> List[Permission]:
        """List all permissions for a specific role"""
        pass