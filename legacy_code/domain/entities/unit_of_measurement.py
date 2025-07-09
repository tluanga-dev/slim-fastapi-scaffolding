from datetime import datetime
from typing import Optional
from uuid import UUID

from .base import BaseEntity


class UnitOfMeasurement(BaseEntity):
    """
    Represents a unit of measurement for items in the inventory.
    """

    def __init__(
        self,
        unit_id: UUID,
        name: str,
        abbreviation: Optional[str] = None,
        description: Optional[str] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        super().__init__(id, created_at, updated_at, is_active, created_by, updated_by)
        self.unit_id = unit_id
        self.name = name
        self.abbreviation = abbreviation
        self.description = description

    def update_details(
        self,
        name: Optional[str] = None,
        abbreviation: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update unit of measurement details."""
        if name is not None:
            self.name = name
        if abbreviation is not None:
            self.abbreviation = abbreviation
        if description is not None:
            self.description = description
        self.update_timestamp(updated_by)