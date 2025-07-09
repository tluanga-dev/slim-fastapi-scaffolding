import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from ....domain.entities.inventory_unit import InventoryUnit
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


class RecordCompletedSaleReturnUseCase:
    """Use case for recording a completed sale return transaction (customer returning purchased items)."""

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
        customer_id: UUID,
        location_id: UUID,
        original_sale_id: UUID,
        items: List[Dict],
        return_date: date,
        refund_amount: Decimal = Decimal("0.00"),
        refund_method: Optional[str] = None,
        return_reason: Optional[str] = None,
        restocking_fee: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> TransactionHeader:
        """Execute the use case to record a completed sale return transaction."""
        # Validate customer exists and is active
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")

        if not customer.is_active:
            raise ValueError("Cannot record return for inactive customer")

        # Validate original sale transaction exists
        original_sale = await self.transaction_repository.get_by_id(original_sale_id)
        if not original_sale:
            raise ValueError(
                f"Original sale transaction with id {original_sale_id} not found"
            )

        if original_sale.transaction_type != TransactionType.SALE:
            raise ValueError("Referenced transaction is not a sale")

        if original_sale.customer_id != customer_id:
            raise ValueError("Customer does not match original sale customer")

        # Validate return items against original sale
        await self._validate_return_items(original_sale_id, items)

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
            customer_id=customer_id,
            location_id=location_id,
            status=TransactionStatus.COMPLETED,  # Return already completed
            payment_status=PaymentStatus.PAID,  # Refund already processed
            reference_transaction_id=original_sale_id,
            notes=notes,
            created_by=created_by,
        )

        # Add return information to notes
        return_info = []
        if return_reason:
            return_info.append(f"Reason: {return_reason}")
        if refund_method:
            return_info.append(f"Refund method: {refund_method}")
        if refund_amount > 0:
            return_info.append(f"Refund: ${refund_amount}")
        if restocking_fee > 0:
            return_info.append(f"Restocking fee: ${restocking_fee}")

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

            # Process inventory return immediately
            await self._process_inventory_return(
                item=item_obj,
                quantity=quantity,
                unit_price=unit_price,
                location_id=location_id,
                return_date=return_date,
                serial_numbers=serial_numbers,
                condition_notes=condition_notes,
                created_by=created_by,
            )

            # Update stock levels immediately (reverse sale)
            await self._update_stock_levels_for_return(
                item_id=item_id,
                location_id=location_id,
                quantity_increase=int(quantity),
                updated_by=created_by,
            )

        # Add restocking fee line if applicable
        if restocking_fee > 0:
            fee_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.FEE,
                description="Restocking fee",
                quantity=Decimal("1"),
                unit_price=restocking_fee,
                created_by=created_by,
            )
            fee_line.calculate_line_total()
            lines.append(fee_line)
            line_number += 1

        # Add refund line if refund amount is specified
        if refund_amount > 0:
            refund_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.REFUND,
                description=f"Sale return refund{' - ' + refund_method if refund_method else ''}",
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
        transaction.total_amount = -total_return_amount + refund_amount + restocking_fee
        transaction.paid_amount = transaction.total_amount  # Return already processed

        # Save transaction
        created_transaction = await self.transaction_repository.create(transaction)

        # Save lines
        for line in lines:
            line.transaction_id = created_transaction.id

        created_lines = await self.line_repository.create_batch(lines)
        created_transaction._lines = created_lines

        return created_transaction

    async def _validate_return_items(self, original_sale_id: UUID, items: List[Dict]):
        """Validate that returned items match the original sale."""
        # Get original sale lines
        original_lines = await self.line_repository.get_by_transaction(original_sale_id)
        original_product_lines = [
            line for line in original_lines if line.line_type == LineItemType.PRODUCT
        ]

        # Create mapping of Item to sold quantities
        sold_quantities = {}
        for line in original_product_lines:
            if line.item_id:
                sold_quantities[line.item_id] = (
                    sold_quantities.get(line.item_id, 0) + line.quantity
                )

        # Validate each return item
        for item in items:
            item_id = item.get("item_id")
            quantity = Decimal(str(item.get("quantity", 1)))
            serial_numbers = item.get("serial_numbers", [])

            if item_id not in sold_quantities:
                item_obj = await self.item_repository.get_by_id(item_id)
                item_name = item_obj.item_code if item_obj else str(item_id)
                raise ValueError(f"Item {item_name} was not part of the original sale")

            if quantity > sold_quantities[item_id]:
                item_obj = await self.item_repository.get_by_id(item_id)
                item_name = item_obj.item_code if item_obj else str(item_id)
                raise ValueError(
                    f"Cannot return {quantity} units of {item_name}. "
                    f"Only {sold_quantities[item_id]} were sold"
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

                # Validate each serial number exists and was sold to this customer
                for serial_number in serial_numbers:
                    inventory_unit = (
                        await self.inventory_repository.get_by_serial_number(
                            serial_number
                        )
                    )
                    if not inventory_unit:
                        raise ValueError(f"Serial number {serial_number} not found")

                    # Check if this item was sold and can be returned
                    if inventory_unit.current_status != InventoryStatus.SOLD:
                        raise ValueError(
                            f"Serial number {serial_number} was not sold "
                            f"(current status: {inventory_unit.current_status})"
                        )

    async def _process_inventory_return(
        self,
        item,
        quantity: Decimal,
        unit_price: Decimal,
        location_id: UUID,
        return_date: date,
        serial_numbers: List[str] = None,
        condition_notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ):
        """Process inventory for returned items (add back to inventory)."""

        if item.is_serialized:
            # Restore specific inventory units (customer returning items)
            for serial_number in serial_numbers:
                inventory_unit = await self.inventory_repository.get_by_serial_number(
                    serial_number
                )
                if inventory_unit:
                    # Restore to available status
                    inventory_unit.current_status = (
                        InventoryStatus.AVAILABLE_SALE
                        if item.is_saleable
                        else InventoryStatus.AVAILABLE_RENT
                    )
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
            # For non-serialized items, we may need to create new inventory units
            # depending on the business logic. For now, we'll manage through stock levels only.
            pass

    async def _update_stock_levels_for_return(
        self,
        item_id: UUID,
        location_id: UUID,
        quantity_increase: int,
        updated_by: Optional[str] = None,
    ):
        """Update stock levels for sale return (increase quantities)."""

        # Get existing stock level
        stock_level = await self.stock_repository.get_by_item_location(
            item_id, location_id
        )

        if stock_level:
            # Reverse the sale (increase stock)
            stock_level.reverse_sale(quantity_increase, updated_by)
            stock_level.last_updated = datetime.utcnow()
            await self.stock_repository.update(stock_level)
        else:
            # This should not happen if validation passed, but handle gracefully
            raise ValueError(
                f"No stock level found for Item {item_id} at location {location_id}"
            )
