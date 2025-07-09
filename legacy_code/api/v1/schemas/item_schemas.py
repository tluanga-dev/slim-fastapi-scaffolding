from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from .category_schemas import CategoryResponse
from .brand_schemas import BrandResponse


class ItemBase(BaseModel):
    """Base schema for Item."""
    sku: str = Field(..., min_length=1, max_length=100, description="Item SKU")
    item_name: str = Field(..., min_length=1, max_length=255, description="Item name")
    category_id: UUID = Field(..., description="Category ID")
    brand_id: Optional[UUID] = Field(None, description="Brand ID")
    description: Optional[str] = Field(None, max_length=1000, description="Item description")
    is_serialized: bool = Field(False, description="Whether item requires serial number tracking")
    barcode: Optional[str] = Field(None, max_length=100, description="Item barcode")
    model_number: Optional[str] = Field(None, max_length=100, description="Model number")
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=3, description="Item weight")
    dimensions: Optional[Dict[str, Decimal]] = Field(None, description="Item dimensions")
    is_rentable: bool = Field(False, description="Whether item can be rented")
    is_saleable: bool = Field(True, description="Whether item can be sold")
    min_rental_days: int = Field(1, ge=1, description="Minimum rental days")
    rental_period: Optional[int] = Field(1, ge=1, description="Default rental period")
    max_rental_days: Optional[int] = Field(None, ge=1, description="Maximum rental days")
    rental_base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Base rental price")
    sale_base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Base sale price")
    
    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Validate SKU is not empty."""
        if not v or not v.strip():
            raise ValueError("SKU cannot be empty")
        return v.strip().upper()
    
    @field_validator('item_name')
    @classmethod
    def validate_item_name(cls, v: str) -> str:
        """Validate item name is not empty."""
        if not v or not v.strip():
            raise ValueError("Item name cannot be empty")
        return v.strip()
    
    @field_validator('barcode')
    @classmethod
    def validate_barcode(cls, v: Optional[str]) -> Optional[str]:
        """Validate barcode format."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
            
        # Check alphanumeric
        if not v.isalnum():
            raise ValueError("Barcode must contain only letters and numbers")
        
        return v.upper()
    
    @model_validator(mode='after')
    def validate_rental_days(self) -> 'ItemBase':
        """Validate max rental days is greater than min rental days."""
        if self.max_rental_days is not None and self.max_rental_days < self.min_rental_days:
            raise ValueError("Maximum rental days must be greater than or equal to minimum rental days")
        return self
    
    @model_validator(mode='after')
    def validate_availability_exclusivity(self) -> 'ItemBase':
        """Validate that item cannot be both rentable and saleable."""
        if self.is_rentable and self.is_saleable:
            raise ValueError("Item cannot be available for both rent and sale simultaneously")
        return self


class ItemCreate(ItemBase):
    """Schema for creating an item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    barcode: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    dimensions: Optional[Dict[str, Decimal]] = Field(None)
    is_rentable: Optional[bool] = Field(None, description="Whether item can be rented")
    is_saleable: Optional[bool] = Field(None, description="Whether item can be sold")
    
    @field_validator('item_name')
    @classmethod
    def validate_item_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate item name if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError("Item name cannot be empty")
            return v.strip()
        return v
    
    @field_validator('barcode')
    @classmethod
    def validate_barcode(cls, v: Optional[str]) -> Optional[str]:
        """Validate barcode if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            
            if not v.isalnum():
                raise ValueError("Barcode must contain only letters and numbers")
            
            return v.upper()
        return v
    
    @model_validator(mode='after')
    def validate_availability_exclusivity(self) -> 'ItemUpdate':
        """Validate that item cannot be both rentable and saleable."""
        if (self.is_rentable is not None and self.is_saleable is not None and 
            self.is_rentable and self.is_saleable):
            raise ValueError("Item cannot be available for both rent and sale simultaneously")
        return self


class ItemPricingUpdate(BaseModel):
    """Schema for updating item pricing."""
    rental_base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    sale_base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class ItemRentalSettingsUpdate(BaseModel):
    """Schema for updating item rental settings."""
    is_rentable: Optional[bool] = Field(None)
    min_rental_days: Optional[int] = Field(None, ge=1)
    rental_period: Optional[int] = Field(None, ge=1)
    max_rental_days: Optional[int] = Field(None, ge=1)
    
    @model_validator(mode='after')
    def validate_rental_days(self) -> 'ItemRentalSettingsUpdate':
        """Validate max rental days is greater than min rental days."""
        if (self.max_rental_days is not None and 
            self.min_rental_days is not None and 
            self.max_rental_days < self.min_rental_days):
            raise ValueError("Maximum rental days must be greater than or equal to minimum rental days")
        return self


class ItemSaleSettingsUpdate(BaseModel):
    """Schema for updating item sale settings."""
    is_saleable: Optional[bool] = Field(None)


class ItemResponse(ItemBase):
    """Schema for item response."""
    id: UUID
    item_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class ItemWithRelationsResponse(ItemBase):
    """Schema for item response with related entities."""
    id: UUID
    item_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool
    
    # Related entities
    category: Optional[CategoryResponse] = None
    brand: Optional[BrandResponse] = None
    
    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """Schema for paginated item list response."""
    items: List[ItemResponse]
    total: int
    skip: int
    limit: int


class ItemListWithRelationsResponse(BaseModel):
    """Schema for paginated item list response with related entities."""
    items: List[ItemWithRelationsResponse]
    total: int
    skip: int
    limit: int


class ItemSearchRequest(BaseModel):
    """Schema for item search request."""
    query: str = Field(..., min_length=1, max_length=255, description="Search query")
    search_type: str = Field("name", description="Search type: 'name' or 'sku'")
    
    @field_validator('search_type')
    @classmethod
    def validate_search_type(cls, v: str) -> str:
        """Validate search type."""
        if v not in ['name', 'sku']:
            raise ValueError("Search type must be 'name' or 'sku'")
        return v