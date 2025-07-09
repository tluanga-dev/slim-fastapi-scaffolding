from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.entities.customer import Customer
from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.entities.item import Item
from ....domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, LineItemType, RentalPeriodUnit
)
from ....domain.value_objects.item_type import InventoryStatus
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.item_repository import ItemRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository


class RentalBookingItem:
    """DTO for rental booking item."""
    def __init__(
        self,
        item_id: UUID,
        quantity: int,
        rental_start_date: date,
        rental_end_date: date,
        inventory_unit_ids: Optional[List[UUID]] = None,
        custom_price: Optional[Decimal] = None,
        discount_percentage: Optional[Decimal] = None,
        notes: Optional[str] = None
    ):
        self.item_id = item_id
        self.quantity = quantity
        self.rental_start_date = rental_start_date
        self.rental_end_date = rental_end_date
        self.inventory_unit_ids = inventory_unit_ids or []
        self.custom_price = custom_price
        self.discount_percentage = discount_percentage
        self.notes = notes


class CreateRentalBookingUseCase:
    """Use case for creating a new rental booking."""
    
    def __init__(
        self,
        transaction_repo: TransactionHeaderRepository,
        transaction_line_repo: TransactionLineRepository,
        customer_repo: CustomerRepository,
        inventory_unit_repo: InventoryUnitRepository,
        item_repo: ItemRepository,
        stock_level_repo: StockLevelRepository
    ):
        self.transaction_repo = transaction_repo
        self.transaction_line_repo = transaction_line_repo
        self.customer_repo = customer_repo
        self.inventory_unit_repo = inventory_unit_repo
        self.item_repo = item_repo
        self.stock_level_repo = stock_level_repo
    
    async def execute(
        self,
        customer_id: UUID,
        location_id: UUID,
        items: List[RentalBookingItem],
        deposit_percentage: Decimal = Decimal("30.00"),
        tax_rate: Decimal = Decimal("8.25"),
        sales_person_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> TransactionHeader:
        """Create a new rental booking."""
        
        # 1. Validate customer
        customer = await self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")
        
        if not customer.is_active:
            raise ValueError("Customer account is inactive")
        
        # 2. Validate all items and check availability
        validated_items = []
        for item in items:
            # Validate item
            item_entity = await self.item_repo.get_by_id(item.item_id)
            if not item_entity:
                raise ValueError(f"Item with id {item.item_id} not found")
            
            if not item_entity.is_rentable:
                raise ValueError(f"Item {item_entity.item_code} is not available for rental")
            
            # Check rental period constraints
            rental_days = (item.rental_end_date - item.rental_start_date).days + 1
            if rental_days < item_entity.min_rental_days:
                raise ValueError(
                    f"Item {item_entity.item_code} requires minimum {item_entity.min_rental_days} days rental"
                )
            
            if item_entity.max_rental_days and rental_days > item_entity.max_rental_days:
                raise ValueError(
                    f"Item {item_entity.item_code} allows maximum {item_entity.max_rental_days} days rental"
                )
            
            # Check availability
            available_units = await self._check_availability(
                item_entity.id, location_id, item.rental_start_date, item.rental_end_date
            )
            
            if len(available_units) < item.quantity:
                raise ValueError(
                    f"Insufficient availability for item {item_entity.item_code}. "
                    f"Requested: {item.quantity}, Available: {len(available_units)}"
                )
            
            # Select specific units if not provided
            if not item.inventory_unit_ids:
                item.inventory_unit_ids = [unit.id for unit in available_units[:item.quantity]]
            
            validated_items.append((item, item_entity, available_units))
        
        # 3. Generate transaction number
        transaction_number = await self._generate_transaction_number()
        
        # 4. Create transaction header
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime.utcnow(),
            customer_id=customer_id,
            location_id=location_id,
            sales_person_id=sales_person_id,
            status=TransactionStatus.DRAFT,
            payment_status=PaymentStatus.PENDING,
            rental_start_date=min(item.rental_start_date for item in items),
            rental_end_date=max(item.rental_end_date for item in items),
            notes=notes,
            created_by=created_by
        )
        
        # 5. Create transaction lines
        lines = []
        line_number = 1
        subtotal = Decimal("0.00")
        
        for item, item_entity, available_units in validated_items:
            # Calculate rental price
            rental_days = (item.rental_end_date - item.rental_start_date).days + 1
            unit_price = item.custom_price or item_entity.rental_base_price or Decimal("0.00")
            
            # Create product line
            line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.PRODUCT,
                item_id=item_entity.id,
                description=f"Rental: {item_entity.item_name}",
                quantity=Decimal(str(item.quantity)),
                unit_price=unit_price,
                discount_percentage=item.discount_percentage or Decimal("0.00"),
                rental_period_value=rental_days,
                rental_period_unit=RentalPeriodUnit.DAY,
                rental_start_date=item.rental_start_date,
                rental_end_date=item.rental_end_date,
                notes=item.notes,
                created_by=created_by
            )
            
            # Calculate line total
            line.calculate_line_total()
            lines.append(line)
            subtotal += line.line_total
            line_number += 1
            
            # Reserve inventory units
            for unit_id in item.inventory_unit_ids:
                await self._reserve_inventory_unit(
                    unit_id, transaction.id, item.rental_start_date, item.rental_end_date
                )
        
        # 6. Add tax line
        tax_amount = subtotal * (tax_rate / 100)
        if tax_amount > 0:
            tax_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.TAX,
                description=f"Sales Tax ({tax_rate}%)",
                quantity=Decimal("1"),
                unit_price=tax_amount,
                line_total=tax_amount,
                created_by=created_by
            )
            lines.append(tax_line)
            line_number += 1
        
        # 7. Calculate deposit
        total_before_deposit = subtotal + tax_amount
        deposit_amount = total_before_deposit * (deposit_percentage / 100)
        
        if deposit_amount > 0:
            deposit_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.DEPOSIT,
                description=f"Security Deposit ({deposit_percentage}%)",
                quantity=Decimal("1"),
                unit_price=deposit_amount,
                line_total=deposit_amount,
                created_by=created_by
            )
            lines.append(deposit_line)
        
        # 8. Update transaction totals
        transaction.subtotal = subtotal
        transaction.tax_amount = tax_amount
        transaction.deposit_amount = deposit_amount
        transaction.total_amount = total_before_deposit
        
        # 9. Save transaction and lines
        transaction = await self.transaction_repo.create(transaction)
        
        for line in lines:
            line.transaction_id = transaction.id
            await self.transaction_line_repo.create(line)
        
        transaction._lines = lines
        
        return transaction
    
    async def _check_availability(
        self,
        item_id: UUID,
        location_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[InventoryUnit]:
        """Check inventory availability for rental period."""
        # Get all inventory units for item at location
        all_units = await self.inventory_unit_repo.get_by_item_and_location(
            item_id, location_id
        )
        
        # Filter for rentable units
        available_units = []
        for unit in all_units:
            if unit.current_status != InventoryStatus.AVAILABLE_RENT:
                continue
            
            # Check if unit has any conflicting reservations
            has_conflict = await self._check_reservation_conflict(
                unit.id, start_date, end_date
            )
            
            if not has_conflict:
                available_units.append(unit)
        
        return available_units
    
    async def _check_reservation_conflict(
        self,
        unit_id: UUID,
        start_date: date,
        end_date: date
    ) -> bool:
        """Check if inventory unit has conflicting reservations."""
        # Get all rental transactions with this unit
        transactions = await self.transaction_repo.get_active_rentals_by_unit(unit_id)
        
        for transaction in transactions:
            # Check date overlap
            if (transaction.rental_start_date <= end_date and 
                transaction.rental_end_date >= start_date):
                return True
        
        return False
    
    async def _reserve_inventory_unit(
        self,
        unit_id: UUID,
        transaction_id: UUID,
        start_date: date,
        end_date: date
    ):
        """Reserve inventory unit for rental."""
        unit = await self.inventory_unit_repo.get_by_id(unit_id)
        if not unit:
            raise ValueError(f"Inventory unit {unit_id} not found")
        
        # Update status to reserved
        unit.current_status = InventoryStatus.RESERVED_RENT
        unit.notes = (unit.notes or "") + f"\n[RESERVED] Transaction: {transaction_id}"
        
        await self.inventory_unit_repo.update(unit.id, unit)
    
    async def _generate_transaction_number(self) -> str:
        """Generate unique transaction number."""
        # Format: RNT-YYYYMMDD-XXXX
        today = datetime.utcnow().strftime("%Y%m%d")
        
        # Get count of transactions today
        count = await self.transaction_repo.count_by_date(datetime.utcnow().date())
        
        return f"RNT-{today}-{count + 1:04d}"