from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Numeric, Date, Index
from sqlalchemy.orm import relationship

from app.db.base import BaseModel, UUID as SQLAlchemyUUID
from app.core.domain.entities.rental_return import RentalReturn
from app.core.domain.entities.rental_return_line import RentalReturnLine
from app.core.domain.value_objects.rental_return_type import ReturnStatus, ReturnType, DamageLevel
from app.core.domain.value_objects.item_type import ConditionGrade


class RentalReturnModel(BaseModel):
    """SQLAlchemy model for rental returns."""
    
    __tablename__ = "rental_returns"
    
    # Core fields
    rental_transaction_id = Column(
        SQLAlchemyUUID(),
        # ForeignKey("transaction_headers.id"),  # Temporarily disabled until transaction_headers table exists
        nullable=False,
        index=True
    )
    return_date = Column(Date, nullable=False, index=True)
    return_type = Column(String(20), nullable=False, default=ReturnType.FULL.value, index=True)
    return_status = Column(String(30), nullable=False, default=ReturnStatus.INITIATED.value, index=True)
    return_location_id = Column(
        SQLAlchemyUUID(),
        ForeignKey("locations.id"),
        nullable=True,
        index=True
    )
    expected_return_date = Column(Date, nullable=True, index=True)
    processed_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Calculated financial fields
    total_late_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_damage_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_deposit_release = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_refund_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Relationships
    return_location = relationship(
        "Location",
        foreign_keys=[return_location_id]
    )
    lines = relationship(
        "RentalReturnLineModel",
        back_populates="rental_return", 
        cascade="all, delete-orphan"
    )
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_return_transaction', 'rental_transaction_id'),
        Index('idx_return_date', 'return_date'),
        Index('idx_return_status', 'return_status'),
        Index('idx_return_type', 'return_type'),
        Index('idx_return_location', 'return_location_id'),
        Index('idx_return_expected_date', 'expected_return_date'),
        Index('idx_return_status_active', 'return_status', 'is_active'),
        Index('idx_return_date_status', 'return_date', 'return_status'),
    )
    
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
            total_late_fee=float(entity.total_late_fee),
            total_damage_fee=float(entity.total_damage_fee),
            total_deposit_release=float(entity.total_deposit_release),
            total_refund_amount=float(entity.total_refund_amount),
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
        self.total_late_fee = float(entity.total_late_fee)
        self.total_damage_fee = float(entity.total_damage_fee)
        self.total_deposit_release = float(entity.total_deposit_release)
        self.total_refund_amount = float(entity.total_refund_amount)
        self.updated_at = entity.updated_at
        self.updated_by = entity.updated_by
        self.is_active = entity.is_active
    
    def __repr__(self) -> str:
        """String representation of RentalReturnModel."""
        return f"<RentalReturnModel(id={self.id}, transaction_id='{self.rental_transaction_id}', status='{self.return_status}', date='{self.return_date}', active={self.is_active})>"


class RentalReturnLineModel(BaseModel):
    """SQLAlchemy model for rental return lines."""
    
    __tablename__ = "rental_return_lines"
    
    # Core fields
    return_id = Column(
        SQLAlchemyUUID(),
        ForeignKey("rental_returns.id"),
        nullable=False,
        index=True
    )
    inventory_unit_id = Column(
        SQLAlchemyUUID(),
        ForeignKey("inventory_units.id"),
        nullable=False,
        index=True
    )
    original_quantity = Column(Integer, nullable=False)
    returned_quantity = Column(Integer, nullable=False, default=0)
    condition_grade = Column(String(1), nullable=False, default=ConditionGrade.A.value, index=True)
    damage_level = Column(String(20), nullable=False, default=DamageLevel.NONE.value, index=True)
    
    # Fee fields
    late_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    damage_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    cleaning_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    replacement_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Processing tracking
    is_processed = Column(Boolean, nullable=False, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String(255), nullable=True)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    
    # Relationships
    rental_return = relationship(
        "RentalReturnModel", 
        back_populates="lines",
        foreign_keys=[return_id]
    )
    inventory_unit = relationship(
        "InventoryUnitModel",
        foreign_keys=[inventory_unit_id]
    )
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_return_line_return', 'return_id'),
        Index('idx_return_line_inventory_unit', 'inventory_unit_id'),
        Index('idx_return_line_condition', 'condition_grade'),
        Index('idx_return_line_damage', 'damage_level'),
        Index('idx_return_line_processed', 'is_processed'),
        Index('idx_return_line_processed_at', 'processed_at'),
        Index('idx_return_line_return_processed', 'return_id', 'is_processed'),
        Index('idx_return_line_active', 'is_active'),
    )
    
    @classmethod
    def from_entity(cls, entity: RentalReturnLine) -> "RentalReturnLineModel":
        """Create model from domain entity."""
        return cls(
            id=entity.id,
            return_id=entity.return_id,
            inventory_unit_id=entity.inventory_unit_id,
            original_quantity=entity.original_quantity,
            returned_quantity=entity.returned_quantity,
            condition_grade=entity.condition_grade.value,
            damage_level=entity.damage_level.value,
            late_fee=float(entity.late_fee),
            damage_fee=float(entity.damage_fee),
            cleaning_fee=float(entity.cleaning_fee),
            replacement_fee=float(entity.replacement_fee),
            is_processed=entity.is_processed,
            processed_at=entity.processed_at,
            processed_by=entity.processed_by,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )
    
    def to_entity(self) -> RentalReturnLine:
        """Convert model to domain entity."""
        entity = RentalReturnLine(
            id=self.id,
            return_id=self.return_id,
            inventory_unit_id=self.inventory_unit_id,
            original_quantity=self.original_quantity,
            returned_quantity=self.returned_quantity,
            condition_grade=ConditionGrade(self.condition_grade),
            damage_level=DamageLevel(self.damage_level),
            late_fee=Decimal(str(self.late_fee)),
            damage_fee=Decimal(str(self.damage_fee)),
            cleaning_fee=Decimal(str(self.cleaning_fee)),
            replacement_fee=Decimal(str(self.replacement_fee)),
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
        
        # Set processing fields
        entity._is_processed = self.is_processed
        entity._processed_at = self.processed_at
        entity._processed_by = self.processed_by
        
        return entity
    
    def update_from_entity(self, entity: RentalReturnLine) -> None:
        """Update model from domain entity."""
        self.return_id = entity.return_id
        self.inventory_unit_id = entity.inventory_unit_id
        self.original_quantity = entity.original_quantity
        self.returned_quantity = entity.returned_quantity
        self.condition_grade = entity.condition_grade.value
        self.damage_level = entity.damage_level.value
        self.late_fee = float(entity.late_fee)
        self.damage_fee = float(entity.damage_fee)
        self.cleaning_fee = float(entity.cleaning_fee)
        self.replacement_fee = float(entity.replacement_fee)
        self.is_processed = entity.is_processed
        self.processed_at = entity.processed_at
        self.processed_by = entity.processed_by
        self.notes = entity.notes
        self.updated_at = entity.updated_at
        self.updated_by = entity.updated_by
        self.is_active = entity.is_active
    
    def __repr__(self) -> str:
        """String representation of RentalReturnLineModel."""
        return f"<RentalReturnLineModel(id={self.id}, return_id='{self.return_id}', inventory_unit_id='{self.inventory_unit_id}', quantity={self.returned_quantity}/{self.original_quantity}, processed={self.is_processed}, active={self.is_active})>"