from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod
)
from ....domain.value_objects.item_type import InventoryStatus


class ProcessPaymentUseCase:
    """Use case for processing payment for a transaction."""
    
    def __init__(
        self,
        transaction_repository: TransactionHeaderRepository,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository
    ):
        """Initialize use case with repositories."""
        self.transaction_repository = transaction_repository
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
    
    async def execute(
        self,
        transaction_id: UUID,
        payment_amount: Decimal,
        payment_method: PaymentMethod,
        payment_reference: Optional[str] = None,
        process_inventory: bool = True,
        processed_by: Optional[str] = None
    ) -> TransactionHeader:
        """Execute the use case to process payment."""
        # Get transaction
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction with id {transaction_id} not found")
        
        # Validate transaction status
        if transaction.status not in [TransactionStatus.PENDING, TransactionStatus.CONFIRMED]:
            raise ValueError(
                f"Cannot process payment for transaction in {transaction.status.value} status"
            )
        
        # Validate payment amount
        if payment_amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if payment_amount > transaction.balance_due:
            raise ValueError(
                f"Payment amount (${payment_amount}) exceeds balance due (${transaction.balance_due})"
            )
        
        # Apply payment
        transaction.apply_payment(
            amount=payment_amount,
            payment_method=payment_method,
            payment_reference=payment_reference,
            updated_by=processed_by
        )
        
        # Update transaction status based on payment
        if transaction.is_paid_in_full:
            if transaction.status == TransactionStatus.PENDING:
                transaction.update_status(TransactionStatus.CONFIRMED, processed_by)
            
            # For rentals, move to IN_PROGRESS if start date is today or past
            if (transaction.is_rental and 
                transaction.rental_start_date and 
                transaction.rental_start_date <= datetime.now().date()):
                transaction.update_status(TransactionStatus.IN_PROGRESS, processed_by)
                
                # Update inventory status for rentals
                if process_inventory:
                    await self._process_rental_inventory(transaction, processed_by)
            
            # For sales, complete the transaction
            elif transaction.is_sale:
                transaction.update_status(TransactionStatus.COMPLETED, processed_by)
                
                # Process sale inventory
                if process_inventory:
                    await self._process_sale_inventory(transaction, processed_by)
        
        # Save updated transaction
        updated_transaction = await self.transaction_repository.update(transaction)
        
        return updated_transaction
    
    async def _process_sale_inventory(
        self,
        transaction: TransactionHeader,
        processed_by: Optional[str] = None
    ):
        """Process inventory for completed sale."""
        if not transaction._lines:
            # Load lines if not already loaded
            from ....infrastructure.repositories.transaction_line_repository import SQLAlchemyTransactionLineRepository
            from ....infrastructure.database import get_session
            
            async for session in get_session():
                line_repo = SQLAlchemyTransactionLineRepository(session)
                transaction._lines = await line_repo.get_by_transaction(transaction.id)
        
        for line in transaction._lines:
            if line.line_type == "PRODUCT" and line.item_id:
                # Update stock levels
                stock_level = await self.stock_repository.get_by_item_location(
                    line.item_id,
                    transaction.location_id
                )
                
                if stock_level:
                    # Ship the reserved stock
                    stock_level.confirm_sale(int(line.quantity), processed_by)
                    await self.stock_repository.update(stock_level)
                
                # If specific inventory units were assigned, mark them as sold
                if line.inventory_unit_id:
                    unit = await self.inventory_repository.get_by_id(line.inventory_unit_id)
                    if unit:
                        unit.update_status(InventoryStatus.SOLD, processed_by)
                        await self.inventory_repository.update(unit)
    
    async def _process_rental_inventory(
        self,
        transaction: TransactionHeader,
        processed_by: Optional[str] = None
    ):
        """Process inventory for rental start."""
        if not transaction._lines:
            # Load lines if not already loaded
            from ....infrastructure.repositories.transaction_line_repository import SQLAlchemyTransactionLineRepository
            from ....infrastructure.database import get_session
            
            async for session in get_session():
                line_repo = SQLAlchemyTransactionLineRepository(session)
                transaction._lines = await line_repo.get_by_transaction(transaction.id)
        
        for line in transaction._lines:
            if line.line_type == "PRODUCT" and line.inventory_unit_id:
                # Update specific inventory unit status
                unit = await self.inventory_repository.get_by_id(line.inventory_unit_id)
                if unit:
                    if unit.current_status == InventoryStatus.RESERVED_RENT:
                        unit.update_status(InventoryStatus.RENTED, processed_by)
                        unit.increment_rental_stats(line.rental_days, processed_by)
                        await self.inventory_repository.update(unit)
            elif line.line_type == "PRODUCT" and line.item_id:
                # Reserve general units if not already assigned
                available_units = await self.inventory_repository.get_available_units(
                    item_id=line.item_id,
                    location_id=transaction.location_id
                )
                
                rentable_units = [
                    u for u in available_units 
                    if u.current_status == InventoryStatus.AVAILABLE_RENT
                ]
                
                # Assign and update units
                for i in range(min(int(line.quantity), len(rentable_units))):
                    unit = rentable_units[i]
                    unit.update_status(InventoryStatus.RENTED, processed_by)
                    unit.increment_rental_stats(line.rental_days, processed_by)
                    await self.inventory_repository.update(unit)
                    
                    # Update line with assigned unit
                    line.inventory_unit_id = unit.id
                    from ....infrastructure.repositories.transaction_line_repository import SQLAlchemyTransactionLineRepository
                    from ....infrastructure.database import get_session
                    
                    async for session in get_session():
                        line_repo = SQLAlchemyTransactionLineRepository(session)
                        await line_repo.update(line)