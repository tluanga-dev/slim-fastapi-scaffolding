"""
Schemas for rentals due today API endpoints.
"""
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


class RentalItemResponse(BaseModel):
    """Schema for rental item in due today response."""
    sku_code: str
    item_name: str
    quantity: float
    unit_price: float


class RentalDueTodayResponse(BaseModel):
    """Schema for a single rental due today."""
    transaction_id: UUID
    transaction_number: str
    customer_id: UUID
    customer_name: str
    customer_phone: Optional[str] = None
    rental_start_date: date
    rental_end_date: date
    rental_days: int
    is_overdue: bool
    days_overdue: int = 0
    days_remaining: int = 0
    total_amount: float
    deposit_amount: float
    balance_due: float
    items: List[RentalItemResponse]
    location_id: UUID
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RentalDueTodaySummary(BaseModel):
    """Summary statistics for rentals due today."""
    total_due_today: int = 0
    total_overdue: int = 0
    total_due_soon: int = 0
    total_revenue_at_risk: float = 0.0
    total_deposits_held: float = 0.0


class RentalDueTodayListResponse(BaseModel):
    """Response schema for list of rentals due today with pagination."""
    rentals: List[RentalDueTodayResponse]
    total: int
    skip: int
    limit: int
    summary: RentalDueTodaySummary

    class Config:
        from_attributes = True
