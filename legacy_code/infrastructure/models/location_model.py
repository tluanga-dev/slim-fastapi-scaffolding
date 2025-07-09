from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from ..database import Base
from .base import BaseModel, UUID
from ...domain.entities.location import Location, LocationType


class LocationModel(BaseModel):
    """SQLAlchemy model for Location entity."""
    
    __tablename__ = "locations"
    
    location_code = Column(String(20), unique=True, nullable=False, index=True)
    location_name = Column(String(100), nullable=False)
    location_type = Column(Enum(LocationType), nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(50), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    country = Column(String(50), nullable=False)
    postal_code = Column(String(20))
    contact_number = Column(String(20))
    email = Column(String(100))
    manager_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    manager = relationship("UserModel", foreign_keys=[manager_user_id])
    inventory_units = relationship("InventoryUnitModel", back_populates="location")
    stock_levels = relationship("StockLevelModel", back_populates="location")
    
    def to_entity(self) -> Location:
        """Convert ORM model to domain entity."""
        return Location(
            id=self.id,
            location_code=self.location_code,
            location_name=self.location_name,
            location_type=self.location_type,
            address=self.address,
            city=self.city,
            state=self.state,
            country=self.country,
            postal_code=self.postal_code,
            contact_number=self.contact_number,
            email=self.email,
            manager_user_id=self.manager_user_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
    
    @classmethod
    def from_entity(cls, location: Location) -> "LocationModel":
        """Create ORM model from domain entity."""
        return cls(
            id=location.id,
            location_code=location.location_code,
            location_name=location.location_name,
            location_type=location.location_type,
            address=location.address,
            city=location.city,
            state=location.state,
            country=location.country,
            postal_code=location.postal_code,
            contact_number=location.contact_number,
            email=location.email,
            manager_user_id=location.manager_user_id,
            created_at=location.created_at,
            updated_at=location.updated_at,
            created_by=location.created_by,
            updated_by=location.updated_by,
            is_active=location.is_active
        )