from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from .base import BaseEntity
from ..value_objects.rental_return_type import DamageLevel, FeeType
from ..value_objects.item_type import ConditionGrade


class RentalReturnLine(BaseEntity):
    """Rental return line entity representing individual items being returned."""
    
    def __init__(
        self,
        return_id: UUID,
        inventory_unit_id: UUID,
        original_quantity: int,
        returned_quantity: int,
        condition_grade: ConditionGrade = ConditionGrade.A,
        damage_level: DamageLevel = DamageLevel.NONE,
        late_fee: Decimal = Decimal("0.00"),
        damage_fee: Decimal = Decimal("0.00"),
        cleaning_fee: Decimal = Decimal("0.00"),
        replacement_fee: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
        is_active: bool = True
    ):
        """Initialize a rental return line."""
        super().__init__(id, created_at, updated_at, created_by, updated_by, is_active)
        
        self._return_id = return_id
        self._inventory_unit_id = inventory_unit_id
        self._original_quantity = original_quantity
        self._returned_quantity = returned_quantity
        self._condition_grade = condition_grade
        self._damage_level = damage_level
        self._late_fee = late_fee
        self._damage_fee = damage_fee
        self._cleaning_fee = cleaning_fee
        self._replacement_fee = replacement_fee
        self._notes = notes
        
        # Processing status
        self._is_processed = False
        self._processed_at: Optional[datetime] = None
        self._processed_by: Optional[str] = None
        
        # Validate business rules
        self._validate()
    
    def _validate(self):
        """Validate business rules."""
        if not self._return_id:
            raise ValueError("Return ID is required")
        
        if not self._inventory_unit_id:
            raise ValueError("Inventory unit ID is required")
        
        if self._original_quantity <= 0:
            raise ValueError("Original quantity must be positive")
        
        if self._returned_quantity < 0:
            raise ValueError("Returned quantity cannot be negative")
        
        if self._returned_quantity > self._original_quantity:
            raise ValueError("Returned quantity cannot exceed original quantity")
        
        if self._late_fee < 0:
            raise ValueError("Late fee cannot be negative")
        
        if self._damage_fee < 0:
            raise ValueError("Damage fee cannot be negative")
        
        if self._cleaning_fee < 0:
            raise ValueError("Cleaning fee cannot be negative")
        
        if self._replacement_fee < 0:
            raise ValueError("Replacement fee cannot be negative")
    
    @property
    def return_id(self) -> UUID:
        return self._return_id
    
    @property
    def inventory_unit_id(self) -> UUID:
        return self._inventory_unit_id
    
    @property
    def original_quantity(self) -> int:
        return self._original_quantity
    
    @property
    def returned_quantity(self) -> int:
        return self._returned_quantity
    
    @property
    def outstanding_quantity(self) -> int:
        """Calculate outstanding quantity not yet returned."""
        return self._original_quantity - self._returned_quantity
    
    @property
    def condition_grade(self) -> ConditionGrade:
        return self._condition_grade
    
    @property
    def damage_level(self) -> DamageLevel:
        return self._damage_level
    
    @property
    def late_fee(self) -> Decimal:
        return self._late_fee
    
    @property
    def damage_fee(self) -> Decimal:
        return self._damage_fee
    
    @property
    def cleaning_fee(self) -> Decimal:
        return self._cleaning_fee
    
    @property
    def replacement_fee(self) -> Decimal:
        return self._replacement_fee
    
    @property
    def total_fees(self) -> Decimal:
        """Calculate total fees for this line."""
        return self._late_fee + self._damage_fee + self._cleaning_fee + self._replacement_fee
    
    @property
    def notes(self) -> Optional[str]:
        return self._notes
    
    @property
    def is_processed(self) -> bool:
        return self._is_processed
    
    @property
    def processed_at(self) -> Optional[datetime]:
        return self._processed_at
    
    @property
    def processed_by(self) -> Optional[str]:
        return self._processed_by
    
    def is_fully_returned(self) -> bool:
        """Check if all items have been returned."""
        return self._returned_quantity == self._original_quantity
    
    def is_partially_returned(self) -> bool:
        """Check if this is a partial return."""
        return 0 < self._returned_quantity < self._original_quantity
    
    def has_damage(self) -> bool:
        """Check if the item has damage."""
        return self._damage_level != DamageLevel.NONE
    
    def needs_cleaning(self) -> bool:
        """Check if the item needs cleaning (based on condition grade)."""
        return self._condition_grade in [ConditionGrade.C, ConditionGrade.D]
    
    def update_return_quantity(self, new_quantity: int, updated_by: Optional[str] = None) -> None:
        """Update the returned quantity."""
        if self._is_processed:
            raise ValueError("Cannot update processed return line")
        
        if new_quantity < 0:
            raise ValueError("Returned quantity cannot be negative")
        
        if new_quantity > self._original_quantity:
            raise ValueError("Returned quantity cannot exceed original quantity")
        
        self._returned_quantity = new_quantity
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def update_condition(
        self,
        condition_grade: ConditionGrade,
        damage_level: DamageLevel = DamageLevel.NONE,
        notes: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> None:
        """Update item condition after inspection."""
        if self._is_processed:
            raise ValueError("Cannot update processed return line")
        
        self._condition_grade = condition_grade
        self._damage_level = damage_level
        
        if notes:
            self._notes = f"{self._notes or ''}\n{notes}".strip()
        
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def set_late_fee(self, amount: Decimal, updated_by: Optional[str] = None) -> None:
        """Set the late fee for this line."""
        if amount < 0:
            raise ValueError("Late fee cannot be negative")
        
        self._late_fee = amount
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def set_damage_fee(self, amount: Decimal, updated_by: Optional[str] = None) -> None:
        """Set the damage fee for this line."""
        if amount < 0:
            raise ValueError("Damage fee cannot be negative")
        
        self._damage_fee = amount
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def set_cleaning_fee(self, amount: Decimal, updated_by: Optional[str] = None) -> None:
        """Set the cleaning fee for this line."""
        if amount < 0:
            raise ValueError("Cleaning fee cannot be negative")
        
        self._cleaning_fee = amount
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def set_replacement_fee(self, amount: Decimal, updated_by: Optional[str] = None) -> None:
        """Set the replacement fee for this line."""
        if amount < 0:
            raise ValueError("Replacement fee cannot be negative")
        
        self._replacement_fee = amount
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def add_fee(self, fee_type: FeeType, amount: Decimal, updated_by: Optional[str] = None) -> None:
        """Add a fee of specific type."""
        if amount < 0:
            raise ValueError("Fee amount cannot be negative")
        
        if fee_type == FeeType.LATE_FEE:
            self._late_fee += amount
        elif fee_type == FeeType.DAMAGE_FEE:
            self._damage_fee += amount
        elif fee_type == FeeType.CLEANING_FEE:
            self._cleaning_fee += amount
        elif fee_type == FeeType.REPLACEMENT_FEE:
            self._replacement_fee += amount
        else:
            raise ValueError(f"Unsupported fee type: {fee_type}")
        
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def process_line(self, processed_by: str) -> None:
        """Mark the line as processed."""
        if self._is_processed:
            raise ValueError("Line is already processed")
        
        if self._returned_quantity == 0:
            raise ValueError("Cannot process line with zero returned quantity")
        
        self._is_processed = True
        self._processed_at = datetime.utcnow()
        self._processed_by = processed_by
        self.updated_at = datetime.utcnow()
        self.updated_by = processed_by
    
    def undo_processing(self, updated_by: str) -> None:
        """Undo line processing (for corrections)."""
        if not self._is_processed:
            raise ValueError("Line is not processed")
        
        self._is_processed = False
        self._processed_at = None
        self._processed_by = None
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def get_line_summary(self) -> dict:
        """Get a summary of this return line."""
        return {
            "line_id": str(self.id),
            "inventory_unit_id": str(self._inventory_unit_id),
            "original_quantity": self._original_quantity,
            "returned_quantity": self._returned_quantity,
            "outstanding_quantity": self.outstanding_quantity,
            "condition_grade": self._condition_grade.value,
            "damage_level": self._damage_level.value,
            "has_damage": self.has_damage(),
            "needs_cleaning": self.needs_cleaning(),
            "late_fee": float(self._late_fee),
            "damage_fee": float(self._damage_fee),
            "cleaning_fee": float(self._cleaning_fee),
            "replacement_fee": float(self._replacement_fee),
            "total_fees": float(self.total_fees),
            "is_processed": self._is_processed,
            "is_fully_returned": self.is_fully_returned(),
            "is_partially_returned": self.is_partially_returned()
        }