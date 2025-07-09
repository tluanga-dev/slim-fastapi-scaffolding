from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid

from ...domain.entities.stock_level import StockLevel
from .base import BaseModel, UUID
from ..database import Base


class StockLevelModel(BaseModel):
    """SQLAlchemy model for Stock Level."""
    
    __tablename__ = "stock_levels"
    
    item_id = Column(UUID(), ForeignKey("items.id"), nullable=False)
    location_id = Column(UUID(), ForeignKey("locations.id"), nullable=False)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    quantity_in_transit = Column(Integer, nullable=False, default=0)
    quantity_damaged = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=0)
    reorder_quantity = Column(Integer, nullable=False, default=0)
    maximum_stock = Column(Integer, nullable=True)
    
    # Relationships
    item = relationship("ItemModel", back_populates="stock_levels")
    location = relationship("LocationModel", back_populates="stock_levels")
    
    # Unique constraint for Item + Location combination
    __table_args__ = (
        UniqueConstraint('item_id', 'location_id', name='uk_item_location'),
    )
    
    def to_entity(self) -> StockLevel:
        """Convert SQLAlchemy model to domain entity."""
        return StockLevel(
            id=self.id,
            item_id=self.item_id,
            location_id=self.location_id,
            quantity_on_hand=self.quantity_on_hand,
            quantity_available=self.quantity_available,
            quantity_reserved=self.quantity_reserved,
            quantity_in_transit=self.quantity_in_transit,
            quantity_damaged=self.quantity_damaged,
            reorder_point=self.reorder_point,
            reorder_quantity=self.reorder_quantity,
            maximum_stock=self.maximum_stock,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by
        )
    
    @classmethod
    def from_entity(cls, entity: StockLevel) -> "StockLevelModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id if entity.id else uuid.uuid4(),
            item_id=entity.item_id,
            location_id=entity.location_id,
            quantity_on_hand=entity.quantity_on_hand,
            quantity_available=entity.quantity_available,
            quantity_reserved=entity.quantity_reserved,
            quantity_in_transit=entity.quantity_in_transit,
            quantity_damaged=entity.quantity_damaged,
            reorder_point=entity.reorder_point,
            reorder_quantity=entity.reorder_quantity,
            maximum_stock=entity.maximum_stock,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )