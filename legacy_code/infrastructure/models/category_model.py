from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from ..database import Base
from .base import BaseModel, UUID
from ...domain.entities.category import Category


class CategoryModel(BaseModel):
    """SQLAlchemy model for Category entity."""
    
    __tablename__ = "categories"
    
    category_name = Column(String(100), nullable=False)
    parent_category_id = Column(UUID(), ForeignKey("categories.id"), nullable=True)
    category_path = Column(String(500), nullable=False, index=True)
    category_level = Column(Integer, nullable=False, default=1)
    display_order = Column(Integer, nullable=False, default=0)
    is_leaf = Column(Boolean, nullable=False, default=True)
    
    # Self-referential relationship
    parent = relationship("CategoryModel", remote_side="CategoryModel.id", backref="children")
    
    # Items in this category
    items = relationship("ItemModel", back_populates="category")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_parent_category', 'parent_category_id'),
        Index('idx_category_path', 'category_path'),
        Index('idx_active_leaf', 'is_active', 'is_leaf'),
        Index('idx_category_level', 'category_level'),
        # Unique constraint: category name must be unique within parent
        Index('uk_category_name_parent', 'category_name', 'parent_category_id', unique=True),
    )
    
    def to_entity(self) -> Category:
        """Convert ORM model to domain entity."""
        return Category(
            id=self.id,
            category_name=self.category_name,
            parent_category_id=self.parent_category_id,
            category_path=self.category_path,
            category_level=self.category_level,
            display_order=self.display_order,
            is_leaf=self.is_leaf,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
    
    @classmethod
    def from_entity(cls, category: Category) -> "CategoryModel":
        """Create ORM model from domain entity."""
        return cls(
            id=category.id,
            category_name=category.category_name,
            parent_category_id=category.parent_category_id,
            category_path=category.category_path,
            category_level=category.category_level,
            display_order=category.display_order,
            is_leaf=category.is_leaf,
            created_at=category.created_at,
            updated_at=category.updated_at,
            created_by=category.created_by,
            updated_by=category.updated_by,
            is_active=category.is_active
        )