from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class UnitOfMeasurementBase(BaseModel):
    """Base schema for UnitOfMeasurement."""
    name: str = Field(..., min_length=1, max_length=100, description="Unit name")
    abbreviation: Optional[str] = Field(None, max_length=10, description="Unit abbreviation")
    description: Optional[str] = Field(None, max_length=500, description="Unit description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate unit name is not empty."""
        if not v or not v.strip():
            raise ValueError("Unit name cannot be empty")
        return v.strip()
    
    @field_validator('abbreviation')
    @classmethod
    def validate_abbreviation(cls, v: Optional[str]) -> Optional[str]:
        """Validate unit abbreviation format."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
            
        # Check alphanumeric with basic punctuation
        if not v.replace(".", "").replace("/", "").replace("-", "").isalnum():
            raise ValueError("Unit abbreviation must contain only letters, numbers, dots, slashes, and hyphens")
        
        return v.upper()  # Store abbreviations in uppercase


class UnitOfMeasurementCreate(UnitOfMeasurementBase):
    """Schema for creating a unit of measurement."""
    pass


class UnitOfMeasurementUpdate(BaseModel):
    """Schema for updating a unit of measurement."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    abbreviation: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate unit name if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError("Unit name cannot be empty")
            return v.strip()
        return v
    
    @field_validator('abbreviation')
    @classmethod
    def validate_abbreviation(cls, v: Optional[str]) -> Optional[str]:
        """Validate unit abbreviation if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            
            if not v.replace(".", "").replace("/", "").replace("-", "").isalnum():
                raise ValueError("Unit abbreviation must contain only letters, numbers, dots, slashes, and hyphens")
            
            return v.upper()
        return v


class UnitOfMeasurementResponse(UnitOfMeasurementBase):
    """Schema for unit of measurement response."""
    id: UUID
    unit_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class UnitOfMeasurementListResponse(BaseModel):
    """Schema for paginated unit of measurement list response."""
    items: List[UnitOfMeasurementResponse]
    total: int
    skip: int
    limit: int