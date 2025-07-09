from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ..entities.base import BaseEntity
from ..value_objects.transaction_type import LineItemType, RentalPeriodUnit


class TransactionLine(BaseEntity):
    """Transaction Line entity representing a line item in a transaction."""
    
    def __init__(
        self,
        transaction_id: UUID,
        line_number: int,
        line_type: LineItemType,
        item_id: Optional[UUID] = None,
        inventory_unit_id: Optional[UUID] = None,
        description: str = "",
        quantity: Decimal = Decimal("1"),
        unit_price: Decimal = Decimal("0.00"),
        discount_percentage: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        tax_rate: Decimal = Decimal("0.00"),
        tax_amount: Decimal = Decimal("0.00"),
        line_total: Decimal = Decimal("0.00"),
        rental_period_value: Optional[int] = None,
        rental_period_unit: Optional[RentalPeriodUnit] = None,
        rental_start_date: Optional[date] = None,
        rental_end_date: Optional[date] = None,
        returned_quantity: Decimal = Decimal("0"),
        return_date: Optional[date] = None,
        notes: Optional[str] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Initialize Transaction Line entity."""
        super().__init__(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            is_active=is_active,
            created_by=created_by,
            updated_by=updated_by
        )
        self.transaction_id = transaction_id
        self.line_number = line_number
        self.line_type = line_type
        self.item_id = item_id
        self.inventory_unit_id = inventory_unit_id
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.discount_percentage = discount_percentage
        self.discount_amount = discount_amount
        self.tax_rate = tax_rate
        self.tax_amount = tax_amount
        self.line_total = line_total
        self.rental_period_value = rental_period_value
        self.rental_period_unit = rental_period_unit
        self.rental_start_date = rental_start_date
        self.rental_end_date = rental_end_date
        self.returned_quantity = returned_quantity
        self.return_date = return_date
        self.notes = notes
        self._validate()
    
    def _validate(self):
        """Validate transaction line business rules."""
        if not self.transaction_id:
            raise ValueError("Transaction ID is required")
        
        if self.line_number < 1:
            raise ValueError("Line number must be positive")
        
        if self.line_type not in LineItemType:
            raise ValueError(f"Invalid line item type: {self.line_type}")
        
        if not self.description or not self.description.strip():
            raise ValueError("Description is required")
        
        # Validate quantities and amounts
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        # Allow negative unit prices for discount lines
        if self.unit_price < 0 and self.line_type != LineItemType.DISCOUNT:
            raise ValueError("Unit price cannot be negative")
        
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        
        if self.discount_amount < 0:
            raise ValueError("Discount amount cannot be negative")
        
        if self.tax_rate < 0:
            raise ValueError("Tax rate cannot be negative")
        
        if self.tax_amount < 0:
            raise ValueError("Tax amount cannot be negative")
        
        if self.returned_quantity < 0:
            raise ValueError("Returned quantity cannot be negative")
        
        if self.returned_quantity > self.quantity:
            raise ValueError("Returned quantity cannot exceed ordered quantity")
        
        # Validate product/service lines have SKU
        if self.line_type in [LineItemType.PRODUCT, LineItemType.SERVICE]:
            if not self.item_id:
                raise ValueError(f"Item ID is required for {self.line_type.value} lines")
        
        # Validate rental information
        if self.rental_period_value is not None:
            if self.rental_period_value < 1:
                raise ValueError("Rental period value must be positive")
            if not self.rental_period_unit:
                raise ValueError("Rental period unit is required when period value is specified")
        
        if self.rental_start_date and self.rental_end_date:
            if self.rental_end_date < self.rental_start_date:
                raise ValueError("Rental end date must be after start date")
    
    def calculate_line_total(self):
        """Calculate line total based on quantity, price, discount, and tax."""
        # Base calculation
        subtotal = self.quantity * self.unit_price
        
        # Apply discount
        if self.discount_percentage > 0:
            self.discount_amount = subtotal * (self.discount_percentage / 100)
        
        discounted_amount = subtotal - self.discount_amount
        
        # Calculate tax
        if self.tax_rate > 0:
            self.tax_amount = discounted_amount * (self.tax_rate / 100)
        
        # Calculate final total
        self.line_total = discounted_amount + self.tax_amount
        
        # For discount lines, make total negative
        if self.line_type == LineItemType.DISCOUNT:
            self.line_total = -abs(self.line_total)
    
    def apply_discount(
        self,
        discount_percentage: Optional[Decimal] = None,
        discount_amount: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ):
        """Apply discount to line item."""
        if discount_percentage is not None and discount_amount is not None:
            raise ValueError("Cannot apply both percentage and amount discount")
        
        if discount_percentage is not None:
            if discount_percentage < 0 or discount_percentage > 100:
                raise ValueError("Discount percentage must be between 0 and 100")
            self.discount_percentage = discount_percentage
            self.discount_amount = Decimal("0.00")
        
        if discount_amount is not None:
            if discount_amount < 0:
                raise ValueError("Discount amount cannot be negative")
            self.discount_amount = discount_amount
            self.discount_percentage = Decimal("0.00")
        
        self.calculate_line_total()
        self.update_timestamp(updated_by)
    
    def process_return(
        self,
        return_quantity: Decimal,
        return_date: date,
        return_reason: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Process return for this line item."""
        if return_quantity <= 0:
            raise ValueError("Return quantity must be positive")
        
        if return_quantity > (self.quantity - self.returned_quantity):
            raise ValueError("Return quantity exceeds remaining quantity")
        
        self.returned_quantity += return_quantity
        self.return_date = return_date
        
        if return_reason:
            return_note = f"\n[RETURN] {return_date}: Qty {return_quantity} - {return_reason}"
            self.notes = (self.notes or "") + return_note
        
        self.update_timestamp(updated_by)
    
    def update_rental_period(
        self,
        new_end_date: date,
        updated_by: Optional[str] = None
    ):
        """Update rental period end date."""
        if not self.rental_start_date:
            raise ValueError("Cannot update rental period for non-rental line")
        
        if new_end_date < self.rental_start_date:
            raise ValueError("End date must be after start date")
        
        self.rental_end_date = new_end_date
        
        # Recalculate rental days
        rental_days = (new_end_date - self.rental_start_date).days + 1
        
        # Update rental period value if using day units
        if self.rental_period_unit == RentalPeriodUnit.DAY:
            self.rental_period_value = rental_days
        
        self.update_timestamp(updated_by)
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity not yet returned."""
        return self.quantity - self.returned_quantity
    
    @property
    def is_fully_returned(self) -> bool:
        """Check if all items have been returned."""
        return self.returned_quantity >= self.quantity
    
    @property
    def is_partially_returned(self) -> bool:
        """Check if some items have been returned."""
        return 0 < self.returned_quantity < self.quantity
    
    @property
    def rental_days(self) -> int:
        """Calculate rental days."""
        if not self.rental_start_date or not self.rental_end_date:
            return 0
        return (self.rental_end_date - self.rental_start_date).days + 1
    
    @property
    def effective_unit_price(self) -> Decimal:
        """Calculate effective unit price after discount."""
        if self.quantity == 0:
            return Decimal("0.00")
        
        subtotal = self.quantity * self.unit_price
        discounted_amount = subtotal - self.discount_amount
        
        return discounted_amount / self.quantity
    
    def __str__(self) -> str:
        """String representation of transaction line."""
        return f"TransactionLine({self.line_number}: {self.description} - Qty: {self.quantity})"
    
    def __repr__(self) -> str:
        """Developer representation of transaction line."""
        return (
            f"TransactionLine(id={self.id}, line={self.line_number}, "
            f"type={self.line_type.value}, qty={self.quantity}, "
            f"total=${self.line_total})"
        )