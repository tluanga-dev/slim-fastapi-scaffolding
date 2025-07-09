from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class BrandBase(BaseModel):
    """Base schema for Brand."""
    brand_name: str = Field(..., min_length=1, max_length=100, description="Brand name")
    brand_code: Optional[str] = Field(None, max_length=20, description="Unique brand code")
    description: Optional[str] = Field(None, max_length=500, description="Brand description")
    
    @field_validator('brand_name')
    @classmethod
    def validate_brand_name(cls, v: str) -> str:
        """Validate brand name is not empty."""
        if not v or not v.strip():
            raise ValueError("Brand name cannot be empty")
        return v.strip()
    
    @field_validator('brand_code')
    @classmethod
    def validate_brand_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate brand code format."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
            
        # Check alphanumeric with hyphens and underscores
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Brand code must contain only letters, numbers, hyphens, and underscores")
        
        return v.upper()  # Store codes in uppercase


class BrandCreate(BrandBase):
    """Schema for creating a brand."""
    pass


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""
    brand_name: Optional[str] = Field(None, min_length=1, max_length=100)
    brand_code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('brand_name')
    @classmethod
    def validate_brand_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate brand name if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError("Brand name cannot be empty")
            return v.strip()
        return v
    
    @field_validator('brand_code')
    @classmethod
    def validate_brand_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate brand code if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            
            if not v.replace("-", "").replace("_", "").isalnum():
                raise ValueError("Brand code must contain only letters, numbers, hyphens, and underscores")
            
            return v.upper()
        return v


class BrandResponse(BrandBase):
    """Schema for brand response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    """Schema for paginated brand list response."""
    items: List[BrandResponse]
    total: int
    skip: int
    limit: int