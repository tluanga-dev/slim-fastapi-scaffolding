from sqlalchemy import Column, String, Text, Boolean, Integer, DECIMAL, Index, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import BaseModel, UUID


class ItemModel(BaseModel):
    """SQLAlchemy model for Item entity."""
    
    __tablename__ = "items"
    
    item_id = Column(UUID(), unique=True, nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    item_name = Column(String(255), nullable=False, index=True)
    category_id = Column(UUID(), ForeignKey("categories.id"), nullable=False, index=True)
    brand_id = Column(UUID(), ForeignKey("brands.id"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    is_serialized = Column(Boolean, default=False, nullable=False)
    barcode = Column(String(100), nullable=True, index=True)
    model_number = Column(String(100), nullable=True, index=True)
    weight = Column(DECIMAL(10, 3), nullable=True)
    dimensions = Column(JSON, nullable=True)
    is_rentable = Column(Boolean, default=False, nullable=False, index=True)
    is_saleable = Column(Boolean, default=True, nullable=False, index=True)
    min_rental_days = Column(Integer, default=1, nullable=False)
    rental_period = Column(Integer, default=1, nullable=True)
    max_rental_days = Column(Integer, nullable=True)
    rental_base_price = Column(DECIMAL(10, 2), nullable=True)
    sale_base_price = Column(DECIMAL(10, 2), nullable=True)
    
    # Relationships
    category = relationship("Category", foreign_keys=[category_id])
    brand = relationship("BrandModel", foreign_keys=[brand_id])
    inventory_units = relationship("InventoryUnitModel", back_populates="item")
    stock_levels = relationship("StockLevelModel", back_populates="item")
    
    # Create composite indexes for efficient searching
    __table_args__ = (
        Index('idx_item_name_active', 'item_name', 'is_active'),
        Index('idx_item_sku_active', 'sku', 'is_active'),
        Index('idx_item_barcode_active', 'barcode', 'is_active'),
        Index('idx_item_category_active', 'category_id', 'is_active'),
        Index('idx_item_brand_active', 'brand_id', 'is_active'),
        Index('idx_item_rentable_active', 'is_rentable', 'is_active'),
        Index('idx_item_saleable_active', 'is_saleable', 'is_active'),
    )