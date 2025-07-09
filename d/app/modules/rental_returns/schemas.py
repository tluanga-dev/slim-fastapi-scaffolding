from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from app.core.domain.value_objects.rental_return_type import (
    ReturnStatus, ReturnType, DamageLevel, InspectionStatus, FeeType, ReturnLineStatus
)
from app.core.domain.value_objects.item_type import ConditionGrade


# Return Line Schemas
class RentalReturnLineCreate(BaseModel):
    """Schema for creating a rental return line."""
    inventory_unit_id: UUID = Field(..., description="ID of the inventory unit being returned")
    original_quantity: int = Field(..., ge=1, description="Original quantity rented")
    returned_quantity: int = Field(default=0, ge=0, description="Quantity being returned")
    condition_grade: ConditionGrade = Field(default=ConditionGrade.A, description="Condition grade of returned items")
    damage_level: DamageLevel = Field(default=DamageLevel.NONE, description="Level of damage observed")
    late_fee: Optional[Decimal] = Field(None, ge=0, description="Late return fee")
    damage_fee: Optional[Decimal] = Field(None, ge=0, description="Damage repair fee")
    cleaning_fee: Optional[Decimal] = Field(None, ge=0, description="Cleaning fee")
    replacement_fee: Optional[Decimal] = Field(None, ge=0, description="Replacement fee")
    notes: Optional[str] = Field(None, description="Additional notes about the return")
    
    @field_validator('returned_quantity')
    @classmethod
    def validate_returned_quantity(cls, v, values):
        if 'original_quantity' in values.data and v > values.data['original_quantity']:
            raise ValueError("Returned quantity cannot exceed original quantity")
        return v


class RentalReturnLineUpdate(BaseModel):
    """Schema for updating a rental return line."""
    returned_quantity: Optional[int] = Field(None, ge=0, description="Quantity being returned")
    condition_grade: Optional[ConditionGrade] = Field(None, description="Condition grade of returned items")
    damage_level: Optional[DamageLevel] = Field(None, description="Level of damage observed")
    late_fee: Optional[Decimal] = Field(None, ge=0, description="Late return fee")
    damage_fee: Optional[Decimal] = Field(None, ge=0, description="Damage repair fee")
    cleaning_fee: Optional[Decimal] = Field(None, ge=0, description="Cleaning fee")
    replacement_fee: Optional[Decimal] = Field(None, ge=0, description="Replacement fee")
    notes: Optional[str] = Field(None, description="Additional notes about the return")


class RentalReturnLineProcessing(BaseModel):
    """Schema for processing a rental return line."""
    processed_by: str = Field(..., description="User processing the return line")


class RentalReturnLineResponse(BaseModel):
    """Schema for rental return line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    return_id: UUID
    inventory_unit_id: UUID
    original_quantity: int
    returned_quantity: int
    condition_grade: ConditionGrade
    damage_level: DamageLevel
    late_fee: Decimal
    damage_fee: Decimal
    cleaning_fee: Decimal
    replacement_fee: Decimal
    is_processed: bool
    processed_at: Optional[datetime]
    processed_by: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]


class RentalReturnLineSummary(BaseModel):
    """Schema for rental return line summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    inventory_unit_id: UUID
    returned_quantity: int
    original_quantity: int
    condition_grade: ConditionGrade
    damage_level: DamageLevel
    total_fees: Decimal
    is_processed: bool


# Return Schemas
class RentalReturnCreate(BaseModel):
    """Schema for creating a rental return."""
    rental_transaction_id: UUID = Field(..., description="ID of the rental transaction being returned")
    return_date: date = Field(..., description="Date of the return")
    return_type: ReturnType = Field(default=ReturnType.FULL, description="Type of return (full or partial)")
    return_location_id: Optional[UUID] = Field(None, description="Location where items are being returned")
    expected_return_date: Optional[date] = Field(None, description="Originally expected return date")
    notes: Optional[str] = Field(None, description="Additional notes about the return")
    lines: List[RentalReturnLineCreate] = Field(..., min_length=1, description="Return lines")
    
    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v):
        if v > date.today():
            raise ValueError("Return date cannot be in the future")
        return v
    
    @field_validator('lines')
    @classmethod
    def validate_lines(cls, v):
        if not v:
            raise ValueError("At least one return line is required")
        return v


class RentalReturnUpdate(BaseModel):
    """Schema for updating a rental return."""
    return_date: Optional[date] = Field(None, description="Date of the return")
    return_type: Optional[ReturnType] = Field(None, description="Type of return")
    return_location_id: Optional[UUID] = Field(None, description="Return location")
    expected_return_date: Optional[date] = Field(None, description="Expected return date")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v):
        if v and v > date.today():
            raise ValueError("Return date cannot be in the future")
        return v


class RentalReturnStatusUpdate(BaseModel):
    """Schema for updating return status."""
    return_status: ReturnStatus = Field(..., description="New return status")


class RentalReturnFinancialUpdate(BaseModel):
    """Schema for updating financial information."""
    total_deposit_release: Optional[Decimal] = Field(None, ge=0, description="Total deposit release amount")
    total_refund_amount: Optional[Decimal] = Field(None, ge=0, description="Total refund amount")


class RentalReturnResponse(BaseModel):
    """Schema for rental return response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_transaction_id: UUID
    return_date: date
    return_type: ReturnType
    return_status: ReturnStatus
    return_location_id: Optional[UUID]
    expected_return_date: Optional[date]
    processed_by: Optional[str]
    notes: Optional[str]
    total_late_fee: Decimal
    total_damage_fee: Decimal
    total_deposit_release: Decimal
    total_refund_amount: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]


class RentalReturnWithLines(RentalReturnResponse):
    """Schema for rental return with lines."""
    lines: List[RentalReturnLineResponse] = Field(default_factory=list)


class RentalReturnListResponse(BaseModel):
    """Schema for rental return list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_transaction_id: UUID
    return_date: date
    return_type: ReturnType
    return_status: ReturnStatus
    return_location_id: Optional[UUID]
    total_late_fee: Decimal
    total_damage_fee: Decimal
    total_refund_amount: Decimal
    is_active: bool


class RentalReturnSummary(BaseModel):
    """Schema for rental return summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    return_date: date
    return_status: ReturnStatus
    return_type: ReturnType
    total_fees: Decimal
    total_refund: Decimal
    net_amount: Decimal


# Search and Filter Schemas
class RentalReturnSearchRequest(BaseModel):
    """Schema for rental return search request."""
    rental_transaction_id: Optional[UUID] = None
    return_location_id: Optional[UUID] = None
    return_status: Optional[ReturnStatus] = None
    return_type: Optional[ReturnType] = None
    return_date_from: Optional[date] = None
    return_date_to: Optional[date] = None
    processed_by: Optional[str] = None
    is_active: Optional[bool] = True
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class RentalReturnLineSearchRequest(BaseModel):
    """Schema for rental return line search request."""
    return_id: Optional[UUID] = None
    inventory_unit_id: Optional[UUID] = None
    condition_grade: Optional[ConditionGrade] = None
    damage_level: Optional[DamageLevel] = None
    is_processed: Optional[bool] = None
    processed_by: Optional[str] = None
    is_active: Optional[bool] = True
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# Bulk Operations Schemas
class RentalReturnBulkStatusUpdate(BaseModel):
    """Schema for bulk status update."""
    return_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    new_status: ReturnStatus
    
    @field_validator('return_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Return IDs must be unique")
        return v


class RentalReturnLineBulkProcessing(BaseModel):
    """Schema for bulk line processing."""
    line_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    processed_by: str
    
    @field_validator('line_ids')
    @classmethod
    def validate_unique_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Line IDs must be unique")
        return v


# Analytics and Reporting Schemas
class RentalReturnMetrics(BaseModel):
    """Schema for rental return metrics."""
    total_returns: int
    completed_returns: int
    cancelled_returns: int
    returns_with_damage: int
    returns_with_late_fees: int
    average_return_time_days: float
    total_fees_collected: Decimal
    total_refunds_issued: Decimal


class ReturnStatusSummary(BaseModel):
    """Schema for return status summary."""
    status: ReturnStatus
    count: int
    percentage: float


class DamageLevelSummary(BaseModel):
    """Schema for damage level summary."""
    damage_level: DamageLevel
    count: int
    total_damage_fees: Decimal


class RentalReturnAnalytics(BaseModel):
    """Schema for rental return analytics."""
    metrics: RentalReturnMetrics
    status_breakdown: List[ReturnStatusSummary]
    damage_breakdown: List[DamageLevelSummary]
    period_start: date
    period_end: date


# Validation Response Schemas
class RentalReturnValidationResponse(BaseModel):
    """Schema for rental return validation response."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class RentalReturnEstimate(BaseModel):
    """Schema for rental return cost estimate."""
    estimated_late_fees: Decimal
    estimated_damage_fees: Decimal
    estimated_total_fees: Decimal
    estimated_deposit_release: Decimal
    estimated_refund_amount: Decimal
    days_late: int