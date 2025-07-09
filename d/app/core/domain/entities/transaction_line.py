from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, validator

from .base import BaseEntity
from ..value_objects import LineItemType, RentalPeriodUnit


class TransactionLine(BaseEntity):
    """Domain entity for transaction line items."""
    
    transaction_id: UUID
    line_number: int = Field(gt=0, description="Line number must be positive")
    line_type: LineItemType
    item_id: Optional[UUID] = None
    inventory_unit_id: Optional[UUID] = None
    description: str = Field(max_length=500)
    
    # Quantity and pricing fields
    quantity: Decimal = Field(default=Decimal("1"), ge=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    discount_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    line_total: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Rental specific fields
    rental_period_value: Optional[int] = Field(default=None, gt=0)
    rental_period_unit: Optional[RentalPeriodUnit] = None
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    
    # Return tracking
    returned_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    return_date: Optional[date] = None
    
    # Additional fields
    notes: Optional[str] = None
    
    @validator('returned_quantity')
    def validate_returned_quantity(cls, v, values):
        """Ensure returned quantity doesn't exceed original quantity."""
        if 'quantity' in values and v > values['quantity']:
            raise ValueError("Returned quantity cannot exceed original quantity")
        return v
    
    @validator('rental_end_date')
    def validate_rental_dates(cls, v, values):
        """Ensure rental end date is after start date."""
        if v and 'rental_start_date' in values and values['rental_start_date']:
            if v < values['rental_start_date']:
                raise ValueError("Rental end date must be after start date")
        return v
    
    @validator('line_type')
    def validate_rental_fields(cls, v, values):
        """Ensure rental fields are set for rental line items."""
        if v == LineItemType.RENTAL:
            if not all([
                values.get('rental_period_value'),
                values.get('rental_period_unit'),
                values.get('rental_start_date'),
                values.get('rental_end_date')
            ]):
                raise ValueError("Rental line items must have all rental fields set")
        return v
    
    def calculate_line_total(self) -> Decimal:
        """Calculate the line total based on quantity, price, discounts, and tax."""
        subtotal = self.quantity * self.unit_price
        
        # Apply discount
        if self.discount_percentage > 0:
            discount = subtotal * (self.discount_percentage / 100)
            subtotal -= discount
        elif self.discount_amount > 0:
            subtotal -= self.discount_amount
            
        # Ensure subtotal is not negative
        subtotal = max(Decimal("0"), subtotal)
        
        # Add tax
        total = subtotal + self.tax_amount
        
        return total
    
    def calculate_tax_amount(self) -> Decimal:
        """Calculate tax amount based on the taxable subtotal."""
        subtotal = self.quantity * self.unit_price
        
        # Apply discount to get taxable amount
        if self.discount_percentage > 0:
            discount = subtotal * (self.discount_percentage / 100)
            subtotal -= discount
        elif self.discount_amount > 0:
            subtotal -= self.discount_amount
            
        # Ensure subtotal is not negative
        subtotal = max(Decimal("0"), subtotal)
        
        # Calculate tax
        tax = subtotal * (self.tax_rate / 100)
        
        return tax.quantize(Decimal("0.01"))
    
    def update_calculations(self) -> None:
        """Update calculated fields."""
        self.tax_amount = self.calculate_tax_amount()
        self.line_total = self.calculate_line_total()
    
    def process_return(self, quantity_to_return: Decimal, return_date: date) -> None:
        """Process a return for this line item."""
        if quantity_to_return <= 0:
            raise ValueError("Return quantity must be positive")
            
        if self.returned_quantity + quantity_to_return > self.quantity:
            raise ValueError("Cannot return more than original quantity")
            
        self.returned_quantity += quantity_to_return
        self.return_date = return_date
    
    def get_remaining_quantity(self) -> Decimal:
        """Get the quantity that hasn't been returned."""
        return self.quantity - self.returned_quantity
    
    def is_fully_returned(self) -> bool:
        """Check if all items have been returned."""
        return self.returned_quantity >= self.quantity
    
    def is_rental(self) -> bool:
        """Check if this is a rental line item."""
        return self.line_type == LineItemType.RENTAL
    
    def get_rental_duration_days(self) -> Optional[int]:
        """Calculate rental duration in days."""
        if self.rental_start_date and self.rental_end_date:
            return (self.rental_end_date - self.rental_start_date).days + 1
        return None