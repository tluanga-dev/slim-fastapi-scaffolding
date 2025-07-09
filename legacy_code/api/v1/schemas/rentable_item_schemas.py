from typing import Optional, List, Dict
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field


class RentableItemLocation(BaseModel):
    """Schema for rental item location availability."""
    location_id: str = Field(..., description="Location ID")
    location_name: str = Field(..., description="Location name")
    available_quantity: int = Field(..., ge=0, description="Available quantity for rent")
    total_stock: int = Field(..., ge=0, description="Total stock at location")


class RentableItemAvailability(BaseModel):
    """Schema for rental item availability information."""
    total_available: int = Field(..., ge=0, description="Total available quantity across all locations")
    locations: List[RentableItemLocation] = Field(..., description="Locations with available stock")


class RentableItemCategory(BaseModel):
    """Schema for rental item category information."""
    id: Optional[str] = Field(None, description="Category ID")
    name: Optional[str] = Field(None, description="Category name")


class RentableItemBrand(BaseModel):
    """Schema for rental item brand information."""
    id: Optional[str] = Field(None, description="Brand ID")
    name: Optional[str] = Field(None, description="Brand name")


class RentableItemPricing(BaseModel):
    """Schema for rental item pricing information."""
    base_price: Optional[float] = Field(None, ge=0, description="Base rental price")
    min_rental_days: int = Field(..., ge=1, description="Minimum rental days")
    max_rental_days: Optional[int] = Field(None, ge=1, description="Maximum rental days")
    rental_period: Optional[str] = Field(None, description="Default rental period")


class RentableItemDetails(BaseModel):
    """Schema for rental item additional details."""
    model_number: Optional[str] = Field(None, description="Model number")
    barcode: Optional[str] = Field(None, description="Barcode")
    weight: Optional[float] = Field(None, ge=0, description="Item weight")
    dimensions: Optional[str] = Field(None, description="Item dimensions")
    is_serialized: bool = Field(False, description="Whether item requires serial tracking")


class RentableItemResponse(BaseModel):
    """Schema for rentable item response."""
    id: str = Field(..., description="Item ID")
    sku: str = Field(..., description="Item SKU")
    item_name: str = Field(..., description="Item name")
    category: Optional[RentableItemCategory] = Field(None, description="Item category")
    brand: Optional[RentableItemBrand] = Field(None, description="Item brand")
    rental_pricing: RentableItemPricing = Field(..., description="Rental pricing information")
    availability: RentableItemAvailability = Field(..., description="Availability information")
    item_details: RentableItemDetails = Field(..., description="Additional item details")


class RentableItemListResponse(BaseModel):
    """Schema for paginated rentable item list response."""
    items: List[RentableItemResponse] = Field(..., description="List of rentable items")
    total: int = Field(..., ge=0, description="Total number of items")
    skip: int = Field(..., ge=0, description="Number of items skipped")
    limit: int = Field(..., ge=1, description="Number of items per page")


class RentableItemSearchParams(BaseModel):
    """Schema for rentable item search parameters."""
    search: Optional[str] = Field(None, min_length=1, max_length=255, description="Search term for name or SKU")
    location_id: Optional[str] = Field(None, description="Location ID filter")
    category_id: Optional[str] = Field(None, description="Category ID filter")
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "search": "drill",
                "location_id": "550e8400-e29b-41d4-a716-446655440000",
                "category_id": "550e8400-e29b-41d4-a716-446655440001",
                "skip": 0,
                "limit": 20
            }
        }