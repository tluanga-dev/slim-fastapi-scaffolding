from typing import Optional, List, Dict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.rental_return import RentalReturn
from ....domain.entities.rental_return_line import RentalReturnLine
from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.value_objects.transaction_type import TransactionType, TransactionStatus, PaymentStatus, PaymentMethod
from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade
from ....domain.value_objects.rental_return_type import ReturnStatus, ReturnLineStatus
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.rental_return_repository import RentalReturnRepository
from ....domain.repositories.rental_return_line_repository import RentalReturnLineRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.inspection_report_repository import InspectionReportRepository


class ReturnItem:
    """DTO for return item."""
    def __init__(
        self,
        inventory_unit_id: UUID,
        condition_grade: ConditionGrade,
        is_damaged: bool = False,
        damage_description: Optional[str] = None,
        damage_photos: Optional[List[str]] = None,
        missing_accessories: Optional[List[str]] = None,
        cleaning_required: bool = False
    ):
        self.inventory_unit_id = inventory_unit_id
        self.condition_grade = condition_grade
        self.is_damaged = is_damaged
        self.damage_description = damage_description
        self.damage_photos = damage_photos or []
        self.missing_accessories = missing_accessories or []
        self.cleaning_required = cleaning_required


class CompleteRentalReturnUseCase:
    """Use case for completing rental return process."""
    
    def __init__(
        self,
        transaction_repo: TransactionHeaderRepository,
        transaction_line_repo: TransactionLineRepository,
        rental_return_repo: RentalReturnRepository,
        rental_return_line_repo: RentalReturnLineRepository,
        inventory_unit_repo: InventoryUnitRepository,
        inspection_repo: InspectionReportRepository
    ):
        self.transaction_repo = transaction_repo
        self.transaction_line_repo = transaction_line_repo
        self.rental_return_repo = rental_return_repo
        self.rental_return_line_repo = rental_return_line_repo
        self.inventory_unit_repo = inventory_unit_repo
        self.inspection_repo = inspection_repo
    
    async def execute(
        self,
        transaction_id: UUID,
        return_items: List[ReturnItem],
        is_partial_return: bool = False,
        late_fee_waived: bool = False,
        damage_fee_percentage: Decimal = Decimal("80.00"),  # % of item value
        process_refund: bool = True,
        refund_method: Optional[PaymentMethod] = None,
        return_notes: Optional[str] = None,
        processed_by: Optional[str] = None
    ) -> Dict:
        """Complete rental return with inspection and fee calculation."""
        
        # 1. Get and validate transaction
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if transaction.transaction_type != TransactionType.RENTAL:
            raise ValueError("This use case only processes rental transactions")
        
        if transaction.status != TransactionStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot process return for transaction in {transaction.status.value} status"
            )
        
        # 2. Create rental return header
        return_number = await self._generate_return_number()
        
        rental_return = RentalReturn(
            return_number=return_number,
            transaction_id=transaction_id,
            customer_id=transaction.customer_id,
            return_date=date.today(),
            expected_return_date=transaction.rental_end_date,
            is_partial_return=is_partial_return,
            status=ReturnStatus.PENDING,
            deposit_amount=transaction.deposit_amount,
            created_by=processed_by
        )
        
        # 3. Process each return item
        return_lines = []
        total_late_fees = Decimal("0.00")
        total_damage_fees = Decimal("0.00")
        
        for idx, return_item in enumerate(return_items, 1):
            # Get inventory unit
            unit = await self.inventory_unit_repo.get_by_id(return_item.inventory_unit_id)
            if not unit:
                raise ValueError(f"Inventory unit {return_item.inventory_unit_id} not found")
            
            # Find transaction line for this unit
            transaction_lines = await self.transaction_line_repo.get_by_transaction_id(
                transaction_id
            )
            
            matching_line = None
            for line in transaction_lines:
                if line.inventory_unit_id == unit.id or (
                    line.item_id == unit.item_id and not line.inventory_unit_id
                ):
                    matching_line = line
                    break
            
            if not matching_line:
                raise ValueError(f"No transaction line found for unit {unit.serial_number}")
            
            # Calculate late fees
            days_late = max((date.today() - transaction.rental_end_date).days, 0)
            late_fee = Decimal("0.00")
            
            if days_late > 0 and not late_fee_waived:
                # Late fee is 10% of daily rate per day late
                daily_rate = matching_line.unit_price
                late_fee = daily_rate * Decimal("0.10") * days_late
                total_late_fees += late_fee
            
            # Calculate damage fees
            damage_fee = Decimal("0.00")
            if return_item.is_damaged:
                # Get item value
                item_value = matching_line.unit_price * Decimal("30")  # Assume 30x daily rate
                damage_fee = item_value * (damage_fee_percentage / 100)
                total_damage_fees += damage_fee
            
            # Create return line
            return_line = RentalReturnLine(
                return_id=rental_return.id,
                line_number=idx,
                transaction_line_id=matching_line.id,
                inventory_unit_id=unit.id,
                quantity_returned=Decimal("1"),
                condition_at_return=return_item.condition_grade,
                is_damaged=return_item.is_damaged,
                damage_description=return_item.damage_description,
                damage_assessment_photos=return_item.damage_photos,
                late_days=days_late,
                late_fee_amount=late_fee,
                damage_fee_amount=damage_fee,
                total_charges=late_fee + damage_fee,
                status=ReturnLineStatus.PENDING,
                created_by=processed_by
            )
            
            return_lines.append(return_line)
        
        # 4. Update rental return totals
        rental_return.total_late_fees = total_late_fees
        rental_return.total_damage_fees = total_damage_fees
        rental_return.total_fees = total_late_fees + total_damage_fees
        
        # Calculate deposit release
        deposit_release = rental_return.calculate_deposit_release()
        rental_return.deposit_released = deposit_release
        rental_return.deposit_forfeited = rental_return.deposit_amount - deposit_release
        
        # 5. Save rental return and lines
        rental_return = await self.rental_return_repo.create(rental_return)
        
        for line in return_lines:
            line.return_id = rental_return.id
            await self.rental_return_line_repo.create(line)
        
        # 6. Update inventory units
        for return_item in return_items:
            unit = await self.inventory_unit_repo.get_by_id(return_item.inventory_unit_id)
            
            # Update condition and status
            unit.condition_grade = return_item.condition_grade
            
            if return_item.cleaning_required:
                unit.current_status = InventoryStatus.CLEANING
            elif return_item.is_damaged:
                unit.current_status = InventoryStatus.REPAIR
            else:
                unit.current_status = InventoryStatus.AVAILABLE_RENT
            
            unit.last_inspection_date = date.today()
            unit.rental_count += 1
            
            # Add return notes
            return_note = (
                f"\n[RETURNED] {date.today()} - Condition: {return_item.condition_grade.value}"
            )
            if return_item.is_damaged:
                return_note += f"\nDamage: {return_item.damage_description}"
            
            unit.notes = (unit.notes or "") + return_note
            
            await self.inventory_unit_repo.update(unit.id, unit)
        
        # 7. Process transaction completion
        if not is_partial_return:
            # Complete the transaction
            transaction.complete_rental_return(
                actual_return_date=date.today(),
                updated_by=processed_by
            )
            
            # Process refund if applicable
            if process_refund and deposit_release > 0:
                refund_amount = deposit_release
                
                # If customer paid more than required, refund the difference
                if transaction.paid_amount > transaction.total_amount:
                    refund_amount += transaction.paid_amount - transaction.total_amount
                
                transaction.process_refund(
                    refund_amount=refund_amount,
                    reason="Rental return - deposit release",
                    refunded_by=processed_by
                )
        
        # Add return notes
        if return_notes:
            transaction.notes = (transaction.notes or "") + f"\n[RETURN] {return_notes}"
        
        # 8. Update return status
        rental_return.status = ReturnStatus.COMPLETED
        await self.rental_return_repo.update(rental_return.id, rental_return)
        
        # 9. Save transaction
        await self.transaction_repo.update(transaction.id, transaction)
        
        return {
            "transaction": transaction,
            "rental_return": rental_return,
            "return_lines": return_lines,
            "summary": {
                "items_returned": len(return_items),
                "late_fees": total_late_fees,
                "damage_fees": total_damage_fees,
                "total_charges": total_late_fees + total_damage_fees,
                "deposit_released": deposit_release,
                "deposit_forfeited": rental_return.deposit_forfeited,
                "is_complete": not is_partial_return
            }
        }
    
    async def _generate_return_number(self) -> str:
        """Generate unique return number."""
        # Format: RET-YYYYMMDD-XXXX
        today = datetime.utcnow().strftime("%Y%m%d")
        
        # Get count of returns today
        count = await self.rental_return_repo.count()  # Would need date filter
        
        return f"RET-{today}-{count + 1:04d}"