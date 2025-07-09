from typing import Optional, List
from uuid import UUID, uuid4

from .base import BaseEntity


class UnitOfMeasurement(BaseEntity):
    """Unit of Measurement domain entity representing measurement units for inventory items."""
    
    def __init__(
        self,
        unit_id: Optional[UUID] = None,
        name: str = "",
        abbreviation: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """Initialize a UnitOfMeasurement entity."""
        super().__init__(**kwargs)
        self.unit_id = unit_id or uuid4()
        self.name = name
        self.abbreviation = abbreviation
        self.description = description
        self._validate()
    
    def _validate(self):
        """Validate unit of measurement business rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Unit name cannot be empty")
        
        if len(self.name.strip()) > 100:
            raise ValueError("Unit name cannot exceed 100 characters")
        
        if self.abbreviation:
            if len(self.abbreviation.strip()) > 10:
                raise ValueError("Unit abbreviation cannot exceed 10 characters")
            
            # Ensure abbreviation doesn't contain invalid characters
            if not self.abbreviation.replace(" ", "").replace("-", "").replace("/", "").replace(".", "").isalnum():
                raise ValueError("Unit abbreviation contains invalid characters")
        
        if self.description and len(self.description) > 1000:
            raise ValueError("Unit description cannot exceed 1000 characters")
    
    def update_details(
        self,
        name: Optional[str] = None,
        abbreviation: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update unit of measurement details."""
        if name is not None:
            self.name = name
        if abbreviation is not None:
            self.abbreviation = abbreviation
        if description is not None:
            self.description = description
        
        self._validate()
        self.update_timestamp(updated_by)
    
    def deactivate(self, updated_by: Optional[str] = None):
        """Deactivate the unit of measurement."""
        self.is_active = False
        self.update_timestamp(updated_by)
    
    def activate(self, updated_by: Optional[str] = None):
        """Activate the unit of measurement."""
        self.is_active = True
        self.update_timestamp(updated_by)
    
    def get_display_name(self) -> str:
        """Get the display name for the unit of measurement."""
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name
    
    def is_same_unit(self, other: 'UnitOfMeasurement') -> bool:
        """Check if this unit represents the same measurement as another unit."""
        if not isinstance(other, UnitOfMeasurement):
            return False
        
        # Check by unit_id first
        if self.unit_id == other.unit_id:
            return True
        
        # Check by name (case-insensitive)
        if self.name.lower().strip() == other.name.lower().strip():
            return True
        
        # Check by abbreviation if both have them
        if (self.abbreviation and other.abbreviation and 
            self.abbreviation.lower().strip() == other.abbreviation.lower().strip()):
            return True
        
        return False
    
    def validate_for_item_usage(self) -> List[str]:
        """Validate if this unit can be used for item measurements."""
        errors = []
        
        if not self.is_active:
            errors.append("Unit of measurement is not active")
        
        if not self.name or not self.name.strip():
            errors.append("Unit name is required for item usage")
        
        return errors
    
    def get_conversion_info(self) -> dict:
        """Get conversion information for this unit."""
        # This could be extended to include conversion factors to base units
        return {
            "unit_id": str(self.unit_id),
            "name": self.name,
            "abbreviation": self.abbreviation,
            "can_convert": False,  # Future enhancement for unit conversions
            "base_unit": None      # Future enhancement for base unit relationships
        }
    
    def __str__(self) -> str:
        return f"UnitOfMeasurement({self.name})"
    
    def __repr__(self) -> str:
        return (f"UnitOfMeasurement(id={self.id}, unit_id={self.unit_id}, "
                f"name='{self.name}', abbreviation='{self.abbreviation}')")