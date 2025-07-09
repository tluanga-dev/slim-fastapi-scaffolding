from typing import Optional, List
from datetime import datetime
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
from ....domain.repositories.customer_repository import CustomerRepository


class CheckoutRentalUseCase:
    """Use case for checking out a rental booking (confirming and processing payment)."""
    
    def __init__(
        self,
        transaction_repo: TransactionHeaderRepository,
        transaction_line_repo: TransactionLineRepository,
        inventory_unit_repo: InventoryUnitRepository,
        customer_repo: CustomerRepository
    ):
        self.transaction_repo = transaction_repo
        self.transaction_line_repo = transaction_line_repo
        self.inventory_unit_repo = inventory_unit_repo
        self.customer_repo = customer_repo
    
    async def execute(
        self,
        transaction_id: UUID,
        payment_amount: Decimal,
        payment_method: PaymentMethod,
        payment_reference: Optional[str] = None,
        collect_full_payment: bool = False,
        additional_notes: Optional[str] = None,
        processed_by: Optional[str] = None
    ) -> TransactionHeader:
        """Process rental checkout - confirm booking and process payment."""
        
        # 1. Get and validate transaction
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if transaction.transaction_type != TransactionType.RENTAL:
            raise ValueError("This use case only processes rental transactions")
        
        if transaction.status not in [TransactionStatus.DRAFT, TransactionStatus.PENDING]:
            raise ValueError(
                f"Cannot checkout transaction in {transaction.status.value} status"
            )
        
        # 2. Validate customer
        customer = await self.customer_repo.get_by_id(transaction.customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        if not customer.is_active:
            raise ValueError("Customer account is inactive")
        
        # Check blacklist status
        if customer.blacklist_status != "CLEAR":
            raise ValueError(
                f"Cannot process checkout. Customer is {customer.blacklist_status}"
            )
        
        # 3. Load transaction lines
        lines = await self.transaction_line_repo.get_by_transaction_id(transaction_id)
        transaction._lines = lines
        
        # 4. Validate payment amount
        if collect_full_payment:
            required_payment = transaction.total_amount
        else:
            # Minimum payment is deposit amount
            required_payment = transaction.deposit_amount
        
        if payment_amount < required_payment:
            raise ValueError(
                f"Insufficient payment. Required: ${required_payment}, "
                f"Provided: ${payment_amount}"
            )
        
        # 5. Get all reserved inventory units and update their status
        inventory_updates = []
        for line in lines:
            if line.line_type == "PRODUCT" and line.inventory_unit_id:
                unit = await self.inventory_unit_repo.get_by_id(line.inventory_unit_id)
                if unit:
                    inventory_updates.append(unit)
        
        # If no specific units, get units by item
        if not inventory_updates:
            for line in lines:
                if line.line_type == "PRODUCT" and line.item_id:
                    units = await self._get_reserved_units_for_transaction(
                        transaction_id, line.item_id, int(line.quantity)
                    )
                    inventory_updates.extend(units)
        
        # 6. Process payment
        transaction.apply_payment(
            amount=payment_amount,
            payment_method=payment_method,
            payment_reference=payment_reference,
            updated_by=processed_by
        )
        
        # 7. Update transaction status
        if transaction.rental_start_date == datetime.utcnow().date():
            # If rental starts today, move to IN_PROGRESS
            transaction.update_status(TransactionStatus.IN_PROGRESS, processed_by)
            
            # Update inventory status to RENTED
            for unit in inventory_updates:
                unit.current_status = InventoryStatus.RENTED
                unit.notes = (unit.notes or "") + f"\n[RENTED] {datetime.utcnow()}"
                await self.inventory_unit_repo.update(unit.id, unit)
        else:
            # Otherwise, confirm the booking
            transaction.update_status(TransactionStatus.CONFIRMED, processed_by)
        
        # 8. Add checkout notes
        if additional_notes:
            transaction.notes = (transaction.notes or "") + f"\n[CHECKOUT] {additional_notes}"
        
        checkout_note = (
            f"\n[CHECKOUT] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} "
            f"by {processed_by or 'System'} - "
            f"Payment: ${payment_amount} via {payment_method.value}"
        )
        transaction.notes = (transaction.notes or "") + checkout_note
        
        # 9. Update customer lifetime value
        customer.lifetime_value += payment_amount
        customer.last_transaction_date = datetime.utcnow()
        await self.customer_repo.update(customer.id, customer)
        
        # 10. Save transaction
        await self.transaction_repo.update(transaction.id, transaction)
        
        return transaction
    
    async def _get_reserved_units_for_transaction(
        self,
        transaction_id: UUID,
        item_id: UUID,
        quantity: int
    ) -> List[InventoryUnit]:
        """Get inventory units reserved for this transaction."""
        # This would typically check a reservation table or notes
        # For now, we'll get units with RESERVED_RENT status at the location
        units = await self.inventory_unit_repo.get_by_status_and_item(
            InventoryStatus.RESERVED_RENT, item_id
        )
        
        # Filter units that mention this transaction in notes
        reserved_units = []
        for unit in units:
            if unit.notes and str(transaction_id) in unit.notes:
                reserved_units.append(unit)
                if len(reserved_units) >= quantity:
                    break
        
        return reserved_units