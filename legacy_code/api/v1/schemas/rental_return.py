from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from ....domain.value_objects.rental_return_type import ReturnType, ReturnStatus
from ....domain.value_objects.item_type import ConditionGrade
from ....domain.value_objects.inspection_type import InspectionStatus, DamageSeverity


# Base schemas
class RentalReturnLineBase(BaseModel):
    """Base schema for rental return lines."""
    inventory_unit_id: UUID
    original_quantity: int = Field(gt=0, description="Original rented quantity")
    returned_quantity: int = Field(ge=0, description="Quantity being returned")
    condition_grade: Optional[ConditionGrade] = None
    late_fee: Optional[Decimal] = Field(None, ge=0)
    damage_fee: Optional[Decimal] = Field(None, ge=0)
    cleaning_fee: Optional[Decimal] = Field(None, ge=0)
    replacement_fee: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class RentalReturnBase(BaseModel):
    """Base schema for rental returns."""
    rental_transaction_id: UUID
    return_date: date
    return_type: ReturnType = ReturnType.FULL
    return_location_id: Optional[UUID] = None
    expected_return_date: Optional[date] = None
    notes: Optional[str] = None


# Request schemas
class InitiateReturnRequest(BaseModel):
    """Request schema for initiating a rental return."""
    rental_transaction_id: UUID
    return_date: date
    return_items: List[Dict[str, Any]] = Field(
        description="List of items being returned with quantities",
        example=[{"inventory_unit_id": "uuid", "quantity": 1, "notes": "Good condition"}]
    )
    return_location_id: Optional[UUID] = None
    return_type: ReturnType = ReturnType.FULL
    notes: Optional[str] = None
    processed_by: Optional[str] = None


class ProcessPartialReturnRequest(BaseModel):
    """Request schema for processing partial returns."""
    line_updates: List[Dict[str, Any]] = Field(
        description="Updates for return lines",
        example=[{
            "line_id": "uuid",
            "returned_quantity": 1,
            "condition_grade": "A",
            "notes": "Item in excellent condition"
        }]
    )
    process_inventory: bool = True
    updated_by: Optional[str] = None


class CalculateLateFeeRequest(BaseModel):
    """Request schema for calculating late fees."""
    daily_late_fee_rate: Optional[Decimal] = Field(None, ge=0)
    use_percentage_of_rental_rate: bool = True
    percentage_rate: Decimal = Field(Decimal("0.10"), ge=0, le=1)
    updated_by: Optional[str] = None


class AssessDamageRequest(BaseModel):
    """Request schema for damage assessment."""
    inspector_id: str
    line_assessments: List[Dict[str, Any]] = Field(
        description="Damage assessments for each line",
        example=[{
            "line_id": "uuid",
            "condition_grade": "C",
            "damage_description": "Minor scratches on surface",
            "damage_photos": ["photo1.jpg", "photo2.jpg"],
            "estimated_repair_cost": 25.00,
            "cleaning_required": False,
            "replacement_required": False
        }]
    )
    general_notes: Optional[str] = None
    inspection_date: Optional[datetime] = None


class CompleteInspectionRequest(BaseModel):
    """Request schema for completing inspections."""
    approved: bool
    approver_id: str
    approval_notes: Optional[str] = None


class FinalizeReturnRequest(BaseModel):
    """Request schema for finalizing returns."""
    finalized_by: str
    force_finalize: bool = False
    finalization_notes: Optional[str] = None


class ReleaseDepositRequest(BaseModel):
    """Request schema for releasing deposits."""
    processed_by: str
    override_amount: Optional[Decimal] = Field(None, ge=0)
    release_notes: Optional[str] = None


class ReverseDepositReleaseRequest(BaseModel):
    """Request schema for reversing deposit releases."""
    reason: str
    processed_by: str


# Response schemas
class RentalReturnLineResponse(RentalReturnLineBase):
    """Response schema for rental return lines."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    return_id: UUID
    is_processed: bool = False
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool = True


class InspectionReportResponse(BaseModel):
    """Response schema for inspection reports."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    return_id: UUID
    inspector_id: str
    inspection_date: datetime
    inspection_status: InspectionStatus
    damage_found: bool = False
    total_damage_cost: Decimal = Field(default=Decimal("0.00"))
    general_notes: Optional[str] = None
    damage_findings: List[Dict[str, Any]] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)
    is_approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RentalReturnResponse(RentalReturnBase):
    """Response schema for rental returns."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    return_status: ReturnStatus
    total_late_fee: Optional[Decimal] = Field(None, ge=0)
    total_damage_fee: Optional[Decimal] = Field(None, ge=0)
    total_cleaning_fee: Optional[Decimal] = Field(None, ge=0)
    total_replacement_fee: Optional[Decimal] = Field(None, ge=0)
    deposit_released: bool = False
    deposit_release_amount: Optional[Decimal] = None
    deposit_release_date: Optional[datetime] = None
    finalized_at: Optional[datetime] = None
    finalized_by: Optional[str] = None
    processed_by: Optional[str] = None
    lines: List[RentalReturnLineResponse] = Field(default_factory=list)
    inspection_reports: List[InspectionReportResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool = True


class RentalReturnListResponse(BaseModel):
    """Response schema for paginated rental return lists."""
    returns: List[RentalReturnResponse]
    total: int
    skip: int
    limit: int


# Validation and preview schemas
class PartialReturnValidationResponse(BaseModel):
    """Response schema for partial return validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class LateFeeCalculationResponse(BaseModel):
    """Response schema for late fee calculations."""
    return_id: str
    is_late: bool
    days_late: int = 0
    expected_return_date: Optional[str] = None
    actual_return_date: Optional[str] = None
    total_late_fee: float = 0.0
    line_fees: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectedLateFeeResponse(BaseModel):
    """Response schema for projected late fees."""
    return_id: str
    projected_return_date: str
    expected_return_date: Optional[str] = None
    would_be_late: bool
    projected_days_late: int = 0
    projected_late_fee: float = 0.0
    daily_rate_used: Optional[float] = None


class InspectionSummaryResponse(BaseModel):
    """Response schema for inspection summaries."""
    return_id: str
    has_inspections: bool
    total_reports: int = 0
    completed_inspections: int = 0
    approved_inspections: int = 0
    damage_findings: int = 0
    total_damage_cost: float = 0.0
    total_assessed_fees: float = 0.0
    inspection_complete: bool = False


class FinalizationPreviewResponse(BaseModel):
    """Response schema for finalization previews."""
    return_id: str
    current_status: str
    can_finalize: bool
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    fee_totals: Dict[str, float] = Field(default_factory=dict)
    inventory_changes: List[Dict[str, Any]] = Field(default_factory=list)
    lines_processed: int = 0
    total_lines: int = 0


class DepositCalculationResponse(BaseModel):
    """Response schema for deposit calculations."""
    original_deposit: float
    release_amount: float
    withheld_amount: float
    calculation_method: str
    fee_breakdown: Dict[str, float] = Field(default_factory=dict)


class DepositPreviewResponse(BaseModel):
    """Response schema for deposit release previews."""
    return_id: str
    return_status: str
    can_release_deposit: bool
    deposit_calculation: DepositCalculationResponse
    scenarios: Optional[List[Dict[str, Any]]] = None


class DepositReleaseResponse(BaseModel):
    """Response schema for deposit releases."""
    return_id: str
    transaction_id: str
    customer_id: str
    original_deposit: float
    release_amount: float
    withheld_amount: float
    calculation_method: str
    fee_breakdown: Dict[str, float]
    payment_result: Dict[str, Any]
    processed_by: str
    processed_at: str
    notes: Optional[str] = None


class DepositReversalResponse(BaseModel):
    """Response schema for deposit reversals."""
    return_id: str
    original_release_amount: float
    reversal_reason: str
    processed_by: str
    processed_at: str
    status: str


# Filter schemas
class RentalReturnFilters(BaseModel):
    """Filters for rental return queries."""
    transaction_id: Optional[UUID] = None
    return_status: Optional[ReturnStatus] = None
    return_type: Optional[ReturnType] = None
    location_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_late: Optional[bool] = None
    needs_inspection: Optional[bool] = None
    is_active: Optional[bool] = True
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)