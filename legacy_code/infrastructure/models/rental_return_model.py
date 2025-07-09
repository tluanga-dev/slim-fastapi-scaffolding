from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlalchemy import Column, String, Date, DateTime, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from ...domain.entities.rental_return import RentalReturn
from ...domain.value_objects.rental_return_type import ReturnStatus, ReturnType


class RentalReturnModel(BaseModel):
    """SQLAlchemy model for rental returns."""
    
    __tablename__ = "rental_returns"
    
    # Core fields
    rental_transaction_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("transaction_headers.id"),
        nullable=False,
        index=True
    )
    return_date = Column(Date, nullable=False)
    return_type = Column(String(20), nullable=False, default=ReturnType.FULL.value)
    return_status = Column(String(30), nullable=False, default=ReturnStatus.INITIATED.value)
    return_location_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True,
        index=True
    )
    expected_return_date = Column(Date, nullable=True)
    processed_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Calculated financial fields
    total_late_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_damage_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_deposit_release = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_refund_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Relationships
    # rental_transaction = relationship(
    #     "TransactionHeaderModel",
    #     back_populates="rental_returns",
    #     foreign_keys=[rental_transaction_id]
    # )
    return_location = relationship(
        "LocationModel",
        foreign_keys=[return_location_id]
    )
    # lines = relationship(
    #     "RentalReturnLineModel",
    #     back_populates="rental_return", 
    #     cascade="all, delete-orphan"
    # )
    # inspection_reports = relationship(
    #     "InspectionReportModel",
    #     back_populates="rental_return",
    #     cascade="all, delete-orphan"
    # )
    
    @classmethod
    def from_entity(cls, entity: RentalReturn) -> "RentalReturnModel":
        """Create model from domain entity."""
        return cls(
            id=entity.id,
            rental_transaction_id=entity.rental_transaction_id,
            return_date=entity.return_date,
            return_type=entity.return_type.value,
            return_status=entity.return_status.value,
            return_location_id=entity.return_location_id,
            expected_return_date=entity.expected_return_date,
            processed_by=entity.processed_by,
            notes=entity.notes,
            total_late_fee=entity.total_late_fee,
            total_damage_fee=entity.total_damage_fee,
            total_deposit_release=entity.total_deposit_release,
            total_refund_amount=entity.total_refund_amount,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )
    
    def to_entity(self) -> RentalReturn:
        """Convert model to domain entity."""
        entity = RentalReturn(
            id=self.id,
            rental_transaction_id=self.rental_transaction_id,
            return_date=self.return_date,
            return_type=ReturnType(self.return_type),
            return_status=ReturnStatus(self.return_status),
            return_location_id=self.return_location_id,
            expected_return_date=self.expected_return_date,
            processed_by=self.processed_by,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
        
        # Set calculated fields
        entity._total_late_fee = Decimal(str(self.total_late_fee))
        entity._total_damage_fee = Decimal(str(self.total_damage_fee))
        entity._total_deposit_release = Decimal(str(self.total_deposit_release))
        entity._total_refund_amount = Decimal(str(self.total_refund_amount))
        
        return entity
    
    def update_from_entity(self, entity: RentalReturn) -> None:
        """Update model from domain entity."""
        self.rental_transaction_id = entity.rental_transaction_id
        self.return_date = entity.return_date
        self.return_type = entity.return_type.value
        self.return_status = entity.return_status.value
        self.return_location_id = entity.return_location_id
        self.expected_return_date = entity.expected_return_date
        self.processed_by = entity.processed_by
        self.notes = entity.notes
        self.total_late_fee = entity.total_late_fee
        self.total_damage_fee = entity.total_damage_fee
        self.total_deposit_release = entity.total_deposit_release
        self.total_refund_amount = entity.total_refund_amount
        self.updated_at = entity.updated_at
        self.updated_by = entity.updated_by
        self.is_active = entity.is_active