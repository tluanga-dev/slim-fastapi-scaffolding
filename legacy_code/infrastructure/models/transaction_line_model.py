from sqlalchemy import Column, String, Integer, Enum, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import relationship

from ..database import Base
from .base import BaseModel, UUID
from ...domain.entities.transaction_line import TransactionLine
from ...domain.value_objects.transaction_type import LineItemType, RentalPeriodUnit


class TransactionLineModel(BaseModel):
    """SQLAlchemy model for TransactionLine entity."""
    
    __tablename__ = "transaction_lines"
    
    transaction_id = Column(UUID(), ForeignKey("transaction_headers.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    line_type = Column(Enum(LineItemType), nullable=False, index=True)
    item_id = Column(UUID(), ForeignKey("items.id"), nullable=True, index=True)
    inventory_unit_id = Column(UUID(), ForeignKey("inventory_units.id"), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    
    # Quantity and pricing fields - using Numeric for precision
    quantity = Column(Numeric(10, 3), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False, default=0)
    discount_percentage = Column(Numeric(5, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    line_total = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Rental specific fields
    rental_period_value = Column(Integer, nullable=True)
    rental_period_unit = Column(Enum(RentalPeriodUnit), nullable=True)
    rental_start_date = Column(Date, nullable=True)
    rental_end_date = Column(Date, nullable=True)
    
    # Return tracking
    returned_quantity = Column(Numeric(10, 3), nullable=False, default=0)
    return_date = Column(Date, nullable=True)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    
    # Relationships
    transaction = relationship("TransactionHeaderModel", back_populates="lines")
    item = relationship("ItemModel", foreign_keys=[item_id])
    inventory_unit = relationship("InventoryUnitModel", foreign_keys=[inventory_unit_id])
    
    def to_entity(self) -> TransactionLine:
        """Convert ORM model to domain entity."""
        return TransactionLine(
            id=self.id,
            transaction_id=self.transaction_id,
            line_number=self.line_number,
            line_type=self.line_type,
            item_id=self.item_id,
            inventory_unit_id=self.inventory_unit_id,
            description=self.description,
            quantity=self.quantity,
            unit_price=self.unit_price,
            discount_percentage=self.discount_percentage,
            discount_amount=self.discount_amount,
            tax_rate=self.tax_rate,
            tax_amount=self.tax_amount,
            line_total=self.line_total,
            rental_period_value=self.rental_period_value,
            rental_period_unit=self.rental_period_unit,
            rental_start_date=self.rental_start_date,
            rental_end_date=self.rental_end_date,
            returned_quantity=self.returned_quantity,
            return_date=self.return_date,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
    
    @classmethod
    def from_entity(cls, line: TransactionLine) -> "TransactionLineModel":
        """Create ORM model from domain entity."""
        return cls(
            id=line.id,
            transaction_id=line.transaction_id,
            line_number=line.line_number,
            line_type=line.line_type,
            item_id=line.item_id,
            inventory_unit_id=line.inventory_unit_id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percentage=line.discount_percentage,
            discount_amount=line.discount_amount,
            tax_rate=line.tax_rate,
            tax_amount=line.tax_amount,
            line_total=line.line_total,
            rental_period_value=line.rental_period_value,
            rental_period_unit=line.rental_period_unit,
            rental_start_date=line.rental_start_date,
            rental_end_date=line.rental_end_date,
            returned_quantity=line.returned_quantity,
            return_date=line.return_date,
            notes=line.notes,
            created_at=line.created_at,
            updated_at=line.updated_at,
            created_by=line.created_by,
            updated_by=line.updated_by,
            is_active=line.is_active
        )