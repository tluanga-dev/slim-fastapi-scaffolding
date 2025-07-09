from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
import uuid

from .base import BaseModel


class SupplierModel(BaseModel):
    """SQLAlchemy model for suppliers."""
    
    __tablename__ = "suppliers"

    # Core supplier information
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    supplier_type = Column(String(50), nullable=False)  # MANUFACTURER, DISTRIBUTOR, etc.
    
    # Contact information
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    
    # Business information
    tax_id = Column(String(50), nullable=True)
    payment_terms = Column(String(20), nullable=False, default="NET30")
    credit_limit = Column(Numeric(10, 2), nullable=False, default=0)
    supplier_tier = Column(String(20), nullable=False, default="STANDARD")
    
    # Performance metrics
    total_orders = Column(Integer, nullable=False, default=0)
    total_spend = Column(Numeric(12, 2), nullable=False, default=0)
    average_delivery_days = Column(Integer, nullable=False, default=0)
    quality_rating = Column(Numeric(3, 2), nullable=False, default=0)
    last_order_date = Column(DateTime, nullable=True)

    def to_entity(self):
        """Convert SQLAlchemy model to domain entity."""
        from ...domain.entities.supplier import Supplier
        from ...domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms
        
        return Supplier(
            id=self.id,
            supplier_code=self.supplier_code,
            company_name=self.company_name,
            supplier_type=SupplierType(self.supplier_type),
            contact_person=self.contact_person,
            email=self.email,
            phone=self.phone,
            address=self.address,
            tax_id=self.tax_id,
            payment_terms=PaymentTerms(self.payment_terms),
            credit_limit=Decimal(str(self.credit_limit)),
            supplier_tier=SupplierTier(self.supplier_tier),
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by
        )

    @classmethod
    def from_entity(cls, supplier):
        """Create SQLAlchemy model from domain entity."""
        model = cls(
            id=supplier.id,
            supplier_code=supplier.supplier_code,
            company_name=supplier.company_name,
            supplier_type=supplier.supplier_type.value,
            contact_person=supplier.contact_person,
            email=supplier.email,
            phone=supplier.phone,
            address=supplier.address,
            tax_id=supplier.tax_id,
            payment_terms=supplier.payment_terms.value,
            credit_limit=float(supplier.credit_limit),
            supplier_tier=supplier.supplier_tier.value,
            total_orders=supplier.total_orders,
            total_spend=float(supplier.total_spend),
            average_delivery_days=supplier.average_delivery_days,
            quality_rating=float(supplier.quality_rating),
            last_order_date=supplier.last_order_date,
            is_active=supplier.is_active,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at,
            created_by=supplier.created_by,
            updated_by=supplier.updated_by
        )
        
        # Update performance metrics
        if hasattr(supplier, '_total_orders'):
            model.total_orders = supplier._total_orders
            model.total_spend = float(supplier._total_spend)
            model.average_delivery_days = supplier._average_delivery_days
            model.quality_rating = float(supplier._quality_rating)
            model.last_order_date = supplier._last_order_date
            
        return model

    def update_from_entity(self, supplier):
        """Update model fields from domain entity."""
        self.supplier_code = supplier.supplier_code
        self.company_name = supplier.company_name
        self.supplier_type = supplier.supplier_type.value
        self.contact_person = supplier.contact_person
        self.email = supplier.email
        self.phone = supplier.phone
        self.address = supplier.address
        self.tax_id = supplier.tax_id
        self.payment_terms = supplier.payment_terms.value
        self.credit_limit = float(supplier.credit_limit)
        self.supplier_tier = supplier.supplier_tier.value
        self.total_orders = supplier.total_orders
        self.total_spend = float(supplier.total_spend)
        self.average_delivery_days = supplier.average_delivery_days
        self.quality_rating = float(supplier.quality_rating)
        self.last_order_date = supplier.last_order_date
        self.is_active = supplier.is_active
        self.updated_at = supplier.updated_at
        self.updated_by = supplier.updated_by