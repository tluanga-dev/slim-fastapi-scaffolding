from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UnitOfMeasurementCreate(BaseModel):
    """Schema for creating a new unit of measurement."""
    name: str = Field(..., min_length=1, max_length=100, description="Unit name")
    abbreviation: Optional[str] = Field(None, max_length=10, description="Unit abbreviation")
    description: Optional[str] = Field(None, max_length=1000, description="Unit description")
    created_by: Optional[str] = Field(None, max_length=255, description="User who created the unit")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Unit name cannot be empty')
        return v.strip()
    
    @field_validator('abbreviation')
    @classmethod
    def validate_abbreviation(cls, v):
        if v is not None:
            v = v.strip()
            if v and not v.replace(" ", "").replace("-", "").replace("/", "").replace(".", "").isalnum():
                raise ValueError('Unit abbreviation contains invalid characters')
        return v


class UnitOfMeasurementUpdate(BaseModel):
    """Schema for updating an existing unit of measurement."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Unit name")
    abbreviation: Optional[str] = Field(None, max_length=10, description="Unit abbreviation")
    description: Optional[str] = Field(None, max_length=1000, description="Unit description")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the unit")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Unit name cannot be empty')
        return v.strip() if v else v
    
    @field_validator('abbreviation')
    @classmethod
    def validate_abbreviation(cls, v):
        if v is not None:
            v = v.strip()
            if v and not v.replace(" ", "").replace("-", "").replace("/", "").replace(".", "").isalnum():
                raise ValueError('Unit abbreviation contains invalid characters')
        return v


class UnitOfMeasurementStatusUpdate(BaseModel):
    """Schema for updating unit of measurement status."""
    is_active: bool = Field(..., description="Unit active status")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the status")


class UnitOfMeasurementResponse(BaseModel):
    """Schema for unit of measurement response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    unit_id: UUID
    name: str
    abbreviation: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    def get_display_name(self) -> str:
        """Get the display name for the unit of measurement."""
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name
    
    def get_conversion_info(self) -> dict:
        """Get conversion information for this unit."""
        return {
            "unit_id": str(self.unit_id),
            "name": self.name,
            "abbreviation": self.abbreviation,
            "can_convert": False,  # Future enhancement for unit conversions
            "base_unit": None      # Future enhancement for base unit relationships
        }


class UnitOfMeasurementListResponse(BaseModel):
    """Schema for unit of measurement list response."""
    units: list[UnitOfMeasurementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UnitOfMeasurementSummary(BaseModel):
    """Schema for unit of measurement summary (lightweight response)."""
    id: UUID
    unit_id: UUID
    name: str
    abbreviation: Optional[str] = None
    is_active: bool
    
    def get_display_name(self) -> str:
        """Get the display name for the unit of measurement."""
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name


class UnitOfMeasurementValidationResponse(BaseModel):
    """Schema for unit of measurement validation response."""
    unit_id: UUID
    name: str
    abbreviation: Optional[str] = None
    is_valid_for_use: bool
    validation_errors: list[str]
    display_name: str