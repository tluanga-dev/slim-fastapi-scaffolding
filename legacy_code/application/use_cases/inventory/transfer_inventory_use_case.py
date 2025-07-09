from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.location_repository import LocationRepository
from ....domain.value_objects.item_type import InventoryStatus


class TransferInventoryUseCase:
    """Use case for transferring inventory between locations."""
    
    def __init__(
        self,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository,
        location_repository: LocationRepository
    ):
        """Initialize use case with repositories."""
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
        self.location_repository = location_repository
    
    async def execute(
        self,
        inventory_id: UUID,
        to_location_id: UUID,
        transfer_reason: str,
        transferred_by: Optional[str] = None
    ) -> InventoryUnit:
        """Execute the use case to transfer a single inventory unit."""
        # Get the inventory unit
        inventory_unit = await self.inventory_repository.get_by_id(inventory_id)
        if not inventory_unit:
            raise ValueError(f"Inventory unit with id {inventory_id} not found")
        
        # Verify destination location exists
        to_location = await self.location_repository.get_by_id(to_location_id)
        if not to_location:
            raise ValueError(f"Destination location with id {to_location_id} not found")
        
        # Check if unit can be transferred
        transferable_statuses = [
            InventoryStatus.AVAILABLE_SALE,
            InventoryStatus.AVAILABLE_RENT,
            InventoryStatus.DAMAGED,
            InventoryStatus.REPAIR
        ]
        
        if inventory_unit.current_status not in transferable_statuses:
            raise ValueError(
                f"Cannot transfer unit in status {inventory_unit.current_status.value}. "
                f"Unit must be in one of: {', '.join(s.value for s in transferable_statuses)}"
            )
        
        # Store original location
        from_location_id = inventory_unit.location_id
        
        # Don't transfer to same location
        if from_location_id == to_location_id:
            raise ValueError("Cannot transfer to the same location")
        
        # Update stock levels
        await self._update_stock_levels_for_transfer(
            inventory_unit.item_id,
            from_location_id,
            to_location_id,
            transferred_by
        )
        
        # Update inventory unit location
        inventory_unit.update_location(to_location_id, transferred_by)
        
        # Add transfer notes
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        transfer_note = f"\n[{timestamp}] Transferred from location {from_location_id} to {to_location_id}"
        transfer_note += f"\n  - Reason: {transfer_reason}"
        transfer_note += f"\n  - By: {transferred_by or 'System'}"
        
        current_notes = inventory_unit.notes or ""
        inventory_unit.notes = current_notes + transfer_note
        
        # Save updated inventory unit
        updated_unit = await self.inventory_repository.update(inventory_unit.id, inventory_unit)
        
        return updated_unit
    
    async def bulk_transfer(
        self,
        inventory_ids: List[UUID],
        to_location_id: UUID,
        transfer_reason: str,
        transferred_by: Optional[str] = None
    ) -> Tuple[List[InventoryUnit], List[dict]]:
        """Transfer multiple inventory units at once."""
        transferred_units = []
        errors = []
        
        # Verify destination location exists first
        to_location = await self.location_repository.get_by_id(to_location_id)
        if not to_location:
            raise ValueError(f"Destination location with id {to_location_id} not found")
        
        for inventory_id in inventory_ids:
            try:
                unit = await self.execute(
                    inventory_id=inventory_id,
                    to_location_id=to_location_id,
                    transfer_reason=transfer_reason,
                    transferred_by=transferred_by
                )
                transferred_units.append(unit)
            except ValueError as e:
                errors.append({
                    'inventory_id': str(inventory_id),
                    'error': str(e)
                })
        
        return transferred_units, errors
    
    async def transfer_by_sku(
        self,
        item_id: UUID,
        from_location_id: UUID,
        to_location_id: UUID,
        quantity: int,
        transfer_reason: str,
        transferred_by: Optional[str] = None,
        condition_grade: Optional[str] = None
    ) -> List[InventoryUnit]:
        """Transfer a quantity of items by SKU."""
        # Get available units at source location
        available_units = await self.inventory_repository.get_available_units(
            item_id=item_id,
            location_id=from_location_id,
            condition_grade=condition_grade
        )
        
        if len(available_units) < quantity:
            raise ValueError(
                f"Insufficient units available. Requested: {quantity}, "
                f"Available: {len(available_units)}"
            )
        
        # Transfer the requested quantity
        units_to_transfer = available_units[:quantity]
        transferred_units = []
        
        for unit in units_to_transfer:
            transferred_unit = await self.execute(
                inventory_id=unit.id,
                to_location_id=to_location_id,
                transfer_reason=transfer_reason,
                transferred_by=transferred_by
            )
            transferred_units.append(transferred_unit)
        
        return transferred_units
    
    async def _update_stock_levels_for_transfer(
        self,
        item_id: UUID,
        from_location_id: UUID,
        to_location_id: UUID,
        updated_by: Optional[str] = None
    ):
        """Update stock levels for both locations during transfer."""
        # Use the stock repository's transfer method
        await self.stock_repository.transfer_stock(
            item_id=item_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            quantity=1,
            updated_by=updated_by
        )