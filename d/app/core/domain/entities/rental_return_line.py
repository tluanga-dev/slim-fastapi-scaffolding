from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from .base import BaseEntity
from ..value_objects.rental_return_type import DamageLevel, ReturnLineStatus
from ..value_objects.item_type import ConditionGrade


class RentalReturnLine(BaseEntity):
    """Rental return line domain entity representing individual returned items."""
    
    def __init__(
        self,
        return_id: UUID,
        inventory_unit_id: UUID,
        original_quantity: int,
        returned_quantity: int = 0,
        condition_grade: ConditionGrade = ConditionGrade.A,
        damage_level: DamageLevel = DamageLevel.NONE,
        late_fee: Decimal = Decimal('0.00'),
        damage_fee: Decimal = Decimal('0.00'),
        cleaning_fee: Decimal = Decimal('0.00'),
        replacement_fee: Decimal = Decimal('0.00'),
        notes: Optional[str] = None,
        **kwargs
    ):
        """Initialize a RentalReturnLine entity."""
        super().__init__(**kwargs)
        self.return_id = return_id
        self.inventory_unit_id = inventory_unit_id
        self.original_quantity = original_quantity
        self.returned_quantity = returned_quantity
        self.condition_grade = condition_grade
        self.damage_level = damage_level
        self.late_fee = late_fee
        self.damage_fee = damage_fee
        self.cleaning_fee = cleaning_fee
        self.replacement_fee = replacement_fee
        self.notes = notes
        
        # Processing tracking (private attributes)
        self._is_processed = False
        self._processed_at: Optional[datetime] = None
        self._processed_by: Optional[str] = None
        
        self._validate()
    
    def _validate(self):
        """Validate rental return line business rules."""
        if not self.return_id:
            raise ValueError("Return ID cannot be empty")
        
        if not self.inventory_unit_id:
            raise ValueError("Inventory unit ID cannot be empty")
        
        if self.original_quantity <= 0:
            raise ValueError("Original quantity must be positive")
        
        if self.returned_quantity < 0:
            raise ValueError("Returned quantity cannot be negative")
        
        if self.returned_quantity > self.original_quantity:
            raise ValueError("Returned quantity cannot exceed original quantity")
        
        if not isinstance(self.condition_grade, ConditionGrade):
            raise ValueError(f"Invalid condition grade: {self.condition_grade}")
        
        if not isinstance(self.damage_level, DamageLevel):
            raise ValueError(f"Invalid damage level: {self.damage_level}")
        
        # Validate fee amounts
        for fee_name, fee_value in [
            ("late_fee", self.late_fee),
            ("damage_fee", self.damage_fee),
            ("cleaning_fee", self.cleaning_fee),
            ("replacement_fee", self.replacement_fee)
        ]:
            if fee_value < 0:
                raise ValueError(f"{fee_name} cannot be negative")
    
    @property
    def is_processed(self) -> bool:
        """Check if the return line has been processed."""
        return self._is_processed
    
    @property
    def processed_at(self) -> Optional[datetime]:
        """Get the processing timestamp."""
        return self._processed_at
    
    @property
    def processed_by(self) -> Optional[str]:
        """Get who processed this line."""
        return self._processed_by
    
    def update_returned_quantity(self, quantity: int, updated_by: Optional[str] = None):
        """Update the returned quantity."""
        if quantity < 0:
            raise ValueError("Returned quantity cannot be negative")
        
        if quantity > self.original_quantity:
            raise ValueError("Returned quantity cannot exceed original quantity")
        
        if self._is_processed:
            raise ValueError("Cannot update quantity for processed return line")
        
        self.returned_quantity = quantity
        self.update_timestamp(updated_by)
    
    def update_condition(self, condition_grade: ConditionGrade, updated_by: Optional[str] = None):
        """Update the condition grade."""
        if not isinstance(condition_grade, ConditionGrade):
            raise ValueError(f"Invalid condition grade: {condition_grade}")
        
        if self._is_processed:
            raise ValueError("Cannot update condition for processed return line")
        
        self.condition_grade = condition_grade
        self.update_timestamp(updated_by)
    
    def update_damage_level(self, damage_level: DamageLevel, updated_by: Optional[str] = None):
        """Update the damage level."""
        if not isinstance(damage_level, DamageLevel):
            raise ValueError(f"Invalid damage level: {damage_level}")
        
        if self._is_processed:
            raise ValueError("Cannot update damage level for processed return line")
        
        self.damage_level = damage_level
        self.update_timestamp(updated_by)
    
    def update_fees(
        self,
        late_fee: Optional[Decimal] = None,
        damage_fee: Optional[Decimal] = None,
        cleaning_fee: Optional[Decimal] = None,
        replacement_fee: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ):
        """Update fee amounts."""
        if self._is_processed:
            raise ValueError("Cannot update fees for processed return line")
        
        if late_fee is not None:
            if late_fee < 0:
                raise ValueError("Late fee cannot be negative")
            self.late_fee = late_fee
        
        if damage_fee is not None:
            if damage_fee < 0:
                raise ValueError("Damage fee cannot be negative")
            self.damage_fee = damage_fee
        
        if cleaning_fee is not None:
            if cleaning_fee < 0:
                raise ValueError("Cleaning fee cannot be negative")
            self.cleaning_fee = cleaning_fee
        
        if replacement_fee is not None:
            if replacement_fee < 0:
                raise ValueError("Replacement fee cannot be negative")
            self.replacement_fee = replacement_fee
        
        self.update_timestamp(updated_by)
    
    def update_notes(self, notes: Optional[str], updated_by: Optional[str] = None):
        """Update the notes."""
        self.notes = notes
        self.update_timestamp(updated_by)
    
    def mark_as_processed(self, processed_by: Optional[str] = None):
        """Mark the return line as processed."""
        if self._is_processed:
            raise ValueError("Return line is already processed")
        
        self._is_processed = True
        self._processed_at = datetime.utcnow()
        self._processed_by = processed_by
        self.update_timestamp(processed_by)
    
    def unprocess(self, updated_by: Optional[str] = None):
        """Unprocess the return line (for corrections)."""
        if not self._is_processed:
            raise ValueError("Return line is not processed")
        
        self._is_processed = False
        self._processed_at = None
        self._processed_by = None
        self.update_timestamp(updated_by)
    
    def get_total_fees(self) -> Decimal:
        """Calculate total fees for this return line."""
        return self.late_fee + self.damage_fee + self.cleaning_fee + self.replacement_fee
    
    def is_fully_returned(self) -> bool:
        """Check if all items have been returned."""
        return self.returned_quantity == self.original_quantity
    
    def is_partially_returned(self) -> bool:
        """Check if items have been partially returned."""
        return 0 < self.returned_quantity < self.original_quantity
    
    def has_outstanding_quantity(self) -> bool:
        """Check if there are outstanding items not yet returned."""
        return self.returned_quantity < self.original_quantity
    
    def get_outstanding_quantity(self) -> int:
        """Get the quantity of items not yet returned."""
        return self.original_quantity - self.returned_quantity
    
    def has_damage(self) -> bool:
        """Check if the returned items have damage."""
        return self.damage_level != DamageLevel.NONE
    
    def requires_repair(self) -> bool:
        """Check if the returned items require repair."""
        return self.damage_level.requires_repair()
    
    def requires_replacement(self) -> bool:
        """Check if the returned items require replacement."""
        return self.damage_level.requires_replacement()
    
    def affects_rentability(self) -> bool:
        """Check if the damage affects future rentability."""
        return self.damage_level.affects_rentability()
    
    def has_fees(self) -> bool:
        """Check if there are any fees associated with this return line."""
        return self.get_total_fees() > 0
    
    def is_condition_acceptable(self) -> bool:
        """Check if the condition is acceptable for rental."""
        return self.condition_grade.is_rentable() and not self.affects_rentability()
    
    def get_return_percentage(self) -> float:
        """Get the percentage of items returned."""
        if self.original_quantity == 0:
            return 0.0
        return (self.returned_quantity / self.original_quantity) * 100
    
    def can_be_modified(self) -> bool:
        """Check if this return line can still be modified."""
        return not self._is_processed