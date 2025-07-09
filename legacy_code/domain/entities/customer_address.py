from typing import Optional
from uuid import UUID

from .base import BaseEntity
from ..value_objects.customer_type import AddressType
from ..value_objects.address import Address


class CustomerAddress(BaseEntity):
    """Customer address domain entity."""
    
    def __init__(
        self,
        customer_id: UUID,
        address_type: AddressType,
        street: str,
        city: str,
        state: str,
        country: str,
        postal_code: Optional[str] = None,
        address_line2: Optional[str] = None,
        is_default: bool = False,
        **kwargs
    ):
        """Initialize a CustomerAddress entity.
        
        Args:
            customer_id: Parent customer ID
            address_type: Type of address (BILLING, SHIPPING, BOTH)
            street: Street address (line 1)
            city: City name
            state: State or province
            country: Country name
            postal_code: ZIP or postal code
            address_line2: Additional address line
            is_default: Whether this is the default address
        """
        super().__init__(**kwargs)
        self.customer_id = customer_id
        self.address_type = address_type
        self.street = street
        self.city = city
        self.state = state
        self.country = country
        self.postal_code = postal_code
        self.address_line2 = address_line2
        self.is_default = is_default
        self._validate()
    
    def _validate(self):
        """Validate address business rules."""
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        
        if not self.street or not self.street.strip():
            raise ValueError("Street address cannot be empty")
        
        if len(self.street) > 200:
            raise ValueError("Street address cannot exceed 200 characters")
        
        if self.address_line2 and len(self.address_line2) > 200:
            raise ValueError("Address line 2 cannot exceed 200 characters")
        
        if not self.city or not self.city.strip():
            raise ValueError("City cannot be empty")
        
        if len(self.city) > 50:
            raise ValueError("City cannot exceed 50 characters")
        
        if not self.state or not self.state.strip():
            raise ValueError("State cannot be empty")
        
        if len(self.state) > 50:
            raise ValueError("State cannot exceed 50 characters")
        
        if not self.country or not self.country.strip():
            raise ValueError("Country cannot be empty")
        
        if len(self.country) > 50:
            raise ValueError("Country cannot exceed 50 characters")
        
        if self.postal_code and len(self.postal_code) > 20:
            raise ValueError("Postal code cannot exceed 20 characters")
    
    def to_value_object(self) -> Address:
        """Convert to Address value object."""
        return Address(
            street=self.street,
            city=self.city,
            state=self.state,
            country=self.country,
            postal_code=self.postal_code
        )
    
    def get_full_address(self) -> str:
        """Get formatted full address."""
        lines = [self.street]
        if self.address_line2:
            lines.append(self.address_line2)
        
        city_state_zip = f"{self.city}, {self.state}"
        if self.postal_code:
            city_state_zip += f" {self.postal_code}"
        lines.append(city_state_zip)
        lines.append(self.country)
        
        return "\n".join(lines)
    
    def update_address(
        self,
        street: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        address_line2: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update address details."""
        if street is not None:
            if not street.strip():
                raise ValueError("Street address cannot be empty")
            if len(street) > 200:
                raise ValueError("Street address cannot exceed 200 characters")
            self.street = street
        
        if city is not None:
            if not city.strip():
                raise ValueError("City cannot be empty")
            if len(city) > 50:
                raise ValueError("City cannot exceed 50 characters")
            self.city = city
        
        if state is not None:
            if not state.strip():
                raise ValueError("State cannot be empty")
            if len(state) > 50:
                raise ValueError("State cannot exceed 50 characters")
            self.state = state
        
        if country is not None:
            if not country.strip():
                raise ValueError("Country cannot be empty")
            if len(country) > 50:
                raise ValueError("Country cannot exceed 50 characters")
            self.country = country
        
        if postal_code is not None:
            if postal_code and len(postal_code) > 20:
                raise ValueError("Postal code cannot exceed 20 characters")
            self.postal_code = postal_code
        
        if address_line2 is not None:
            if address_line2 and len(address_line2) > 200:
                raise ValueError("Address line 2 cannot exceed 200 characters")
            self.address_line2 = address_line2
        
        self.update_timestamp(updated_by)
    
    def set_as_default(self, updated_by: Optional[str] = None):
        """Set this address as default."""
        self.is_default = True
        self.update_timestamp(updated_by)
    
    def remove_as_default(self, updated_by: Optional[str] = None):
        """Remove default status."""
        self.is_default = False
        self.update_timestamp(updated_by)
    
    def change_type(self, address_type: AddressType, updated_by: Optional[str] = None):
        """Change address type."""
        self.address_type = address_type
        self.update_timestamp(updated_by)
    
    def is_billing_address(self) -> bool:
        """Check if this is a billing address."""
        return self.address_type in [AddressType.BILLING, AddressType.BOTH]
    
    def is_shipping_address(self) -> bool:
        """Check if this is a shipping address."""
        return self.address_type in [AddressType.SHIPPING, AddressType.BOTH]
    
    def __str__(self) -> str:
        """String representation of address."""
        default = " [Default]" if self.is_default else ""
        return f"{self.address_type.value} Address: {self.city}, {self.state}{default}"
    
    def __repr__(self) -> str:
        """Developer representation of address."""
        return (
            f"CustomerAddress(id={self.id}, type={self.address_type.value}, "
            f"city='{self.city}', state='{self.state}', default={self.is_default})"
        )