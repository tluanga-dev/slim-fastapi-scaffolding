from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from .base import BaseEntity
from ..value_objects.rental_return_type import ReturnStatus, ReturnType


class RentalReturn(BaseEntity):
    """Rental return domain entity representing a return transaction."""
    
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
        **kwargs
    ):
        """Initialize a RentalReturn entity."""
        super().__init__(**kwargs)
        self.rental_transaction_id = rental_transaction_id
        self.return_date = return_date
        self.return_type = return_type
        self.return_status = return_status
        self.return_location_id = return_location_id
        self.expected_return_date = expected_return_date
        self.processed_by = processed_by
        self.notes = notes
        
        # Calculated financial fields (private attributes)
        self._total_late_fee = Decimal('0.00')
        self._total_damage_fee = Decimal('0.00')
        self._total_deposit_release = Decimal('0.00')
        self._total_refund_amount = Decimal('0.00')
        
        self._validate()
    
    def _validate(self):
        """Validate rental return business rules."""
        if not self.rental_transaction_id:
            raise ValueError("Rental transaction ID cannot be empty")
        
        if not self.return_date:
            raise ValueError("Return date cannot be empty")
        
        if not isinstance(self.return_type, ReturnType):
            raise ValueError(f"Invalid return type: {self.return_type}")
        
        if not isinstance(self.return_status, ReturnStatus):
            raise ValueError(f"Invalid return status: {self.return_status}")
        
        if self.return_date > date.today():
            raise ValueError("Return date cannot be in the future")
        
        if self.expected_return_date and self.expected_return_date > self.return_date:
            # Only validate if both dates are provided
            pass  # This is actually valid - expected date can be after actual return date
    
    @property
    def total_late_fee(self) -> Decimal:
        """Get total late fees."""
        return self._total_late_fee
    
    @property
    def total_damage_fee(self) -> Decimal:
        """Get total damage fees."""
        return self._total_damage_fee
    
    @property
    def total_deposit_release(self) -> Decimal:
        """Get total deposit release amount."""
        return self._total_deposit_release
    
    @property
    def total_refund_amount(self) -> Decimal:
        """Get total refund amount."""
        return self._total_refund_amount
    
    def update_return_status(self, new_status: ReturnStatus, updated_by: Optional[str] = None):
        """Update the return status."""
        if not isinstance(new_status, ReturnStatus):
            raise ValueError(f"Invalid return status: {new_status}")
        
        # Business rules for status transitions
        if self.return_status == ReturnStatus.COMPLETED and new_status != ReturnStatus.COMPLETED:
            raise ValueError("Cannot change status from COMPLETED")
        
        if self.return_status == ReturnStatus.CANCELLED and new_status != ReturnStatus.CANCELLED:
            raise ValueError("Cannot change status from CANCELLED")
        
        old_status = self.return_status
        self.return_status = new_status
        self.update_timestamp(updated_by)
        
        # Auto-set processed_by when completing
        if new_status == ReturnStatus.COMPLETED and not self.processed_by:
            self.processed_by = updated_by
    
    def update_return_location(self, location_id: UUID, updated_by: Optional[str] = None):
        """Update the return location."""
        if not location_id:
            raise ValueError("Location ID cannot be empty")
        
        if not self.return_status.can_be_modified():
            raise ValueError(f"Cannot modify return location when status is {self.return_status}")
        
        self.return_location_id = location_id
        self.update_timestamp(updated_by)
    
    def update_expected_return_date(self, expected_date: date, updated_by: Optional[str] = None):
        """Update the expected return date."""
        if expected_date > date.today():
            # Allow future expected dates
            pass
        
        self.expected_return_date = expected_date
        self.update_timestamp(updated_by)
    
    def update_notes(self, notes: Optional[str], updated_by: Optional[str] = None):
        """Update the notes."""
        self.notes = notes
        self.update_timestamp(updated_by)
    
    def calculate_totals(self, return_lines: List['RentalReturnLine']):
        """Calculate total fees and amounts from return lines."""
        self._total_late_fee = sum(line.late_fee for line in return_lines)
        self._total_damage_fee = sum(
            line.damage_fee + line.cleaning_fee + line.replacement_fee 
            for line in return_lines
        )
        
        # These would typically be calculated based on business logic
        # For now, we'll set them to zero and they can be updated separately
        # self._total_deposit_release = Decimal('0.00')
        # self._total_refund_amount = Decimal('0.00')
    
    def update_deposit_release(self, amount: Decimal, updated_by: Optional[str] = None):
        """Update the deposit release amount."""
        if amount < 0:
            raise ValueError("Deposit release amount cannot be negative")
        
        self._total_deposit_release = amount
        self.update_timestamp(updated_by)
    
    def update_refund_amount(self, amount: Decimal, updated_by: Optional[str] = None):
        """Update the refund amount."""
        if amount < 0:
            raise ValueError("Refund amount cannot be negative")
        
        self._total_refund_amount = amount
        self.update_timestamp(updated_by)
    
    def mark_as_completed(self, processed_by: Optional[str] = None):
        """Mark the return as completed."""
        if self.return_status == ReturnStatus.CANCELLED:
            raise ValueError("Cannot complete a cancelled return")
        
        self.return_status = ReturnStatus.COMPLETED
        self.processed_by = processed_by
        self.update_timestamp(processed_by)
    
    def mark_as_cancelled(self, updated_by: Optional[str] = None):
        """Mark the return as cancelled."""
        if self.return_status == ReturnStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed return")
        
        self.return_status = ReturnStatus.CANCELLED
        self.update_timestamp(updated_by)
    
    def initiate_inspection(self, updated_by: Optional[str] = None):
        """Initiate the inspection process."""
        if not self.return_status.can_process_inspection():
            raise ValueError(f"Cannot initiate inspection when status is {self.return_status}")
        
        self.return_status = ReturnStatus.IN_INSPECTION
        self.update_timestamp(updated_by)
    
    def mark_as_partially_completed(self, updated_by: Optional[str] = None):
        """Mark the return as partially completed."""
        if self.return_status not in [ReturnStatus.IN_INSPECTION, ReturnStatus.INITIATED]:
            raise ValueError(f"Cannot mark as partially completed when status is {self.return_status}")
        
        self.return_status = ReturnStatus.PARTIALLY_COMPLETED
        self.update_timestamp(updated_by)
    
    def get_total_fees(self) -> Decimal:
        """Get total of all fees."""
        return self._total_late_fee + self._total_damage_fee
    
    def get_net_amount(self) -> Decimal:
        """Get net amount (refund minus fees)."""
        return self._total_refund_amount - self.get_total_fees()
    
    def is_overdue(self) -> bool:
        """Check if the return is overdue based on expected return date."""
        if not self.expected_return_date:
            return False
        return self.return_date > self.expected_return_date
    
    def get_days_late(self) -> int:
        """Get number of days the return is late."""
        if not self.is_overdue():
            return 0
        return (self.return_date - self.expected_return_date).days
    
    def is_active(self) -> bool:
        """Check if the return is in an active state."""
        return self.return_status.is_active()
    
    def is_completed(self) -> bool:
        """Check if the return is completed."""
        return self.return_status.is_completed()
    
    def is_cancelled(self) -> bool:
        """Check if the return is cancelled."""
        return self.return_status.is_cancelled()
    
    def can_be_modified(self) -> bool:
        """Check if the return can still be modified."""
        return self.return_status.can_be_modified()
    
    def is_full_return(self) -> bool:
        """Check if this is a full return."""
        return self.return_type.is_full_return()
    
    def is_partial_return(self) -> bool:
        """Check if this is a partial return."""
        return self.return_type.is_partial_return()
    
    def has_fees(self) -> bool:
        """Check if there are any fees associated with this return."""
        return self.get_total_fees() > 0
    
    def requires_refund(self) -> bool:
        """Check if this return requires a refund."""
        return self._total_refund_amount > 0
    
    def has_deposit_release(self) -> bool:
        """Check if there is a deposit to be released."""
        return self._total_deposit_release > 0