from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.item_repository import ItemRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, LineItemType, RentalPeriodUnit
)
from ....domain.value_objects.item_type import InventoryStatus


class CreateRentalTransactionUseCase:
    """Use case for creating a rental transaction."""
    
    def __init__(
        self,
        transaction_repository: TransactionHeaderRepository,
        line_repository: TransactionLineRepository,
        item_repository: ItemRepository,
        inventory_repository: InventoryUnitRepository,
        customer_repository: CustomerRepository
    ):
        """Initialize use case with repositories."""
        self.transaction_repository = transaction_repository
        self.line_repository = line_repository
        self.item_repository = item_repository
        self.inventory_repository = inventory_repository
        self.customer_repository = customer_repository
    
    async def execute(
        self,
        customer_id: UUID,
        location_id: UUID,
        rental_start_date: date,
        rental_end_date: date,
        items: List[Dict],
        sales_person_id: Optional[UUID] = None,
        deposit_amount: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        tax_rate: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
        auto_reserve: bool = True,
        created_by: Optional[str] = None
    ) -> TransactionHeader:
        """Execute the use case to create a rental transaction."""
        # Validate dates
        if rental_end_date < rental_start_date:
            raise ValueError("Rental end date must be after start date")
        
        if rental_start_date < date.today():
            raise ValueError("Rental start date cannot be in the past")
        
        # Calculate rental days
        rental_days = (rental_end_date - rental_start_date).days + 1
        
        # Validate customer
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")
        
        if not customer.is_active:
            raise ValueError("Cannot create transaction for inactive customer")
        
        # Check if customer has outstanding rentals
        active_rentals = await self.transaction_repository.get_active_rentals(
            customer_id=customer_id
        )
        
        if active_rentals and customer.max_active_rentals:
            if len(active_rentals) >= customer.max_active_rentals:
                raise ValueError(
                    f"Customer has reached maximum active rentals limit ({customer.max_active_rentals})"
                )
        
        # Generate transaction number
        transaction_number = await self.transaction_repository.generate_transaction_number(
            TransactionType.RENTAL,
            location_id
        )
        
        # Create transaction header
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime.utcnow(),
            customer_id=customer_id,
            location_id=location_id,
            sales_person_id=sales_person_id,
            status=TransactionStatus.DRAFT,
            payment_status=PaymentStatus.PENDING,
            rental_start_date=rental_start_date,
            rental_end_date=rental_end_date,
            deposit_amount=deposit_amount,
            notes=notes,
            created_by=created_by
        )
        
        # Create lines for each rental item
        lines = []
        line_number = 1
        subtotal = Decimal("0.00")
        
        for item in items:
            item_id = item.get('item_id')
            quantity = Decimal(str(item.get('quantity', 1)))
            unit_price = item.get('unit_price')
            discount_percentage = Decimal(str(item.get('discount_percentage', 0)))
            specific_units = item.get('inventory_unit_ids', [])
            
            # Validate Item
            item_entity = await self.item_repository.get_by_id(item_id)
            if not item_entity:
                raise ValueError(f"Item with id {item_id} not found")
            
            if not item_entity.is_rentable:
                raise ValueError(f"Item {item_entity.sku} is not available for rental")
            
            # Check availability for rental period
            if specific_units:
                # Check specific units are available
                for unit_id in specific_units:
                    unit = await self.inventory_repository.get_by_id(unit_id)
                    if not unit:
                        raise ValueError(f"Inventory unit {unit_id} not found")
                    
                    if not unit.is_rentable:
                        raise ValueError(f"Unit {unit.inventory_code} is not available for rent")
                    
                    if unit.item_id != item_id:
                        raise ValueError(f"Unit {unit.inventory_code} does not match Item")
            else:
                # Check general availability
                available_units = await self.inventory_repository.get_available_units(
                    item_id=item_id,
                    location_id=location_id
                )
                
                rentable_units = [u for u in available_units if u.current_status == InventoryStatus.AVAILABLE_RENT]
                
                if len(rentable_units) < int(quantity):
                    raise ValueError(
                        f"Insufficient units available for rental. "
                        f"Requested: {quantity}, Available: {len(rentable_units)}"
                    )
            
            # Calculate rental price
            if unit_price is None:
                # Use daily rate from Item
                if item_entity.rental_daily_rate:
                    unit_price = item_entity.rental_daily_rate * rental_days
                else:
                    raise ValueError(f"No rental rate defined for Item {item_entity.sku}")
            else:
                unit_price = Decimal(str(unit_price))
            
            # Create rental line
            line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.PRODUCT,
                item_id=item_id,
                description=f"{item_entity.sku} - {item_entity.item_name} (Rental: {rental_days} days)",
                quantity=quantity,
                unit_price=unit_price,
                discount_percentage=discount_percentage,
                rental_period_value=rental_days,
                rental_period_unit=RentalPeriodUnit.DAY,
                rental_start_date=rental_start_date,
                rental_end_date=rental_end_date,
                created_by=created_by
            )
            
            # Calculate line total
            line.calculate_line_total()
            subtotal += line.line_total
            
            lines.append(line)
            line_number += 1
            
            # Reserve specific units if provided
            if auto_reserve and specific_units:
                for unit_id in specific_units:
                    unit = await self.inventory_repository.get_by_id(unit_id)
                    if unit:
                        unit.update_status(InventoryStatus.RESERVED_RENT, created_by)
                        await self.inventory_repository.update(unit)
        
        # Add deposit line if applicable
        if deposit_amount > 0:
            deposit_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.DEPOSIT,
                description="Security deposit",
                quantity=Decimal("1"),
                unit_price=deposit_amount,
                created_by=created_by
            )
            deposit_line.calculate_line_total()
            lines.append(deposit_line)
            line_number += 1
        
        # Apply discount if provided
        if discount_amount > 0:
            discount_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.DISCOUNT,
                description="Rental discount",
                quantity=Decimal("1"),
                unit_price=-discount_amount,
                created_by=created_by
            )
            discount_line.calculate_line_total()
            lines.append(discount_line)
            line_number += 1
        
        # Calculate tax
        taxable_amount = subtotal - discount_amount
        if tax_rate > 0 and taxable_amount > 0:
            tax_amount = taxable_amount * (tax_rate / 100)
            tax_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.TAX,
                description=f"Rental tax ({tax_rate}%)",
                quantity=Decimal("1"),
                unit_price=tax_amount,
                created_by=created_by
            )
            tax_line.calculate_line_total()
            lines.append(tax_line)
        
        # Update transaction totals
        transaction.subtotal = subtotal
        transaction.discount_amount = discount_amount
        transaction.tax_amount = tax_amount if tax_rate > 0 else Decimal("0.00")
        transaction.total_amount = taxable_amount + transaction.tax_amount + deposit_amount
        
        # Save transaction
        created_transaction = await self.transaction_repository.create(transaction)
        
        # Save lines
        for line in lines:
            line.transaction_id = created_transaction.id
        
        created_lines = await self.line_repository.create_batch(lines)
        created_transaction._lines = created_lines
        
        # Update status to pending if auto-reserve
        if auto_reserve:
            created_transaction.update_status(TransactionStatus.PENDING, created_by)
            await self.transaction_repository.update(created_transaction)
        
        return created_transaction