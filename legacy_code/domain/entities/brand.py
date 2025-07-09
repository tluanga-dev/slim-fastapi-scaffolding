from typing import Optional

from .base import BaseEntity


class Brand(BaseEntity):
    """Brand domain entity."""
    
    def __init__(
        self,
        brand_name: str,
        brand_code: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """Initialize a Brand entity.
        
        Args:
            brand_name: Name of the brand
            brand_code: Optional unique code for the brand
            description: Optional brand description
        """
        super().__init__(**kwargs)
        self.brand_name = brand_name
        self.brand_code = brand_code
        self.description = description
        self._validate()
    
    def _validate(self):
        """Validate brand business rules."""
        if not self.brand_name or not self.brand_name.strip():
            raise ValueError("Brand name cannot be empty")
        
        if len(self.brand_name) > 100:
            raise ValueError("Brand name cannot exceed 100 characters")
        
        if self.brand_code:
            if not self.brand_code.strip():
                raise ValueError("Brand code cannot be empty if provided")
            
            if len(self.brand_code) > 20:
                raise ValueError("Brand code cannot exceed 20 characters")
            
            # Brand code should be uppercase alphanumeric
            if not self.brand_code.replace("-", "").replace("_", "").isalnum():
                raise ValueError("Brand code must contain only letters, numbers, hyphens, and underscores")
        
        if self.description and len(self.description) > 500:
            raise ValueError("Brand description cannot exceed 500 characters")
    
    def update_name(self, brand_name: str, updated_by: Optional[str] = None):
        """Update brand name."""
        if not brand_name or not brand_name.strip():
            raise ValueError("Brand name cannot be empty")
        
        if len(brand_name) > 100:
            raise ValueError("Brand name cannot exceed 100 characters")
        
        self.brand_name = brand_name
        self.update_timestamp(updated_by)
    
    def update_code(self, brand_code: Optional[str], updated_by: Optional[str] = None):
        """Update brand code."""
        if brand_code is not None:
            if not brand_code.strip():
                raise ValueError("Brand code cannot be empty if provided")
            
            if len(brand_code) > 20:
                raise ValueError("Brand code cannot exceed 20 characters")
            
            if not brand_code.replace("-", "").replace("_", "").isalnum():
                raise ValueError("Brand code must contain only letters, numbers, hyphens, and underscores")
        
        self.brand_code = brand_code
        self.update_timestamp(updated_by)
    
    def update_description(self, description: Optional[str], updated_by: Optional[str] = None):
        """Update brand description."""
        if description and len(description) > 500:
            raise ValueError("Brand description cannot exceed 500 characters")
        
        self.description = description
        self.update_timestamp(updated_by)
    
    def deactivate(self, updated_by: Optional[str] = None):
        """Deactivate the brand."""
        self.is_active = False
        self.update_timestamp(updated_by)
    
    def activate(self, updated_by: Optional[str] = None):
        """Activate the brand."""
        self.is_active = True
        self.update_timestamp(updated_by)
    
    def __str__(self) -> str:
        """String representation of brand."""
        return f"Brand({self.brand_name})"
    
    def __repr__(self) -> str:
        """Developer representation of brand."""
        return f"Brand(id={self.id}, name='{self.brand_name}', code='{self.brand_code}', is_active={self.is_active})"