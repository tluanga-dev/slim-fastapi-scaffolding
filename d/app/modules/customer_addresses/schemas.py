from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, validator
from app.core.domain.value_objects.address_type import AddressType


class CustomerAddressCreate(BaseModel):
    """Schema for creating a customer address."""
    customer_id: UUID = Field(..., description="Customer ID")
    address_type: AddressType = Field(..., description="Type of address")
    street: str = Field(..., min_length=1, max_length=200, description="Street address")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: str = Field(..., min_length=1, max_length=50, description="City")
    state: str = Field(..., min_length=1, max_length=50, description="State")
    country: str = Field(..., min_length=1, max_length=50, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    is_default: bool = Field(False, description="Whether this is the default address")
    created_by: Optional[str] = Field(None, max_length=255, description="User who created the address")
    
    @validator('street', 'city', 'state', 'country')
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('address_line2', 'postal_code')
    def validate_optional_fields(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CustomerAddressUpdate(BaseModel):
    """Schema for updating a customer address."""
    address_type: Optional[AddressType] = Field(None, description="Type of address")
    street: Optional[str] = Field(None, min_length=1, max_length=200, description="Street address")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: Optional[str] = Field(None, min_length=1, max_length=50, description="City")
    state: Optional[str] = Field(None, min_length=1, max_length=50, description="State")
    country: Optional[str] = Field(None, min_length=1, max_length=50, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the address")
    
    @validator('street', 'city', 'state', 'country')
    def validate_required_fields(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Field cannot be empty')
        return v.strip() if v else v
    
    @validator('address_line2', 'postal_code')
    def validate_optional_fields(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CustomerAddressStatusUpdate(BaseModel):
    """Schema for updating customer address status."""
    is_active: bool = Field(..., description="Active status")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the status")


class CustomerAddressDefaultUpdate(BaseModel):
    """Schema for setting address as default."""
    is_default: bool = Field(..., description="Default status")
    updated_by: Optional[str] = Field(None, max_length=255, description="User who updated the default status")


class CustomerAddressResponse(BaseModel):
    """Schema for customer address response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    customer_id: UUID
    address_type: AddressType
    street: str
    address_line2: Optional[str]
    city: str
    state: str
    country: str
    postal_code: Optional[str]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    
    @property
    def formatted_address(self) -> str:
        """Get formatted address string."""
        parts = [self.street]
        if self.address_line2:
            parts.append(self.address_line2)
        
        city_state = f"{self.city}, {self.state}"
        if self.postal_code:
            city_state += f" {self.postal_code}"
        parts.append(city_state)
        parts.append(self.country)
        
        return "\n".join(parts)
    
    @property
    def address_type_display(self) -> str:
        """Get display name for address type."""
        return AddressType.get_display_name(self.address_type)


class CustomerAddressSummary(BaseModel):
    """Schema for customer address summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    customer_id: UUID
    address_type: AddressType
    street: str
    city: str
    state: str
    country: str
    postal_code: Optional[str]
    is_default: bool
    is_active: bool
    
    @property
    def short_address(self) -> str:
        """Get short address string."""
        return f"{self.street}, {self.city}, {self.state}"
    
    @property
    def address_type_display(self) -> str:
        """Get display name for address type."""
        return AddressType.get_display_name(self.address_type)


class CustomerAddressListResponse(BaseModel):
    """Schema for paginated customer address list response."""
    addresses: List[CustomerAddressResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CustomerAddressValidationResponse(BaseModel):
    """Schema for address validation response."""
    address_id: UUID
    is_valid: bool
    is_active: bool
    exists: bool
    validation_message: str


class CustomerAddressBulkResponse(BaseModel):
    """Schema for bulk address operations response."""
    processed: int
    successful: int
    failed: int
    errors: List[str]