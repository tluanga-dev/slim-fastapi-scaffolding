from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, DECIMAL, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms
import uuid


class Supplier(Base):
    """SQLAlchemy model for suppliers table."""
    __tablename__ = "suppliers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    supplier_type = Column(SQLEnum(SupplierType), nullable=False, index=True)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True)
    payment_terms = Column(SQLEnum(PaymentTerms), nullable=False, default=PaymentTerms.NET30)
    credit_limit = Column(DECIMAL(15, 2), nullable=False, default=0)
    supplier_tier = Column(SQLEnum(SupplierTier), nullable=False, default=SupplierTier.STANDARD, index=True)
    
    # Performance metrics
    total_orders = Column(Integer, nullable=False, default=0)
    total_spend = Column(DECIMAL(15, 2), nullable=False, default=0)
    average_delivery_days = Column(Integer, nullable=False, default=0)
    quality_rating = Column(DECIMAL(3, 2), nullable=False, default=0)
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Standard fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)