from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.item_repository import ItemRepository
from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade


class CreateInventoryUnitUseCase:
    """Use case for creating a new inventory unit."""
    
    def __init__(
        self,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository,
        item_repository: ItemRepository
    ):
        """Initialize use case with repositories."""
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
        self.item_repository = item_repository
    
    async def execute(
        self,
        inventory_code: str,
        item_id: UUID,
        location_id: UUID,
        serial_number: Optional[str] = None,
        current_status: InventoryStatus = InventoryStatus.AVAILABLE_SALE,
        condition_grade: ConditionGrade = ConditionGrade.A,
        purchase_date: Optional[date] = None,
        purchase_cost: Optional[Decimal] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> InventoryUnit:
        """Execute the use case to create a new inventory unit."""
        # Verify Item exists
        item = await self.item_repository.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found")
        
        # Check if Item requires serialization
        if item and hasattr(item, 'is_serialized') and item.is_serialized:
            if not serial_number:
                raise ValueError("Serial number is required for serialized items")
        
        # Check if inventory code already exists
        if await self.inventory_repository.exists_by_code(inventory_code):
            raise ValueError(f"Inventory unit with code '{inventory_code}' already exists")
        
        # Check if serial number already exists
        if serial_number and await self.inventory_repository.exists_by_serial(serial_number):
            raise ValueError(f"Inventory unit with serial number '{serial_number}' already exists")
        
        # Determine initial status based on Item settings
        if current_status == InventoryStatus.AVAILABLE_SALE and item.is_rentable and not item.is_saleable:
            current_status = InventoryStatus.AVAILABLE_RENT
        elif current_status == InventoryStatus.AVAILABLE_RENT and item.is_saleable and not item.is_rentable:
            current_status = InventoryStatus.AVAILABLE_SALE
        
        # Create inventory unit entity
        inventory_unit = InventoryUnit(
            inventory_code=inventory_code,
            item_id=item_id,
            location_id=location_id,
            serial_number=serial_number,
            current_status=current_status,
            condition_grade=condition_grade,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            current_value=purchase_cost,
            notes=notes,
            created_by=created_by
        )
        
        # Save to repository
        created_unit = await self.inventory_repository.create(inventory_unit)
        
        # Update stock levels
        stock_level = await self.stock_repository.get_or_create(item_id, location_id)
        stock_level.receive_stock(1, created_by)
        await self.stock_repository.update(stock_level)
        
        return created_unit