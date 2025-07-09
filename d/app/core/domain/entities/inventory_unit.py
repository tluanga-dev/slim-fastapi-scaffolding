from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from .base import BaseEntity
from ..value_objects.item_type import InventoryStatus, ConditionGrade


class InventoryUnit(BaseEntity):
    """Inventory unit domain entity representing individual inventory items."""
    
    def __init__(
        self,
        inventory_code: str,
        item_id: UUID,
        location_id: UUID,
        current_status: InventoryStatus = InventoryStatus.AVAILABLE_SALE,
        condition_grade: ConditionGrade = ConditionGrade.A,
        serial_number: Optional[str] = None,
        purchase_date: Optional[date] = None,
        purchase_cost: Optional[Decimal] = None,
        current_value: Optional[Decimal] = None,
        last_inspection_date: Optional[date] = None,
        total_rental_days: int = 0,
        rental_count: int = 0,
        notes: Optional[str] = None,
        **kwargs
    ):
        """Initialize an InventoryUnit entity."""
        super().__init__(**kwargs)
        self.inventory_code = inventory_code
        self.item_id = item_id
        self.location_id = location_id
        self.serial_number = serial_number
        self.current_status = current_status
        self.condition_grade = condition_grade
        self.purchase_date = purchase_date
        self.purchase_cost = purchase_cost
        self.current_value = current_value
        self.last_inspection_date = last_inspection_date
        self.total_rental_days = total_rental_days
        self.rental_count = rental_count
        self.notes = notes
        self._validate()
    
    def _validate(self):
        """Validate inventory unit business rules."""
        if not self.inventory_code or not self.inventory_code.strip():
            raise ValueError("Inventory code cannot be empty")
        
        if not self.item_id:
            raise ValueError("Item ID cannot be empty")
        
        if not self.location_id:
            raise ValueError("Location ID cannot be empty")
        
        if not isinstance(self.current_status, InventoryStatus):
            raise ValueError(f"Invalid inventory status: {self.current_status}")
        
        if not isinstance(self.condition_grade, ConditionGrade):
            raise ValueError(f"Invalid condition grade: {self.condition_grade}")
        
        if self.purchase_cost is not None and self.purchase_cost < 0:
            raise ValueError("Purchase cost cannot be negative")
        
        if self.current_value is not None and self.current_value < 0:
            raise ValueError("Current value cannot be negative")
        
        if self.total_rental_days < 0:
            raise ValueError("Total rental days cannot be negative")
        
        if self.rental_count < 0:
            raise ValueError("Rental count cannot be negative")
        
        if self.purchase_date and self.purchase_date > date.today():
            raise ValueError("Purchase date cannot be in the future")
        
        if self.last_inspection_date and self.last_inspection_date > date.today():
            raise ValueError("Last inspection date cannot be in the future")
    
    def update_status(self, new_status: InventoryStatus, updated_by: Optional[str] = None):
        """Update the inventory status."""
        if not isinstance(new_status, InventoryStatus):
            raise ValueError(f"Invalid inventory status: {new_status}")
        
        old_status = self.current_status
        self.current_status = new_status
        self.update_timestamp(updated_by)
        
        # Business rule: If marking as rented, increment rental count
        if old_status != InventoryStatus.RENTED and new_status == InventoryStatus.RENTED:
            self.rental_count += 1
    
    def update_condition(self, new_condition: ConditionGrade, updated_by: Optional[str] = None):
        """Update the condition grade."""
        if not isinstance(new_condition, ConditionGrade):
            raise ValueError(f"Invalid condition grade: {new_condition}")
        
        self.condition_grade = new_condition
        self.update_timestamp(updated_by)
    
    def update_location(self, new_location_id: UUID, updated_by: Optional[str] = None):
        """Update the location."""
        if not new_location_id:
            raise ValueError("Location ID cannot be empty")
        
        self.location_id = new_location_id
        self.update_timestamp(updated_by)
    
    def update_value(self, new_value: Decimal, updated_by: Optional[str] = None):
        """Update the current value."""
        if new_value < 0:
            raise ValueError("Current value cannot be negative")
        
        self.current_value = new_value
        self.update_timestamp(updated_by)
    
    def add_rental_days(self, days: int, updated_by: Optional[str] = None):
        """Add rental days to the total."""
        if days < 0:
            raise ValueError("Rental days cannot be negative")
        
        self.total_rental_days += days
        self.update_timestamp(updated_by)
    
    def update_inspection_date(self, inspection_date: date, updated_by: Optional[str] = None):
        """Update the last inspection date."""
        if inspection_date > date.today():
            raise ValueError("Inspection date cannot be in the future")
        
        self.last_inspection_date = inspection_date
        self.update_timestamp(updated_by)
    
    def update_notes(self, notes: Optional[str], updated_by: Optional[str] = None):
        """Update the notes."""
        self.notes = notes
        self.update_timestamp(updated_by)
    
    def mark_as_rented(self, updated_by: Optional[str] = None):
        """Mark the inventory unit as rented."""
        self.update_status(InventoryStatus.RENTED, updated_by)
    
    def mark_as_returned(self, updated_by: Optional[str] = None):
        """Mark the inventory unit as returned (available for rental)."""
        self.update_status(InventoryStatus.AVAILABLE_RENTAL, updated_by)
    
    def mark_as_sold(self, updated_by: Optional[str] = None):
        """Mark the inventory unit as sold."""
        self.update_status(InventoryStatus.SOLD, updated_by)
    
    def mark_as_maintenance(self, updated_by: Optional[str] = None):
        """Mark the inventory unit as under maintenance."""
        self.update_status(InventoryStatus.MAINTENANCE, updated_by)
    
    def mark_as_damaged(self, updated_by: Optional[str] = None):
        """Mark the inventory unit as damaged."""
        self.update_status(InventoryStatus.DAMAGED, updated_by)
    
    def mark_as_lost(self, updated_by: Optional[str] = None):
        """Mark the inventory unit as lost."""
        self.update_status(InventoryStatus.LOST, updated_by)
    
    def retire(self, updated_by: Optional[str] = None):
        """Retire the inventory unit."""
        self.update_status(InventoryStatus.RETIRED, updated_by)
    
    def is_available(self) -> bool:
        """Check if the inventory unit is available."""
        return self.current_status.is_available()
    
    def is_rentable(self) -> bool:
        """Check if the inventory unit can be rented."""
        return (self.current_status.can_be_rented() and 
                self.condition_grade.is_rentable() and 
                self.is_active)
    
    def is_sellable(self) -> bool:
        """Check if the inventory unit can be sold."""
        return (self.current_status.can_be_sold() and 
                self.condition_grade.is_sellable() and 
                self.is_active)
    
    def needs_maintenance(self) -> bool:
        """Check if the inventory unit needs maintenance."""
        return self.condition_grade.requires_maintenance()
    
    def get_depreciation_rate(self) -> float:
        """Calculate depreciation rate based on condition and usage."""
        if not self.purchase_cost or not self.current_value:
            return 0.0
        
        depreciation = float(self.purchase_cost - self.current_value)
        return (depreciation / float(self.purchase_cost)) * 100
    
    def get_utilization_rate(self) -> float:
        """Calculate utilization rate based on rental history."""
        if self.total_rental_days == 0:
            return 0.0
        
        # Simple utilization calculation - could be enhanced with time periods
        if self.purchase_date:
            days_owned = (date.today() - self.purchase_date).days
            if days_owned > 0:
                return (self.total_rental_days / days_owned) * 100
        
        return 0.0
    
    def get_rental_frequency(self) -> float:
        """Calculate average rental frequency."""
        if self.rental_count == 0 or self.total_rental_days == 0:
            return 0.0
        
        return self.total_rental_days / self.rental_count