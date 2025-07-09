from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal
from datetime import date
from typing import Optional
from uuid import UUID

from app.core.domain.value_objects.item_type import InventoryStatus, ConditionGrade


class InventoryUnitCreate(BaseModel):
    """Schema for creating an inventory unit."""
    inventory_code: str = Field(..., min_length=1, max_length=50, description="Unique inventory code")
    item_id: UUID = Field(..., description="ID of the item this unit belongs to")
    location_id: UUID = Field(..., description="ID of the location where this unit is stored")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number of the unit")
    current_status: InventoryStatus = Field(default=InventoryStatus.AVAILABLE_SALE, description="Current status of the inventory unit")
    condition_grade: ConditionGrade = Field(default=ConditionGrade.A, description="Condition grade of the unit")
    purchase_date: Optional[date] = Field(None, description="Date when the unit was purchased")
    purchase_cost: Optional[Decimal] = Field(None, ge=0, description="Cost of purchasing the unit")
    current_value: Optional[Decimal] = Field(None, ge=0, description="Current estimated value of the unit")
    last_inspection_date: Optional[date] = Field(None, description="Date of last inspection")
    notes: Optional[str] = Field(None, description="Additional notes about the unit")
    
    @field_validator('purchase_date', 'last_inspection_date')
    @classmethod
    def validate_dates_not_future(cls, v):
        if v and v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class InventoryUnitUpdate(BaseModel):
    """Schema for updating an inventory unit."""
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number of the unit")
    current_status: Optional[InventoryStatus] = Field(None, description="Current status of the inventory unit")
    condition_grade: Optional[ConditionGrade] = Field(None, description="Condition grade of the unit")
    current_value: Optional[Decimal] = Field(None, ge=0, description="Current estimated value of the unit")
    last_inspection_date: Optional[date] = Field(None, description="Date of last inspection")
    notes: Optional[str] = Field(None, description="Additional notes about the unit")
    
    @field_validator('last_inspection_date')
    @classmethod
    def validate_inspection_date_not_future(cls, v):
        if v and v > date.today():
            raise ValueError("Inspection date cannot be in the future")
        return v


class InventoryUnitLocationUpdate(BaseModel):
    """Schema for updating inventory unit location."""
    location_id: UUID = Field(..., description="New location ID")


class InventoryUnitStatusUpdate(BaseModel):
    """Schema for updating inventory unit status."""
    current_status: InventoryStatus = Field(..., description="New status")


class InventoryUnitConditionUpdate(BaseModel):
    """Schema for updating inventory unit condition."""
    condition_grade: ConditionGrade = Field(..., description="New condition grade")


class InventoryUnitRentalUpdate(BaseModel):
    """Schema for updating rental information."""
    rental_days: int = Field(..., ge=0, description="Number of rental days to add")


class InventoryUnitResponse(BaseModel):
    """Schema for inventory unit response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    inventory_code: str
    item_id: UUID
    location_id: UUID
    serial_number: Optional[str]
    current_status: InventoryStatus
    condition_grade: ConditionGrade
    purchase_date: Optional[date]
    purchase_cost: Optional[Decimal]
    current_value: Optional[Decimal]
    last_inspection_date: Optional[date]
    total_rental_days: int
    rental_count: int
    notes: Optional[str]
    is_active: bool
    created_at: date
    updated_at: date
    created_by: Optional[str]
    updated_by: Optional[str]


class InventoryUnitListResponse(BaseModel):
    """Schema for inventory unit list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    inventory_code: str
    item_id: UUID
    location_id: UUID
    serial_number: Optional[str]
    current_status: InventoryStatus
    condition_grade: ConditionGrade
    current_value: Optional[Decimal]
    total_rental_days: int
    rental_count: int
    is_active: bool


class InventoryUnitSummary(BaseModel):
    """Schema for inventory unit summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    inventory_code: str
    current_status: InventoryStatus
    condition_grade: ConditionGrade
    current_value: Optional[Decimal]


class InventoryUnitMetrics(BaseModel):
    """Schema for inventory unit metrics."""
    inventory_unit_id: UUID
    depreciation_rate: float = Field(..., description="Depreciation rate as percentage")
    utilization_rate: float = Field(..., description="Utilization rate as percentage")
    rental_frequency: float = Field(..., description="Average rental frequency")


class InventoryUnitSearchRequest(BaseModel):
    """Schema for inventory unit search request."""
    item_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    status: Optional[InventoryStatus] = None
    condition_grade: Optional[ConditionGrade] = None
    serial_number: Optional[str] = None
    inventory_code: Optional[str] = None
    is_active: Optional[bool] = True
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class InventoryUnitBulkStatusUpdate(BaseModel):
    """Schema for bulk status update."""
    inventory_unit_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    new_status: InventoryStatus
    
    @field_validator('inventory_unit_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Inventory unit IDs must be unique")
        return v


class InventoryUnitBulkLocationUpdate(BaseModel):
    """Schema for bulk location update."""
    inventory_unit_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    new_location_id: UUID
    
    @field_validator('inventory_unit_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Inventory unit IDs must be unique")
        return v