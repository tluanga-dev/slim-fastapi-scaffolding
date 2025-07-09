from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ....domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod
)
from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade


# Rental Booking Schemas
class RentalBookingItemCreate(BaseModel):
    """Schema for creating a rental booking item."""
    item_id: UUID
    quantity: int = Field(gt=0)
    rental_start_date: date
    rental_end_date: date
    inventory_unit_ids: Optional[List[UUID]] = None
    custom_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    
    @field_validator('rental_end_date')
    def validate_dates(cls, v, values):
        if 'rental_start_date' in values.data and v < values.data['rental_start_date']:
            raise ValueError('End date must be after start date')
        return v


class CreateRentalBookingRequest(BaseModel):
    """Request schema for creating a rental booking."""
    customer_id: UUID
    location_id: UUID
    items: List[RentalBookingItemCreate]
    deposit_percentage: Decimal = Field(default=Decimal("30.00"), ge=0, le=100)
    tax_rate: Decimal = Field(default=Decimal("8.25"), ge=0)
    sales_person_id: Optional[UUID] = None
    notes: Optional[str] = None


# Checkout Schemas
class CheckoutRentalRequest(BaseModel):
    """Request schema for rental checkout."""
    payment_amount: Decimal = Field(gt=0)
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    collect_full_payment: bool = False
    additional_notes: Optional[str] = None


# Pickup Schemas
class RentalPickupItemRequest(BaseModel):
    """Request schema for rental pickup item."""
    inventory_unit_id: UUID
    serial_number: str
    condition_notes: Optional[str] = None
    photos: Optional[List[str]] = None
    accessories_included: Optional[List[str]] = None


class ProcessRentalPickupRequest(BaseModel):
    """Request schema for processing rental pickup."""
    pickup_items: List[RentalPickupItemRequest]
    pickup_person_name: str
    pickup_person_id: Optional[str] = None
    pickup_notes: Optional[str] = None


# Return Schemas
class ReturnItemRequest(BaseModel):
    """Request schema for return item."""
    inventory_unit_id: UUID
    condition_grade: ConditionGrade
    is_damaged: bool = False
    damage_description: Optional[str] = None
    damage_photos: Optional[List[str]] = None
    missing_accessories: Optional[List[str]] = None
    cleaning_required: bool = False


class CompleteRentalReturnRequest(BaseModel):
    """Request schema for completing rental return."""
    return_items: List[ReturnItemRequest]
    is_partial_return: bool = False
    late_fee_waived: bool = False
    damage_fee_percentage: Decimal = Field(default=Decimal("80.00"), ge=0, le=100)
    process_refund: bool = True
    refund_method: Optional[PaymentMethod] = None
    return_notes: Optional[str] = None


# Extension Schemas
class ExtendRentalPeriodRequest(BaseModel):
    """Request schema for extending rental period."""
    new_end_date: date
    payment_amount: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    apply_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    extension_notes: Optional[str] = None


# Cancellation Schemas
class CancelRentalBookingRequest(BaseModel):
    """Request schema for cancelling rental booking."""
    cancellation_reason: str
    refund_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    cancellation_fee: Optional[Decimal] = Field(None, ge=0)
    refund_method: Optional[PaymentMethod] = None
    refund_reference: Optional[str] = None


# Response Schemas
class TransactionLineResponse(BaseModel):
    """Response schema for transaction line."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    line_number: int
    line_type: str
    item_id: Optional[UUID]
    inventory_unit_id: Optional[UUID]
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    returned_quantity: Decimal
    return_date: Optional[date]
    notes: Optional[str]


class RentalTransactionResponse(BaseModel):
    """Response schema for rental transaction."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    transaction_type: TransactionType
    transaction_date: datetime
    customer_id: UUID
    location_id: UUID
    sales_person_id: Optional[UUID]
    status: TransactionStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    deposit_amount: Decimal
    balance_due: Decimal
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    actual_return_date: Optional[date]
    rental_days: int
    notes: Optional[str]
    payment_method: Optional[PaymentMethod]
    payment_reference: Optional[str]
    lines: List[TransactionLineResponse] = []
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]


class RentalBookingResponse(BaseModel):
    """Response schema for rental booking creation."""
    transaction: RentalTransactionResponse
    message: str
    booking_summary: Dict[str, Any]


class RentalCheckoutResponse(BaseModel):
    """Response schema for rental checkout."""
    transaction: RentalTransactionResponse
    message: str
    payment_summary: Dict[str, Any]


class RentalPickupResponse(BaseModel):
    """Response schema for rental pickup."""
    transaction: RentalTransactionResponse
    inspection_reports: List[Dict[str, Any]]
    pickup_summary: Dict[str, Any]
    message: str


class RentalReturnResponse(BaseModel):
    """Response schema for rental return."""
    transaction: RentalTransactionResponse
    rental_return: Dict[str, Any]
    return_summary: Dict[str, Any]
    message: str


class RentalExtensionResponse(BaseModel):
    """Response schema for rental extension."""
    transaction: RentalTransactionResponse
    extension_summary: Dict[str, Any]
    message: str


class RentalCancellationResponse(BaseModel):
    """Response schema for rental cancellation."""
    transaction: RentalTransactionResponse
    refund_summary: Dict[str, Any]
    message: str


# Search and Filter Schemas
class RentalTransactionFilter(BaseModel):
    """Filter schema for rental transactions."""
    customer_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    status: Optional[TransactionStatus] = None
    payment_status: Optional[PaymentStatus] = None
    rental_start_date_from: Optional[date] = None
    rental_start_date_to: Optional[date] = None
    rental_end_date_from: Optional[date] = None
    rental_end_date_to: Optional[date] = None
    transaction_date_from: Optional[date] = None
    transaction_date_to: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    has_overdue_items: Optional[bool] = None
    search: Optional[str] = None


class RentalAvailabilityCheckRequest(BaseModel):
    """Request schema for checking rental availability."""
    item_id: UUID
    location_id: UUID
    rental_start_date: date
    rental_end_date: date
    quantity: int = Field(gt=0)


class RentalAvailabilityResponse(BaseModel):
    """Response schema for rental availability."""
    item_id: UUID
    location_id: UUID
    rental_period: Dict[str, date]
    requested_quantity: int
    available_quantity: int
    is_available: bool
    available_units: List[Dict[str, Any]]
    conflicting_rentals: List[Dict[str, Any]] = []