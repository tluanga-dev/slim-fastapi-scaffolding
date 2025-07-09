from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.brand import Brand


class BrandRepository(ABC):
    """Abstract repository interface for Brand entity."""
    
    @abstractmethod
    async def create(self, brand: Brand) -> Brand:
        """Create a new brand."""
        pass
    
    @abstractmethod
    async def get_by_id(self, brand_id: UUID) -> Optional[Brand]:
        """Get brand by ID."""
        pass
    
    @abstractmethod
    async def get_by_name(self, brand_name: str) -> Optional[Brand]:
        """Get brand by name."""
        pass
    
    @abstractmethod
    async def get_by_code(self, brand_code: str) -> Optional[Brand]:
        """Get brand by code."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[Brand]:
        """List brands with optional search and filters."""
        pass
    
    @abstractmethod
    async def update(self, brand: Brand) -> Brand:
        """Update existing brand."""
        pass
    
    @abstractmethod
    async def delete(self, brand_id: UUID) -> bool:
        """Soft delete brand by setting is_active to False."""
        pass
    
    @abstractmethod
    async def count(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> int:
        """Count brands matching filters."""
        pass
    
    @abstractmethod
    async def exists_by_name(self, brand_name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a brand with the given name exists."""
        pass
    
    @abstractmethod
    async def exists_by_code(self, brand_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a brand with the given code exists."""
        pass
    
    @abstractmethod
    async def has_products(self, brand_id: UUID) -> bool:
        """Check if a brand has any products assigned to it."""
        pass