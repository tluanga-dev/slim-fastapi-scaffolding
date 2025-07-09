from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.domain.value_objects.address_type import AddressType
from app.core.domain.entities.customer_address import CustomerAddress
from sqlalchemy import Enum as SQLEnum
import uuid


class CustomerAddressModel(Base):
    """SQLAlchemy model for CustomerAddress entity."""
    
    __tablename__ = "customer_addresses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    address_type = Column(SQLEnum(AddressType), nullable=False, index=True)
    street = Column(String(200), nullable=False)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(50), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    country = Column(String(50), nullable=False, index=True)
    postal_code = Column(String(20), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_address_customer', 'customer_id', 'is_active'),
        Index('idx_address_type_default', 'customer_id', 'address_type', 'is_default'),
        Index('idx_address_location', 'city', 'state', 'country'),
        Index('idx_address_customer_default', 'customer_id', 'is_default'),
    )
    
    def to_entity(self) -> CustomerAddress:
        """Convert ORM model to domain entity."""
        return CustomerAddress(
            id=self.id,
            customer_id=self.customer_id,
            address_type=self.address_type,
            street=self.street,
            city=self.city,
            state=self.state,
            country=self.country,
            postal_code=self.postal_code,
            address_line2=self.address_line2,
            is_default=self.is_default,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
    
    @classmethod
    def from_entity(cls, address: CustomerAddress) -> "CustomerAddressModel":
        """Create ORM model from domain entity."""
        return cls(
            id=address.id,
            customer_id=address.customer_id,
            address_type=address.address_type,
            street=address.street,
            address_line2=address.address_line2,
            city=address.city,
            state=address.state,
            country=address.country,
            postal_code=address.postal_code,
            is_default=address.is_default,
            created_at=address.created_at,
            updated_at=address.updated_at,
            created_by=address.created_by,
            updated_by=address.updated_by,
            is_active=address.is_active
        )