from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade


# InventoryUnit Schemas
class InventoryUnitBase(BaseModel):
    """Base schema for inventory unit."""
    inventory_code: str = Field(..., description="Unique inventory code")
    item_id: UUID = Field(..., description="Item ID")
    location_id: UUID = Field(..., description="Location ID")
    serial_number: Optional[str] = Field(None, description="Serial number for serialized items")
    current_status: InventoryStatus = Field(InventoryStatus.AVAILABLE_SALE, description="Current status")
    condition_grade: ConditionGrade = Field(ConditionGrade.A, description="Condition grade")
    purchase_date: Optional[date] = Field(None, description="Purchase date")
    purchase_cost: Optional[Decimal] = Field(None, description="Purchase cost")
    notes: Optional[str] = Field(None, description="Additional notes")


class InventoryUnitCreate(InventoryUnitBase):
    """Schema for creating inventory unit."""
    pass


class InventoryUnitUpdate(BaseModel):
    """Schema for updating inventory unit."""
    location_id: Optional[UUID] = None
    current_status: Optional[InventoryStatus] = None
    condition_grade: Optional[ConditionGrade] = None
    current_value: Optional[Decimal] = None
    notes: Optional[str] = None


class InventoryUnitResponse(InventoryUnitBase):
    """Schema for inventory unit response."""
    id: UUID
    current_value: Optional[Decimal]
    last_inspection_date: Optional[date]
    total_rental_days: int
    rental_count: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class InventoryUnitListResponse(BaseModel):
    """Schema for paginated inventory unit list."""
    items: List[InventoryUnitResponse]
    total: int
    skip: int
    limit: int


# StockLevel Schemas
class StockLevelBase(BaseModel):
    """Base schema for stock level."""
    item_id: UUID = Field(..., description="Item ID")
    location_id: UUID = Field(..., description="Location ID")
    reorder_point: int = Field(0, ge=0, description="Reorder point")
    reorder_quantity: int = Field(0, ge=0, description="Reorder quantity")
    maximum_stock: Optional[int] = Field(None, ge=0, description="Maximum stock level")


class StockLevelCreate(StockLevelBase):
    """Schema for creating stock level."""
    quantity_on_hand: int = Field(0, ge=0, description="Initial quantity on hand")


class StockLevelUpdate(BaseModel):
    """Schema for updating stock level parameters."""
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=1)
    maximum_stock: Optional[int] = Field(None, ge=0)


class StockLevelResponse(StockLevelBase):
    """Schema for stock level response."""
    id: UUID
    quantity_on_hand: int
    quantity_available: int
    quantity_reserved: int
    quantity_in_transit: int
    quantity_damaged: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class StockLevelListResponse(BaseModel):
    """Schema for paginated stock level list."""
    items: List[StockLevelResponse]
    total: int
    skip: int
    limit: int


# Operation Schemas
class InventoryStatusUpdate(BaseModel):
    """Schema for updating inventory status."""
    new_status: InventoryStatus
    reason: Optional[str] = Field(None, description="Reason for status change")


class InventoryInspection(BaseModel):
    """Schema for inventory inspection."""
    condition_grade: ConditionGrade
    inspection_notes: str = Field(..., description="Inspection notes")
    passed_inspection: bool = Field(True, description="Whether unit passed inspection")
    photos: Optional[List[str]] = Field(None, description="Photo URLs")


class InventoryTransfer(BaseModel):
    """Schema for inventory transfer."""
    to_location_id: UUID = Field(..., description="Destination location ID")
    transfer_reason: str = Field(..., description="Reason for transfer")


class BulkInventoryTransfer(BaseModel):
    """Schema for bulk inventory transfer."""
    inventory_ids: List[UUID] = Field(..., description="List of inventory IDs to transfer")
    to_location_id: UUID = Field(..., description="Destination location ID")
    transfer_reason: str = Field(..., description="Reason for transfer")


class SkuInventoryTransfer(BaseModel):
    """Schema for transferring inventory by Item."""
    item_id: UUID
    from_location_id: UUID
    to_location_id: UUID
    quantity: int = Field(..., ge=1)
    transfer_reason: str
    condition_grade: Optional[ConditionGrade] = None


class StockOperation(BaseModel):
    """Schema for stock level operations."""
    operation: str = Field(..., description="Operation type: receive, reserve, release, ship, damage, undamage, adjust")
    quantity: int = Field(..., ge=1, description="Quantity to operate on")
    reason: Optional[str] = Field(None, description="Reason for operation")


class StockReconciliation(BaseModel):
    """Schema for stock reconciliation."""
    physical_count: int = Field(..., ge=0, description="Physical count from inventory")
    reason: str = Field(..., description="Reason for reconciliation")


class BulkReceiveItem(BaseModel):
    """Schema for bulk receive item."""
    item_id: UUID
    quantity: int = Field(..., ge=1)


class BulkReceive(BaseModel):
    """Schema for bulk receive operation."""
    items: List[BulkReceiveItem]
    reference_number: Optional[str] = Field(None, description="PO or reference number")


class StockAvailabilityQuery(BaseModel):
    """Schema for checking stock availability."""
    item_id: UUID
    quantity: int = Field(..., ge=1)
    location_id: Optional[UUID] = None
    for_sale: bool = Field(True, description="Check for sale (True) or rent (False)")
    min_condition_grade: Optional[ConditionGrade] = None


class MultiSkuAvailabilityQuery(BaseModel):
    """Schema for checking multiple Item availability."""
    items: List[dict] = Field(..., description="List of items with item_id, quantity, and optional min_condition_grade")
    location_id: Optional[UUID] = None
    for_sale: bool = True


class StockAvailabilityResponse(BaseModel):
    """Schema for stock availability response."""
    available: bool
    requested_quantity: int
    available_quantity: int
    location_id: Optional[str] = None
    total_available_quantity: Optional[int] = None
    stock_details: Optional[dict] = None
    available_units: List[dict] = []
    locations_with_stock: Optional[List[dict]] = None


class LowStockAlert(BaseModel):
    """Schema for low stock alert."""
    item_id: str
    sku: str
    item_name: str
    location_id: str
    location_name: str
    quantity_available: int
    reorder_point: int
    reorder_quantity: int
    urgency: str


class OverstockReport(BaseModel):
    """Schema for overstock report item."""
    item_id: str
    sku_code: str
    sku_name: str
    location_id: str
    location_name: str
    quantity_on_hand: int
    maximum_stock: int
    overage: int
    overage_percentage: float


class StockValuation(BaseModel):
    """Schema for stock valuation summary."""
    total_items: int
    total_units: int
    total_available: int
    total_damaged: int
    location_name: Optional[str] = None


class InventoryStatusCount(BaseModel):
    """Schema for inventory count by status."""
    status_counts: dict


class InventoryConditionCount(BaseModel):
    """Schema for inventory count by condition."""
    condition_counts: dict