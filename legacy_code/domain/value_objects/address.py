from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Address:
    """Immutable address value object."""
    
    street: str
    city: str
    state: str
    country: str
    postal_code: Optional[str] = None
    
    def __post_init__(self):
        """Validate address data."""
        if not self.street or not self.street.strip():
            raise ValueError("Street address cannot be empty")
        
        if not self.city or not self.city.strip():
            raise ValueError("City cannot be empty")
            
        if not self.state or not self.state.strip():
            raise ValueError("State/Province cannot be empty")
            
        if not self.country or not self.country.strip():
            raise ValueError("Country cannot be empty")
            
        # Validate postal code format if provided (example for US ZIP codes)
        if self.postal_code:
            # Strip whitespace
            cleaned_postal = self.postal_code.strip()
            if self.country.upper() in ["US", "USA", "UNITED STATES"]:
                # US ZIP code validation (5 digits or 5+4 format)
                import re
                if not re.match(r'^\d{5}(-\d{4})?$', cleaned_postal):
                    raise ValueError("Invalid US ZIP code format (must be 12345 or 12345-6789)")
            # Can add more country-specific validations here
    
    def __str__(self) -> str:
        """String representation of address."""
        parts = [self.street, self.city, self.state]
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(parts)
    
    def format_multiline(self) -> str:
        """Format address for multi-line display."""
        lines = [self.street, f"{self.city}, {self.state}"]
        if self.postal_code:
            lines[-1] += f" {self.postal_code}"
        lines.append(self.country)
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Address":
        """Create from dictionary."""
        return cls(
            street=data.get("street", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            country=data.get("country", ""),
            postal_code=data.get("postal_code")
        )