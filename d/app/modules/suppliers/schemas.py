from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms


class SupplierCreate(BaseModel):
    """Schema for creating a new supplier."""
    supplier_code: str = Field(..., min_length=1, max_length=50, description="Unique supplier code")
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    supplier_type: SupplierType = Field(..., description="Type of supplier")
    contact_person: Optional[str] = Field(None, max_length=255, description="Contact person name")
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    address: Optional[str] = Field(None, description="Company address")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax identification number")
    payment_terms: Optional[PaymentTerms] = Field(PaymentTerms.NET30, description="Payment terms")
    credit_limit: Optional[Decimal] = Field(Decimal('0'), ge=0, description="Credit limit")
    supplier_tier: Optional[SupplierTier] = Field(SupplierTier.STANDARD, description="Supplier tier")
    created_by: Optional[str] = Field(None, max_length=255, description="User who created the supplier")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and ('@' not in v or '.' not in v.split('@')[-1]):
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('credit_limit')
    @classmethod
    def validate_credit_limit(cls, v):
        if v is not None and v < 0:
            raise ValueError('Credit limit cannot be negative')
        return v


class SupplierUpdate(BaseModel):
    """Schema for updating supplier basic information."""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Company name")
    supplier_type: Optional[SupplierType] = Field(None, description="Type of supplier")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax identification number")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the supplier")


class SupplierContactUpdate(BaseModel):
    """Schema for updating supplier contact information."""
    contact_person: Optional[str] = Field(None, max_length=255, description="Contact person name")
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    address: Optional[str] = Field(None, description="Company address")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the contact info")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and ('@' not in v or '.' not in v.split('@')[-1]):
            raise ValueError('Invalid email format')
        return v


class SupplierPaymentUpdate(BaseModel):
    """Schema for updating supplier payment terms and credit limit."""
    payment_terms: PaymentTerms = Field(..., description="Payment terms")
    credit_limit: Optional[Decimal] = Field(None, ge=0, description="Credit limit")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the payment terms")
    
    @field_validator('credit_limit')
    @classmethod
    def validate_credit_limit(cls, v):
        if v is not None and v < 0:
            raise ValueError('Credit limit cannot be negative')
        return v


class SupplierTierUpdate(BaseModel):
    """Schema for updating supplier tier."""
    supplier_tier: SupplierTier = Field(..., description="Supplier tier")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the tier")


class SupplierStatusUpdate(BaseModel):
    """Schema for updating supplier status."""
    is_active: bool = Field(..., description="Supplier active status")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the status")


class SupplierPerformanceUpdate(BaseModel):
    """Schema for updating supplier performance metrics."""
    total_orders: Optional[int] = Field(None, ge=0, description="Total number of orders")
    total_spend: Optional[Decimal] = Field(None, ge=0, description="Total amount spent")
    average_delivery_days: Optional[int] = Field(None, ge=0, description="Average delivery days")
    quality_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Quality rating (0-5)")
    last_order_date: Optional[datetime] = Field(None, description="Date of last order")
    
    @field_validator('quality_rating')
    @classmethod
    def validate_quality_rating(cls, v):
        if v is not None and not (0 <= v <= 5):
            raise ValueError('Quality rating must be between 0 and 5')
        return v


class SupplierResponse(BaseModel):
    """Schema for supplier response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    supplier_code: str
    company_name: str
    supplier_type: SupplierType
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: PaymentTerms
    credit_limit: Decimal
    supplier_tier: SupplierTier
    
    # Performance metrics
    total_orders: int
    total_spend: Decimal
    average_delivery_days: int
    quality_rating: Decimal
    last_order_date: Optional[datetime] = None
    
    # Standard fields
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    def get_display_name(self) -> str:
        """Get the display name for the supplier."""
        return self.company_name
    
    def can_place_order(self, order_amount: Decimal) -> bool:
        """Check if an order can be placed with this supplier."""
        if not self.is_active:
            return False
        if self.credit_limit > 0 and order_amount > self.credit_limit:
            return False
        return True
    
    def get_performance_score(self) -> Decimal:
        """Calculate overall performance score (0-100)."""
        if self.total_orders == 0:
            return Decimal('0')
            
        # Weighted scoring: Quality (40%), Delivery (30%), Tier (30%)
        quality_score = (self.quality_rating / 5) * 40
        
        # Delivery score (inverse of delivery days, capped at 30 days)
        delivery_score = max(0, (30 - min(self.average_delivery_days, 30)) / 30) * 30
        
        # Tier score
        tier_scores = {
            SupplierTier.PREFERRED: 30,
            SupplierTier.STANDARD: 20,
            SupplierTier.RESTRICTED: 10
        }
        tier_score = tier_scores.get(self.supplier_tier, 15)
        
        return quality_score + Decimal(str(delivery_score)) + Decimal(str(tier_score))


class SupplierListResponse(BaseModel):
    """Schema for supplier list response."""
    suppliers: list[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SupplierPerformanceResponse(BaseModel):
    """Schema for supplier performance metrics response."""
    supplier_id: UUID
    supplier_code: str
    company_name: str
    total_orders: int
    total_spend: Decimal
    average_delivery_days: int
    quality_rating: Decimal
    last_order_date: Optional[datetime] = None
    performance_score: Decimal
    supplier_tier: SupplierTier