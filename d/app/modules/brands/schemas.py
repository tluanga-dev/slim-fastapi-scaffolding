from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BrandCreate(BaseModel):
    """Schema for creating a new brand."""
    brand_name: str = Field(..., min_length=1, max_length=100, description="Brand name")
    brand_code: Optional[str] = Field(None, max_length=20, description="Optional unique brand code")
    description: Optional[str] = Field(None, description="Brand description")
    created_by: Optional[str] = Field(None, max_length=255, description="User who created the brand")
    
    @field_validator('brand_name')
    @classmethod
    def validate_brand_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Brand name cannot be empty')
        return v.strip()
    
    @field_validator('brand_code')
    @classmethod
    def validate_brand_code(cls, v):
        if v is not None:
            v = v.strip().upper()
            if not v:
                return None
            if len(v) > 20:
                raise ValueError('Brand code cannot exceed 20 characters')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class BrandUpdate(BaseModel):
    """Schema for updating brand information."""
    brand_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Brand name")
    brand_code: Optional[str] = Field(None, max_length=20, description="Brand code")
    description: Optional[str] = Field(None, description="Brand description")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the brand")
    
    @field_validator('brand_name')
    @classmethod
    def validate_brand_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Brand name cannot be empty')
        return v.strip() if v else v
    
    @field_validator('brand_code')
    @classmethod
    def validate_brand_code(cls, v):
        if v is not None:
            v = v.strip().upper()
            if not v:
                return None
            if len(v) > 20:
                raise ValueError('Brand code cannot exceed 20 characters')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class BrandStatusUpdate(BaseModel):
    """Schema for updating brand status."""
    is_active: bool = Field(..., description="Brand active status")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the status")


class BrandResponse(BaseModel):
    """Schema for brand response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    brand_name: str
    brand_code: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    def get_display_name(self) -> str:
        """Get the display name for the brand."""
        if self.brand_code:
            return f"{self.brand_name} ({self.brand_code})"
        return self.brand_name
    
    def get_short_name(self) -> str:
        """Get a short name for the brand, preferring code if available."""
        return self.brand_code or self.brand_name


class BrandListResponse(BaseModel):
    """Schema for brand list response."""
    brands: list[BrandResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BrandSearchResponse(BaseModel):
    """Schema for brand search response."""
    id: UUID
    brand_name: str
    brand_code: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    
    def get_display_name(self) -> str:
        """Get the display name for the brand."""
        if self.brand_code:
            return f"{self.brand_name} ({self.brand_code})"
        return self.brand_name