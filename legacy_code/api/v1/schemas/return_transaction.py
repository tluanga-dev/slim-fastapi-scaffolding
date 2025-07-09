from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .transaction import TransactionHeaderBase


class CompletedReturnItemRecord(BaseModel):
    """Schema for recording a completed return line item (used for both purchase and sale returns)."""

    sku_id: UUID = Field(..., description="SKU that was returned")
    quantity: Decimal = Field(..., gt=0, description="Quantity returned")
    unit_price: Decimal = Field(..., ge=0, description="Original unit price/cost")
    serial_numbers: Optional[List[str]] = Field(
        None, description="Serial numbers for serialized items being returned"
    )
    condition_notes: Optional[str] = Field(
        None, description="Condition/quality notes for returned items"
    )
    return_reason: Optional[str] = Field(
        None, description="Reason for return (defective, wrong item, etc.)"
    )
    notes: Optional[str] = Field(None, description="Additional line item notes")


class CompletedPurchaseReturnRecord(TransactionHeaderBase):
    """Schema for recording a completed purchase return transaction (returning items to supplier)."""

    supplier_id: UUID = Field(
        ..., description="Supplier ID (customer with type=BUSINESS) to return items to"
    )
    original_purchase_id: UUID = Field(
        ..., description="ID of the original purchase transaction being returned"
    )
    return_date: date = Field(..., description="Actual date when return was completed")
    items: List[CompletedReturnItemRecord] = Field(
        ..., description="List of items that were returned to supplier"
    )
    refund_amount: Decimal = Field(
        Decimal("0"), ge=0, description="Total refund amount received from supplier"
    )
    return_authorization: Optional[str] = Field(
        None, description="Supplier's return authorization number (RMA)"
    )
    return_reason: Optional[str] = Field(
        None, description="Overall reason for return to supplier"
    )


class CompletedSaleReturnRecord(TransactionHeaderBase):
    """Schema for recording a completed sale return transaction (customer returning purchased items)."""

    original_sale_id: UUID = Field(
        ..., description="ID of the original sale transaction being returned"
    )
    return_date: date = Field(..., description="Actual date when return was completed")
    items: List[CompletedReturnItemRecord] = Field(
        ..., description="List of items that were returned by customer"
    )
    refund_amount: Decimal = Field(
        Decimal("0"), ge=0, description="Total refund amount given to customer"
    )
    refund_method: Optional[str] = Field(
        None, description="Method of refund (cash, credit card, store credit, etc.)"
    )
    return_reason: Optional[str] = Field(
        None, description="Overall reason for customer return"
    )
    restocking_fee: Decimal = Field(
        Decimal("0"), ge=0, description="Restocking fee charged to customer"
    )


# Legacy/alternative schemas for backward compatibility
class PurchaseReturnCreate(CompletedPurchaseReturnRecord):
    """
    Alternative schema name for purchase return creation.
    """

    pass


class SaleReturnCreate(CompletedSaleReturnRecord):
    """
    Alternative schema name for sale return creation.
    """

    pass


# Return validation schemas
class ReturnValidationRequest(BaseModel):
    """Schema for validating if items can be returned."""

    original_transaction_id: UUID = Field(
        ..., description="ID of original transaction to validate return against"
    )
    items: List[CompletedReturnItemRecord] = Field(
        ..., description="Items to validate for return"
    )


class ReturnValidationResponse(BaseModel):
    """Schema for return validation response."""

    is_valid: bool = Field(..., description="Whether the return is valid")
    validation_errors: List[str] = Field(
        default_factory=list, description="List of validation error messages"
    )
    max_returnable_quantities: dict = Field(
        default_factory=dict, description="Maximum returnable quantity per SKU"
    )
    original_transaction_info: dict = Field(
        default_factory=dict, description="Original transaction details"
    )
