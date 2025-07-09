from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod
)
from ....domain.value_objects.item_type import InventoryStatus
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository


class CancelRentalBookingUseCase:
    """Use case for cancelling a rental booking."""
    
    def __init__(
        self,
        transaction_repo: TransactionHeaderRepository,
        transaction_line_repo: TransactionLineRepository,
        inventory_unit_repo: InventoryUnitRepository
    ):
        self.transaction_repo = transaction_repo
        self.transaction_line_repo = transaction_line_repo
        self.inventory_unit_repo = inventory_unit_repo
    
    async def execute(
        self,
        transaction_id: UUID,
        cancellation_reason: str,
        refund_percentage: Decimal = Decimal("100.00"),
        cancellation_fee: Optional[Decimal] = None,
        refund_method: Optional[PaymentMethod] = None,
        refund_reference: Optional[str] = None,
        cancelled_by: Optional[str] = None
    ) -> TransactionHeader:
        """Cancel a rental booking and process refund."""
        
        # 1. Get and validate transaction
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if transaction.transaction_type != TransactionType.RENTAL:
            raise ValueError("Can only cancel rental transactions")
        
        # Check if can be cancelled
        if transaction.status in [TransactionStatus.COMPLETED, TransactionStatus.CANCELLED]:
            raise ValueError(
                f"Cannot cancel transaction in {transaction.status.value} status"
            )
        
        # 2. Calculate cancellation policy
        days_until_rental = (transaction.rental_start_date - date.today()).days
        
        # Apply cancellation policy based on days until rental
        if refund_percentage is None:
            if days_until_rental >= 7:
                refund_percentage = Decimal("100.00")  # Full refund
                cancellation_fee = Decimal("0.00")
            elif days_until_rental >= 3:
                refund_percentage = Decimal("50.00")   # 50% refund
            elif days_until_rental >= 1:
                refund_percentage = Decimal("25.00")   # 25% refund
            else:
                refund_percentage = Decimal("0.00")    # No refund
        
        # 3. Get all reserved inventory units
        lines = await self.transaction_line_repo.get_by_transaction_id(transaction_id)
        reserved_units = []
        
        for line in lines:
            if line.line_type == "PRODUCT":
                # Get units mentioned in transaction notes or by item
                units = await self._get_reserved_units_for_line(
                    transaction_id, line.item_id, int(line.quantity)
                )
                reserved_units.extend(units)
        
        # 4. Release inventory units
        for unit in reserved_units:
            if unit.current_status in [InventoryStatus.RESERVED_RENT, InventoryStatus.RENTED]:
                # Only release if still reserved/rented for this transaction
                unit.current_status = InventoryStatus.AVAILABLE_RENT
                unit.notes = (unit.notes or "") + (
                    f"\n[CANCELLED] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"Booking cancelled"
                )
                await self.inventory_unit_repo.update(unit.id, unit)
        
        # 5. Calculate refund amount
        refund_amount = Decimal("0.00")
        
        if transaction.paid_amount > 0:
            # Calculate base refund
            refund_amount = transaction.paid_amount * (refund_percentage / 100)
            
            # Apply cancellation fee if specified
            if cancellation_fee and cancellation_fee > 0:
                refund_amount = max(refund_amount - cancellation_fee, Decimal("0.00"))
        
        # 6. Cancel the transaction
        transaction.cancel_transaction(
            reason=cancellation_reason,
            cancelled_by=cancelled_by
        )
        
        # 7. Process refund if applicable
        if refund_amount > 0 and refund_method:
            # Create refund note
            refund_note = (
                f"\n[REFUND] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - "
                f"Amount: ${refund_amount} ({refund_percentage}% of ${transaction.paid_amount})"
            )
            
            if cancellation_fee:
                refund_note += f" - Cancellation fee: ${cancellation_fee}"
            
            if refund_reference:
                refund_note += f" - Ref: {refund_reference}"
            
            transaction.notes = (transaction.notes or "") + refund_note
            
            # Update payment status
            transaction.payment_status = PaymentStatus.REFUNDED
            transaction.paid_amount = transaction.paid_amount - refund_amount
        
        # 8. Add cancellation details
        cancellation_note = (
            f"\nCancellation Policy Applied: "
            f"{days_until_rental} days before rental = {refund_percentage}% refund"
        )
        transaction.notes = (transaction.notes or "") + cancellation_note
        
        # 9. Save transaction
        await self.transaction_repo.update(transaction.id, transaction)
        
        return transaction
    
    async def _get_reserved_units_for_line(
        self,
        transaction_id: UUID,
        item_id: UUID,
        quantity: int
    ) -> List[InventoryUnit]:
        """Get inventory units reserved for this transaction line."""
        # Get units with RESERVED_RENT status for this item
        units = await self.inventory_unit_repo.get_by_status_and_item(
            InventoryStatus.RESERVED_RENT, item_id
        )
        
        # Filter units that mention this transaction
        reserved_units = []
        for unit in units:
            if unit.notes and str(transaction_id) in unit.notes:
                reserved_units.append(unit)
                if len(reserved_units) >= quantity:
                    break
        
        # Also check RENTED status if transaction was already in progress
        if len(reserved_units) < quantity:
            rented_units = await self.inventory_unit_repo.get_by_status_and_item(
                InventoryStatus.RENTED, item_id
            )
            
            for unit in rented_units:
                if unit.notes and str(transaction_id) in unit.notes:
                    reserved_units.append(unit)
                    if len(reserved_units) >= quantity:
                        break
        
        return reserved_units