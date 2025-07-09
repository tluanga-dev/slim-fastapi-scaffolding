from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

from ....domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms


class SupplierCreate(BaseModel):
    """Schema for creating a supplier."""
    supplier_code: str = Field(..., min_length=1, max_length=50)
    company_name: str = Field(..., min_length=1, max_length=255)
    supplier_type: SupplierType
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[PaymentTerms] = PaymentTerms.NET30
    credit_limit: Optional[Decimal] = Field(default=0, ge=0)
    supplier_tier: Optional[SupplierTier] = SupplierTier.STANDARD

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @validator('supplier_code')
    def validate_supplier_code(cls, v):
        if not v or not v.strip():
            raise ValueError('Supplier code cannot be empty')
        return v.strip().upper()

    @validator('company_name')
    def validate_company_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        return v.strip()


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier."""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    supplier_type: Optional[SupplierType] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[PaymentTerms] = None
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    supplier_tier: Optional[SupplierTier] = None

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @validator('company_name')
    def validate_company_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Company name cannot be empty')
        return v.strip() if v else v


class SupplierResponse(BaseModel):
    """Schema for supplier response."""
    id: UUID
    supplier_code: str
    company_name: str
    supplier_type: str
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    tax_id: Optional[str]
    payment_terms: str
    credit_limit: Decimal
    supplier_tier: str
    is_active: bool
    total_orders: int
    total_spend: Decimal
    average_delivery_days: int
    quality_rating: Decimal
    last_order_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    display_name: str
    performance_score: Optional[Decimal] = None

    @classmethod
    def from_entity(cls, supplier):
        """Create response from domain entity."""
        return cls(
            id=supplier.id,
            supplier_code=supplier.supplier_code,
            company_name=supplier.company_name,
            supplier_type=supplier.supplier_type.value,
            contact_person=supplier.contact_person,
            email=supplier.email,
            phone=supplier.phone,
            address=supplier.address,
            tax_id=supplier.tax_id,
            payment_terms=supplier.payment_terms.value,
            credit_limit=supplier.credit_limit,
            supplier_tier=supplier.supplier_tier.value,
            is_active=supplier.is_active,
            total_orders=supplier.total_orders,
            total_spend=supplier.total_spend,
            average_delivery_days=supplier.average_delivery_days,
            quality_rating=supplier.quality_rating,
            last_order_date=supplier.last_order_date,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at,
            created_by=supplier.created_by,
            updated_by=supplier.updated_by,
            display_name=supplier.get_display_name(),
            performance_score=supplier.get_performance_score()
        )

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    """Schema for paginated supplier list response."""
    items: List[SupplierResponse]
    total: int
    skip: int
    limit: int


class SupplierPerformanceUpdate(BaseModel):
    """Schema for updating supplier performance metrics."""
    total_orders: Optional[int] = Field(None, ge=0)
    total_spend: Optional[Decimal] = Field(None, ge=0)
    average_delivery_days: Optional[int] = Field(None, ge=0)
    quality_rating: Optional[Decimal] = Field(None, ge=0, le=5)


class SupplierAnalytics(BaseModel):
    """Schema for supplier analytics data."""
    total_suppliers: int
    active_suppliers: int
    supplier_type_distribution: dict
    supplier_tier_distribution: dict
    payment_terms_distribution: dict
    monthly_new_suppliers: List[dict]
    top_suppliers_by_spend: List[dict]
    total_spend: Decimal
    average_quality_rating: Decimal


class SupplierSearchRequest(BaseModel):
    """Schema for supplier search requests."""
    query: str = Field(..., min_length=1)
    limit: Optional[int] = Field(default=10, ge=1, le=50)


class SupplierStatusUpdate(BaseModel):
    """Schema for updating supplier status."""
    is_active: bool