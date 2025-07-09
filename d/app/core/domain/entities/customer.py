from typing import Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from pydantic import Field, validator

from .base import BaseEntity
from ..value_objects import CustomerType, CustomerTier, BlacklistStatus


class Customer(BaseEntity):
    """Customer domain entity."""
    
    customer_code: str = Field(max_length=20, description="Unique customer code")
    customer_type: CustomerType
    business_name: Optional[str] = Field(None, max_length=200)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    customer_tier: CustomerTier = CustomerTier.BRONZE
    credit_limit: Decimal = Field(default=Decimal("0.00"), ge=0)
    blacklist_status: BlacklistStatus = BlacklistStatus.CLEAR
    lifetime_value: Decimal = Field(default=Decimal("0.00"), ge=0)
    last_transaction_date: Optional[datetime] = None
    
    @validator('customer_code')
    def validate_customer_code(cls, v):
        """Validate customer code is not empty."""
        if not v or not v.strip():
            raise ValueError("Customer code cannot be empty")
        return v.strip()
    
    @validator('business_name')
    def validate_business_name(cls, v, values):
        """Validate business name for business customers."""
        if 'customer_type' in values and values['customer_type'] == CustomerType.BUSINESS:
            if not v or not v.strip():
                raise ValueError("Business name is required for business customers")
        return v.strip() if v else v
    
    @validator('last_name')
    def validate_individual_customer(cls, v, values):
        """Validate individual customer has first and last name."""
        if 'customer_type' in values and values['customer_type'] == CustomerType.INDIVIDUAL:
            if 'first_name' in values:
                first_name = values['first_name']
                if not first_name or not first_name.strip():
                    raise ValueError("First name is required for individual customers")
            if not v or not v.strip():
                raise ValueError("Last name is required for individual customers")
        return v.strip() if v else v
    
    def get_display_name(self) -> str:
        """Get display name for the customer."""
        if self.customer_type == CustomerType.BUSINESS:
            return self.business_name or self.customer_code
        else:
            if self.first_name and self.last_name:
                return f"{self.first_name} {self.last_name}"
            return self.customer_code
    
    def update_personal_info(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> None:
        """Update personal information for individual customers."""
        if self.customer_type != CustomerType.INDIVIDUAL:
            raise ValueError("Personal info can only be updated for individual customers")
        
        if first_name is not None:
            if not first_name.strip():
                raise ValueError("First name cannot be empty")
            if len(first_name) > 50:
                raise ValueError("First name cannot exceed 50 characters")
            self.first_name = first_name.strip()
        
        if last_name is not None:
            if not last_name.strip():
                raise ValueError("Last name cannot be empty")
            if len(last_name) > 50:
                raise ValueError("Last name cannot exceed 50 characters")
            self.last_name = last_name.strip()
        
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def update_business_info(
        self,
        business_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> None:
        """Update business information."""
        if business_name is not None:
            if self.customer_type != CustomerType.BUSINESS:
                raise ValueError("Business name can only be updated for business customers")
            if not business_name.strip():
                raise ValueError("Business name cannot be empty")
            if len(business_name) > 200:
                raise ValueError("Business name cannot exceed 200 characters")
            self.business_name = business_name.strip()
        
        if tax_id is not None:
            if tax_id and len(tax_id) > 50:
                raise ValueError("Tax ID cannot exceed 50 characters")
            self.tax_id = tax_id.strip() if tax_id else None
        
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def update_credit_limit(self, credit_limit: Decimal, updated_by: Optional[str] = None) -> None:
        """Update customer credit limit."""
        if credit_limit < Decimal("0"):
            raise ValueError("Credit limit cannot be negative")
        
        self.credit_limit = credit_limit
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def update_tier(self, tier: CustomerTier, updated_by: Optional[str] = None) -> None:
        """Update customer tier."""
        self.customer_tier = tier
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def blacklist(self, updated_by: Optional[str] = None) -> None:
        """Blacklist the customer."""
        if self.blacklist_status == BlacklistStatus.BLACKLISTED:
            raise ValueError("Customer is already blacklisted")
        
        self.blacklist_status = BlacklistStatus.BLACKLISTED
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def remove_from_blacklist(self, updated_by: Optional[str] = None) -> None:
        """Remove customer from blacklist."""
        if self.blacklist_status == BlacklistStatus.CLEAR:
            raise ValueError("Customer is not blacklisted")
        
        self.blacklist_status = BlacklistStatus.CLEAR
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def update_lifetime_value(self, amount: Decimal, updated_by: Optional[str] = None) -> None:
        """Update customer lifetime value."""
        if amount < Decimal("0"):
            raise ValueError("Lifetime value cannot be negative")
        
        self.lifetime_value = amount
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def add_to_lifetime_value(self, amount: Decimal, updated_by: Optional[str] = None) -> None:
        """Add amount to customer lifetime value."""
        if amount < Decimal("0"):
            raise ValueError("Amount cannot be negative")
        
        self.lifetime_value += amount
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def record_transaction(self, updated_by: Optional[str] = None) -> None:
        """Record that a transaction occurred."""
        self.last_transaction_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def can_use_credit(self, amount: Decimal) -> bool:
        """Check if customer can use credit for given amount."""
        return (
            self.is_active and
            self.blacklist_status == BlacklistStatus.CLEAR and
            self.credit_limit >= amount
        )
    
    def is_blacklisted(self) -> bool:
        """Check if customer is blacklisted."""
        return self.blacklist_status == BlacklistStatus.BLACKLISTED
    
    def get_available_credit(self) -> Decimal:
        """Get available credit limit."""
        if not self.is_active or self.is_blacklisted():
            return Decimal("0")
        return self.credit_limit
    
    def is_vip(self) -> bool:
        """Check if customer is VIP based on tier."""
        return self.customer_tier in [CustomerTier.GOLD, CustomerTier.PLATINUM, CustomerTier.DIAMOND]
    
    def calculate_discount_rate(self) -> Decimal:
        """Calculate discount rate based on customer tier."""
        discount_rates = {
            CustomerTier.BRONZE: Decimal("0"),
            CustomerTier.SILVER: Decimal("0.05"),
            CustomerTier.GOLD: Decimal("0.10"),
            CustomerTier.PLATINUM: Decimal("0.15"),
            CustomerTier.DIAMOND: Decimal("0.20"),
        }
        return discount_rates.get(self.customer_tier, Decimal("0"))