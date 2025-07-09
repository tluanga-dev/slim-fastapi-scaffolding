from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from .base import BaseEntity
from ..value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus
from ..value_objects.email import Email
from ..value_objects.phone_number import PhoneNumber
from ..value_objects.address import Address


class Customer(BaseEntity):
    """Customer domain entity."""
    
    def __init__(
        self,
        customer_code: str,
        customer_type: CustomerType,
        business_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        customer_tier: CustomerTier = CustomerTier.BRONZE,
        credit_limit: Decimal = Decimal("0.00"),
        blacklist_status: BlacklistStatus = BlacklistStatus.CLEAR,
        lifetime_value: Decimal = Decimal("0.00"),
        last_transaction_date: Optional[datetime] = None,
        **kwargs
    ):
        """Initialize a Customer entity.
        
        Args:
            customer_code: Unique customer code
            customer_type: Type of customer (INDIVIDUAL or BUSINESS)
            business_name: Company name (required for business customers)
            first_name: First name (required for individual customers)
            last_name: Last name (required for individual customers)
            tax_id: GST/Tax identification number
            customer_tier: Customer tier level
            credit_limit: Credit limit amount
            blacklist_status: Blacklist status
            lifetime_value: Total purchase value
            last_transaction_date: Last transaction date
        """
        super().__init__(**kwargs)
        self.customer_code = customer_code
        self.customer_type = customer_type
        self.business_name = business_name
        self.first_name = first_name
        self.last_name = last_name
        self.tax_id = tax_id
        self.customer_tier = customer_tier
        self.credit_limit = credit_limit
        self.blacklist_status = blacklist_status
        self.lifetime_value = lifetime_value
        self.last_transaction_date = last_transaction_date
        self._validate()
    
    def _validate(self):
        """Validate customer business rules."""
        if not self.customer_code or not self.customer_code.strip():
            raise ValueError("Customer code cannot be empty")
        
        if len(self.customer_code) > 20:
            raise ValueError("Customer code cannot exceed 20 characters")
        
        # Validate based on customer type
        if self.customer_type == CustomerType.BUSINESS:
            if not self.business_name or not self.business_name.strip():
                raise ValueError("Business name is required for business customers")
            if len(self.business_name) > 200:
                raise ValueError("Business name cannot exceed 200 characters")
        elif self.customer_type == CustomerType.INDIVIDUAL:
            if not self.first_name or not self.first_name.strip():
                raise ValueError("First name is required for individual customers")
            if not self.last_name or not self.last_name.strip():
                raise ValueError("Last name is required for individual customers")
            if len(self.first_name) > 50:
                raise ValueError("First name cannot exceed 50 characters")
            if len(self.last_name) > 50:
                raise ValueError("Last name cannot exceed 50 characters")
        
        if self.tax_id and len(self.tax_id) > 50:
            raise ValueError("Tax ID cannot exceed 50 characters")
        
        if self.credit_limit < Decimal("0"):
            raise ValueError("Credit limit cannot be negative")
        
        if self.lifetime_value < Decimal("0"):
            raise ValueError("Lifetime value cannot be negative")
    
    def get_display_name(self) -> str:
        """Get display name for the customer."""
        if self.customer_type == CustomerType.BUSINESS:
            return self.business_name
        else:
            return f"{self.first_name} {self.last_name}"
    
    def update_personal_info(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update personal information for individual customers."""
        if self.customer_type != CustomerType.INDIVIDUAL:
            raise ValueError("Personal info can only be updated for individual customers")
        
        if first_name is not None:
            if not first_name.strip():
                raise ValueError("First name cannot be empty")
            if len(first_name) > 50:
                raise ValueError("First name cannot exceed 50 characters")
            self.first_name = first_name
        
        if last_name is not None:
            if not last_name.strip():
                raise ValueError("Last name cannot be empty")
            if len(last_name) > 50:
                raise ValueError("Last name cannot exceed 50 characters")
            self.last_name = last_name
        
        self.update_timestamp(updated_by)
    
    def update_business_info(
        self,
        business_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update business information."""
        if business_name is not None:
            if self.customer_type != CustomerType.BUSINESS:
                raise ValueError("Business name can only be updated for business customers")
            if not business_name.strip():
                raise ValueError("Business name cannot be empty")
            if len(business_name) > 200:
                raise ValueError("Business name cannot exceed 200 characters")
            self.business_name = business_name
        
        if tax_id is not None:
            if tax_id and len(tax_id) > 50:
                raise ValueError("Tax ID cannot exceed 50 characters")
            self.tax_id = tax_id
        
        self.update_timestamp(updated_by)
    
    def update_credit_limit(self, credit_limit: Decimal, updated_by: Optional[str] = None):
        """Update customer credit limit."""
        if credit_limit < Decimal("0"):
            raise ValueError("Credit limit cannot be negative")
        
        self.credit_limit = credit_limit
        self.update_timestamp(updated_by)
    
    def update_tier(self, tier: CustomerTier, updated_by: Optional[str] = None):
        """Update customer tier."""
        self.customer_tier = tier
        self.update_timestamp(updated_by)
    
    def blacklist(self, updated_by: Optional[str] = None):
        """Blacklist the customer."""
        if self.blacklist_status == BlacklistStatus.BLACKLISTED:
            raise ValueError("Customer is already blacklisted")
        
        self.blacklist_status = BlacklistStatus.BLACKLISTED
        self.update_timestamp(updated_by)
    
    def remove_from_blacklist(self, updated_by: Optional[str] = None):
        """Remove customer from blacklist."""
        if self.blacklist_status == BlacklistStatus.CLEAR:
            raise ValueError("Customer is not blacklisted")
        
        self.blacklist_status = BlacklistStatus.CLEAR
        self.update_timestamp(updated_by)
    
    def update_lifetime_value(self, amount: Decimal, updated_by: Optional[str] = None):
        """Update customer lifetime value."""
        if amount < Decimal("0"):
            raise ValueError("Lifetime value cannot be negative")
        
        self.lifetime_value = amount
        self.update_timestamp(updated_by)
    
    def record_transaction(self, updated_by: Optional[str] = None):
        """Record that a transaction occurred."""
        self.last_transaction_date = datetime.utcnow()
        self.update_timestamp(updated_by)
    
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
    
    def __str__(self) -> str:
        """String representation of customer."""
        return f"Customer({self.customer_code} - {self.get_display_name()})"
    
    def __repr__(self) -> str:
        """Developer representation of customer."""
        return (
            f"Customer(id={self.id}, code='{self.customer_code}', "
            f"type={self.customer_type.value}, name='{self.get_display_name()}', "
            f"tier={self.customer_tier.value}, is_active={self.is_active})"
        )