from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentMethod, LineItemType
)
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.item_repository import ItemRepository


class ExtendRentalPeriodUseCase:
    """Use case for extending an active rental period."""
    
    def __init__(
        self,
        transaction_repo: TransactionHeaderRepository,
        transaction_line_repo: TransactionLineRepository,
        inventory_unit_repo: InventoryUnitRepository,
        item_repo: ItemRepository
    ):
        self.transaction_repo = transaction_repo
        self.transaction_line_repo = transaction_line_repo
        self.inventory_unit_repo = inventory_unit_repo
        self.item_repo = item_repo
    
    async def execute(
        self,
        transaction_id: UUID,
        new_end_date: date,
        payment_amount: Optional[Decimal] = None,
        payment_method: Optional[PaymentMethod] = None,
        payment_reference: Optional[str] = None,
        apply_discount_percentage: Optional[Decimal] = None,
        extension_notes: Optional[str] = None,
        processed_by: Optional[str] = None
    ) -> TransactionHeader:
        """Extend rental period and process additional payment."""
        
        # 1. Get and validate transaction
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if transaction.transaction_type != TransactionType.RENTAL:
            raise ValueError("Can only extend rental transactions")
        
        if transaction.status != TransactionStatus.IN_PROGRESS:
            raise ValueError(
                f"Can only extend active rentals. Current status: {transaction.status.value}"
            )
        
        # Validate new end date
        if new_end_date <= transaction.rental_end_date:
            raise ValueError(
                f"New end date must be after current end date ({transaction.rental_end_date})"
            )
        
        if new_end_date <= date.today():
            raise ValueError("New end date must be in the future")
        
        # 2. Check availability for all items
        lines = await self.transaction_line_repo.get_by_transaction_id(transaction_id)
        
        for line in lines:
            if line.line_type == LineItemType.PRODUCT and line.inventory_unit_id:
                # Check if unit has any conflicting reservations
                has_conflict = await self._check_availability_for_extension(
                    line.inventory_unit_id,
                    transaction.rental_end_date,
                    new_end_date
                )
                
                if has_conflict:
                    unit = await self.inventory_unit_repo.get_by_id(line.inventory_unit_id)
                    raise ValueError(
                        f"Unit {unit.serial_number} is not available for the extended period"
                    )
        
        # 3. Calculate extension charges
        original_days = (transaction.rental_end_date - transaction.rental_start_date).days + 1
        new_total_days = (new_end_date - transaction.rental_start_date).days + 1
        extension_days = new_total_days - original_days
        
        extension_subtotal = Decimal("0.00")
        extension_lines = []
        
        # Get the highest line number
        max_line_number = max(line.line_number for line in lines)
        current_line_number = max_line_number + 1
        
        # Create extension lines for each product
        for line in lines:
            if line.line_type == LineItemType.PRODUCT:
                # Calculate extension charge
                daily_rate = line.unit_price
                extension_charge = daily_rate * extension_days
                
                # Apply discount if provided
                if apply_discount_percentage:
                    discount_amount = extension_charge * (apply_discount_percentage / 100)
                    extension_charge -= discount_amount
                
                # Create extension line
                extension_line = TransactionLine(
                    transaction_id=transaction_id,
                    line_number=current_line_number,
                    line_type=LineItemType.SERVICE,  # Extension as service
                    item_id=line.item_id,
                    description=f"Rental Extension: {line.description} ({extension_days} days)",
                    quantity=Decimal(str(extension_days)),
                    unit_price=daily_rate,
                    discount_percentage=apply_discount_percentage or Decimal("0.00"),
                    rental_start_date=transaction.rental_end_date,
                    rental_end_date=new_end_date,
                    created_by=processed_by
                )
                
                extension_line.calculate_line_total()
                extension_lines.append(extension_line)
                extension_subtotal += extension_line.line_total
                current_line_number += 1
                
                # Update original line's rental end date
                line.update_rental_period(new_end_date, processed_by)
                await self.transaction_line_repo.update(line.id, line)
        
        # 4. Add tax for extension
        if extension_subtotal > 0:
            # Use same tax rate as original transaction
            tax_rate = Decimal("8.25")  # Should get from original tax line
            tax_amount = extension_subtotal * (tax_rate / 100)
            
            tax_line = TransactionLine(
                transaction_id=transaction_id,
                line_number=current_line_number,
                line_type=LineItemType.TAX,
                description=f"Tax on Extension ({tax_rate}%)",
                quantity=Decimal("1"),
                unit_price=tax_amount,
                line_total=tax_amount,
                created_by=processed_by
            )
            extension_lines.append(tax_line)
            current_line_number += 1
        
        # 5. Save extension lines
        for line in extension_lines:
            await self.transaction_line_repo.create(line)
        
        # 6. Update transaction
        transaction.rental_end_date = new_end_date
        
        # Recalculate totals
        all_lines = lines + extension_lines
        transaction._lines = all_lines
        transaction.calculate_totals()
        
        # 7. Process payment if provided
        if payment_amount and payment_method:
            transaction.apply_payment(
                amount=payment_amount,
                payment_method=payment_method,
                payment_reference=payment_reference,
                updated_by=processed_by
            )
        
        # 8. Add extension notes
        extension_note = (
            f"\n[EXTENSION] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - "
            f"Extended to {new_end_date} ({extension_days} additional days) - "
            f"Charge: ${extension_subtotal + (tax_amount if 'tax_amount' in locals() else 0)}"
        )
        
        if extension_notes:
            extension_note += f"\nNotes: {extension_notes}"
        
        transaction.notes = (transaction.notes or "") + extension_note
        
        # 9. Save transaction
        await self.transaction_repo.update(transaction.id, transaction)
        
        return transaction
    
    async def _check_availability_for_extension(
        self,
        unit_id: UUID,
        current_end_date: date,
        new_end_date: date
    ) -> bool:
        """Check if unit is available for the extension period."""
        # Get all rental transactions with this unit
        transactions = await self.transaction_repo.get_active_rentals_by_unit(unit_id)
        
        for other_transaction in transactions:
            # Skip the current transaction
            if other_transaction.id == unit_id:
                continue
            
            # Check if there's any overlap with the extension period
            if (other_transaction.rental_start_date <= new_end_date and 
                other_transaction.rental_end_date > current_end_date):
                return True  # Has conflict
        
        return False  # No conflict