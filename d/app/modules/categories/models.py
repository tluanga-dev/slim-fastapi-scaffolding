from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class UUID(TypeDecorator):
    """Platform-independent UUID type for SQLAlchemy."""
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value
            else:
                return uuid.UUID(value)


class Category(Base):
    """Category model with hierarchical support."""
    __tablename__ = "categories"
    
    # Primary key
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Category fields
    category_name = Column(String(100), nullable=False, index=True)
    parent_category_id = Column(UUID, ForeignKey("categories.id"), nullable=True, index=True)
    category_path = Column(String(500), nullable=False, index=True)
    category_level = Column(Integer, nullable=False, default=1)
    display_order = Column(Integer, nullable=False, default=0)
    is_leaf = Column(Boolean, nullable=False, default=True)
    
    # Base entity fields
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")