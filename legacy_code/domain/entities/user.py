from typing import Optional, Set
from uuid import UUID
from datetime import datetime

from src.domain.entities.base import BaseEntity
from src.domain.entities.role import Role
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_type import UserType


class User(BaseEntity):
    def __init__(
        self,
        email: Email,
        name: str,
        hashed_password: str,
        user_type: UserType = UserType.USER,
        role: Optional[Role] = None,
        role_id: Optional[UUID] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        location_id: Optional[UUID] = None,
        last_login: Optional[datetime] = None,
        is_superuser: bool = False,
        direct_permissions: Optional[Set[str]] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        super().__init__(id, created_at, updated_at, is_active, created_by, updated_by)
        self.email = email
        self.name = name
        self.hashed_password = hashed_password
        self.user_type = user_type
        self.role = role
        self.role_id = role_id
        self.first_name = first_name or name.split()[0] if name else ""
        self.last_name = last_name or " ".join(name.split()[1:]) if name and len(name.split()) > 1 else ""
        self.username = username or email.value
        self.location_id = location_id
        self.last_login = last_login
        self.is_superuser = is_superuser
        self.direct_permissions = direct_permissions or set()
        
        # Auto-set superuser flag based on user type
        if user_type == UserType.SUPERADMIN:
            self.is_superuser = True

    def update_email(self, email: Email, updated_by: Optional[str] = None):
        self.email = email
        self.update_timestamp(updated_by)

    def update_name(self, name: str, updated_by: Optional[str] = None):
        self.name = name
        self.first_name = name.split()[0] if name else ""
        self.last_name = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else ""
        self.update_timestamp(updated_by)

    def update_password(self, hashed_password: str, updated_by: Optional[str] = None):
        self.hashed_password = hashed_password
        self.update_timestamp(updated_by)

    def assign_role(self, role: Role, updated_by: Optional[str] = None):
        self.role = role
        self.update_timestamp(updated_by)

    def update_last_login(self, login_time: datetime, updated_by: Optional[str] = None):
        self.last_login = login_time
        self.update_timestamp(updated_by)

    def make_superuser(self, updated_by: Optional[str] = None):
        self.is_superuser = True
        self.update_timestamp(updated_by)

    def revoke_superuser(self, updated_by: Optional[str] = None):
        self.is_superuser = False
        self.update_timestamp(updated_by)

    def update_user_type(self, user_type: UserType, updated_by: Optional[str] = None):
        """Update the user type."""
        self.user_type = user_type
        # Auto-set superuser flag based on user type
        if user_type == UserType.SUPERADMIN:
            self.is_superuser = True
        elif user_type != UserType.SUPERADMIN and self.is_superuser:
            # Remove superuser if downgrading from SUPERADMIN
            self.is_superuser = False
        self.update_timestamp(updated_by)

    def add_direct_permission(self, permission_code: str, updated_by: Optional[str] = None):
        """Add a direct permission to the user."""
        self.direct_permissions.add(permission_code)
        self.update_timestamp(updated_by)

    def remove_direct_permission(self, permission_code: str, updated_by: Optional[str] = None):
        """Remove a direct permission from the user."""
        self.direct_permissions.discard(permission_code)
        self.update_timestamp(updated_by)

    def has_permission(self, permission_code: str) -> bool:
        """Check if user has a specific permission."""
        # Superadmin has all permissions
        if self.is_superuser or self.user_type == UserType.SUPERADMIN:
            return True
        
        # Check direct permissions
        if permission_code in self.direct_permissions:
            return True
        
        # Check role permissions
        if self.role:
            return self.role.has_permission(permission_code)
        
        return False

    def get_permissions(self) -> Set[str]:
        """Get all permissions for the user."""
        permissions = set()
        
        # Superadmin has all permissions (return empty set as indicator)
        if self.is_superuser or self.user_type == UserType.SUPERADMIN:
            from src.domain.constants.permissions import Permission
            return {perm.value for perm in Permission}
        
        # Add role permissions
        if self.role:
            permissions.update(perm.code for perm in self.role.permissions)
        
        # Add direct permissions
        permissions.update(self.direct_permissions)
        
        return permissions

    def can_manage_user(self, other_user: 'User') -> bool:
        """Check if this user can manage another user."""
        # Check user type hierarchy
        if not self.user_type.can_manage(other_user.user_type):
            return False
        
        # Additional checks can be added here (e.g., same location requirement)
        return True

    def get_effective_permissions(self) -> dict:
        """Get permissions organized by source."""
        return {
            'user_type': self.user_type.value,
            'is_superuser': self.is_superuser,
            'role_permissions': [perm.code for perm in self.role.permissions] if self.role else [],
            'direct_permissions': list(self.direct_permissions),
            'all_permissions': list(self.get_permissions())
        }