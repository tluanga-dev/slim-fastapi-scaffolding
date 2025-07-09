from typing import Optional
from datetime import datetime
from uuid import UUID

from .base import BaseEntity
from ..value_objects.customer_type import ContactType
from ..value_objects.email import Email
from ..value_objects.phone_number import PhoneNumber


class CustomerContactMethod(BaseEntity):
    """Customer contact method domain entity."""
    
    def __init__(
        self,
        customer_id: UUID,
        contact_type: ContactType,
        contact_value: str,
        contact_label: Optional[str] = None,
        is_primary: bool = False,
        is_verified: bool = False,
        verified_date: Optional[datetime] = None,
        opt_in_marketing: bool = True,
        **kwargs
    ):
        """Initialize a CustomerContactMethod entity.
        
        Args:
            customer_id: Parent customer ID
            contact_type: Type of contact (MOBILE, EMAIL, PHONE, FAX)
            contact_value: Actual contact value
            contact_label: Label like Personal, Work, Home
            is_primary: Whether this is the primary contact
            is_verified: Whether contact is verified
            verified_date: When contact was verified
            opt_in_marketing: Marketing consent
        """
        super().__init__(**kwargs)
        self.customer_id = customer_id
        self.contact_type = contact_type
        self.contact_value = contact_value
        self.contact_label = contact_label
        self.is_primary = is_primary
        self.is_verified = is_verified
        self.verified_date = verified_date
        self.opt_in_marketing = opt_in_marketing
        self._validate()
    
    def _validate(self):
        """Validate contact method business rules."""
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        
        if not self.contact_value or not self.contact_value.strip():
            raise ValueError("Contact value cannot be empty")
        
        if len(self.contact_value) > 100:
            raise ValueError("Contact value cannot exceed 100 characters")
        
        if self.contact_label and len(self.contact_label) > 50:
            raise ValueError("Contact label cannot exceed 50 characters")
        
        # Validate contact value format based on type
        if self.contact_type == ContactType.EMAIL:
            try:
                Email(self.contact_value)
            except ValueError as e:
                raise ValueError(f"Invalid email format: {str(e)}")
        elif self.contact_type in [ContactType.MOBILE, ContactType.PHONE]:
            try:
                PhoneNumber(self.contact_value)
            except ValueError as e:
                raise ValueError(f"Invalid phone number format: {str(e)}")
        
        # Verified date should not be set if not verified
        if not self.is_verified and self.verified_date:
            raise ValueError("Verified date cannot be set when contact is not verified")
        
        # If verified, must have verified date
        if self.is_verified and not self.verified_date:
            self.verified_date = datetime.utcnow()
    
    def get_formatted_value(self) -> str:
        """Get formatted contact value."""
        if self.contact_type == ContactType.EMAIL:
            return Email(self.contact_value).value
        elif self.contact_type in [ContactType.MOBILE, ContactType.PHONE]:
            return PhoneNumber(self.contact_value).value
        return self.contact_value
    
    def set_as_primary(self, updated_by: Optional[str] = None):
        """Set this contact as primary."""
        self.is_primary = True
        self.update_timestamp(updated_by)
    
    def remove_as_primary(self, updated_by: Optional[str] = None):
        """Remove primary status."""
        self.is_primary = False
        self.update_timestamp(updated_by)
    
    def verify(self, updated_by: Optional[str] = None):
        """Mark contact as verified."""
        if self.is_verified:
            raise ValueError("Contact is already verified")
        
        self.is_verified = True
        self.verified_date = datetime.utcnow()
        self.update_timestamp(updated_by)
    
    def unverify(self, updated_by: Optional[str] = None):
        """Mark contact as unverified."""
        if not self.is_verified:
            raise ValueError("Contact is already unverified")
        
        self.is_verified = False
        self.verified_date = None
        self.update_timestamp(updated_by)
    
    def update_marketing_consent(self, opt_in: bool, updated_by: Optional[str] = None):
        """Update marketing consent."""
        self.opt_in_marketing = opt_in
        self.update_timestamp(updated_by)
    
    def update_label(self, label: Optional[str], updated_by: Optional[str] = None):
        """Update contact label."""
        if label and len(label) > 50:
            raise ValueError("Contact label cannot exceed 50 characters")
        
        self.contact_label = label
        self.update_timestamp(updated_by)
    
    def is_email(self) -> bool:
        """Check if this is an email contact."""
        return self.contact_type == ContactType.EMAIL
    
    def is_phone(self) -> bool:
        """Check if this is a phone contact."""
        return self.contact_type in [ContactType.MOBILE, ContactType.PHONE]
    
    def __str__(self) -> str:
        """String representation of contact method."""
        label = f" ({self.contact_label})" if self.contact_label else ""
        primary = " [Primary]" if self.is_primary else ""
        return f"{self.contact_type.value}: {self.contact_value}{label}{primary}"
    
    def __repr__(self) -> str:
        """Developer representation of contact method."""
        return (
            f"CustomerContactMethod(id={self.id}, type={self.contact_type.value}, "
            f"value='{self.contact_value}', primary={self.is_primary}, "
            f"verified={self.is_verified})"
        )