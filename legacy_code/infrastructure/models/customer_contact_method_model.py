from sqlalchemy import Column, String, Enum, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from ..database import Base
from .base import BaseModel, UUID
from ...domain.entities.customer_contact_method import CustomerContactMethod
from ...domain.value_objects.customer_type import ContactType


class CustomerContactMethodModel(BaseModel):
    """SQLAlchemy model for CustomerContactMethod entity."""
    
    __tablename__ = "customer_contact_methods"
    
    customer_id = Column(UUID(), ForeignKey("customers.id"), nullable=False)
    contact_type = Column(Enum(ContactType), nullable=False)
    contact_value = Column(String(100), nullable=False)
    contact_label = Column(String(50), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    verified_date = Column(DateTime, nullable=True)
    opt_in_marketing = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    customer = relationship("CustomerModel", back_populates="contact_methods")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('customer_id', 'contact_type', 'contact_value', name='uk_customer_contact'),
        Index('idx_contact_customer', 'customer_id', 'is_active'),
        Index('idx_contact_type_primary', 'customer_id', 'contact_type', 'is_primary'),
        Index('idx_contact_verified', 'is_verified', 'contact_type'),
    )
    
    def to_entity(self) -> CustomerContactMethod:
        """Convert ORM model to domain entity."""
        return CustomerContactMethod(
            id=self.id,
            customer_id=self.customer_id,
            contact_type=self.contact_type,
            contact_value=self.contact_value,
            contact_label=self.contact_label,
            is_primary=self.is_primary,
            is_verified=self.is_verified,
            verified_date=self.verified_date,
            opt_in_marketing=self.opt_in_marketing,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
    
    @classmethod
    def from_entity(cls, contact_method: CustomerContactMethod) -> "CustomerContactMethodModel":
        """Create ORM model from domain entity."""
        return cls(
            id=contact_method.id,
            customer_id=contact_method.customer_id,
            contact_type=contact_method.contact_type,
            contact_value=contact_method.contact_value,
            contact_label=contact_method.contact_label,
            is_primary=contact_method.is_primary,
            is_verified=contact_method.is_verified,
            verified_date=contact_method.verified_date,
            opt_in_marketing=contact_method.opt_in_marketing,
            created_at=contact_method.created_at,
            updated_at=contact_method.updated_at,
            created_by=contact_method.created_by,
            updated_by=contact_method.updated_by,
            is_active=contact_method.is_active
        )