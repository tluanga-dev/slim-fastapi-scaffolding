from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from ..entities.base import BaseEntity
from ..value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod
)


class TransactionHeader(BaseEntity):
    """Transaction Header entity representing a transaction."""
    
    def __init__(
        self,
        transaction_number: str,
        transaction_type: TransactionType,
        transaction_date: datetime,
        customer_id: UUID,
        location_id: UUID,
        sales_person_id: Optional[UUID] = None,
        status: TransactionStatus = TransactionStatus.DRAFT,
        payment_status: PaymentStatus = PaymentStatus.PENDING,
        subtotal: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        tax_amount: Decimal = Decimal("0.00"),
        total_amount: Decimal = Decimal("0.00"),
        paid_amount: Decimal = Decimal("0.00"),
        deposit_amount: Decimal = Decimal("0.00"),
        reference_transaction_id: Optional[UUID] = None,
        rental_start_date: Optional[date] = None,
        rental_end_date: Optional[date] = None,
        actual_return_date: Optional[date] = None,
        notes: Optional[str] = None,
        payment_method: Optional[PaymentMethod] = None,
        payment_reference: Optional[str] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Initialize Transaction Header entity."""
        super().__init__(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            is_active=is_active,
            created_by=created_by,
            updated_by=updated_by
        )
        self.transaction_number = transaction_number
        self.transaction_type = transaction_type
        self.transaction_date = transaction_date
        self.customer_id = customer_id
        self.location_id = location_id
        self.sales_person_id = sales_person_id
        self.status = status
        self.payment_status = payment_status
        self.subtotal = subtotal
        self.discount_amount = discount_amount
        self.tax_amount = tax_amount
        self.total_amount = total_amount
        self.paid_amount = paid_amount
        self.deposit_amount = deposit_amount
        self.reference_transaction_id = reference_transaction_id
        self.rental_start_date = rental_start_date
        self.rental_end_date = rental_end_date
        self.actual_return_date = actual_return_date
        self.notes = notes
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self._lines: List = []  # Will hold TransactionLine entities
        self._validate()
    
    def _validate(self):
        """Validate transaction header business rules."""
        if not self.transaction_number or not self.transaction_number.strip():
            raise ValueError("Transaction number is required")
        
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        
        if not self.location_id:
            raise ValueError("Location ID is required")
        
        if self.transaction_type not in TransactionType:
            raise ValueError(f"Invalid transaction type: {self.transaction_type}")
        
        if self.status not in TransactionStatus:
            raise ValueError(f"Invalid transaction status: {self.status}")
        
        if self.payment_status not in PaymentStatus:
            raise ValueError(f"Invalid payment status: {self.payment_status}")
        
        # Validate amounts
        if self.subtotal < 0:
            raise ValueError("Subtotal cannot be negative")
        
        if self.discount_amount < 0:
            raise ValueError("Discount amount cannot be negative")
        
        if self.tax_amount < 0:
            raise ValueError("Tax amount cannot be negative")
        
        if self.total_amount < 0:
            raise ValueError("Total amount cannot be negative")
        
        if self.paid_amount < 0:
            raise ValueError("Paid amount cannot be negative")
        
        if self.deposit_amount < 0:
            raise ValueError("Deposit amount cannot be negative")
        
        # Validate rental dates for rental transactions
        if self.transaction_type == TransactionType.RENTAL:
            if not self.rental_start_date:
                raise ValueError("Rental start date is required for rental transactions")
            if not self.rental_end_date:
                raise ValueError("Rental end date is required for rental transactions")
            if self.rental_end_date < self.rental_start_date:
                raise ValueError("Rental end date must be after start date")
    
    def can_transition_to(self, new_status: TransactionStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            TransactionStatus.DRAFT: [
                TransactionStatus.PENDING,
                TransactionStatus.CANCELLED
            ],
            TransactionStatus.PENDING: [
                TransactionStatus.CONFIRMED,
                TransactionStatus.CANCELLED
            ],
            TransactionStatus.CONFIRMED: [
                TransactionStatus.IN_PROGRESS,
                TransactionStatus.CANCELLED
            ],
            TransactionStatus.IN_PROGRESS: [
                TransactionStatus.COMPLETED,
                TransactionStatus.CANCELLED
            ],
            TransactionStatus.COMPLETED: [
                TransactionStatus.REFUNDED
            ],
            TransactionStatus.CANCELLED: [],  # Terminal status
            TransactionStatus.REFUNDED: []    # Terminal status
        }
        
        return new_status in valid_transitions.get(self.status, [])
    
    def update_status(self, new_status: TransactionStatus, updated_by: Optional[str] = None):
        """Update transaction status with validation."""
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        
        self.status = new_status
        self.update_timestamp(updated_by)
    
    def calculate_totals(self):
        """Recalculate transaction totals from lines."""
        if not self._lines:
            self.subtotal = Decimal("0.00")
            self.total_amount = Decimal("0.00")
            return
        
        # Calculate subtotal from product/service lines
        self.subtotal = sum(
            line.line_total for line in self._lines
            if line.line_type in ["PRODUCT", "SERVICE"]
        )
        
        # Calculate discount from discount lines
        self.discount_amount = abs(sum(
            line.line_total for line in self._lines
            if line.line_type == "DISCOUNT"
        ))
        
        # Calculate tax from tax lines
        self.tax_amount = sum(
            line.line_total for line in self._lines
            if line.line_type == "TAX"
        )
        
        # Calculate deposit amount
        self.deposit_amount = sum(
            line.line_total for line in self._lines
            if line.line_type == "DEPOSIT"
        )
        
        # Calculate total
        self.total_amount = (
            self.subtotal - self.discount_amount + self.tax_amount
        )
    
    def apply_payment(
        self,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_reference: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Apply payment to transaction."""
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if self.status not in [TransactionStatus.PENDING, TransactionStatus.CONFIRMED]:
            raise ValueError(f"Cannot apply payment to transaction in {self.status.value} status")
        
        self.paid_amount += amount
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        
        # Update payment status
        if self.paid_amount >= self.total_amount:
            self.payment_status = PaymentStatus.PAID
        elif self.paid_amount > 0:
            self.payment_status = PaymentStatus.PARTIALLY_PAID
        
        self.update_timestamp(updated_by)
    
    def cancel_transaction(self, reason: str, cancelled_by: Optional[str] = None):
        """Cancel the transaction."""
        if self.status == TransactionStatus.COMPLETED:
            raise ValueError("Cannot cancel completed transaction. Use refund instead.")
        
        if self.status == TransactionStatus.CANCELLED:
            raise ValueError("Transaction is already cancelled")
        
        self.status = TransactionStatus.CANCELLED
        self.payment_status = PaymentStatus.CANCELLED
        
        # Add cancellation note
        cancel_note = f"\n[CANCELLED] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {reason}"
        self.notes = (self.notes or "") + cancel_note
        
        self.update_timestamp(cancelled_by)
    
    def process_refund(
        self,
        refund_amount: Decimal,
        reason: str,
        refunded_by: Optional[str] = None
    ):
        """Process refund for completed transaction."""
        if self.status != TransactionStatus.COMPLETED:
            raise ValueError("Can only refund completed transactions")
        
        if refund_amount <= 0:
            raise ValueError("Refund amount must be positive")
        
        if refund_amount > self.paid_amount:
            raise ValueError("Refund amount cannot exceed paid amount")
        
        self.paid_amount -= refund_amount
        self.status = TransactionStatus.REFUNDED
        self.payment_status = PaymentStatus.REFUNDED
        
        # Add refund note
        refund_note = f"\n[REFUNDED] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: ${refund_amount} - {reason}"
        self.notes = (self.notes or "") + refund_note
        
        self.update_timestamp(refunded_by)
    
    def mark_as_overdue(self, updated_by: Optional[str] = None):
        """Mark transaction payment as overdue."""
        if self.payment_status == PaymentStatus.PAID:
            raise ValueError("Cannot mark paid transaction as overdue")
        
        if self.status == TransactionStatus.CANCELLED:
            raise ValueError("Cannot mark cancelled transaction as overdue")
        
        self.payment_status = PaymentStatus.OVERDUE
        self.update_timestamp(updated_by)
    
    def complete_rental_return(
        self,
        actual_return_date: date,
        updated_by: Optional[str] = None
    ):
        """Complete rental return."""
        if self.transaction_type != TransactionType.RENTAL:
            raise ValueError("Can only process return for rental transactions")
        
        if self.status != TransactionStatus.IN_PROGRESS:
            raise ValueError("Can only process return for in-progress rentals")
        
        self.actual_return_date = actual_return_date
        self.status = TransactionStatus.COMPLETED
        self.update_timestamp(updated_by)
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate balance due."""
        return max(self.total_amount - self.paid_amount, Decimal("0.00"))
    
    @property
    def is_paid_in_full(self) -> bool:
        """Check if transaction is paid in full."""
        return self.paid_amount >= self.total_amount
    
    @property
    def is_rental(self) -> bool:
        """Check if this is a rental transaction."""
        return self.transaction_type == TransactionType.RENTAL
    
    @property
    def is_sale(self) -> bool:
        """Check if this is a sale transaction."""
        return self.transaction_type == TransactionType.SALE
    
    @property
    def rental_days(self) -> int:
        """Calculate rental days for rental transactions."""
        if not self.is_rental or not self.rental_start_date or not self.rental_end_date:
            return 0
        return (self.rental_end_date - self.rental_start_date).days + 1
    
    def __str__(self) -> str:
        """String representation of transaction."""
        return f"Transaction({self.transaction_number}: {self.transaction_type.value} - ${self.total_amount})"
    
    def __repr__(self) -> str:
        """Developer representation of transaction."""
        return (
            f"TransactionHeader(id={self.id}, number='{self.transaction_number}', "
            f"type={self.transaction_type.value}, status={self.status.value}, "
            f"total=${self.total_amount})"
        )