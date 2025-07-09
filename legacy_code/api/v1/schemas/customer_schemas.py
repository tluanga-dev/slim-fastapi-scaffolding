from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict

from ....domain.value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus


class CustomerBase(BaseModel):
    """Base schema for Customer."""
    customer_code: str = Field(..., min_length=1, max_length=20, description="Unique customer code")
    customer_type: CustomerType = Field(..., description="Type of customer")
    business_name: Optional[str] = Field(None, max_length=200, description="Business name")
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax ID")
    customer_tier: CustomerTier = Field(default=CustomerTier.BRONZE, description="Customer tier")
    credit_limit: Decimal = Field(default=Decimal("0.00"), ge=0, description="Credit limit")
    
    @field_validator('customer_code')
    @classmethod
    def validate_customer_code(cls, v: str) -> str:
        """Validate customer code is not empty."""
        if not v or not v.strip():
            raise ValueError("Customer code cannot be empty")
        return v.strip()
    
    @field_validator('business_name', 'first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate names are not empty if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    @field_validator('tax_id')
    @classmethod
    def validate_tax_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate tax ID format."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    model_config = ConfigDict(use_enum_values=True)


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    business_name: Optional[str] = Field(None, max_length=200)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    customer_tier: Optional[CustomerTier] = None
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    
    model_config = ConfigDict(use_enum_values=True)


class CustomerResponse(CustomerBase):
    """Schema for customer response."""
    id: UUID
    blacklist_status: BlacklistStatus
    lifetime_value: Decimal
    last_transaction_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool
    display_name: str = Field(..., description="Computed display name")
    
    @classmethod
    def from_entity(cls, customer):
        """Create response from customer entity."""
        return cls(
            id=customer.id,
            customer_code=customer.customer_code,
            customer_type=customer.customer_type.value,
            business_name=customer.business_name,
            first_name=customer.first_name,
            last_name=customer.last_name,
            tax_id=customer.tax_id,
            customer_tier=customer.customer_tier.value,
            credit_limit=customer.credit_limit,
            blacklist_status=customer.blacklist_status.value,
            lifetime_value=customer.lifetime_value,
            last_transaction_date=customer.last_transaction_date,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            created_by=customer.created_by,
            updated_by=customer.updated_by,
            is_active=customer.is_active,
            display_name=customer.get_display_name()
        )
    
    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    """Schema for paginated customer list response."""
    items: List[CustomerResponse]
    total: int
    skip: int
    limit: int


class CustomerBlacklistRequest(BaseModel):
    """Schema for blacklisting/unblacklisting a customer."""
    action: str = Field(..., pattern="^(blacklist|unblacklist)$", description="Action to perform")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for action")


class CustomerCreditLimitUpdate(BaseModel):
    """Schema for updating customer credit limit."""
    credit_limit: Decimal = Field(..., ge=0, description="New credit limit")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for change")


class CustomerTierUpdate(BaseModel):
    """Schema for updating customer tier."""
    customer_tier: CustomerTier = Field(..., description="New customer tier")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for change")