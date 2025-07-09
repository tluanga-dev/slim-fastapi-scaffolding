from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class BaseEntity:
    """Base entity class with common fields and methods."""
    
    def __init__(
        self,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
        is_active: bool = True,
        **kwargs
    ):
        """Initialize base entity with common fields."""
        self.id = id or uuid4()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.created_by = created_by
        self.updated_by = updated_by
        self.is_active = is_active
    
    def update_timestamp(self, updated_by: Optional[str] = None):
        """Update the timestamp and updated_by fields."""
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def __eq__(self, other):
        """Check equality based on ID."""
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id
    
    def __hash__(self):
        """Hash based on ID."""
        return hash(self.id)
    
    def __repr__(self):
        """String representation."""
        return f"<{self.__class__.__name__}(id={self.id})>"