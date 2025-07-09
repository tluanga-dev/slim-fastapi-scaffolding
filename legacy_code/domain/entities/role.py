from typing import List, Optional
from uuid import UUID
from datetime import datetime

from src.domain.entities.base import BaseEntity


class Permission(BaseEntity):
    def __init__(
        self,
        code: str,
        name: str,
        description: str,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        super().__init__(id, created_at, updated_at, is_active, created_by, updated_by)
        self.code = code
        self.name = name
        self.description = description


class Role(BaseEntity):
    def __init__(
        self,
        name: str,
        description: str,
        permissions: List[Permission] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        super().__init__(id, created_at, updated_at, is_active, created_by, updated_by)
        self.name = name
        self.description = description
        self.permissions = permissions or []

    def add_permission(self, permission: Permission, updated_by: Optional[str] = None):
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.update_timestamp(updated_by)

    def remove_permission(self, permission: Permission, updated_by: Optional[str] = None):
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.update_timestamp(updated_by)

    def has_permission(self, permission_code: str) -> bool:
        return any(perm.code == permission_code for perm in self.permissions)
