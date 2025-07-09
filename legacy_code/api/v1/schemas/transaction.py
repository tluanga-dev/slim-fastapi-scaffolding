from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from ....domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod,
    LineItemType, RentalPeriodUnit
)


# TransactionLine Schemas
class TransactionLineBase(BaseModel):
    """Base schema for transaction line."""
    line_type: LineItemType = Field(..., description="Type of line item")
    item_id: Optional[UUID] = Field(None, description="Item ID for product/service lines")
    inventory_unit_id: Optional[UUID] = Field(None, description="Specific inventory unit ID")
    description: str = Field(..., description="Line item description")
    quantity: Decimal = Field(Decimal("1"), ge=0, description="Quantity")
    unit_price: Optional[Decimal] = Field(None, description="Unit price (uses SKU price if not provided, can be negative for discounts)")
    discount_percentage: Decimal = Field(Decimal("0"), ge=0, le=100, description="Discount percentage")
    discount_amount: Decimal = Field(Decimal("0"), ge=0, description="Discount amount")
    tax_rate: Decimal = Field(Decimal("0"), ge=0, description="Tax rate percentage")


class RentalLineCreate(TransactionLineBase):
    """Schema for creating rental line."""
    rental_period_value: Optional[int] = Field(None, ge=1, description="Rental period value")
    rental_period_unit: Optional[RentalPeriodUnit] = Field(None, description="Rental period unit")


class TransactionLineCreate(TransactionLineBase):
    """Schema for creating transaction line."""
    pass


class TransactionLineUpdate(BaseModel):
    """Schema for updating transaction line."""
    quantity: Optional[Decimal] = Field(None, ge=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class TransactionLineResponse(TransactionLineBase):
    """Schema for transaction line response."""
    id: UUID
    transaction_id: UUID
    line_number: int
    tax_amount: Decimal
    line_total: Decimal
    rental_period_value: Optional[int]
    rental_period_unit: Optional[RentalPeriodUnit]
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    returned_quantity: Decimal
    return_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    # Enhanced item details
    item_name: Optional[str] = None
    item_sku: Optional[str] = None
    item_category: Optional[str] = None
    item_brand: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# TransactionHeader Schemas
class TransactionHeaderBase(BaseModel):
    """Base schema for transaction header."""
    customer_id: UUID = Field(..., description="Customer ID")
    location_id: UUID = Field(..., description="Location ID")
    sales_person_id: Optional[UUID] = Field(None, description="Sales person ID")
    notes: Optional[str] = Field(None, description="Transaction notes")


class SaleTransactionCreate(TransactionHeaderBase):
    """Schema for creating sale transaction."""
    items: List[Dict[str, Any]] = Field(..., description="List of items to sell")
    discount_amount: Decimal = Field(Decimal("0"), ge=0, description="Overall discount")
    tax_rate: Decimal = Field(Decimal("0"), ge=0, description="Tax rate percentage")
    auto_reserve: bool = Field(True, description="Auto-reserve inventory")


class RentalTransactionCreate(TransactionHeaderBase):
    """Schema for creating rental transaction."""
    rental_start_date: date = Field(..., description="Rental start date")
    rental_end_date: date = Field(..., description="Rental end date")
    items: List[Dict[str, Any]] = Field(..., description="List of items to rent")
    deposit_amount: Decimal = Field(Decimal("0"), ge=0, description="Security deposit")
    discount_amount: Decimal = Field(Decimal("0"), ge=0, description="Overall discount")
    tax_rate: Decimal = Field(Decimal("0"), ge=0, description="Tax rate percentage")
    auto_reserve: bool = Field(True, description="Auto-reserve inventory")


class TransactionHeaderUpdate(BaseModel):
    """Schema for updating transaction header."""
    sales_person_id: Optional[UUID] = None
    notes: Optional[str] = None
    rental_end_date: Optional[date] = None


class SupplierAddress(BaseModel):
    """Supplier address information."""
    street: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None


class SupplierContact(BaseModel):
    """Supplier contact information."""
    contact_type: str
    contact_value: str
    contact_label: Optional[str] = None
    is_primary: bool = False


class SupplierSummary(BaseModel):
    """Supplier summary for transaction responses."""
    id: str
    company_name: str
    supplier_code: str
    display_name: str
    contact_person: Optional[str] = None
    supplier_type: str
    supplier_tier: str
    is_active: bool
    # Enhanced contact and address information
    contacts: List[SupplierContact] = []
    addresses: List[SupplierAddress] = []
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None


class TransactionHeaderResponse(TransactionHeaderBase):
    """Schema for transaction header response."""
    id: UUID
    transaction_number: str
    transaction_type: TransactionType
    transaction_date: datetime
    status: TransactionStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    deposit_amount: Decimal
    balance_due: Decimal = Field(..., description="Calculated balance due")
    total_items: Optional[int] = Field(None, description="Total number of items in transaction")
    reference_transaction_id: Optional[UUID]
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    actual_return_date: Optional[date]
    payment_method: Optional[PaymentMethod]
    payment_reference: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    lines: Optional[List[TransactionLineResponse]] = None
    supplier: Optional[SupplierSummary] = None
    
    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""
    items: List[TransactionHeaderResponse]
    total: int
    skip: int
    limit: int


# Payment Schemas
class PaymentRequest(BaseModel):
    """Schema for processing payment."""
    payment_amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_reference: Optional[str] = Field(None, description="Payment reference (check #, transaction ID, etc.)")
    process_inventory: bool = Field(True, description="Process inventory updates")


class RefundRequest(BaseModel):
    """Schema for processing refund."""
    refund_amount: Decimal = Field(..., gt=0, description="Refund amount")
    reason: str = Field(..., description="Refund reason")


# Transaction Operation Schemas
class CancelTransactionRequest(BaseModel):
    """Schema for cancelling transaction."""
    cancellation_reason: str = Field(..., description="Cancellation reason")
    release_inventory: bool = Field(True, description="Release reserved inventory")


class CompleteRentalReturnRequest(BaseModel):
    """Schema for completing rental return."""
    actual_return_date: date = Field(..., description="Actual return date")
    condition_notes: Optional[str] = Field(None, description="Condition notes")


# Return Processing Schemas
class ProcessReturnLineRequest(BaseModel):
    """Schema for processing return on a line."""
    line_id: UUID = Field(..., description="Transaction line ID")
    return_quantity: Decimal = Field(..., gt=0, description="Quantity to return")
    return_reason: Optional[str] = Field(None, description="Return reason")


class ProcessPartialReturnRequest(BaseModel):
    """Schema for processing partial return."""
    lines: List[ProcessReturnLineRequest] = Field(..., description="Lines to return")
    process_refund: bool = Field(False, description="Process refund immediately")


# Query Schemas
class TransactionFilterParams(BaseModel):
    """Schema for transaction filter parameters."""
    transaction_type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    payment_status: Optional[PaymentStatus] = None
    customer_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_cancelled: bool = False


# Summary and Report Schemas
class CustomerTransactionSummary(BaseModel):
    """Schema for customer transaction summary."""
    customer_id: str
    customer_name: str
    total_transactions: int
    total_sales: int
    total_rentals: int
    total_revenue: float
    total_paid: float
    total_outstanding: float
    active_rentals: int
    overdue_rentals: int
    customer_since: datetime
    customer_tier: Optional[str]


class DailyTransactionSummary(BaseModel):
    """Schema for daily transaction summary."""
    date: date
    transaction_count: int
    total_revenue: float
    total_paid: float
    total_discount: float
    total_tax: float
    outstanding_amount: float
    transactions: Optional[List[TransactionHeaderResponse]] = None


class RevenueReport(BaseModel):
    """Schema for revenue report."""
    period: date
    transaction_count: int
    total_revenue: float
    total_paid: float
    outstanding: float


class OverdueRental(BaseModel):
    """Schema for overdue rental."""
    transaction_id: UUID
    transaction_number: str
    customer_id: UUID
    customer_name: str
    rental_end_date: date
    days_overdue: int
    total_amount: Decimal
    balance_due: Decimal
    items: List[str]