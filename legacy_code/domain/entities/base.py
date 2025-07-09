from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


class BaseEntity:
    def __init__(
        self,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        self.id = id or uuid4()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.is_active = is_active
        self.created_by = created_by
        self.updated_by = updated_by

    def update_timestamp(self, updated_by: Optional[str] = None):
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by

    def soft_delete(self, deleted_by: Optional[str] = None):
        self.is_active = False
        self.update_timestamp(deleted_by)

    def __eq__(self, other):
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)