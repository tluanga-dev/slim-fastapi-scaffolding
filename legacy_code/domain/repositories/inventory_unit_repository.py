from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import date

from ..entities.inventory_unit import InventoryUnit
from ..value_objects.item_type import InventoryStatus, ConditionGrade


class InventoryUnitRepository(ABC):
    """Abstract repository interface for InventoryUnit entity."""
    
    @abstractmethod
    async def create(self, inventory_unit: InventoryUnit) -> InventoryUnit:
        """Create a new inventory unit."""
        pass
    
    @abstractmethod
    async def get_by_id(self, inventory_id: UUID) -> Optional[InventoryUnit]:
        """Get inventory unit by ID."""
        pass
    
    @abstractmethod
    async def get_by_code(self, inventory_code: str) -> Optional[InventoryUnit]:
        """Get inventory unit by inventory code."""
        pass
    
    @abstractmethod
    async def get_by_serial_number(self, serial_number: str) -> Optional[InventoryUnit]:
        """Get inventory unit by serial number."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        sku_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[InventoryStatus] = None,
        condition_grade: Optional[ConditionGrade] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[InventoryUnit], int]:
        """List inventory units with filters and pagination."""
        pass
    
    @abstractmethod
    async def update(self, inventory_unit: InventoryUnit) -> InventoryUnit:
        """Update existing inventory unit."""
        pass
    
    @abstractmethod
    async def delete(self, inventory_id: UUID) -> bool:
        """Soft delete inventory unit."""
        pass
    
    @abstractmethod
    async def exists_by_code(self, inventory_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if an inventory unit with the given code exists."""
        pass
    
    @abstractmethod
    async def exists_by_serial(self, serial_number: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if an inventory unit with the given serial number exists."""
        pass
    
    @abstractmethod
    async def get_available_units(
        self,
        sku_id: UUID,
        location_id: Optional[UUID] = None,
        condition_grade: Optional[ConditionGrade] = None
    ) -> List[InventoryUnit]:
        """Get available units for a SKU."""
        pass
    
    @abstractmethod
    async def get_units_by_status(
        self,
        status: InventoryStatus,
        location_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[InventoryUnit], int]:
        """Get inventory units by status."""
        pass
    
    @abstractmethod
    async def get_units_needing_inspection(
        self,
        days_since_last: int = 30,
        location_id: Optional[UUID] = None
    ) -> List[InventoryUnit]:
        """Get units that need inspection."""
        pass
    
    @abstractmethod
    async def get_rental_history(
        self,
        inventory_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[dict]:
        """Get rental history for an inventory unit."""
        pass
    
    @abstractmethod
    async def count_by_status(self, location_id: Optional[UUID] = None) -> dict:
        """Get count of inventory units by status."""
        pass
    
    @abstractmethod
    async def count_by_condition(self, location_id: Optional[UUID] = None) -> dict:
        """Get count of inventory units by condition grade."""
        pass
    
    @abstractmethod
    async def get_high_value_units(
        self,
        min_value: float,
        location_id: Optional[UUID] = None
    ) -> List[InventoryUnit]:
        """Get high value inventory units."""
        pass
    
    @abstractmethod
    async def get_by_sku_and_location(
        self,
        sku_id: UUID,
        location_id: UUID
    ) -> List[InventoryUnit]:
        """Get all inventory units for a SKU at a specific location."""
        pass
    
    @abstractmethod
    async def get_by_status_and_sku(
        self,
        status: InventoryStatus,
        sku_id: UUID
    ) -> List[InventoryUnit]:
        """Get inventory units by status and SKU."""
        pass