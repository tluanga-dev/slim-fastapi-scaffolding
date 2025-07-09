from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from ...domain.entities.rental_return_line import RentalReturnLine
from ...domain.value_objects.rental_return_type import DamageLevel
from ...domain.value_objects.item_type import ConditionGrade


class RentalReturnLineModel(BaseModel):
    """SQLAlchemy model for rental return lines."""
    
    __tablename__ = "rental_return_lines"
    
    # Core fields
    return_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("rental_returns.id"),
        nullable=False,
        index=True
    )
    inventory_unit_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("inventory_units.id"),
        nullable=False,
        index=True
    )
    original_quantity = Column(Integer, nullable=False)
    returned_quantity = Column(Integer, nullable=False, default=0)
    condition_grade = Column(String(1), nullable=False, default=ConditionGrade.A.value)
    damage_level = Column(String(20), nullable=False, default=DamageLevel.NONE.value)
    
    # Fee fields
    late_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    damage_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    cleaning_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    replacement_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Processing tracking
    is_processed = Column(Boolean, nullable=False, default=False)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String(255), nullable=True)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    
    # Relationships
    # rental_return = relationship(
    #     "RentalReturnModel", 
    #     back_populates="lines",
    #     foreign_keys=[return_id]
    # )
    inventory_unit = relationship(
        "InventoryUnitModel",
        foreign_keys=[inventory_unit_id]
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
            late_fee=entity.late_fee,
            damage_fee=entity.damage_fee,
            cleaning_fee=entity.cleaning_fee,
            replacement_fee=entity.replacement_fee,
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
        self.late_fee = entity.late_fee
        self.damage_fee = entity.damage_fee
        self.cleaning_fee = entity.cleaning_fee
        self.replacement_fee = entity.replacement_fee
        self.is_processed = entity.is_processed
        self.processed_at = entity.processed_at
        self.processed_by = entity.processed_by
        self.notes = entity.notes
        self.updated_at = entity.updated_at
        self.updated_by = entity.updated_by
        self.is_active = entity.is_active