from typing import Optional
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.value_objects.transaction_type import TransactionStatus
from ....domain.value_objects.item_type import InventoryStatus


class CancelTransactionUseCase:
    """Use case for cancelling a transaction."""
    
    def __init__(
        self,
        transaction_repository: TransactionHeaderRepository,
        line_repository: TransactionLineRepository,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository
    ):
        """Initialize use case with repositories."""
        self.transaction_repository = transaction_repository
        self.line_repository = line_repository
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
    
    async def execute(
        self,
        transaction_id: UUID,
        cancellation_reason: str,
        release_inventory: bool = True,
        cancelled_by: Optional[str] = None
    ) -> TransactionHeader:
        """Execute the use case to cancel a transaction."""
        # Get transaction
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction with id {transaction_id} not found")
        
        # Validate can be cancelled
        if transaction.status == TransactionStatus.COMPLETED:
            raise ValueError(
                "Cannot cancel completed transaction. Process a return or refund instead."
            )
        
        if transaction.status == TransactionStatus.CANCELLED:
            raise ValueError("Transaction is already cancelled")
        
        # Get transaction lines
        lines = await self.line_repository.get_by_transaction(transaction_id)
        
        # Release inventory if requested
        if release_inventory:
            await self._release_reserved_inventory(transaction, lines, cancelled_by)
        
        # Cancel the transaction
        transaction.cancel_transaction(cancellation_reason, cancelled_by)
        
        # Save updated transaction
        updated_transaction = await self.transaction_repository.update(transaction)
        
        return updated_transaction
    
    async def _release_reserved_inventory(
        self,
        transaction: TransactionHeader,
        lines: list,
        cancelled_by: Optional[str] = None
    ):
        """Release any reserved inventory."""
        for line in lines:
            if line.line_type == "PRODUCT":
                # Release specific inventory units
                if line.inventory_unit_id:
                    unit = await self.inventory_repository.get_by_id(line.inventory_unit_id)
                    if unit and unit.current_status in [
                        InventoryStatus.RESERVED_SALE,
                        InventoryStatus.RESERVED_RENT
                    ]:
                        # Determine target status based on transaction type
                        if transaction.is_rental:
                            new_status = InventoryStatus.AVAILABLE_RENT
                        else:
                            new_status = InventoryStatus.AVAILABLE_SALE
                        
                        unit.update_status(new_status, cancelled_by)
                        await self.inventory_repository.update(unit)
                
                # Release stock reservations
                elif line.item_id and transaction.is_sale:
                    stock_level = await self.stock_repository.get_by_item_location(
                        line.item_id,
                        transaction.location_id
                    )
                    
                    if stock_level and stock_level.quantity_reserved >= int(line.quantity):
                        stock_level.release_reservation(int(line.quantity), cancelled_by)
                        await self.stock_repository.update(stock_level)