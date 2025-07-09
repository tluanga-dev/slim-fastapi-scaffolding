from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.domain.entities.location import LocationType


class LocationCreate(BaseModel):
    """Schema for creating a new location."""
    location_code: str = Field(..., min_length=1, max_length=50, description="Unique location code")
    location_name: str = Field(..., min_length=1, max_length=255, description="Location name")
    location_type: LocationType = Field(..., description="Type of location")
    address: str = Field(..., min_length=1, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    state: str = Field(..., min_length=1, max_length=100, description="State/Province")
    country: str = Field(..., min_length=1, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    manager_user_id: Optional[UUID] = Field(None, description="Manager user ID")
    created_by: Optional[str] = Field(None, max_length=255, description="User who created the location")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and ('@' not in v or '.' not in v.split('@')[-1]):
            raise ValueError('Invalid email format')
        return v


class LocationUpdate(BaseModel):
    """Schema for updating an existing location."""
    location_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Location name")
    address: Optional[str] = Field(None, min_length=1, description="Street address")
    city: Optional[str] = Field(None, min_length=1, max_length=100, description="City")
    state: Optional[str] = Field(None, min_length=1, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, min_length=1, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the location")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and ('@' not in v or '.' not in v.split('@')[-1]):
            raise ValueError('Invalid email format')
        return v


class LocationContactUpdate(BaseModel):
    """Schema for updating location contact information."""
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the contact info")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and ('@' not in v or '.' not in v.split('@')[-1]):
            raise ValueError('Invalid email format')
        return v


class LocationManagerUpdate(BaseModel):
    """Schema for updating location manager."""
    manager_user_id: Optional[UUID] = Field(None, description="Manager user ID (null to remove)")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the manager")


class LocationStatusUpdate(BaseModel):
    """Schema for updating location status."""
    is_active: bool = Field(..., description="Location active status")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the status")


class LocationResponse(BaseModel):
    """Schema for location response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    location_code: str
    location_name: str
    location_type: LocationType
    address: str
    city: str
    state: str
    country: str
    postal_code: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    manager_user_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    def get_full_address(self) -> str:
        """Get the full formatted address."""
        parts = [self.address, self.city, self.state]
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(parts)


class LocationListResponse(BaseModel):
    """Schema for location list response."""
    locations: list[LocationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int