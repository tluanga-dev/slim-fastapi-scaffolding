from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects.address_type import AddressType


class CustomerAddress:
    """Domain entity for customer addresses."""
    
    def __init__(
        self,
        customer_id: UUID,
        address_type: AddressType,
        street: str,
        city: str,
        state: str,
        country: str,
        id: Optional[UUID] = None,
        address_line2: Optional[str] = None,
        postal_code: Optional[str] = None,
        is_default: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
        is_active: bool = True
    ):
        self.id = id or uuid4()
        self.customer_id = customer_id
        self.address_type = address_type
        self.street = street
        self.address_line2 = address_line2
        self.city = city
        self.state = state
        self.country = country
        self.postal_code = postal_code
        self.is_default = is_default
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.created_by = created_by
        self.updated_by = updated_by
        self.is_active = is_active
        
        self._validate()
    
    def _validate(self) -> None:
        """Validate customer address business rules."""
        if not self.street or not self.street.strip():
            raise ValueError("Street address is required")
        
        if not self.city or not self.city.strip():
            raise ValueError("City is required")
        
        if not self.state or not self.state.strip():
            raise ValueError("State is required")
        
        if not self.country or not self.country.strip():
            raise ValueError("Country is required")
        
        if len(self.street.strip()) > 200:
            raise ValueError("Street address cannot exceed 200 characters")
        
        if self.address_line2 and len(self.address_line2.strip()) > 200:
            raise ValueError("Address line 2 cannot exceed 200 characters")
        
        if len(self.city.strip()) > 50:
            raise ValueError("City cannot exceed 50 characters")
        
        if len(self.state.strip()) > 50:
            raise ValueError("State cannot exceed 50 characters")
        
        if len(self.country.strip()) > 50:
            raise ValueError("Country cannot exceed 50 characters")
        
        if self.postal_code and len(self.postal_code.strip()) > 20:
            raise ValueError("Postal code cannot exceed 20 characters")
    
    def get_formatted_address(self, include_country: bool = True) -> str:
        """Get formatted address string."""
        parts = [self.street]
        
        if self.address_line2:
            parts.append(self.address_line2)
        
        city_state = f"{self.city}, {self.state}"
        if self.postal_code:
            city_state += f" {self.postal_code}"
        parts.append(city_state)
        
        if include_country:
            parts.append(self.country)
        
        return "\n".join(parts)
    
    def is_same_location(self, other: "CustomerAddress") -> bool:
        """Check if this address represents the same physical location as another."""
        return (
            self.street.strip().lower() == other.street.strip().lower() and
            (self.address_line2 or "").strip().lower() == (other.address_line2 or "").strip().lower() and
            self.city.strip().lower() == other.city.strip().lower() and
            self.state.strip().lower() == other.state.strip().lower() and
            self.country.strip().lower() == other.country.strip().lower() and
            (self.postal_code or "").strip().lower() == (other.postal_code or "").strip().lower()
        )
    
    def can_be_default(self) -> bool:
        """Check if this address can be set as default."""
        return self.is_active
    
    def set_as_default(self) -> None:
        """Mark this address as default."""
        if not self.can_be_default():
            raise ValueError("Cannot set inactive address as default")
        self.is_default = True
        self.updated_at = datetime.utcnow()
    
    def unset_as_default(self) -> None:
        """Remove default status from this address."""
        self.is_default = False
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate this address."""
        if self.is_default:
            raise ValueError("Cannot deactivate default address. Set another address as default first.")
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate this address."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def update_details(
        self,
        street: Optional[str] = None,
        address_line2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> None:
        """Update address details."""
        if street is not None:
            self.street = street
        if address_line2 is not None:
            self.address_line2 = address_line2
        if city is not None:
            self.city = city
        if state is not None:
            self.state = state
        if country is not None:
            self.country = country
        if postal_code is not None:
            self.postal_code = postal_code
        
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
        
        self._validate()
    
    def __str__(self) -> str:
        return f"CustomerAddress({self.address_type.value}: {self.get_formatted_address(include_country=False)})"
    
    def __repr__(self) -> str:
        return f"CustomerAddress(id={self.id}, customer_id={self.customer_id}, type={self.address_type.value})"