from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Date, Numeric, Integer, Text, Index
from sqlalchemy.orm import relationship
import uuid
from decimal import Decimal
from datetime import date

from app.db.base import BaseModel, UUID
from app.core.domain.entities.inventory_unit import InventoryUnit
from app.core.domain.value_objects.item_type import InventoryStatus, ConditionGrade


class InventoryUnitModel(BaseModel):
    """SQLAlchemy model for Inventory Unit."""
    
    __tablename__ = "inventory_units"
    
    # Inventory unit specific fields
    inventory_code = Column(String(50), unique=True, nullable=False, index=True)
    serial_number = Column(String(100), unique=True, nullable=True, index=True)
    current_status = Column(SQLEnum(InventoryStatus), nullable=False, default=InventoryStatus.AVAILABLE_SALE, index=True)
    condition_grade = Column(SQLEnum(ConditionGrade), nullable=False, default=ConditionGrade.A, index=True)
    
    # Financial fields
    purchase_date = Column(Date, nullable=True, index=True)
    purchase_cost = Column(Numeric(15, 2), nullable=True)
    current_value = Column(Numeric(15, 2), nullable=True)
    
    # Usage tracking
    last_inspection_date = Column(Date, nullable=True)
    total_rental_days = Column(Integer, nullable=False, default=0)
    rental_count = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    item_id = Column(UUID(), ForeignKey("items.id"), nullable=False, index=True)
    location_id = Column(UUID(), ForeignKey("locations.id"), nullable=False, index=True)
    
    # Relationships
    item = relationship("ItemModel", back_populates="inventory_units")
    location = relationship("Location", back_populates="inventory_units")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_inventory_code', 'inventory_code'),
        Index('idx_inventory_serial', 'serial_number'),
        Index('idx_inventory_status', 'current_status'),
        Index('idx_inventory_condition', 'condition_grade'),
        Index('idx_inventory_item', 'item_id'),
        Index('idx_inventory_location', 'location_id'),
        Index('idx_inventory_active', 'is_active'),
        Index('idx_inventory_status_active', 'current_status', 'is_active'),
        Index('idx_inventory_location_status', 'location_id', 'current_status'),
        Index('idx_inventory_item_status', 'item_id', 'current_status'),
        Index('idx_inventory_purchase_date', 'purchase_date'),
    )
    
    def to_entity(self) -> InventoryUnit:
        """Convert SQLAlchemy model to domain entity."""
        return InventoryUnit(
            id=self.id,
            inventory_code=self.inventory_code,
            item_id=self.item_id,
            location_id=self.location_id,
            serial_number=self.serial_number,
            current_status=self.current_status,
            condition_grade=self.condition_grade,
            purchase_date=self.purchase_date,
            purchase_cost=Decimal(str(self.purchase_cost)) if self.purchase_cost else None,
            current_value=Decimal(str(self.current_value)) if self.current_value else None,
            last_inspection_date=self.last_inspection_date,
            total_rental_days=self.total_rental_days,
            rental_count=self.rental_count,
            notes=self.notes,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by
        )
    
    @classmethod
    def from_entity(cls, entity: InventoryUnit) -> "InventoryUnitModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id,
            inventory_code=entity.inventory_code,
            item_id=entity.item_id,
            location_id=entity.location_id,
            serial_number=entity.serial_number,
            current_status=entity.current_status,
            condition_grade=entity.condition_grade,
            purchase_date=entity.purchase_date,
            purchase_cost=float(entity.purchase_cost) if entity.purchase_cost else None,
            current_value=float(entity.current_value) if entity.current_value else None,
            last_inspection_date=entity.last_inspection_date,
            total_rental_days=entity.total_rental_days,
            rental_count=entity.rental_count,
            notes=entity.notes,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )
    
    def __repr__(self) -> str:
        """String representation of InventoryUnitModel."""
        return f"<InventoryUnitModel(id={self.id}, code='{self.inventory_code}', status='{self.current_status}', condition='{self.condition_grade}', active={self.is_active})>"