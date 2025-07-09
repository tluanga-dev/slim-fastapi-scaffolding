from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .transaction import TransactionHeaderBase


class CompletedSaleItemRecord(BaseModel):
    """Schema for recording a completed sale line item."""

    item_id: UUID = Field(..., description="Item that was sold")
    quantity: Decimal = Field(..., gt=0, description="Quantity sold")
    unit_price: Decimal = Field(..., ge=0, description="Sale price per unit")
    discount_percentage: Decimal = Field(
        Decimal("0"), ge=0, le=100, description="Item-level discount percentage"
    )
    serial_numbers: Optional[List[str]] = Field(
        None, description="Serial numbers for serialized items"
    )
    condition_notes: Optional[str] = Field(
        None, description="Condition/quality notes for sold items"
    )
    notes: Optional[str] = Field(None, description="Additional line item notes")


class CompletedSaleRecord(TransactionHeaderBase):
    """Schema for recording a completed sale transaction."""

    sale_date: date = Field(..., description="Actual date when sale was completed")
    items: List[CompletedSaleItemRecord] = Field(
        ..., description="List of items that were sold"
    )
    tax_rate: Decimal = Field(Decimal("0"), ge=0, description="Tax rate percentage")
    discount_amount: Decimal = Field(
        Decimal("0"), ge=0, description="Overall transaction discount amount"
    )
    receipt_number: Optional[str] = Field(
        None, description="External receipt or reference number"
    )
    receipt_date: Optional[date] = Field(None, description="Date of external receipt")


# Legacy schemas kept for backward compatibility (marked as deprecated)
class SaleItemCreate(CompletedSaleItemRecord):
    """
    DEPRECATED: Use CompletedSaleItemRecord instead.
    Schema for sale line item.
    """

    pass


class SaleTransactionCreate(CompletedSaleRecord):
    """
    DEPRECATED: Use CompletedSaleRecord instead.
    Schema for creating sale transaction.
    """

    # Legacy fields for backward compatibility
    auto_reserve: bool = Field(
        True, description="DEPRECATED: Not used in completed sale recording"
    )

    def __init__(self, **data):
        # Handle backward compatibility - use today's date if sale_date not provided
        if "sale_date" not in data:
            data["sale_date"] = date.today()
        super().__init__(**data)


# Remove unused schemas from the new flow
# These are no longer needed since we don't have an order management process
# class SaleOrderApprovalRequest - REMOVED
# class SaleOrderCancellationRequest - REMOVED
