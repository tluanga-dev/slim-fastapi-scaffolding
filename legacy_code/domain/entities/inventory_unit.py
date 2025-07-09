from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ..entities.base import BaseEntity
from ..value_objects.item_type import InventoryStatus, ConditionGrade


class InventoryUnit(BaseEntity):
    """Inventory Unit entity representing an individual inventory item."""
    
    def __init__(
        self,
        inventory_code: str,
        item_id: UUID,
        location_id: UUID,
        serial_number: Optional[str] = None,
        current_status: InventoryStatus = InventoryStatus.AVAILABLE_SALE,
        condition_grade: ConditionGrade = ConditionGrade.A,
        purchase_date: Optional[date] = None,
        purchase_cost: Optional[Decimal] = None,
        current_value: Optional[Decimal] = None,
        last_inspection_date: Optional[date] = None,
        total_rental_days: int = 0,
        rental_count: int = 0,
        notes: Optional[str] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Initialize Inventory Unit entity."""
        super().__init__(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            is_active=is_active,
            created_by=created_by,
            updated_by=updated_by
        )
        self.inventory_code = inventory_code
        self.item_id = item_id
        self.location_id = location_id
        self.serial_number = serial_number
        self.current_status = current_status
        self.condition_grade = condition_grade
        self.purchase_date = purchase_date
        self.purchase_cost = purchase_cost
        self.current_value = current_value or purchase_cost
        self.last_inspection_date = last_inspection_date
        self.total_rental_days = total_rental_days
        self.rental_count = rental_count
        self.notes = notes
        self._validate()
    
    def _validate(self):
        """Validate inventory unit business rules."""
        if not self.inventory_code or not self.inventory_code.strip():
            raise ValueError("Inventory code is required")
        
        if not self.item_id:
            raise ValueError("Item ID is required")
        
        if not self.location_id:
            raise ValueError("Location ID is required")
        
        if self.current_status not in InventoryStatus:
            raise ValueError(f"Invalid inventory status: {self.current_status}")
        
        if self.condition_grade not in ConditionGrade:
            raise ValueError(f"Invalid condition grade: {self.condition_grade}")
        
        if self.purchase_cost is not None and self.purchase_cost < 0:
            raise ValueError("Purchase cost cannot be negative")
        
        if self.current_value is not None and self.current_value < 0:
            raise ValueError("Current value cannot be negative")
        
        if self.total_rental_days < 0:
            raise ValueError("Total rental days cannot be negative")
        
        if self.rental_count < 0:
            raise ValueError("Rental count cannot be negative")
    
    def can_transition_to(self, new_status: InventoryStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            InventoryStatus.AVAILABLE_SALE: [
                InventoryStatus.RESERVED_SALE,
                InventoryStatus.AVAILABLE_RENT,
                InventoryStatus.INSPECTION_PENDING,
                InventoryStatus.DAMAGED,
                InventoryStatus.LOST
            ],
            InventoryStatus.AVAILABLE_RENT: [
                InventoryStatus.RESERVED_RENT,
                InventoryStatus.AVAILABLE_SALE,
                InventoryStatus.INSPECTION_PENDING,
                InventoryStatus.DAMAGED,
                InventoryStatus.LOST
            ],
            InventoryStatus.RESERVED_SALE: [
                InventoryStatus.SOLD,
                InventoryStatus.AVAILABLE_SALE
            ],
            InventoryStatus.RESERVED_RENT: [
                InventoryStatus.RENTED,
                InventoryStatus.AVAILABLE_RENT
            ],
            InventoryStatus.RENTED: [
                InventoryStatus.INSPECTION_PENDING,
                InventoryStatus.LOST,
                InventoryStatus.DAMAGED
            ],
            InventoryStatus.SOLD: [],  # Terminal status
            InventoryStatus.INSPECTION_PENDING: [
                InventoryStatus.AVAILABLE_RENT,
                InventoryStatus.CLEANING,
                InventoryStatus.REPAIR,
                InventoryStatus.DAMAGED
            ],
            InventoryStatus.CLEANING: [
                InventoryStatus.AVAILABLE_RENT,
                InventoryStatus.REPAIR
            ],
            InventoryStatus.REPAIR: [
                InventoryStatus.AVAILABLE_RENT,
                InventoryStatus.DAMAGED
            ],
            InventoryStatus.DAMAGED: [
                InventoryStatus.REPAIR,
                InventoryStatus.AVAILABLE_SALE,  # Sell as-is
                InventoryStatus.LOST  # Write off
            ],
            InventoryStatus.IN_TRANSIT: [
                InventoryStatus.AVAILABLE_SALE,
                InventoryStatus.AVAILABLE_RENT,
                InventoryStatus.INSPECTION_PENDING
            ],
            InventoryStatus.LOST: []  # Terminal status
        }
        
        return new_status in valid_transitions.get(self.current_status, [])
    
    def update_status(self, new_status: InventoryStatus, updated_by: Optional[str] = None):
        """Update inventory status with validation."""
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.current_status.value} to {new_status.value}"
            )
        
        self.current_status = new_status
        self.update_timestamp(updated_by)
    
    def update_location(self, location_id: UUID, updated_by: Optional[str] = None):
        """Update inventory location."""
        if not location_id:
            raise ValueError("Location ID is required")
        
        # Can only move if not currently rented or sold
        if self.current_status in [InventoryStatus.RENTED, InventoryStatus.SOLD]:
            raise ValueError(f"Cannot move inventory in {self.current_status.value} status")
        
        self.location_id = location_id
        self.update_timestamp(updated_by)
    
    def update_condition(
        self,
        condition_grade: ConditionGrade,
        notes: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update condition grade."""
        self.condition_grade = condition_grade
        if notes:
            self.notes = f"{self.notes}\n{notes}" if self.notes else notes
        self.update_timestamp(updated_by)
    
    def record_inspection(
        self,
        condition_grade: ConditionGrade,
        notes: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Record an inspection."""
        self.condition_grade = condition_grade
        self.last_inspection_date = date.today()
        if notes:
            self.notes = f"{self.notes}\n{notes}" if self.notes else notes
        self.update_timestamp(updated_by)
    
    def increment_rental_stats(self, rental_days: int, updated_by: Optional[str] = None):
        """Increment rental statistics."""
        if rental_days < 0:
            raise ValueError("Rental days cannot be negative")
        
        self.total_rental_days += rental_days
        self.rental_count += 1
        self.update_timestamp(updated_by)
    
    def update_value(self, current_value: Decimal, updated_by: Optional[str] = None):
        """Update current value."""
        if current_value < 0:
            raise ValueError("Current value cannot be negative")
        
        self.current_value = current_value
        self.update_timestamp(updated_by)
    
    def mark_as_sold(self, updated_by: Optional[str] = None):
        """Mark inventory as sold."""
        if self.current_status != InventoryStatus.RESERVED_SALE:
            raise ValueError("Can only sell inventory that is reserved for sale")
        
        self.current_status = InventoryStatus.SOLD
        self.update_timestamp(updated_by)
    
    def mark_as_lost(self, notes: str, updated_by: Optional[str] = None):
        """Mark inventory as lost."""
        if self.current_status == InventoryStatus.SOLD:
            raise ValueError("Cannot mark sold inventory as lost")
        
        self.current_status = InventoryStatus.LOST
        self.notes = f"{self.notes}\nLOST: {notes}" if self.notes else f"LOST: {notes}"
        self.update_timestamp(updated_by)
    
    @property
    def is_available(self) -> bool:
        """Check if inventory is available for sale or rent."""
        return self.current_status in [
            InventoryStatus.AVAILABLE_SALE,
            InventoryStatus.AVAILABLE_RENT
        ]
    
    @property
    def is_rentable(self) -> bool:
        """Check if inventory can be rented."""
        return self.current_status == InventoryStatus.AVAILABLE_RENT
    
    @property
    def is_saleable(self) -> bool:
        """Check if inventory can be sold."""
        return self.current_status == InventoryStatus.AVAILABLE_SALE
    
    @property
    def requires_inspection(self) -> bool:
        """Check if inventory requires inspection."""
        return self.current_status == InventoryStatus.INSPECTION_PENDING
    
    @property
    def is_in_service(self) -> bool:
        """Check if inventory is being serviced."""
        return self.current_status in [
            InventoryStatus.CLEANING,
            InventoryStatus.REPAIR
        ]
    
    def __str__(self) -> str:
        """String representation of inventory unit."""
        return f"InventoryUnit({self.inventory_code}: {self.current_status.value})"
    
    def __repr__(self) -> str:
        """Developer representation of inventory unit."""
        return (
            f"InventoryUnit(id={self.id}, inventory_code='{self.inventory_code}', "
            f"status={self.current_status.value}, condition={self.condition_grade.value})"
        )