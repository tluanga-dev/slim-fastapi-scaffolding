from enum import Enum
from typing import Optional
from uuid import UUID

from .base import BaseEntity
from ..value_objects.phone_number import PhoneNumber


class LocationType(str, Enum):
    """Location type enumeration."""
    STORE = "STORE"
    WAREHOUSE = "WAREHOUSE"
    SERVICE_CENTER = "SERVICE_CENTER"


class Location(BaseEntity):
    """Location domain entity representing physical locations."""
    
    def __init__(
        self,
        location_code: str,
        location_name: str,
        location_type: LocationType,
        address: str,
        city: str,
        state: str,
        country: str,
        postal_code: Optional[str] = None,
        contact_number: Optional[str] = None,
        email: Optional[str] = None,
        manager_user_id: Optional[UUID] = None,
        **kwargs
    ):
        """Initialize a Location entity."""
        super().__init__(**kwargs)
        self.location_code = location_code
        self.location_name = location_name
        self.location_type = location_type
        self.address = address
        self.city = city
        self.state = state
        self.country = country
        self.postal_code = postal_code
        self.contact_number = contact_number
        self.email = email
        self.manager_user_id = manager_user_id
        self._validate()
    
    def _validate(self):
        """Validate location business rules."""
        if not self.location_code or not self.location_code.strip():
            raise ValueError("Location code cannot be empty")
        
        if not self.location_name or not self.location_name.strip():
            raise ValueError("Location name cannot be empty")
        
        if not isinstance(self.location_type, LocationType):
            raise ValueError(f"Invalid location type: {self.location_type}")
        
        if not self.address or not self.address.strip():
            raise ValueError("Address cannot be empty")
        
        if not self.city or not self.city.strip():
            raise ValueError("City cannot be empty")
        
        if not self.state or not self.state.strip():
            raise ValueError("State cannot be empty")
        
        if not self.country or not self.country.strip():
            raise ValueError("Country cannot be empty")
        
        # Validate email format if provided
        if self.email:
            if "@" not in self.email or "." not in self.email.split("@")[-1]:
                raise ValueError("Invalid email format")
        
        # Validate phone number if provided
        if self.contact_number:
            try:
                # Validate using PhoneNumber value object
                PhoneNumber(self.contact_number)
            except ValueError as e:
                raise ValueError(f"Invalid contact number: {str(e)}")
    
    def update_details(
        self,
        location_name: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update location details."""
        if location_name:
            self.location_name = location_name
        if address:
            self.address = address
        if city:
            self.city = city
        if state:
            self.state = state
        if country:
            self.country = country
        if postal_code is not None:  # Allow clearing postal code
            self.postal_code = postal_code
        
        self._validate()
        self.update_timestamp(updated_by)
    
    def update_contact_info(
        self,
        contact_number: Optional[str] = None,
        email: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update location contact information.
        
        Pass None to clear a value, or don't pass the parameter to keep existing value.
        """
        self.contact_number = contact_number
        self.email = email
        
        self._validate()
        self.update_timestamp(updated_by)
    
    def assign_manager(self, manager_user_id: UUID, updated_by: Optional[str] = None):
        """Assign a manager to the location."""
        self.manager_user_id = manager_user_id
        self.update_timestamp(updated_by)
    
    def remove_manager(self, updated_by: Optional[str] = None):
        """Remove the manager from the location."""
        self.manager_user_id = None
        self.update_timestamp(updated_by)
    
    def deactivate(self, updated_by: Optional[str] = None):
        """Deactivate the location."""
        self.is_active = False
        self.update_timestamp(updated_by)
    
    def activate(self, updated_by: Optional[str] = None):
        """Activate the location."""
        self.is_active = True
        self.update_timestamp(updated_by)
    
    def get_full_address(self) -> str:
        """Get the full formatted address."""
        parts = [self.address, self.city, self.state]
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(parts)
    
    def is_store(self) -> bool:
        """Check if location is a store."""
        return self.location_type == LocationType.STORE
    
    def is_warehouse(self) -> bool:
        """Check if location is a warehouse."""
        return self.location_type == LocationType.WAREHOUSE
    
    def is_service_center(self) -> bool:
        """Check if location is a service center."""
        return self.location_type == LocationType.SERVICE_CENTER