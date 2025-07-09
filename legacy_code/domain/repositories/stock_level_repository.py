from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities.stock_level import StockLevel


class StockLevelRepository(ABC):
    """Abstract repository interface for StockLevel entity."""
    
    @abstractmethod
    async def create(self, stock_level: StockLevel) -> StockLevel:
        """Create a new stock level record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, stock_level_id: UUID) -> Optional[StockLevel]:
        """Get stock level by ID."""
        pass
    
    @abstractmethod
    async def get_by_item_location(self, item_id: UUID, location_id: UUID) -> Optional[StockLevel]:
        """Get stock level for a specific Item at a location."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        location_id: Optional[UUID] = None,
        item_id: Optional[UUID] = None,
        low_stock_only: bool = False,
        is_active: Optional[bool] = True
    ) -> Tuple[List[StockLevel], int]:
        """List stock levels with filters and pagination."""
        pass
    
    @abstractmethod
    async def update(self, stock_level: StockLevel) -> StockLevel:
        """Update existing stock level."""
        pass
    
    @abstractmethod
    async def delete(self, stock_level_id: UUID) -> bool:
        """Soft delete stock level."""
        pass
    
    @abstractmethod
    async def get_or_create(self, item_id: UUID, location_id: UUID) -> StockLevel:
        """Get existing stock level or create new one."""
        pass
    
    @abstractmethod
    async def get_total_stock_by_item(self, item_id: UUID) -> dict:
        """Get total stock quantities across all locations for an Item."""
        pass
    
    @abstractmethod
    async def get_stock_by_location(self, location_id: UUID) -> List[StockLevel]:
        """Get all stock levels for a location."""
        pass
    
    @abstractmethod
    async def get_low_stock_items(
        self,
        location_id: Optional[UUID] = None,
        include_zero: bool = True
    ) -> List[StockLevel]:
        """Get items that are at or below reorder point."""
        pass
    
    @abstractmethod
    async def get_overstock_items(self, location_id: Optional[UUID] = None) -> List[StockLevel]:
        """Get items that exceed maximum stock level."""
        pass
    
    @abstractmethod
    async def check_availability(
        self,
        item_id: UUID,
        quantity: int,
        location_id: Optional[UUID] = None
    ) -> Tuple[bool, int]:
        """Check if quantity is available. Returns (is_available, total_available)."""
        pass
    
    @abstractmethod
    async def get_stock_valuation(self, location_id: Optional[UUID] = None) -> dict:
        """Get stock valuation summary."""
        pass
    
    @abstractmethod
    async def transfer_stock(
        self,
        item_id: UUID,
        from_location_id: UUID,
        to_location_id: UUID,
        quantity: int,
        updated_by: Optional[str] = None
    ) -> Tuple[StockLevel, StockLevel]:
        """Transfer stock between locations. Returns (from_stock, to_stock)."""
        pass