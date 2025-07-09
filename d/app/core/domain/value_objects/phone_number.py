import re
from typing import Optional


class PhoneNumber:
    """Value object for phone number validation and formatting."""
    
    def __init__(self, value: str):
        """Initialize phone number with validation."""
        self.value = self._validate_and_format(value)
    
    def _validate_and_format(self, value: str) -> str:
        """Validate and format phone number."""
        if not value or not isinstance(value, str):
            raise ValueError("Phone number must be a non-empty string")
        
        # Remove all non-digit characters
        cleaned = re.sub(r'\D', '', value)
        
        if not cleaned:
            raise ValueError("Phone number must contain at least one digit")
        
        # Check length (minimum 7 digits, maximum 15 digits per E.164 standard)
        if len(cleaned) < 7:
            raise ValueError("Phone number must be at least 7 digits long")
        
        if len(cleaned) > 15:
            raise ValueError("Phone number cannot exceed 15 digits")
        
        # Basic format validation - must start with digit
        if not cleaned[0].isdigit():
            raise ValueError("Phone number must start with a digit")
        
        return cleaned
    
    def formatted(self, format_type: str = "international") -> str:
        """Return formatted phone number."""
        if format_type == "international":
            # Simple international format: +1 234 567 8900
            if len(self.value) == 10:
                return f"+1 {self.value[:3]} {self.value[3:6]} {self.value[6:]}"
            elif len(self.value) == 11 and self.value.startswith('1'):
                return f"+{self.value[0]} {self.value[1:4]} {self.value[4:7]} {self.value[7:]}"
            else:
                return f"+{self.value}"
        elif format_type == "national":
            # National format: (234) 567-8900
            if len(self.value) == 10:
                return f"({self.value[:3]}) {self.value[3:6]}-{self.value[6:]}"
            elif len(self.value) == 11 and self.value.startswith('1'):
                return f"({self.value[1:4]}) {self.value[4:7]}-{self.value[7:]}"
            else:
                return self.value
        else:
            return self.value
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"PhoneNumber('{self.value}')"
    
    def __eq__(self, other) -> bool:
        """Check equality with another PhoneNumber."""
        if not isinstance(other, PhoneNumber):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)