from sqlalchemy import Column, String, ForeignKey, Enum, Date, Numeric, Integer, Text
from sqlalchemy.orm import relationship
import uuid
from decimal import Decimal
from datetime import date

from ...domain.entities.inventory_unit import InventoryUnit
from ...domain.value_objects.item_type import InventoryStatus, ConditionGrade
from .base import BaseModel, UUID
from ..database import Base


class InventoryUnitModel(BaseModel):
    """SQLAlchemy model for Inventory Unit."""
    
    __tablename__ = "inventory_units"
    
    inventory_code = Column(String(50), unique=True, nullable=False, index=True)
    item_id = Column(UUID(), ForeignKey("items.id"), nullable=False)
    location_id = Column(UUID(), ForeignKey("locations.id"), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=True, index=True)
    current_status = Column(Enum(InventoryStatus), nullable=False, default=InventoryStatus.AVAILABLE_SALE)
    condition_grade = Column(Enum(ConditionGrade), nullable=False, default=ConditionGrade.A)
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Numeric(15, 2), nullable=True)
    current_value = Column(Numeric(15, 2), nullable=True)
    last_inspection_date = Column(Date, nullable=True)
    total_rental_days = Column(Integer, nullable=False, default=0)
    rental_count = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    
    # Relationships
    item = relationship("ItemModel", back_populates="inventory_units")
    location = relationship("LocationModel", back_populates="inventory_units")
    
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
            id=entity.id if entity.id else uuid.uuid4(),
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