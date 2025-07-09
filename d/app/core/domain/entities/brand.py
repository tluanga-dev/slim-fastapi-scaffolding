from datetime import datetime
from typing import Optional
from uuid import UUID

from .base import BaseEntity


class Brand(BaseEntity):
    """Brand domain entity."""
    
    def __init__(
        self,
        brand_name: str,
        brand_code: Optional[str] = None,
        description: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        """Initialize Brand entity."""
        super().__init__(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            is_active=is_active,
            created_by=created_by,
            updated_by=updated_by
        )
        self.brand_name = brand_name
        self.brand_code = brand_code
        self.description = description
    
    def update_name(self, new_name: str, updated_by: Optional[str] = None) -> None:
        """Update brand name."""
        if not new_name or not new_name.strip():
            raise ValueError("Brand name cannot be empty")
        
        self.brand_name = new_name.strip()
        self.update_timestamp(updated_by)
    
    def update_code(self, new_code: Optional[str], updated_by: Optional[str] = None) -> None:
        """Update brand code."""
        if new_code:
            new_code = new_code.strip().upper()
            if not new_code:
                new_code = None
        
        self.brand_code = new_code
        self.update_timestamp(updated_by)
    
    def update_description(self, new_description: Optional[str], updated_by: Optional[str] = None) -> None:
        """Update brand description."""
        if new_description:
            new_description = new_description.strip()
            if not new_description:
                new_description = None
        
        self.description = new_description
        self.update_timestamp(updated_by)
    
    def __str__(self) -> str:
        """String representation of Brand."""
        return f"Brand(name='{self.brand_name}', code='{self.brand_code}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of Brand."""
        return (f"Brand(id={self.id}, brand_name='{self.brand_name}', "
                f"brand_code='{self.brand_code}', is_active={self.is_active})")