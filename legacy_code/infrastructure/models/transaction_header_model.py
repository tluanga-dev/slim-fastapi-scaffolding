from sqlalchemy import Column, String, Enum, ForeignKey, DateTime, Date, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base
from .base import BaseModel, UUID
from ...domain.entities.transaction_header import TransactionHeader
from ...domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod
)


class TransactionHeaderModel(BaseModel):
    """SQLAlchemy model for TransactionHeader entity."""
    
    __tablename__ = "transaction_headers"
    
    transaction_number = Column(String(50), unique=True, nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    customer_id = Column(UUID(), ForeignKey("customers.id"), nullable=False, index=True)
    location_id = Column(UUID(), ForeignKey("locations.id"), nullable=False, index=True)
    sales_person_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.DRAFT, index=True)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    
    # Financial fields - using Numeric for precision
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    deposit_amount = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Reference to another transaction (for returns, refunds, etc.)
    reference_transaction_id = Column(UUID(), ForeignKey("transaction_headers.id"), nullable=True)
    
    # Rental specific fields
    rental_start_date = Column(Date, nullable=True, index=True)
    rental_end_date = Column(Date, nullable=True, index=True)
    actual_return_date = Column(Date, nullable=True)
    
    # Payment information
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    
    # Relationships
    customer = relationship("CustomerModel", foreign_keys=[customer_id])
    location = relationship("LocationModel", foreign_keys=[location_id])
    sales_person = relationship("UserModel", foreign_keys=[sales_person_id])
    reference_transaction = relationship("TransactionHeaderModel", remote_side="TransactionHeaderModel.id")
    lines = relationship("TransactionLineModel", back_populates="transaction", lazy="select")
    
    def to_entity(self) -> TransactionHeader:
        """Convert ORM model to domain entity."""
        transaction = TransactionHeader(
            id=self.id,
            transaction_number=self.transaction_number,
            transaction_type=self.transaction_type,
            transaction_date=self.transaction_date,
            customer_id=self.customer_id,
            location_id=self.location_id,
            sales_person_id=self.sales_person_id,
            status=self.status,
            payment_status=self.payment_status,
            subtotal=self.subtotal,
            discount_amount=self.discount_amount,
            tax_amount=self.tax_amount,
            total_amount=self.total_amount,
            paid_amount=self.paid_amount,
            deposit_amount=self.deposit_amount,
            reference_transaction_id=self.reference_transaction_id,
            rental_start_date=self.rental_start_date,
            rental_end_date=self.rental_end_date,
            actual_return_date=self.actual_return_date,
            notes=self.notes,
            payment_method=self.payment_method,
            payment_reference=self.payment_reference,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
        
        # Add lines if loaded - check if lines attribute was loaded without triggering lazy load
        # Use hasattr to check if the lines attribute has been loaded into the instance dict
        if hasattr(self, '_sa_instance_state') and 'lines' in self.__dict__:
            transaction._lines = [line.to_entity() for line in self.lines]
        
        return transaction
    
    @classmethod
    def from_entity(cls, transaction: TransactionHeader) -> "TransactionHeaderModel":
        """Create ORM model from domain entity."""
        return cls(
            id=transaction.id,
            transaction_number=transaction.transaction_number,
            transaction_type=transaction.transaction_type,
            transaction_date=transaction.transaction_date,
            customer_id=transaction.customer_id,
            location_id=transaction.location_id,
            sales_person_id=transaction.sales_person_id,
            status=transaction.status,
            payment_status=transaction.payment_status,
            subtotal=transaction.subtotal,
            discount_amount=transaction.discount_amount,
            tax_amount=transaction.tax_amount,
            total_amount=transaction.total_amount,
            paid_amount=transaction.paid_amount,
            deposit_amount=transaction.deposit_amount,
            reference_transaction_id=transaction.reference_transaction_id,
            rental_start_date=transaction.rental_start_date,
            rental_end_date=transaction.rental_end_date,
            actual_return_date=transaction.actual_return_date,
            notes=transaction.notes,
            payment_method=transaction.payment_method,
            payment_reference=transaction.payment_reference,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
            created_by=transaction.created_by,
            updated_by=transaction.updated_by,
            is_active=transaction.is_active
        )