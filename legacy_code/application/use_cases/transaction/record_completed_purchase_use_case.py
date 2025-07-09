from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
import uuid

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.entities.stock_level import StockLevel
from ....domain.repositories.transaction_header_repository import (
    TransactionHeaderRepository,
)
from ....domain.repositories.transaction_line_repository import (
    TransactionLineRepository,
)
from ....domain.repositories.item_repository import ItemRepository
from ....domain.repositories.supplier_repository import SupplierRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.value_objects.transaction_type import (
    TransactionType,
    TransactionStatus,
    PaymentStatus,
    LineItemType,
)
from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade


class RecordCompletedPurchaseUseCase:
    """Use case for recording a completed purchase transaction and creating inventory records."""

    def __init__(
        self,
        transaction_repository: TransactionHeaderRepository,
        line_repository: TransactionLineRepository,
        item_repository: ItemRepository,
        supplier_repository: SupplierRepository,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository,
    ):
        """Initialize use case with repositories."""
        self.transaction_repository = transaction_repository
        self.line_repository = line_repository
        self.item_repository = item_repository
        self.supplier_repository = supplier_repository
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository

    async def execute(
        self,
        supplier_id: UUID,
        location_id: UUID,
        items: List[Dict],
        purchase_date: date,
        tax_rate: Decimal = Decimal("0.00"),
        tax_amount: Optional[Decimal] = None,
        discount_amount: Decimal = Decimal("0.00"),
        invoice_number: Optional[str] = None,
        invoice_date: Optional[date] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> TransactionHeader:
        """Execute the use case to record a completed purchase transaction."""
        # Validate supplier exists and is active
        supplier = await self.supplier_repository.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")

        if not supplier.is_active:
            raise ValueError("Cannot record purchase for inactive supplier")

        # Generate purchase transaction number
        transaction_number = (
            await self.transaction_repository.generate_transaction_number(
                TransactionType.PURCHASE, location_id
            )
        )

        # Create transaction header
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.PURCHASE,
            transaction_date=datetime.combine(purchase_date, datetime.min.time()),
            customer_id=supplier_id,  # Supplier stored as customer
            location_id=location_id,
            status=TransactionStatus.COMPLETED,  # Immediately completed
            payment_status=PaymentStatus.PAID,  # Purchase is already paid
            notes=notes,
            created_by=created_by,
        )

        # Add invoice information to notes if provided
        invoice_info = []
        if invoice_number:
            invoice_info.append(f"Invoice: {invoice_number}")
        if invoice_date:
            invoice_info.append(f"Invoice Date: {invoice_date.strftime('%Y-%m-%d')}")

        if invoice_info:
            invoice_note = " | ".join(invoice_info)
            transaction.notes = f"{notes}\n{invoice_note}" if notes else invoice_note

        # Create lines for each item and process inventory immediately
        lines = []
        line_number = 1
        subtotal = Decimal("0.00")
        total_item_discount = Decimal("0.00")
        total_item_tax = Decimal("0.00")

        for item in items:
            item_id = item.get("item_id")
            quantity = Decimal(str(item.get("quantity", 1)))
            unit_cost = Decimal(str(item.get("unit_cost", 0)))
            item_tax_rate = Decimal(str(item.get("tax_rate", 0)))
            item_tax_amount = Decimal(str(item.get("tax_amount", 0)))
            item_discount_amount = Decimal(str(item.get("discount_amount", 0)))
            serial_numbers = item.get("serial_numbers", [])
            condition_notes = item.get("condition_notes")
            item_notes = item.get("notes")

            # Validate Item
            item_obj = await self.item_repository.get_by_id(item_id)
            if not item_obj:
                raise ValueError(f"Item with id {item_id} not found")

            if not item_obj.is_active:
                raise ValueError(f"Item {item_obj.item_id or item_obj.id} is not active")

            # Create main product line with tax and discount information
            description = f"{item_obj.item_id or item_obj.id} - {item_obj.item_name}"
            if item_notes:
                description += f" ({item_notes})"

            # Calculate discount percentage if we have both amount and base price
            discount_percentage = Decimal("0")
            if item_discount_amount > 0 and unit_cost > 0:
                discount_percentage = (item_discount_amount / (quantity * unit_cost)) * 100

            # Calculate tax amount if not provided but tax rate is given
            final_tax_amount = item_tax_amount
            if final_tax_amount == 0 and item_tax_rate > 0:
                taxable_amount = (quantity * unit_cost) - item_discount_amount
                final_tax_amount = taxable_amount * (item_tax_rate / 100)

            line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.PRODUCT,
                item_id=item_id,
                description=description,
                quantity=quantity,
                unit_price=unit_cost,  # This is the purchase cost
                discount_percentage=discount_percentage,
                discount_amount=item_discount_amount,
                tax_rate=item_tax_rate,
                tax_amount=final_tax_amount,
                created_by=created_by,
            )

            # Calculate line total using the built-in method
            line.calculate_line_total()
            item_subtotal = (quantity * unit_cost)  # Base subtotal before tax/discount
            subtotal += item_subtotal

            lines.append(line)
            line_number += 1

            # Track totals for purchase-level calculations
            total_item_discount += item_discount_amount
            total_item_tax += final_tax_amount

            # Item-level tax and discount are now included in the product line above
            # No separate lines needed for item-level adjustments

            # Create inventory records immediately
            await self._create_inventory_units(
                item=item_obj,
                quantity=quantity,
                unit_cost=unit_cost,
                location_id=location_id,
                purchase_date=purchase_date,
                serial_numbers=serial_numbers,
                condition_notes=condition_notes,
                created_by=created_by,
            )

            # Update stock levels immediately
            await self._update_stock_levels(
                item_id=item_id,
                location_id=location_id,
                quantity_increase=int(quantity),
                updated_by=created_by,
            )

        # No separate purchase-level discount or tax lines needed
        # All tax and discount information is now embedded in the product lines
        
        # Note: The tax_amount and discount_amount parameters from the frontend
        # represent the sum of all item-level taxes and discounts, not additional
        # purchase-level amounts. We use these for validation and header totals only.

        # Update transaction totals
        transaction.subtotal = subtotal
        transaction.discount_amount = total_item_discount  # Sum of all item discounts
        transaction.tax_amount = total_item_tax  # Sum of all item taxes  
        transaction.total_amount = subtotal - total_item_discount + total_item_tax
        transaction.paid_amount = transaction.total_amount  # Purchase is already paid

        # Save transaction
        created_transaction = await self.transaction_repository.create(transaction)

        # Save lines
        for line in lines:
            line.transaction_id = created_transaction.id

        created_lines = await self.line_repository.create_batch(lines)
        created_transaction._lines = created_lines

        return created_transaction

    async def _create_inventory_units(
        self,
        item,
        quantity: Decimal,
        unit_cost: Decimal,
        location_id: UUID,
        purchase_date: date,
        serial_numbers: List[str] = None,
        condition_notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ):
        """Create inventory units for purchased goods."""

        if item.is_serialized:
            # Create one inventory unit per serial number
            if not serial_numbers:
                raise ValueError(
                    f"Serial numbers required for serialized Item {item.item_id or item.id}"
                )

            if len(serial_numbers) != int(quantity):
                raise ValueError(
                    f"Number of serial numbers ({len(serial_numbers)}) "
                    f"must match quantity ({quantity})"
                )

            for serial_number in serial_numbers:
                # Check if serial number already exists
                existing = await self.inventory_repository.get_by_serial_number(
                    serial_number
                )
                if existing:
                    raise ValueError(f"Serial number {serial_number} already exists")

                inventory_unit = InventoryUnit(
                    inventory_code=self._generate_inventory_id(),
                    item_id=item.id,
                    serial_number=serial_number,
                    location_id=location_id,
                    current_status=(
                        InventoryStatus.AVAILABLE_SALE
                        if item.is_saleable
                        else InventoryStatus.AVAILABLE_RENT
                    ),
                    condition_grade=ConditionGrade.A,  # New items start with grade A
                    purchase_date=purchase_date,
                    purchase_cost=unit_cost,
                    created_by=created_by,
                )

                if condition_notes:
                    inventory_unit.notes = condition_notes

                await self.inventory_repository.create(inventory_unit)
        else:
            # For non-serialized items, we don't create individual inventory units
            # Stock levels are updated separately
            pass

    async def _update_stock_levels(
        self,
        item_id: UUID,
        location_id: UUID,
        quantity_increase: int,
        updated_by: Optional[str] = None,
    ):
        """Update stock levels for purchased goods."""

        # Get existing stock level or create new one
        stock_level = await self.stock_repository.get_by_item_location(
            item_id, location_id
        )

        if stock_level:
            # Update existing stock level
            stock_level.quantity_on_hand += quantity_increase
            stock_level.quantity_available += quantity_increase
            stock_level.updated_by = updated_by
            await self.stock_repository.update(stock_level)
        else:
            # Create new stock level
            item = await self.item_repository.get_by_id(item_id)
            stock_level = StockLevel(
                item_id=item_id,
                location_id=location_id,
                quantity_on_hand=quantity_increase,
                quantity_available=quantity_increase,
                quantity_reserved=0,
                quantity_in_transit=0,
                quantity_damaged=0,
                reorder_point=0,
                reorder_quantity=0,
                maximum_stock=None,
                created_by=updated_by,
            )
            await self.stock_repository.create(stock_level)

    def _generate_inventory_id(self) -> str:
        """Generate a unique inventory ID."""
        return f"INV-{str(uuid.uuid4())[:8].upper()}"
