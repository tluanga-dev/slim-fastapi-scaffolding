from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID, uuid4

from .base import BaseEntity
from ..value_objects.rental_return_type import ReturnStatus, ReturnType, DamageLevel, FeeType


class RentalReturn(BaseEntity):
    """Rental return domain entity representing the return of rental items."""
    
    def __init__(
        self,
        rental_transaction_id: UUID,
        return_date: date,
        return_type: ReturnType = ReturnType.FULL,
        return_status: ReturnStatus = ReturnStatus.INITIATED,
        return_location_id: Optional[UUID] = None,
        expected_return_date: Optional[date] = None,
        processed_by: Optional[str] = None,
        notes: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
        is_active: bool = True
    ):
        """Initialize a rental return."""
        super().__init__(id, created_at, updated_at, created_by, updated_by, is_active)
        
        self._rental_transaction_id = rental_transaction_id
        self._return_date = return_date
        self._return_type = return_type
        self._return_status = return_status
        self._return_location_id = return_location_id
        self._expected_return_date = expected_return_date
        self._processed_by = processed_by
        self._notes = notes
        
        # Calculated fields
        self._total_late_fee = Decimal("0.00")
        self._total_damage_fee = Decimal("0.00")
        self._total_deposit_release = Decimal("0.00")
        self._total_refund_amount = Decimal("0.00")
        
        # Related entities (to be populated by repository)
        self._lines: List['RentalReturnLine'] = []
        self._inspection_reports: List['InspectionReport'] = []
        
        # Validate business rules
        self._validate()
    
    def _validate(self):
        """Validate business rules."""
        if not self._rental_transaction_id:
            raise ValueError("Rental transaction ID is required")
        
        if not self._return_date:
            raise ValueError("Return date is required")
        
        if self._expected_return_date and self._return_date < self._expected_return_date:
            pass  # Early return is allowed
    
    @property
    def rental_transaction_id(self) -> UUID:
        return self._rental_transaction_id
    
    @property
    def return_date(self) -> date:
        return self._return_date
    
    @property
    def return_type(self) -> ReturnType:
        return self._return_type
    
    @property
    def return_status(self) -> ReturnStatus:
        return self._return_status
    
    @property
    def return_location_id(self) -> Optional[UUID]:
        return self._return_location_id
    
    @property
    def expected_return_date(self) -> Optional[date]:
        return self._expected_return_date
    
    @property
    def processed_by(self) -> Optional[str]:
        return self._processed_by
    
    @property
    def notes(self) -> Optional[str]:
        return self._notes
    
    @property
    def total_late_fee(self) -> Decimal:
        return self._total_late_fee
    
    @property
    def total_damage_fee(self) -> Decimal:
        return self._total_damage_fee
    
    @property
    def total_deposit_release(self) -> Decimal:
        return self._total_deposit_release
    
    @property
    def total_refund_amount(self) -> Decimal:
        return self._total_refund_amount
    
    @property
    def lines(self) -> List['RentalReturnLine']:
        return self._lines.copy()
    
    @property
    def inspection_reports(self) -> List['InspectionReport']:
        return self._inspection_reports.copy()
    
    def is_late(self) -> bool:
        """Check if the return is late."""
        if not self._expected_return_date:
            return False
        return self._return_date > self._expected_return_date
    
    def days_late(self) -> int:
        """Calculate number of days late."""
        if not self.is_late():
            return 0
        return (self._return_date - self._expected_return_date).days
    
    def is_partial_return(self) -> bool:
        """Check if this is a partial return."""
        return self._return_type == ReturnType.PARTIAL
    
    def is_completed(self) -> bool:
        """Check if the return is completed."""
        return self._return_status == ReturnStatus.COMPLETED
    
    def add_line(self, line: 'RentalReturnLine') -> None:
        """Add a return line."""
        if line.return_id != self.id:
            raise ValueError("Return line must belong to this return")
        
        # Check for duplicate items
        existing_line = next(
            (l for l in self._lines if l.inventory_unit_id == line.inventory_unit_id),
            None
        )
        if existing_line:
            raise ValueError(f"Item {line.inventory_unit_id} is already in this return")
        
        self._lines.append(line)
        self._recalculate_totals()
    
    def remove_line(self, line_id: UUID) -> bool:
        """Remove a return line."""
        initial_count = len(self._lines)
        self._lines = [line for line in self._lines if line.id != line_id]
        
        if len(self._lines) < initial_count:
            self._recalculate_totals()
            return True
        return False
    
    def update_status(self, new_status: ReturnStatus, updated_by: Optional[str] = None) -> None:
        """Update return status."""
        if self._return_status == ReturnStatus.COMPLETED:
            raise ValueError("Cannot change status of completed return")
        
        if self._return_status == ReturnStatus.CANCELLED:
            raise ValueError("Cannot change status of cancelled return")
        
        # Validate status transitions
        valid_transitions = {
            ReturnStatus.INITIATED: [ReturnStatus.IN_INSPECTION, ReturnStatus.CANCELLED],
            ReturnStatus.IN_INSPECTION: [ReturnStatus.PARTIALLY_COMPLETED, ReturnStatus.COMPLETED, ReturnStatus.CANCELLED],
            ReturnStatus.PARTIALLY_COMPLETED: [ReturnStatus.IN_INSPECTION, ReturnStatus.COMPLETED, ReturnStatus.CANCELLED]
        }
        
        if new_status not in valid_transitions.get(self._return_status, []):
            raise ValueError(f"Invalid status transition from {self._return_status} to {new_status}")
        
        self._return_status = new_status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def calculate_late_fees(self, daily_late_fee_rate: Decimal) -> Decimal:
        """Calculate total late fees based on days late and daily rate."""
        if not self.is_late():
            return Decimal("0.00")
        
        days_late = self.days_late()
        total_late_fee = Decimal("0.00")
        
        # Calculate late fees for each line item
        for line in self._lines:
            if line.returned_quantity > 0:
                # Late fee is per item per day
                line_late_fee = line.returned_quantity * daily_late_fee_rate * days_late
                line.set_late_fee(line_late_fee)
                total_late_fee += line_late_fee
        
        self._total_late_fee = total_late_fee
        return total_late_fee
    
    def calculate_damage_fees(self, damage_fee_rates: Dict[DamageLevel, Decimal]) -> Decimal:
        """Calculate total damage fees based on damage assessments."""
        total_damage_fee = Decimal("0.00")
        
        for line in self._lines:
            if line.damage_level and line.damage_level != DamageLevel.NONE:
                damage_rate = damage_fee_rates.get(line.damage_level, Decimal("0.00"))
                # Damage fee typically based on item value or fixed rates
                line_damage_fee = line.returned_quantity * damage_rate
                line.set_damage_fee(line_damage_fee)
                total_damage_fee += line_damage_fee
        
        self._total_damage_fee = total_damage_fee
        return total_damage_fee
    
    def calculate_deposit_release(self, total_deposit: Decimal) -> Decimal:
        """Calculate proportional deposit release for partial returns."""
        if not self._lines:
            return Decimal("0.00")
        
        # Calculate percentage of items returned
        total_original_quantity = sum(line.original_quantity for line in self._lines)
        total_returned_quantity = sum(line.returned_quantity for line in self._lines)
        
        if total_original_quantity == 0:
            return Decimal("0.00")
        
        return_percentage = total_returned_quantity / total_original_quantity
        
        # Deposit release = (percentage returned * total deposit) - fees
        deposit_release = (return_percentage * total_deposit) - self._total_late_fee - self._total_damage_fee
        
        # Ensure non-negative
        self._total_deposit_release = max(deposit_release, Decimal("0.00"))
        return self._total_deposit_release
    
    def finalize_return(self, updated_by: Optional[str] = None) -> None:
        """Finalize the return process."""
        if not self._lines:
            raise ValueError("Cannot finalize return without return lines")
        
        # Validate all lines have been processed
        for line in self._lines:
            if not line.is_processed:
                raise ValueError(f"Line {line.id} has not been processed")
        
        self.update_status(ReturnStatus.COMPLETED, updated_by)
        self._recalculate_totals()
    
    def cancel_return(self, reason: Optional[str] = None, updated_by: Optional[str] = None) -> None:
        """Cancel the return."""
        if self._return_status == ReturnStatus.COMPLETED:
            raise ValueError("Cannot cancel completed return")
        
        self._return_status = ReturnStatus.CANCELLED
        if reason:
            self._notes = f"{self._notes or ''}\nCancelled: {reason}".strip()
        
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def _recalculate_totals(self) -> None:
        """Recalculate all totals based on current lines."""
        self._total_late_fee = sum(line.late_fee for line in self._lines)
        self._total_damage_fee = sum(line.damage_fee for line in self._lines)
        
        # Total refund = deposit release - any additional fees
        self._total_refund_amount = self._total_deposit_release - self._total_late_fee - self._total_damage_fee
        self._total_refund_amount = max(self._total_refund_amount, Decimal("0.00"))
    
    def get_return_summary(self) -> Dict:
        """Get a summary of the return."""
        return {
            "return_id": str(self.id),
            "rental_transaction_id": str(self._rental_transaction_id),
            "return_date": self._return_date.isoformat(),
            "return_type": self._return_type.value,
            "return_status": self._return_status.value,
            "is_late": self.is_late(),
            "days_late": self.days_late(),
            "total_items": len(self._lines),
            "total_returned_quantity": sum(line.returned_quantity for line in self._lines),
            "total_late_fee": float(self._total_late_fee),
            "total_damage_fee": float(self._total_damage_fee),
            "total_deposit_release": float(self._total_deposit_release),
            "total_refund_amount": float(self._total_refund_amount)
        }