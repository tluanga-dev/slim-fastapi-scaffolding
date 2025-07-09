import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PhoneNumber:
    """Immutable phone number value object with E.164 format validation."""
    
    value: str
    
    def __post_init__(self):
        """Validate phone number format."""
        # First check if there are any letters
        if re.search(r'[a-zA-Z]', self.value):
            raise ValueError(
                "Invalid phone number format. Must be in E.164 format "
                "(e.g., +1234567890, max 15 digits)"
            )
        
        # Remove all non-digit characters except leading +
        cleaned = re.sub(r'[^\d+]', '', self.value)
        
        # E.164 format validation
        if not re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
            raise ValueError(
                "Invalid phone number format. Must be in E.164 format "
                "(e.g., +1234567890, max 15 digits)"
            )
        
        # Ensure it starts with +
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
            
        # Use object.__setattr__ to set value on frozen dataclass
        object.__setattr__(self, 'value', cleaned)
    
    def __str__(self) -> str:
        """String representation of phone number."""
        return self.value
    
    def format_display(self) -> str:
        """Format phone number for display (US format example)."""
        # This is a simple US formatting example
        # Can be extended for international formats
        if self.value.startswith('+1') and len(self.value) == 12:
            # US format: +1 (xxx) xxx-xxxx
            return f"+1 ({self.value[2:5]}) {self.value[5:8]}-{self.value[8:12]}"
        return self.value
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {"phone_number": self.value}
    
    @classmethod
    def from_dict(cls, data: dict) -> "PhoneNumber":
        """Create from dictionary."""
        return cls(data.get("phone_number", ""))