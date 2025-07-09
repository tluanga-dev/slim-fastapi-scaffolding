from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .enums import TransactionType, TransactionStatus, PaymentStatus, PaymentMethod, LineItemType, RentalPeriodUnit


class TransactionHeaderBase(BaseModel):
    """Base schema for TransactionHeader."""
    transaction_number: str = Field(..., min_length=1, max_length=50)
    transaction_type: TransactionType
    transaction_date: datetime
    customer_id: UUID
    location_id: UUID
    sales_person_id: Optional[UUID] = None
    status: TransactionStatus = TransactionStatus.DRAFT
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Financial fields
    subtotal: Decimal = Field(default=Decimal('0.00'), ge=0)
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    tax_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    total_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    paid_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    deposit_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    
    # Reference to another transaction
    reference_transaction_id: Optional[UUID] = None
    
    # Payment information
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = Field(None, max_length=100)
    
    # Additional fields
    notes: Optional[str] = None


class TransactionHeaderCreate(TransactionHeaderBase):
    """Schema for creating a TransactionHeader."""
    pass


class TransactionHeaderUpdate(BaseModel):
    """Schema for updating a TransactionHeader."""
    transaction_number: Optional[str] = Field(None, min_length=1, max_length=50)
    transaction_type: Optional[TransactionType] = None
    transaction_date: Optional[datetime] = None
    customer_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    sales_person_id: Optional[UUID] = None
    status: Optional[TransactionStatus] = None
    payment_status: Optional[PaymentStatus] = None
    
    # Financial fields
    subtotal: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    deposit_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Reference to another transaction
    reference_transaction_id: Optional[UUID] = None
    
    # Payment information
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = Field(None, max_length=100)
    
    # Additional fields
    notes: Optional[str] = None


class TransactionHeaderResponse(TransactionHeaderBase):
    """Schema for TransactionHeader response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class TransactionHeaderWithDetails(TransactionHeaderResponse):
    """Schema for TransactionHeader with related details."""
    # Note: These would be populated when the related models exist
    # customer: Optional[CustomerResponse] = None
    # location: Optional[LocationResponse] = None
    # sales_person: Optional[UserResponse] = None
    # reference_transaction: Optional[TransactionHeaderResponse] = None
    # lines: List[TransactionLineResponse] = []
    pass


class TransactionHeaderListResponse(BaseModel):
    """Schema for paginated TransactionHeader list response."""
    items: List[TransactionHeaderResponse]
    total: int
    page: int
    size: int
    pages: int


# Transaction Line Schemas

class TransactionLineBase(BaseModel):
    """Base schema for TransactionLine."""
    transaction_id: UUID
    line_number: int = Field(..., ge=1)
    line_type: LineItemType
    item_id: Optional[UUID] = None
    inventory_unit_id: Optional[UUID] = None
    description: str = Field(..., min_length=1, max_length=500)
    
    # Quantity and pricing fields
    quantity: Decimal = Field(default=Decimal('1.000'), gt=0)
    unit_price: Decimal = Field(default=Decimal('0.00'), ge=0)
    discount_percentage: Decimal = Field(default=Decimal('0.00'), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    tax_rate: Decimal = Field(default=Decimal('0.00'), ge=0, le=100)
    tax_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    line_total: Decimal = Field(default=Decimal('0.00'), ge=0)
    
    # Rental specific fields
    rental_period_value: Optional[int] = Field(None, gt=0)
    rental_period_unit: Optional[RentalPeriodUnit] = None
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    
    # Return tracking
    returned_quantity: Decimal = Field(default=Decimal('0.000'), ge=0)
    return_date: Optional[date] = None
    
    # Additional fields
    notes: Optional[str] = None


class TransactionLineCreate(TransactionLineBase):
    """Schema for creating a TransactionLine."""
    pass


class TransactionLineUpdate(BaseModel):
    """Schema for updating a TransactionLine."""
    line_number: Optional[int] = Field(None, ge=1)
    line_type: Optional[LineItemType] = None
    item_id: Optional[UUID] = None
    inventory_unit_id: Optional[UUID] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    
    # Quantity and pricing fields
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    
    # Rental specific fields
    rental_period_value: Optional[int] = Field(None, gt=0)
    rental_period_unit: Optional[RentalPeriodUnit] = None
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    
    # Return tracking
    returned_quantity: Optional[Decimal] = Field(None, ge=0)
    return_date: Optional[date] = None
    
    # Additional fields
    notes: Optional[str] = None


class TransactionLineResponse(TransactionLineBase):
    """Schema for TransactionLine response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class TransactionLineWithDetails(TransactionLineResponse):
    """Schema for TransactionLine with related details."""
    # Note: These would be populated when the related models exist
    # item: Optional[ItemResponse] = None
    # inventory_unit: Optional[InventoryUnitResponse] = None
    pass


class TransactionLineListResponse(BaseModel):
    """Schema for paginated TransactionLine list response."""
    items: List[TransactionLineResponse]
    total: int
    page: int
    size: int
    pages: int


# Combined Transaction with Lines
class TransactionHeaderWithLines(TransactionHeaderResponse):
    """Schema for TransactionHeader with its lines."""
    lines: List[TransactionLineResponse] = []


class TransactionCreateWithLines(BaseModel):
    """Schema for creating a complete transaction with lines."""
    header: TransactionHeaderCreate
    lines: List[TransactionLineCreate] = []