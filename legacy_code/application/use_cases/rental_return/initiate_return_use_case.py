from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from ....domain.entities.rental_return import RentalReturn
from ....domain.entities.rental_return_line import RentalReturnLine
from ....domain.repositories.rental_return_repository import RentalReturnRepository
from ....domain.repositories.rental_return_line_repository import RentalReturnLineRepository
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.value_objects.rental_return_type import ReturnType, ReturnStatus
from ....domain.value_objects.transaction_type import TransactionType, TransactionStatus


class InitiateReturnUseCase:
    """Use case for initiating a rental return."""
    
    def __init__(
        self,
        return_repository: RentalReturnRepository,
        line_repository: RentalReturnLineRepository,
        transaction_repository: TransactionHeaderRepository,
        transaction_line_repository: TransactionLineRepository,
        inventory_repository: InventoryUnitRepository
    ):
        """Initialize use case with repositories."""
        self.return_repository = return_repository
        self.line_repository = line_repository
        self.transaction_repository = transaction_repository
        self.transaction_line_repository = transaction_line_repository
        self.inventory_repository = inventory_repository
    
    async def execute(
        self,
        rental_transaction_id: UUID,
        return_date: date,
        return_items: List[Dict],  # [{"inventory_unit_id": UUID, "quantity": int}]
        return_location_id: Optional[UUID] = None,
        return_type: ReturnType = ReturnType.FULL,
        notes: Optional[str] = None,
        processed_by: Optional[str] = None
    ) -> RentalReturn:
        """Execute the initiate return use case."""
        
        # 1. Validate rental transaction exists and is active
        rental_transaction = await self.transaction_repository.get_by_id(rental_transaction_id)
        if not rental_transaction:
            raise ValueError(f"Rental transaction {rental_transaction_id} not found")
        
        if rental_transaction.transaction_type != TransactionType.RENTAL:
            raise ValueError("Transaction is not a rental transaction")
        
        if rental_transaction.status not in [TransactionStatus.IN_PROGRESS, TransactionStatus.CONFIRMED]:
            raise ValueError("Rental transaction is not active")
        
        # 2. Get rental transaction lines to understand what was rented
        rental_lines = await self.transaction_line_repository.get_by_transaction(rental_transaction_id)
        if not rental_lines:
            raise ValueError("No rental lines found for transaction")
        
        # 3. Validate return items
        rental_items_map = {}
        for line in rental_lines:
            if line.inventory_unit_id:
                rental_items_map[line.inventory_unit_id] = line
        
        # 4. Check for existing returns to handle partial returns
        existing_returns = await self.return_repository.get_by_transaction_id(rental_transaction_id)
        returned_quantities = {}
        
        for existing_return in existing_returns:
            if existing_return.return_status != ReturnStatus.CANCELLED:
                for line in existing_return.lines:
                    unit_id = line.inventory_unit_id
                    returned_quantities[unit_id] = returned_quantities.get(unit_id, 0) + line.returned_quantity
        
        # 5. Create rental return entity
        rental_return = RentalReturn(
            rental_transaction_id=rental_transaction_id,
            return_date=return_date,
            return_type=return_type,
            return_status=ReturnStatus.INITIATED,
            return_location_id=return_location_id,
            expected_return_date=rental_transaction.rental_end_date,
            processed_by=processed_by,
            notes=notes
        )
        
        # 6. Create rental return
        created_return = await self.return_repository.create(rental_return)
        
        # 7. Create return lines for each item
        return_lines = []
        for return_item in return_items:
            inventory_unit_id = return_item["inventory_unit_id"]
            return_quantity = return_item["quantity"]
            
            # Validate item was actually rented
            if inventory_unit_id not in rental_items_map:
                raise ValueError(f"Inventory unit {inventory_unit_id} was not part of this rental")
            
            rental_line = rental_items_map[inventory_unit_id]
            original_quantity = int(rental_line.quantity)
            already_returned = returned_quantities.get(inventory_unit_id, 0)
            
            # Validate return quantity
            if return_quantity <= 0:
                raise ValueError("Return quantity must be positive")
            
            if already_returned + return_quantity > original_quantity:
                raise ValueError(
                    f"Cannot return {return_quantity} units of {inventory_unit_id}. "
                    f"Original: {original_quantity}, Already returned: {already_returned}"
                )
            
            # Get inventory unit for condition tracking
            inventory_unit = await self.inventory_repository.get_by_id(inventory_unit_id)
            if not inventory_unit:
                raise ValueError(f"Inventory unit {inventory_unit_id} not found")
            
            # Create return line
            return_line = RentalReturnLine(
                return_id=created_return.id,
                inventory_unit_id=inventory_unit_id,
                original_quantity=original_quantity,
                returned_quantity=return_quantity,
                condition_grade=inventory_unit.condition_grade,  # Start with current condition
                notes=return_item.get("notes"),
                created_by=processed_by
            )
            
            return_lines.append(return_line)
        
        # 8. Create all return lines
        if return_lines:
            created_lines = await self.line_repository.create_batch(return_lines)
            
            # Add lines to the return entity
            for line in created_lines:
                created_return.add_line(line)
        
        # 9. Determine return type based on quantities
        total_original = sum(rental_items_map[item["inventory_unit_id"]].quantity for item in return_items)
        total_returning = sum(item["quantity"] for item in return_items)
        total_already_returned = sum(returned_quantities.get(
            rental_items_map[item["inventory_unit_id"]].inventory_unit_id, 0
        ) for item in return_items if rental_items_map[item["inventory_unit_id"]].inventory_unit_id in returned_quantities)
        
        # Check if this completes the return or is partial
        all_items_total = sum(int(line.quantity) for line in rental_lines)
        all_returned_total = sum(returned_quantities.values()) + total_returning
        
        if all_returned_total >= all_items_total:
            # This completes the rental return
            actual_return_type = ReturnType.FULL
        else:
            # This is a partial return
            actual_return_type = ReturnType.PARTIAL
        
        # Update return type if different from requested
        if actual_return_type != return_type:
            created_return._return_type = actual_return_type
            await self.return_repository.update(created_return)
        
        return created_return