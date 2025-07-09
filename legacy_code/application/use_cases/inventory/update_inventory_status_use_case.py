from typing import Optional
from uuid import UUID
from datetime import datetime

from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.value_objects.item_type import InventoryStatus


class UpdateInventoryStatusUseCase:
    """Use case for updating inventory unit status."""
    
    def __init__(
        self,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository
    ):
        """Initialize use case with repositories."""
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
    
    async def execute(
        self,
        inventory_id: UUID,
        new_status: InventoryStatus,
        reason: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> InventoryUnit:
        """Execute the use case to update inventory status."""
        # Get the inventory unit
        inventory_unit = await self.inventory_repository.get_by_id(inventory_id)
        if not inventory_unit:
            raise ValueError(f"Inventory unit with id {inventory_id} not found")
        
        # Check if transition is valid
        if not inventory_unit.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {inventory_unit.current_status.value} "
                f"to {new_status.value}"
            )
        
        # Store old status for stock level updates
        old_status = inventory_unit.current_status
        
        # Update status
        inventory_unit.update_status(new_status, updated_by)
        
        # Add notes if reason provided
        if reason:
            current_notes = inventory_unit.notes or ""
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            status_note = f"\n[{timestamp}] Status changed from {old_status.value} to {new_status.value}: {reason}"
            inventory_unit.notes = current_notes + status_note
        
        # Save updated inventory unit
        updated_unit = await self.inventory_repository.update(inventory_unit.id, inventory_unit)
        
        # Update stock levels based on status change
        await self._update_stock_levels(
            inventory_unit.sku_id,
            inventory_unit.location_id,
            old_status,
            new_status,
            updated_by
        )
        
        return updated_unit
    
    async def _update_stock_levels(
        self,
        sku_id: UUID,
        location_id: UUID,
        old_status: InventoryStatus,
        new_status: InventoryStatus,
        updated_by: Optional[str] = None
    ):
        """Update stock levels based on status change."""
        stock_level = await self.stock_repository.get_by_sku_location(sku_id, location_id)
        if not stock_level:
            return
        
        # Determine stock level changes
        if self._is_available_status(old_status) and not self._is_available_status(new_status):
            # Moving from available to unavailable
            stock_level.reserve_stock(1, updated_by)
        elif not self._is_available_status(old_status) and self._is_available_status(new_status):
            # Moving from unavailable to available
            stock_level.release_stock(1, updated_by)
        elif self._is_damaged_status(new_status) and not self._is_damaged_status(old_status):
            # Moving to damaged
            stock_level.mark_damaged(1, updated_by)
        elif self._is_damaged_status(old_status) and not self._is_damaged_status(new_status):
            # Moving from damaged
            stock_level.unmark_damaged(1, updated_by)
        
        # Save stock level changes
        await self.stock_repository.update(stock_level)
    
    def _is_available_status(self, status: InventoryStatus) -> bool:
        """Check if status represents available inventory."""
        return status in [
            InventoryStatus.AVAILABLE_SALE,
            InventoryStatus.AVAILABLE_RENT
        ]
    
    def _is_damaged_status(self, status: InventoryStatus) -> bool:
        """Check if status represents damaged inventory."""
        return status == InventoryStatus.DAMAGED