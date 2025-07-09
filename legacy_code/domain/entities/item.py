from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

from .base import BaseEntity


class Item(BaseEntity):
    """
    Represents an item in the inventory.
    """

    def __init__(
        self,
        item_id: UUID,
        sku: str,
        item_name: str,
        category_id: UUID,
        brand_id: Optional[UUID] = None,
        description: Optional[str] = None,
        is_serialized: bool = False,
        barcode: Optional[str] = None,
        model_number: Optional[str] = None,
        weight: Optional[Decimal] = None,
        dimensions: Optional[Dict[str, Decimal]] = None,
        is_rentable: bool = False,
        is_saleable: bool = True,
        min_rental_days: int = 1,
        rental_period: Optional[int] = 1,
        max_rental_days: Optional[int] = None,
        rental_base_price: Optional[Decimal] = None,
        sale_base_price: Optional[Decimal] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        super().__init__(id, created_at, updated_at, is_active, created_by, updated_by)
        self.item_id = item_id
        self.sku = sku
        self.item_name = item_name
        self.category_id = category_id
        self.brand_id = brand_id
        self.description = description
        self.is_serialized = is_serialized
        self.barcode = barcode
        self.model_number = model_number
        self.weight = weight
        self.dimensions = dimensions or {}
        self.is_rentable = is_rentable
        self.is_saleable = is_saleable
        self.min_rental_days = min_rental_days
        self.rental_period = rental_period
        self.max_rental_days = max_rental_days
        self.rental_base_price = rental_base_price
        self.sale_base_price = sale_base_price

    def update_basic_info(
        self,
        item_name: Optional[str] = None,
        description: Optional[str] = None,
        barcode: Optional[str] = None,
        model_number: Optional[str] = None,
        weight: Optional[Decimal] = None,
        dimensions: Optional[Dict[str, Decimal]] = None,
        updated_by: Optional[str] = None
    ):
        """Update basic item information."""
        if item_name is not None:
            self.item_name = item_name
        if description is not None:
            self.description = description
        if barcode is not None:
            self.barcode = barcode
        if model_number is not None:
            self.model_number = model_number
        if weight is not None:
            self.weight = weight
        if dimensions is not None:
            self.dimensions = dimensions
        self.update_timestamp(updated_by)

    def update_pricing(
        self,
        rental_base_price: Optional[Decimal] = None,
        sale_base_price: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ):
        """Update item pricing information."""
        if rental_base_price is not None:
            self.rental_base_price = rental_base_price
        if sale_base_price is not None:
            self.sale_base_price = sale_base_price
        self.update_timestamp(updated_by)

    def update_rental_settings(
        self,
        is_rentable: Optional[bool] = None,
        min_rental_days: Optional[int] = None,
        rental_period: Optional[int] = None,
        max_rental_days: Optional[int] = None,
        updated_by: Optional[str] = None
    ):
        """Update rental-specific settings."""
        if is_rentable is not None:
            self.is_rentable = is_rentable
        if min_rental_days is not None:
            self.min_rental_days = min_rental_days
        if rental_period is not None:
            self.rental_period = rental_period
        if max_rental_days is not None:
            self.max_rental_days = max_rental_days
        self.update_timestamp(updated_by)

    def update_sale_settings(
        self,
        is_saleable: Optional[bool] = None,
        updated_by: Optional[str] = None
    ):
        """Update sale-specific settings."""
        if is_saleable is not None:
            self.is_saleable = is_saleable
        self.update_timestamp(updated_by)

    def can_be_rented(self) -> bool:
        """Check if item can be rented."""
        return self.is_rentable and self.is_active

    def can_be_sold(self) -> bool:
        """Check if item can be sold."""
        return self.is_saleable and self.is_active