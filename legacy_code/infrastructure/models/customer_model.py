from sqlalchemy import Column, String, Enum, DECIMAL, DateTime, Boolean, Text, Index
from sqlalchemy.orm import relationship
import enum

from ..database import Base
from .base import BaseModel
from ...domain.entities.customer import Customer
from ...domain.value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus


class CustomerModel(BaseModel):
    """SQLAlchemy model for Customer entity."""
    
    __tablename__ = "customers"
    
    customer_code = Column(String(20), unique=True, nullable=False, index=True)
    customer_type = Column(Enum(CustomerType), nullable=False)
    business_name = Column(String(200), nullable=True, index=True)
    first_name = Column(String(50), nullable=True, index=True)
    last_name = Column(String(50), nullable=True, index=True)
    tax_id = Column(String(50), nullable=True, index=True)
    customer_tier = Column(Enum(CustomerTier), nullable=False, default=CustomerTier.BRONZE)
    credit_limit = Column(DECIMAL(15, 2), nullable=False, default=0)
    blacklist_status = Column(Enum(BlacklistStatus), nullable=False, default=BlacklistStatus.CLEAR)
    lifetime_value = Column(DECIMAL(15, 2), nullable=False, default=0)
    last_transaction_date = Column(DateTime, nullable=True)
    
    # Relationships
    contact_methods = relationship("CustomerContactMethodModel", back_populates="customer", lazy="selectin")
    addresses = relationship("CustomerAddressModel", back_populates="customer", lazy="selectin")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_customer_type_tier', 'customer_type', 'customer_tier'),
        Index('idx_customer_blacklist', 'blacklist_status', 'is_active'),
        Index('idx_customer_name', 'first_name', 'last_name'),
        Index('idx_customer_business', 'business_name'),
    )
    
    def to_entity(self) -> Customer:
        """Convert ORM model to domain entity."""
        return Customer(
            id=self.id,
            customer_code=self.customer_code,
            customer_type=self.customer_type,
            business_name=self.business_name,
            first_name=self.first_name,
            last_name=self.last_name,
            tax_id=self.tax_id,
            customer_tier=self.customer_tier,
            credit_limit=self.credit_limit,
            blacklist_status=self.blacklist_status,
            lifetime_value=self.lifetime_value,
            last_transaction_date=self.last_transaction_date,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
    
    @classmethod
    def from_entity(cls, customer: Customer) -> "CustomerModel":
        """Create ORM model from domain entity."""
        return cls(
            id=customer.id,
            customer_code=customer.customer_code,
            customer_type=customer.customer_type,
            business_name=customer.business_name,
            first_name=customer.first_name,
            last_name=customer.last_name,
            tax_id=customer.tax_id,
            customer_tier=customer.customer_tier,
            credit_limit=customer.credit_limit,
            blacklist_status=customer.blacklist_status,
            lifetime_value=customer.lifetime_value,
            last_transaction_date=customer.last_transaction_date,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            created_by=customer.created_by,
            updated_by=customer.updated_by,
            is_active=customer.is_active
        )