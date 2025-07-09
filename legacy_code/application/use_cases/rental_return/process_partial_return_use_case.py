from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from ....domain.entities.rental_return import RentalReturn
from ....domain.entities.rental_return_line import RentalReturnLine
from ....domain.repositories.rental_return_repository import RentalReturnRepository
from ....domain.repositories.rental_return_line_repository import RentalReturnLineRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.value_objects.rental_return_type import ReturnStatus
from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade


class ProcessPartialReturnUseCase:
    """Use case for processing partial returns with inventory updates."""
    
    def __init__(
        self,
        return_repository: RentalReturnRepository,
        line_repository: RentalReturnLineRepository,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository
    ):
        """Initialize use case with repositories."""
        self.return_repository = return_repository
        self.line_repository = line_repository
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
    
    async def execute(
        self,
        return_id: UUID,
        line_updates: List[Dict],  # [{"line_id": UUID, "returned_quantity": int, "condition_grade": str, "notes": str}]
        process_inventory: bool = True,
        updated_by: Optional[str] = None
    ) -> RentalReturn:
        """Execute the process partial return use case."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Validate return status
        if rental_return.return_status not in [ReturnStatus.INITIATED, ReturnStatus.IN_INSPECTION]:
            raise ValueError(f"Cannot process return in status {rental_return.return_status}")
        
        # 3. Get all return lines
        return_lines = await self.line_repository.get_by_return_id(return_id)
        line_map = {line.id: line for line in return_lines}
        
        # 4. Process each line update
        processed_lines = []
        inventory_updates = []
        
        for update in line_updates:
            line_id = update["line_id"]
            new_quantity = update.get("returned_quantity", 0)
            condition_grade = update.get("condition_grade")
            notes = update.get("notes")
            
            # Validate line exists
            if line_id not in line_map:
                raise ValueError(f"Return line {line_id} not found")
            
            line = line_map[line_id]
            
            # Validate quantity
            if new_quantity < 0:
                raise ValueError("Returned quantity cannot be negative")
            
            if new_quantity > line.original_quantity:
                raise ValueError(f"Cannot return {new_quantity} items, only {line.original_quantity} were originally rented")
            
            # Update return quantity
            if new_quantity != line.returned_quantity:
                line.update_return_quantity(new_quantity, updated_by)
            
            # Update condition if provided
            if condition_grade:
                try:
                    condition = ConditionGrade(condition_grade)
                    line.update_condition(condition, notes=notes, updated_by=updated_by)
                except ValueError:
                    raise ValueError(f"Invalid condition grade: {condition_grade}")
            
            # Mark line as processed if quantity > 0
            if new_quantity > 0 and not line.is_processed:
                line.process_line(updated_by or "system")
            
            # Update line in database
            updated_line = await self.line_repository.update(line)
            processed_lines.append(updated_line)
            
            # Prepare inventory updates if processing inventory
            if process_inventory and new_quantity > 0:
                inventory_updates.append({
                    "inventory_unit_id": line.inventory_unit_id,
                    "returned_quantity": new_quantity,
                    "condition_grade": line.condition_grade,
                    "line": line
                })
        
        # 5. Process inventory updates
        if process_inventory:
            await self._process_inventory_updates(inventory_updates, updated_by)
        
        # 6. Update return status based on completion
        total_expected = sum(line.original_quantity for line in return_lines)
        total_returned = sum(line.returned_quantity for line in processed_lines)
        
        if total_returned == total_expected:
            # All items returned - mark as completed
            rental_return.update_status(ReturnStatus.COMPLETED, updated_by)
        elif total_returned > 0:
            # Some items returned - mark as partially completed
            rental_return.update_status(ReturnStatus.PARTIALLY_COMPLETED, updated_by)
        
        # 7. Update rental return
        updated_return = await self.return_repository.update(rental_return)
        
        # 8. Reload with updated lines
        final_return = await self.return_repository.get_by_id(return_id)
        
        return final_return
    
    async def _process_inventory_updates(
        self,
        inventory_updates: List[Dict],
        updated_by: Optional[str]
    ) -> None:
        """Process inventory status updates for returned items."""
        
        for update in inventory_updates:
            inventory_unit_id = update["inventory_unit_id"]
            returned_quantity = update["returned_quantity"]
            condition_grade = update["condition_grade"]
            line = update["line"]
            
            # Get inventory unit
            inventory_unit = await self.inventory_repository.get_by_id(inventory_unit_id)
            if not inventory_unit:
                continue  # Skip if unit not found
            
            # Determine new inventory status based on condition
            if condition_grade == ConditionGrade.A:
                # Excellent condition - available for rent/sale
                if inventory_unit.item_id:
                    # Check what the item was originally available for
                    new_status = InventoryStatus.AVAILABLE_RENT  # Default to rent
                else:
                    new_status = InventoryStatus.AVAILABLE_SALE
            elif condition_grade in [ConditionGrade.B, ConditionGrade.C]:
                # Good/Fair condition - needs inspection or cleaning
                new_status = InventoryStatus.INSPECTION_PENDING
            else:  # ConditionGrade.D
                # Poor condition - needs repair
                new_status = InventoryStatus.MAINTENANCE_REQUIRED
            
            # Update inventory unit status and condition
            try:
                inventory_unit.update_status(new_status, updated_by)
                inventory_unit.update_condition(condition_grade, updated_by)
                await self.inventory_repository.update(inventory_unit)
            except Exception as e:
                # Log error but don't fail the entire operation
                print(f"Failed to update inventory unit {inventory_unit_id}: {e}")
            
            # Update stock levels if applicable
            try:
                stock_level = await self.stock_repository.get_by_item_location(
                    inventory_unit.item_id, 
                    inventory_unit.location_id
                )
                if stock_level:
                    # Return items to available stock
                    stock_level.receive_stock(returned_quantity, updated_by)
                    await self.stock_repository.update(stock_level)
            except Exception as e:
                # Log error but don't fail the entire operation
                print(f"Failed to update stock level for unit {inventory_unit_id}: {e}")
    
    async def validate_partial_return(
        self,
        return_id: UUID,
        proposed_quantities: Dict[UUID, int]  # {line_id: quantity}
    ) -> Dict:
        """Validate a proposed partial return without processing it."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Get return lines
        return_lines = await self.line_repository.get_by_return_id(return_id)
        line_map = {line.id: line for line in return_lines}
        
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "summary": {
                "total_lines": len(return_lines),
                "lines_being_returned": 0,
                "total_original_quantity": 0,
                "total_proposed_quantity": 0,
                "completion_percentage": 0.0
            }
        }
        
        lines_being_returned = 0
        total_original = 0
        total_proposed = 0
        
        # 3. Validate each proposed quantity
        for line_id, proposed_qty in proposed_quantities.items():
            if line_id not in line_map:
                validation_results["errors"].append(f"Line {line_id} not found")
                validation_results["is_valid"] = False
                continue
            
            line = line_map[line_id]
            total_original += line.original_quantity
            
            # Validate quantity
            if proposed_qty < 0:
                validation_results["errors"].append(f"Line {line_id}: quantity cannot be negative")
                validation_results["is_valid"] = False
            elif proposed_qty > line.original_quantity:
                validation_results["errors"].append(
                    f"Line {line_id}: cannot return {proposed_qty}, only {line.original_quantity} available"
                )
                validation_results["is_valid"] = False
            elif proposed_qty > 0:
                lines_being_returned += 1
                total_proposed += proposed_qty
                
                # Check if line was already processed
                if line.is_processed:
                    validation_results["warnings"].append(
                        f"Line {line_id}: already processed, will be reprocessed"
                    )
        
        # 4. Calculate summary
        validation_results["summary"].update({
            "lines_being_returned": lines_being_returned,
            "total_original_quantity": total_original,
            "total_proposed_quantity": total_proposed,
            "completion_percentage": (total_proposed / total_original * 100) if total_original > 0 else 0.0
        })
        
        # 5. Add warnings for edge cases
        if total_proposed == 0:
            validation_results["warnings"].append("No items are being returned")
        elif total_proposed == total_original:
            validation_results["warnings"].append("This will complete the entire return")
        
        return validation_results