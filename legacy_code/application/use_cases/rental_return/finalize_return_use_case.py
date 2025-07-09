from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from ....domain.entities.rental_return import RentalReturn
from ....domain.entities.rental_return_line import RentalReturnLine
from ....domain.repositories.rental_return_repository import RentalReturnRepository
from ....domain.repositories.rental_return_line_repository import RentalReturnLineRepository
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.value_objects.rental_return_type import ReturnStatus
from ....domain.value_objects.transaction_type import TransactionStatus
from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade


class FinalizeReturnUseCase:
    """Use case for finalizing rental returns."""
    
    def __init__(
        self,
        return_repository: RentalReturnRepository,
        line_repository: RentalReturnLineRepository,
        transaction_repository: TransactionHeaderRepository,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository
    ):
        """Initialize use case with repositories."""
        self.return_repository = return_repository
        self.line_repository = line_repository
        self.transaction_repository = transaction_repository
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
    
    async def execute(
        self,
        return_id: UUID,
        finalized_by: str,
        force_finalize: bool = False,
        finalization_notes: Optional[str] = None
    ) -> RentalReturn:
        """Execute the finalize return use case."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Validate return can be finalized
        if not force_finalize:
            validation_result = await self._validate_can_finalize(rental_return)
            if not validation_result["can_finalize"]:
                raise ValueError(f"Cannot finalize return: {'; '.join(validation_result['errors'])}")
        
        # 3. Get all return lines
        return_lines = await self.line_repository.get_by_return_id(return_id)
        if not return_lines:
            raise ValueError("No return lines found")
        
        # 4. Validate all lines are processed
        unprocessed_lines = [line for line in return_lines if not line.is_processed and line.returned_quantity > 0]
        if unprocessed_lines and not force_finalize:
            raise ValueError(f"Cannot finalize: {len(unprocessed_lines)} lines are not processed")
        
        # 5. Process final inventory updates
        inventory_updates = []
        for line in return_lines:
            if line.returned_quantity > 0:
                inventory_updates.append({
                    "inventory_unit_id": line.inventory_unit_id,
                    "returned_quantity": line.returned_quantity,
                    "condition_grade": line.condition_grade,
                    "line": line
                })
        
        if inventory_updates:
            await self._finalize_inventory_updates(inventory_updates, finalized_by)
        
        # 6. Calculate final fees and totals
        total_fees = await self._calculate_final_totals(return_lines)
        
        # 7. Update rental return status
        rental_return.finalize_return(
            finalized_by=finalized_by,
            total_late_fee=total_fees["late_fee"],
            total_damage_fee=total_fees["damage_fee"],
            total_cleaning_fee=total_fees["cleaning_fee"],
            total_replacement_fee=total_fees["replacement_fee"],
            notes=finalization_notes
        )
        
        # 8. Update rental transaction status if fully returned
        rental_transaction = await self.transaction_repository.get_by_id(rental_return.rental_transaction_id)
        if rental_transaction:
            # Check if all items from the rental have been returned
            is_fully_returned = await self._check_rental_fully_returned(rental_return.rental_transaction_id)
            if is_fully_returned:
                rental_transaction.update_status(TransactionStatus.COMPLETED, finalized_by)
                await self.transaction_repository.update(rental_transaction)
        
        # 9. Update return in database
        finalized_return = await self.return_repository.update(rental_return)
        
        return finalized_return
    
    async def _validate_can_finalize(self, rental_return: RentalReturn) -> Dict:
        """Validate if a return can be finalized."""
        errors = []
        warnings = []
        
        # Check return status
        if rental_return.return_status == ReturnStatus.COMPLETED:
            errors.append("Return is already completed")
        elif rental_return.return_status == ReturnStatus.CANCELLED:
            errors.append("Return is cancelled")
        
        # Check if inspection is required and completed
        return_lines = await self.line_repository.get_by_return_id(rental_return.id)
        
        # Check for damage fees without inspection approval
        has_damage_fees = any(
            (line.damage_fee and line.damage_fee > 0) or 
            (line.cleaning_fee and line.cleaning_fee > 0) or 
            (line.replacement_fee and line.replacement_fee > 0)
            for line in return_lines
        )
        
        if has_damage_fees:
            # Should have approved inspection reports
            from ....domain.repositories.inspection_report_repository import InspectionReportRepository
            # This would require dependency injection - for now we'll just warn
            warnings.append("Return has damage fees but inspection approval not verified")
        
        # Check for unprocessed lines
        unprocessed_lines = [line for line in return_lines if not line.is_processed and line.returned_quantity > 0]
        if unprocessed_lines:
            errors.append(f"{len(unprocessed_lines)} lines are not processed")
        
        # Check for missing condition assessments
        lines_without_condition = [line for line in return_lines if not line.condition_grade and line.returned_quantity > 0]
        if lines_without_condition:
            warnings.append(f"{len(lines_without_condition)} lines missing condition assessment")
        
        return {
            "can_finalize": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _finalize_inventory_updates(
        self,
        inventory_updates: List[Dict],
        finalized_by: str
    ) -> None:
        """Finalize inventory status updates for returned items."""
        
        for update in inventory_updates:
            inventory_unit_id = update["inventory_unit_id"]
            returned_quantity = update["returned_quantity"]
            condition_grade = update["condition_grade"]
            line = update["line"]
            
            try:
                # Get inventory unit
                inventory_unit = await self.inventory_repository.get_by_id(inventory_unit_id)
                if not inventory_unit:
                    continue
                
                # Determine final inventory status based on condition and fees
                final_status = self._determine_final_inventory_status(line, condition_grade)
                
                # Update inventory unit
                inventory_unit.update_status(final_status, finalized_by)
                if condition_grade:
                    inventory_unit.update_condition(condition_grade, finalized_by)
                
                await self.inventory_repository.update(inventory_unit)
                
                # Update stock levels
                if inventory_unit.item_id and inventory_unit.location_id:
                    stock_level = await self.stock_repository.get_by_item_location(
                        inventory_unit.item_id,
                        inventory_unit.location_id
                    )
                    if stock_level:
                        # Add back to appropriate stock category based on status
                        if final_status in [InventoryStatus.AVAILABLE_RENT, InventoryStatus.AVAILABLE_SALE]:
                            stock_level.receive_stock(returned_quantity, finalized_by)
                        else:
                            # Items needing maintenance/repair don't go to available stock immediately
                            pass
                        
                        await self.stock_repository.update(stock_level)
                
            except Exception as e:
                # Log error but continue with other updates
                print(f"Failed to finalize inventory for unit {inventory_unit_id}: {e}")
    
    def _determine_final_inventory_status(
        self,
        line: RentalReturnLine,
        condition_grade: Optional[ConditionGrade]
    ) -> InventoryStatus:
        """Determine final inventory status based on condition and fees."""
        
        # If there are replacement fees, item is likely damaged beyond repair
        if line.replacement_fee and line.replacement_fee > 0:
            return InventoryStatus.DAMAGED
        
        # If there are significant damage fees, needs maintenance
        if line.damage_fee and line.damage_fee > 50:  # Configurable threshold
            return InventoryStatus.MAINTENANCE_REQUIRED
        
        # If cleaning fee, needs cleaning
        if line.cleaning_fee and line.cleaning_fee > 0:
            return InventoryStatus.CLEANING_REQUIRED
        
        # Based on condition grade
        if condition_grade:
            if condition_grade == ConditionGrade.A:
                return InventoryStatus.AVAILABLE_RENT
            elif condition_grade == ConditionGrade.B:
                return InventoryStatus.AVAILABLE_RENT  # Good condition still rentable
            elif condition_grade == ConditionGrade.C:
                return InventoryStatus.INSPECTION_PENDING  # Fair condition needs review
            else:  # ConditionGrade.D
                return InventoryStatus.MAINTENANCE_REQUIRED
        
        # Default to inspection pending if no clear condition
        return InventoryStatus.INSPECTION_PENDING
    
    async def _calculate_final_totals(self, return_lines: List[RentalReturnLine]) -> Dict:
        """Calculate final fee totals for the return."""
        
        total_late_fee = Decimal("0.00")
        total_damage_fee = Decimal("0.00")
        total_cleaning_fee = Decimal("0.00")
        total_replacement_fee = Decimal("0.00")
        
        for line in return_lines:
            if line.late_fee:
                total_late_fee += line.late_fee
            if line.damage_fee:
                total_damage_fee += line.damage_fee
            if line.cleaning_fee:
                total_cleaning_fee += line.cleaning_fee
            if line.replacement_fee:
                total_replacement_fee += line.replacement_fee
        
        return {
            "late_fee": total_late_fee,
            "damage_fee": total_damage_fee,
            "cleaning_fee": total_cleaning_fee,
            "replacement_fee": total_replacement_fee,
            "total": total_late_fee + total_damage_fee + total_cleaning_fee + total_replacement_fee
        }
    
    async def _check_rental_fully_returned(self, rental_transaction_id: UUID) -> bool:
        """Check if all items from a rental transaction have been returned."""
        
        # Get all returns for this transaction
        all_returns = await self.return_repository.get_by_transaction_id(rental_transaction_id)
        
        # Get original rental transaction lines
        from ....domain.repositories.transaction_line_repository import TransactionLineRepository
        # This would need to be injected - simplified for now
        
        # For now, assume if there's at least one completed return, the rental is done
        # In a full implementation, we'd compare original quantities vs returned quantities
        completed_returns = [r for r in all_returns if r.return_status == ReturnStatus.COMPLETED]
        
        return len(completed_returns) > 0
    
    async def get_finalization_preview(self, return_id: UUID) -> Dict:
        """Get a preview of what will happen when finalizing a return."""
        
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        return_lines = await self.line_repository.get_by_return_id(return_id)
        
        # Calculate totals
        totals = await self._calculate_final_totals(return_lines)
        
        # Validation
        validation = await self._validate_can_finalize(rental_return)
        
        # Inventory impact
        inventory_changes = []
        for line in return_lines:
            if line.returned_quantity > 0:
                final_status = self._determine_final_inventory_status(line, line.condition_grade)
                inventory_changes.append({
                    "inventory_unit_id": str(line.inventory_unit_id),
                    "current_status": "RENTED",  # Assumed
                    "new_status": final_status.value,
                    "condition_grade": line.condition_grade.value if line.condition_grade else None,
                    "returned_quantity": line.returned_quantity
                })
        
        return {
            "return_id": str(return_id),
            "current_status": rental_return.return_status.value,
            "can_finalize": validation["can_finalize"],
            "validation_errors": validation["errors"],
            "validation_warnings": validation["warnings"],
            "fee_totals": {
                "late_fee": float(totals["late_fee"]),
                "damage_fee": float(totals["damage_fee"]),
                "cleaning_fee": float(totals["cleaning_fee"]),
                "replacement_fee": float(totals["replacement_fee"]),
                "total_fees": float(totals["total"])
            },
            "inventory_changes": inventory_changes,
            "lines_processed": sum(1 for line in return_lines if line.is_processed),
            "total_lines": len(return_lines)
        }