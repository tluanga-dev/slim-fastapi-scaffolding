from sqlalchemy import Column, String, Text, Index
from sqlalchemy.orm import relationship

from .base import BaseModel, UUID


class UnitOfMeasurementModel(BaseModel):
    """SQLAlchemy model for UnitOfMeasurement entity."""
    
    __tablename__ = "units_of_measurement"
    
    unit_id = Column(UUID(), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    abbreviation = Column(String(10), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Create composite index for efficient searching
    __table_args__ = (
        Index('idx_unit_name_active', 'name', 'is_active'),
        Index('idx_unit_abbreviation_active', 'abbreviation', 'is_active'),
    )