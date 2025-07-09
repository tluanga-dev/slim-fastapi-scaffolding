from sqlalchemy import Column, String, Text, Index, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base
from app.core.domain.entities.brand import Brand


class BrandModel(Base):
    """SQLAlchemy model for Brand entity."""
    
    __tablename__ = "brands"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Brand specific fields
    brand_name = Column(String(100), nullable=False, unique=True, index=True)
    brand_code = Column(String(20), unique=True, index=True, nullable=True)
    description = Column(Text, nullable=True)
    
    # Base entity fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Relationships
    # items = relationship("ItemModel", back_populates="brand")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_brand_name', 'brand_name'),
        Index('idx_brand_code', 'brand_code'),
        Index('idx_brand_active', 'is_active'),
        Index('idx_brand_name_active', 'brand_name', 'is_active'),
    )
    
    def to_entity(self) -> Brand:
        """Convert ORM model to domain entity."""
        return Brand(
            id=self.id,
            brand_name=self.brand_name,
            brand_code=self.brand_code,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
    
    @classmethod
    def from_entity(cls, brand: Brand) -> "BrandModel":
        """Create ORM model from domain entity."""
        return cls(
            id=brand.id,
            brand_name=brand.brand_name,
            brand_code=brand.brand_code,
            description=brand.description,
            created_at=brand.created_at,
            updated_at=brand.updated_at,
            created_by=brand.created_by,
            updated_by=brand.updated_by,
            is_active=brand.is_active
        )
    
    def __repr__(self) -> str:
        """String representation of BrandModel."""
        return f"<BrandModel(id={self.id}, name='{self.brand_name}', code='{self.brand_code}', active={self.is_active})>"