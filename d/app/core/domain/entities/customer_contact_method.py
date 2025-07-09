from typing import Optional
from datetime import datetime
from uuid import UUID
import re

from pydantic import Field, validator

from .base import BaseEntity
from ..value_objects import ContactMethodType, ContactMethodPurpose
from ..value_objects.phone_number import PhoneNumber


class CustomerContactMethod(BaseEntity):
    """Customer contact method domain entity."""
    
    customer_id: UUID
    contact_type: ContactMethodType
    contact_value: str = Field(max_length=100)
    contact_label: Optional[str] = Field(None, max_length=50)
    purpose: ContactMethodPurpose = ContactMethodPurpose.PRIMARY
    is_primary: bool = False
    is_verified: bool = False
    verified_date: Optional[datetime] = None
    opt_in_marketing: bool = True
    
    @validator('contact_value')
    def validate_contact_value(cls, v):
        """Validate contact value is not empty."""
        if not v or not v.strip():
            raise ValueError("Contact value cannot be empty")
        return v.strip()
    
    @validator('contact_value')
    def validate_contact_format(cls, v, values):
        """Validate contact value format based on type."""
        if 'contact_type' not in values:
            return v
            
        contact_type = values['contact_type']
        
        if contact_type == ContactMethodType.EMAIL:
            # Basic email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format")
                
        elif contact_type in [ContactMethodType.MOBILE, ContactMethodType.PHONE]:
            # Try to validate as phone number
            try:
                PhoneNumber(v)
            except ValueError:
                raise ValueError(f"Invalid phone number format: {v}")
                
        return v
    
    @validator('verified_date')
    def validate_verified_date(cls, v, values):
        """Validate verified date consistency."""
        if 'is_verified' in values:
            if not values['is_verified'] and v:
                raise ValueError("Verified date cannot be set when contact is not verified")
            if values['is_verified'] and not v:
                return datetime.utcnow()
        return v
    
    def get_formatted_value(self) -> str:
        """Get formatted contact value."""
        if self.contact_type == ContactMethodType.EMAIL:
            return self.contact_value.lower()
        elif self.contact_type in [ContactMethodType.MOBILE, ContactMethodType.PHONE]:
            try:
                phone = PhoneNumber(self.contact_value)
                return phone.value
            except:
                return self.contact_value
        return self.contact_value
    
    def set_as_primary(self, updated_by: Optional[str] = None) -> None:
        """Set this contact as primary."""
        self.is_primary = True
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def remove_as_primary(self, updated_by: Optional[str] = None) -> None:
        """Remove primary status."""
        self.is_primary = False
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def mark_as_verified(self, updated_by: Optional[str] = None) -> None:
        """Mark contact as verified."""
        if self.is_verified:
            raise ValueError("Contact is already verified")
            
        self.is_verified = True
        self.verified_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def revoke_verification(self, updated_by: Optional[str] = None) -> None:
        """Revoke verification status."""
        if not self.is_verified:
            raise ValueError("Contact is not verified")
            
        self.is_verified = False
        self.verified_date = None
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def update_marketing_consent(self, opt_in: bool, updated_by: Optional[str] = None) -> None:
        """Update marketing consent."""
        self.opt_in_marketing = opt_in
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def update_contact_value(self, new_value: str, updated_by: Optional[str] = None) -> None:
        """Update contact value and reset verification."""
        if not new_value or not new_value.strip():
            raise ValueError("Contact value cannot be empty")
            
        # Create a temporary instance to validate the new value
        temp = CustomerContactMethod(
            customer_id=self.customer_id,
            contact_type=self.contact_type,
            contact_value=new_value,
            contact_label=self.contact_label,
            purpose=self.purpose
        )
        
        self.contact_value = new_value.strip()
        self.is_verified = False
        self.verified_date = None
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def update_label(self, label: Optional[str], updated_by: Optional[str] = None) -> None:
        """Update contact label."""
        if label and len(label) > 50:
            raise ValueError("Contact label cannot exceed 50 characters")
            
        self.contact_label = label.strip() if label else None
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def is_valid_for_purpose(self, purpose: ContactMethodPurpose) -> bool:
        """Check if contact is valid for given purpose."""
        # Email required for billing
        if purpose == ContactMethodPurpose.BILLING and self.contact_type != ContactMethodType.EMAIL:
            return False
            
        # Phone required for emergency
        if purpose == ContactMethodPurpose.EMERGENCY and self.contact_type not in [
            ContactMethodType.PHONE, ContactMethodType.MOBILE
        ]:
            return False
            
        return self.is_active and self.is_verified