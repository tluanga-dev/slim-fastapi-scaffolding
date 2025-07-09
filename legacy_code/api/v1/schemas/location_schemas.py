from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from enum import Enum


class LocationTypeEnum(str, Enum):
    """Location type enumeration for API."""
    STORE = "STORE"
    WAREHOUSE = "WAREHOUSE"
    SERVICE_CENTER = "SERVICE_CENTER"


class LocationBase(BaseModel):
    """Base location schema."""
    location_code: str = Field(..., min_length=1, max_length=20, description="Unique location code")
    location_name: str = Field(..., min_length=1, max_length=100, description="Location name")
    location_type: LocationTypeEnum = Field(..., description="Type of location")
    address: str = Field(..., min_length=1, max_length=500, description="Street address")
    city: str = Field(..., min_length=1, max_length=50, description="City")
    state: str = Field(..., min_length=1, max_length=50, description="State/Province")
    country: str = Field(..., min_length=1, max_length=50, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    manager_user_id: Optional[UUID] = Field(None, description="Manager's user ID")


class LocationCreate(LocationBase):
    """Schema for creating a location."""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    location_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    city: Optional[str] = Field(None, min_length=1, max_length=50)
    state: Optional[str] = Field(None, min_length=1, max_length=50)
    country: Optional[str] = Field(None, min_length=1, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    contact_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    manager_user_id: Optional[UUID] = None


class LocationResponse(LocationBase):
    """Schema for location responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool = True


class LocationListResponse(BaseModel):
    """Schema for paginated location list."""
    items: list[LocationResponse]
    total: int
    skip: int
    limit: int


class LocationFilter(BaseModel):
    """Schema for location filtering."""
    location_type: Optional[LocationTypeEnum] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: Optional[bool] = True


class AssignManagerRequest(BaseModel):
    """Schema for assigning a manager to a location."""
    manager_user_id: UUID = Field(..., description="Manager's user ID")