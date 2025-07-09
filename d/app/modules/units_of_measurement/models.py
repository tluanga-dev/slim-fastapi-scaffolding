from sqlalchemy import Column, String, Text, Index, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class UnitOfMeasurement(Base):
    """SQLAlchemy model for UnitOfMeasurement entity."""
    
    __tablename__ = "units_of_measurement"
    
    # Primary key (following existing pattern)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Business identifier
    unit_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid.uuid4)
    
    # Core fields
    name = Column(String(100), nullable=False, index=True)
    abbreviation = Column(String(10), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Standard fields (following existing pattern)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Create composite indexes for efficient searching
    __table_args__ = (
        Index('idx_unit_name_active', 'name', 'is_active'),
        Index('idx_unit_abbreviation_active', 'abbreviation', 'is_active'),
        Index('idx_unit_id_active', 'unit_id', 'is_active'),
    )