from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.item import Item
from src.domain.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    """Repository interface for Item entity."""
    
    @abstractmethod
    async def get_by_item_id(self, item_id: UUID) -> Optional[Item]:
        """Get item by item_id."""
        pass
    
    @abstractmethod
    async def get_by_sku(self, sku: str) -> Optional[Item]:
        """Get item by SKU."""
        pass
    
    @abstractmethod
    async def get_by_barcode(self, barcode: str) -> Optional[Item]:
        """Get item by barcode."""
        pass
    
    @abstractmethod
    async def get_by_category_id(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items by category."""
        pass
    
    @abstractmethod
    async def get_by_brand_id(self, brand_id: UUID, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items by brand."""
        pass
    
    @abstractmethod
    async def get_rentable_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items that can be rented."""
        pass
    
    @abstractmethod
    async def get_saleable_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items that can be sold."""
        pass
    
    @abstractmethod
    async def search_by_name(self, name_pattern: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """Search items by name pattern."""
        pass
    
    @abstractmethod
    async def search_by_sku(self, sku_pattern: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """Search items by SKU pattern."""
        pass
    
    @abstractmethod
    async def get_rentable_items_with_search(
        self, 
        search: Optional[str] = None, 
        category_id: Optional[UUID] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Item]:
        """Get rentable items with optional search and category filter."""
        pass
    
    @abstractmethod
    async def count_rentable_items(
        self, 
        search: Optional[str] = None, 
        category_id: Optional[UUID] = None
    ) -> int:
        """Count rentable items with optional search and category filter."""
        pass