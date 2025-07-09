from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.item_repository import ItemRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.transaction_header_repository import (
    TransactionHeaderRepository,
)
from ....domain.repositories.transaction_line_repository import (
    TransactionLineRepository,
)
from ....domain.value_objects.item_type import InventoryStatus
from ....domain.value_objects.transaction_type import (
    LineItemType,
    PaymentStatus,
    TransactionStatus,
    TransactionType,
)


class RecordCompletedPurchaseReturnUseCase:
    """Use case for recording a completed purchase return transaction (returning items to supplier)."""

    def __init__(
        self,
        transaction_repository: TransactionHeaderRepository,
        line_repository: TransactionLineRepository,
        item_repository: ItemRepository,
        customer_repository: CustomerRepository,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository,
    ):
        """Initialize use case with repositories."""
        self.transaction_repository = transaction_repository
        self.line_repository = line_repository
        self.item_repository = item_repository
        self.customer_repository = customer_repository
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository

    async def execute(
        self,
        supplier_id: UUID,
        location_id: UUID,
        original_purchase_id: UUID,
        items: List[Dict],
        return_date: date,
        refund_amount: Decimal = Decimal("0.00"),
        return_authorization: Optional[str] = None,
        return_reason: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> TransactionHeader:
        """Execute the use case to record a completed purchase return transaction."""
        # Validate supplier exists and is active
        supplier = await self.customer_repository.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")

        if not supplier.is_active:
            raise ValueError("Cannot record return for inactive supplier")

        # Validate original purchase transaction exists
        original_purchase = await self.transaction_repository.get_by_id(
            original_purchase_id
        )
        if not original_purchase:
            raise ValueError(
                f"Original purchase transaction with id {original_purchase_id} not found"
            )

        if original_purchase.transaction_type != TransactionType.PURCHASE:
            raise ValueError("Referenced transaction is not a purchase")

        if original_purchase.customer_id != supplier_id:
            raise ValueError("Supplier does not match original purchase supplier")

        # Validate return items against original purchase
        await self._validate_return_items(original_purchase_id, items)

        # Generate return transaction number
        transaction_number = (
            await self.transaction_repository.generate_transaction_number(
                TransactionType.RETURN, location_id
            )
        )

        # Create transaction header
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.RETURN,
            transaction_date=datetime.combine(return_date, datetime.min.time()),
            customer_id=supplier_id,  # Supplier as customer
            location_id=location_id,
            status=TransactionStatus.COMPLETED,  # Return already completed
            payment_status=PaymentStatus.PAID,  # Refund already processed
            reference_transaction_id=original_purchase_id,
            notes=notes,
            created_by=created_by,
        )

        # Add return information to notes
        return_info = []
        if return_authorization:
            return_info.append(f"RMA: {return_authorization}")
        if return_reason:
            return_info.append(f"Reason: {return_reason}")
        if refund_amount > 0:
            return_info.append(f"Refund: ${refund_amount}")

        if return_info:
            return_note = " | ".join(return_info)
            transaction.notes = f"{notes}\n{return_note}" if notes else return_note

        # Create lines for each returned item and process inventory immediately
        lines = []
        line_number = 1
        total_return_amount = Decimal("0.00")

        for item in items:
            item_id = item.get("item_id")
            quantity = Decimal(str(item.get("quantity", 1)))
            unit_price = Decimal(str(item.get("unit_price", 0)))
            serial_numbers = item.get("serial_numbers", [])
            condition_notes = item.get("condition_notes")
            item_notes = item.get("notes")
            item_return_reason = item.get("return_reason")

            # Get Item details
            item_obj = await self.item_repository.get_by_id(item_id)
            if not item_obj:
                raise ValueError(f"Item with id {item_id} not found")

            # Create line
            description = f"RETURN: {item_obj.item_code} - {item_obj.item_name}"
            if item_return_reason:
                description += f" (Reason: {item_return_reason})"
            if item_notes:
                description += f" ({item_notes})"

            # For returns, use negative unit price to represent return value
            line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.PRODUCT,
                item_id=item_id,
                description=description,
                quantity=quantity,
                unit_price=-unit_price,  # Negative for return
                discount_percentage=Decimal("0"),
                created_by=created_by,
            )

            # Calculate line total (will be negative)
            line.calculate_line_total()
            total_return_amount += abs(line.line_total)  # Track positive return amount

            lines.append(line)
            line_number += 1

            # Process inventory reversal immediately
            await self._process_inventory_return(
                item=item_obj,
                quantity=quantity,
                location_id=location_id,
                return_date=return_date,
                serial_numbers=serial_numbers,
                condition_notes=condition_notes,
                created_by=created_by,
            )

            # Update stock levels immediately (reverse purchase)
            await self._update_stock_levels_for_return(
                item_id=item_id,
                location_id=location_id,
                quantity_decrease=int(quantity),
                updated_by=created_by,
            )

        # Add refund line if refund amount is specified
        if refund_amount > 0:
            refund_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.REFUND,
                description=f"Purchase return refund{' - ' + return_authorization if return_authorization else ''}",
                quantity=Decimal("1"),
                unit_price=refund_amount,
                created_by=created_by,
            )
            refund_line.calculate_line_total()
            lines.append(refund_line)

        # Update transaction totals
        transaction.subtotal = -total_return_amount  # Negative for return
        transaction.discount_amount = Decimal("0.00")
        transaction.tax_amount = Decimal("0.00")
        transaction.total_amount = -total_return_amount + refund_amount
        transaction.paid_amount = transaction.total_amount  # Return already processed

        # Save transaction
        created_transaction = await self.transaction_repository.create(transaction)

        # Save lines
        for line in lines:
            line.transaction_id = created_transaction.id

        created_lines = await self.line_repository.create_batch(lines)
        created_transaction._lines = created_lines

        return created_transaction

    async def _validate_return_items(
        self, original_purchase_id: UUID, items: List[Dict]
    ):
        """Validate that returned items match the original purchase."""
        # Get original purchase lines
        original_lines = await self.line_repository.get_by_transaction(
            original_purchase_id
        )
        original_product_lines = [
            line for line in original_lines if line.line_type == LineItemType.PRODUCT
        ]

        # Create mapping of Item to purchased quantities
        purchased_quantities = {}
        for line in original_product_lines:
            if line.item_id:
                purchased_quantities[line.item_id] = (
                    purchased_quantities.get(line.item_id, 0) + line.quantity
                )

        # Validate each return item
        for item in items:
            item_id = item.get("item_id")
            quantity = Decimal(str(item.get("quantity", 1)))
            serial_numbers = item.get("serial_numbers", [])

            if item_id not in purchased_quantities:
                item_obj = await self.item_repository.get_by_id(item_id)
                item_name = item_obj.item_code if item_obj else str(item_id)
                raise ValueError(
                    f"Item {item_name} was not part of the original purchase"
                )

            if quantity > purchased_quantities[item_id]:
                item_obj = await self.item_repository.get_by_id(item_id)
                item_name = item_obj.item_code if item_obj else str(item_id)
                raise ValueError(
                    f"Cannot return {quantity} units of {item_name}. "
                    f"Only {purchased_quantities[item_id]} were purchased"
                )

            # For serialized items, validate serial numbers
            item_obj = await self.item_repository.get_by_id(item_id)
            if item_obj and item_obj.is_serialized:
                if not serial_numbers:
                    raise ValueError(
                        f"Serial numbers required for serialized Item {item_obj.item_code}"
                    )

                if len(serial_numbers) != int(quantity):
                    raise ValueError(
                        f"Number of serial numbers ({len(serial_numbers)}) "
                        f"must match quantity ({quantity})"
                    )

                # Validate each serial number exists and is available for return
                for serial_number in serial_numbers:
                    inventory_unit = (
                        await self.inventory_repository.get_by_serial_number(
                            serial_number
                        )
                    )
                    if not inventory_unit:
                        raise ValueError(f"Serial number {serial_number} not found")

                    # Check if this item is in a state that allows return to supplier
                    if inventory_unit.current_status not in [
                        InventoryStatus.AVAILABLE_SALE,
                        InventoryStatus.AVAILABLE_RENT,
                        InventoryStatus.DAMAGED,
                        InventoryStatus.INSPECTION_PENDING,
                    ]:
                        raise ValueError(
                            f"Serial number {serial_number} cannot be returned "
                            f"(current status: {inventory_unit.current_status})"
                        )

    async def _process_inventory_return(
        self,
        item,
        quantity: Decimal,
        location_id: UUID,
        return_date: date,
        serial_numbers: List[str] = None,
        condition_notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ):
        """Process inventory for returned items (remove from inventory)."""

        if item.is_serialized:
            # Remove specific inventory units (returning to supplier)
            for serial_number in serial_numbers:
                inventory_unit = await self.inventory_repository.get_by_serial_number(
                    serial_number
                )
                if inventory_unit:
                    # Mark as returned to supplier (remove from inventory)
                    inventory_unit.current_status = InventoryStatus.RETURNED_TO_SUPPLIER
                    inventory_unit.return_date = return_date

                    if condition_notes:
                        inventory_unit.notes = (
                            f"{inventory_unit.notes}\nReturn condition: {condition_notes}"
                            if inventory_unit.notes
                            else f"Return condition: {condition_notes}"
                        )

                    inventory_unit.updated_by = created_by
                    inventory_unit.updated_at = datetime.utcnow()

                    await self.inventory_repository.update(inventory_unit)
        else:
            # For non-serialized items, inventory is managed through stock levels only
            # No individual inventory units to process
            pass

    async def _update_stock_levels_for_return(
        self,
        item_id: UUID,
        location_id: UUID,
        quantity_decrease: int,
        updated_by: Optional[str] = None,
    ):
        """Update stock levels for purchase return (decrease quantities)."""

        # Get existing stock level
        stock_level = await self.stock_repository.get_by_item_location(
            item_id, location_id
        )

        if stock_level:
            # Reverse the purchase (decrease stock)
            stock_level.reverse_purchase(quantity_decrease, updated_by)
            stock_level.last_updated = datetime.utcnow()
            await self.stock_repository.update(stock_level)
        else:
            # This should not happen if validation passed, but handle gracefully
            raise ValueError(
                f"No stock level found for Item {item_id} at location {location_id}"
            )
