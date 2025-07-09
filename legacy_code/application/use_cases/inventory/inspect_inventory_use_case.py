from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.value_objects.item_type import ConditionGrade, InventoryStatus


class InspectInventoryUseCase:
    """Use case for inspecting inventory units."""
    
    def __init__(self, inventory_repository: InventoryUnitRepository):
        """Initialize use case with repository."""
        self.inventory_repository = inventory_repository
    
    async def execute(
        self,
        inventory_id: UUID,
        condition_grade: ConditionGrade,
        inspection_notes: str,
        passed_inspection: bool = True,
        inspected_by: Optional[str] = None,
        photos: Optional[List[str]] = None
    ) -> InventoryUnit:
        """Execute the use case to inspect an inventory unit."""
        # Get the inventory unit
        inventory_unit = await self.inventory_repository.get_by_id(inventory_id)
        if not inventory_unit:
            raise ValueError(f"Inventory unit with id {inventory_id} not found")
        
        # Check if unit is in inspectable status
        inspectable_statuses = [
            InventoryStatus.INSPECTION_PENDING,
            InventoryStatus.AVAILABLE_RENT,
            InventoryStatus.AVAILABLE_SALE,
            InventoryStatus.DAMAGED,
            InventoryStatus.REPAIR
        ]
        
        if inventory_unit.current_status not in inspectable_statuses:
            raise ValueError(
                f"Cannot inspect unit in status {inventory_unit.current_status.value}. "
                f"Unit must be in one of: {', '.join(s.value for s in inspectable_statuses)}"
            )
        
        # Save old condition grade before updating
        old_grade = inventory_unit.condition_grade
        
        # Update inspection details and condition grade
        inventory_unit.record_inspection(condition_grade, inspection_notes, inspected_by)
        
        # Build inspection notes
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        inspection_result = "PASSED" if passed_inspection else "FAILED"
        
        inspection_note = f"\n[{timestamp}] Inspection {inspection_result} by {inspected_by or 'System'}:"
        inspection_note += f"\n  - Condition: {old_grade.value} -> {condition_grade.value}"
        inspection_note += f"\n  - Notes: {inspection_notes}"
        
        if photos:
            inspection_note += f"\n  - Photos: {', '.join(photos)}"
        
        # Update notes
        current_notes = inventory_unit.notes or ""
        inventory_unit.notes = current_notes + inspection_note
        
        # Update status based on inspection result
        if not passed_inspection:
            if condition_grade == ConditionGrade.D:
                # Failed inspection with grade D means damaged
                if inventory_unit.can_transition_to(InventoryStatus.DAMAGED):
                    inventory_unit.update_status(InventoryStatus.DAMAGED, inspected_by)
            else:
                # Failed inspection but not damaged means repair needed
                if inventory_unit.can_transition_to(InventoryStatus.REPAIR):
                    inventory_unit.update_status(InventoryStatus.REPAIR, inspected_by)
        else:
            # Passed inspection
            if inventory_unit.current_status == InventoryStatus.INSPECTION_PENDING:
                # Determine next status based on Item settings
                # For now, default to available for rent
                if inventory_unit.can_transition_to(InventoryStatus.AVAILABLE_RENT):
                    inventory_unit.update_status(InventoryStatus.AVAILABLE_RENT, inspected_by)
        
        # Save updated inventory unit
        updated_unit = await self.inventory_repository.update(inventory_unit.id, inventory_unit)
        
        return updated_unit
    
    async def bulk_inspect(
        self,
        inventory_ids: List[UUID],
        condition_grade: ConditionGrade,
        inspection_notes: str,
        passed_inspection: bool = True,
        inspected_by: Optional[str] = None
    ) -> List[InventoryUnit]:
        """Inspect multiple inventory units at once."""
        updated_units = []
        
        for inventory_id in inventory_ids:
            try:
                unit = await self.execute(
                    inventory_id=inventory_id,
                    condition_grade=condition_grade,
                    inspection_notes=inspection_notes,
                    passed_inspection=passed_inspection,
                    inspected_by=inspected_by
                )
                updated_units.append(unit)
            except ValueError as e:
                # Log error but continue with other units
                # In production, we might want to collect errors and return them
                print(f"Error inspecting unit {inventory_id}: {str(e)}")
                continue
        
        return updated_units