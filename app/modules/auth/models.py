from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Table, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
import bcrypt

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from app.modules.master_data.locations.models import Location


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    LOCKED = "LOCKED"


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"
    CUSTOMER = "CUSTOMER"
    READONLY = "READONLY"


# Association table for user-role many-to-many relationship
user_roles_table = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', UUIDType(), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUIDType(), ForeignKey('roles.id'), primary_key=True),
    Index('idx_user_roles_user', 'user_id'),
    Index('idx_user_roles_role', 'role_id'),
)

# Association table for role-permission many-to-many relationship
role_permissions_table = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', UUIDType(), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUIDType(), ForeignKey('permissions.id'), primary_key=True),
    Index('idx_role_permissions_role', 'role_id'),
    Index('idx_role_permissions_permission', 'permission_id'),
)


class User(BaseModel):
    """
    User model for authentication and authorization.
    
    Attributes:
        username: Unique username
        email: User email address
        password_hash: Hashed password
        first_name: User's first name
        last_name: User's last name
        phone_number: User's phone number
        status: User status (ACTIVE, INACTIVE, SUSPENDED, LOCKED)
        last_login: Last login timestamp
        failed_login_attempts: Number of failed login attempts
        password_reset_token: Token for password reset
        password_reset_expires: Password reset token expiration
        roles: User roles
        managed_locations: Locations managed by this user
    """
    
    __tablename__ = "users"
    
    username = Column(String(50), nullable=False, unique=True, index=True, comment="Unique username")
    email = Column(String(255), nullable=False, unique=True, index=True, comment="User email address")
    password_hash = Column(String(255), nullable=False, comment="Hashed password")
    first_name = Column(String(100), nullable=False, comment="User's first name")
    last_name = Column(String(100), nullable=False, comment="User's last name")
    phone_number = Column(String(20), nullable=True, comment="User's phone number")
    status = Column(String(20), nullable=False, default=UserStatus.ACTIVE.value, comment="User status")
    last_login = Column(DateTime, nullable=True, comment="Last login timestamp")
    failed_login_attempts = Column(String(10), nullable=False, default="0", comment="Failed login attempts")
    password_reset_token = Column(String(255), nullable=True, comment="Password reset token")
    password_reset_expires = Column(DateTime, nullable=True, comment="Password reset token expiration")
    
    # Relationships
    roles = relationship("Role", secondary=user_roles_table, back_populates="users", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_status', 'status'),
        Index('idx_user_last_login', 'last_login'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: Optional[str] = None,
        status: UserStatus = UserStatus.ACTIVE,
        **kwargs
    ):
        """
        Initialize a User.
        
        Args:
            username: Unique username
            email: User email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            phone_number: User's phone number
            status: User status
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        self.password_hash = self._hash_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.status = status.value if isinstance(status, UserStatus) else status
        self.failed_login_attempts = "0"
        self._validate()
    
    def _validate(self):
        """Validate user business rules."""
        # Username validation
        if not self.username or not self.username.strip():
            raise ValueError("Username cannot be empty")
        
        if len(self.username) > 50:
            raise ValueError("Username cannot exceed 50 characters")
        
        # Email validation
        if not self.email or not self.email.strip():
            raise ValueError("Email cannot be empty")
        
        if len(self.email) > 255:
            raise ValueError("Email cannot exceed 255 characters")
        
        if "@" not in self.email or "." not in self.email.split("@")[-1]:
            raise ValueError("Invalid email format")
        
        # Name validation
        if not self.first_name or not self.first_name.strip():
            raise ValueError("First name cannot be empty")
        
        if len(self.first_name) > 100:
            raise ValueError("First name cannot exceed 100 characters")
        
        if not self.last_name or not self.last_name.strip():
            raise ValueError("Last name cannot be empty")
        
        if len(self.last_name) > 100:
            raise ValueError("Last name cannot exceed 100 characters")
        
        # Phone number validation
        if self.phone_number:
            if len(self.phone_number) > 20:
                raise ValueError("Phone number cannot exceed 20 characters")
        
        # Status validation
        if self.status not in [status.value for status in UserStatus]:
            raise ValueError(f"Invalid user status: {self.status}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        if not password:
            return False
        
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except:
            return False
    
    def set_password(self, password: str, updated_by: Optional[str] = None):
        """Set new password."""
        self.password_hash = self._hash_password(password)
        self.password_reset_token = None
        self.password_reset_expires = None
        self.failed_login_attempts = "0"
        self.updated_by = updated_by
    
    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update user profile."""
        if first_name is not None:
            if not first_name or not first_name.strip():
                raise ValueError("First name cannot be empty")
            if len(first_name) > 100:
                raise ValueError("First name cannot exceed 100 characters")
            self.first_name = first_name.strip()
        
        if last_name is not None:
            if not last_name or not last_name.strip():
                raise ValueError("Last name cannot be empty")
            if len(last_name) > 100:
                raise ValueError("Last name cannot exceed 100 characters")
            self.last_name = last_name.strip()
        
        if phone_number is not None:
            if phone_number and len(phone_number) > 20:
                raise ValueError("Phone number cannot exceed 20 characters")
            self.phone_number = phone_number.strip() if phone_number else None
        
        self.updated_by = updated_by
    
    def record_login(self):
        """Record successful login."""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = "0"
    
    def record_failed_login(self):
        """Record failed login attempt."""
        current_attempts = int(self.failed_login_attempts)
        self.failed_login_attempts = str(current_attempts + 1)
        
        # Lock account after 5 failed attempts
        if current_attempts >= 4:
            self.status = UserStatus.LOCKED.value
    
    def unlock_account(self, updated_by: Optional[str] = None):
        """Unlock user account."""
        self.status = UserStatus.ACTIVE.value
        self.failed_login_attempts = "0"
        self.updated_by = updated_by
    
    def activate(self, updated_by: Optional[str] = None):
        """Activate user account."""
        self.status = UserStatus.ACTIVE.value
        self.updated_by = updated_by
    
    def deactivate(self, updated_by: Optional[str] = None):
        """Deactivate user account."""
        self.status = UserStatus.INACTIVE.value
        self.updated_by = updated_by
    
    def suspend(self, updated_by: Optional[str] = None):
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED.value
        self.updated_by = updated_by
    
    def set_password_reset_token(self, token: str, expires: datetime):
        """Set password reset token."""
        self.password_reset_token = token
        self.password_reset_expires = expires
    
    def clear_password_reset_token(self):
        """Clear password reset token."""
        self.password_reset_token = None
        self.password_reset_expires = None
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False
    
    def get_permissions(self) -> List[str]:
        """Get all permissions for the user."""
        permissions = set()
        for role in self.roles:
            permissions.update(role.get_permissions())
        return list(permissions)
    
    def is_active_user(self) -> bool:
        """Check if user is active and not locked."""
        return self.status == UserStatus.ACTIVE.value and self.is_active
    
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        return self.status == UserStatus.LOCKED.value
    
    def is_suspended(self) -> bool:
        """Check if user account is suspended."""
        return self.status == UserStatus.SUSPENDED.value
    
    def can_login(self) -> bool:
        """Check if user can login."""
        return self.is_active_user() and not self.is_locked() and not self.is_suspended()
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get user's display name."""
        return f"{self.full_name} ({self.username})"
    
    @property
    def role_names(self) -> List[str]:
        """Get list of role names."""
        return [role.name for role in self.roles]
    
    def __str__(self) -> str:
        """String representation of user."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of user."""
        return (
            f"User(id={self.id}, username='{self.username}', "
            f"email='{self.email}', status='{self.status}', active={self.is_active})"
        )


class Role(BaseModel):
    """
    Role model for role-based access control.
    
    Attributes:
        name: Role name
        description: Role description
        is_system_role: Whether this is a system role (cannot be deleted)
        permissions: Role permissions
        users: Users with this role
    """
    
    __tablename__ = "roles"
    
    name = Column(String(50), nullable=False, unique=True, index=True, comment="Role name")
    description = Column(Text, nullable=True, comment="Role description")
    is_system_role = Column(Boolean, nullable=False, default=False, comment="System role flag")
    
    # Relationships
    permissions = relationship("Permission", secondary=role_permissions_table, back_populates="roles", lazy="select")
    users = relationship("User", secondary=user_roles_table, back_populates="roles", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_role_name', 'name'),
        Index('idx_role_system', 'is_system_role'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        is_system_role: bool = False,
        **kwargs
    ):
        """
        Initialize a Role.
        
        Args:
            name: Role name
            description: Role description
            is_system_role: Whether this is a system role
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.name = name
        self.description = description
        self.is_system_role = is_system_role
        self._validate()
    
    def _validate(self):
        """Validate role business rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Role name cannot be empty")
        
        if len(self.name) > 50:
            raise ValueError("Role name cannot exceed 50 characters")
        
        if self.description and len(self.description) > 1000:
            raise ValueError("Role description cannot exceed 1000 characters")
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission."""
        return any(perm.name == permission_name for perm in self.permissions)
    
    def get_permissions(self) -> List[str]:
        """Get all permission names for this role."""
        return [perm.name for perm in self.permissions]
    
    def can_delete(self) -> bool:
        """Check if role can be deleted."""
        return not self.is_system_role and self.is_active and len(self.users) == 0
    
    @property
    def user_count(self) -> int:
        """Get number of users with this role."""
        return len(self.users) if self.users else 0
    
    @property
    def permission_count(self) -> int:
        """Get number of permissions for this role."""
        return len(self.permissions) if self.permissions else 0
    
    def __str__(self) -> str:
        """String representation of role."""
        return self.name
    
    def __repr__(self) -> str:
        """Developer representation of role."""
        return (
            f"Role(id={self.id}, name='{self.name}', "
            f"system={self.is_system_role}, active={self.is_active})"
        )


class Permission(BaseModel):
    """
    Permission model for fine-grained access control.
    
    Attributes:
        name: Permission name
        description: Permission description
        resource: Resource this permission applies to
        action: Action this permission allows
        is_system_permission: Whether this is a system permission
        roles: Roles that have this permission
    """
    
    __tablename__ = "permissions"
    
    name = Column(String(100), nullable=False, unique=True, index=True, comment="Permission name")
    description = Column(Text, nullable=True, comment="Permission description")
    resource = Column(String(50), nullable=False, comment="Resource name")
    action = Column(String(50), nullable=False, comment="Action name")
    is_system_permission = Column(Boolean, nullable=False, default=False, comment="System permission flag")
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions_table, back_populates="permissions", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_permission_name', 'name'),
        Index('idx_permission_resource', 'resource'),
        Index('idx_permission_action', 'action'),
        Index('idx_permission_system', 'is_system_permission'),
# Removed is_active index - column is inherited from BaseModel
        Index('idx_permission_resource_action', 'resource', 'action'),
    )
    
    def __init__(
        self,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None,
        is_system_permission: bool = False,
        **kwargs
    ):
        """
        Initialize a Permission.
        
        Args:
            name: Permission name
            resource: Resource name
            action: Action name
            description: Permission description
            is_system_permission: Whether this is a system permission
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.name = name
        self.resource = resource
        self.action = action
        self.description = description
        self.is_system_permission = is_system_permission
        self._validate()
    
    def _validate(self):
        """Validate permission business rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Permission name cannot be empty")
        
        if len(self.name) > 100:
            raise ValueError("Permission name cannot exceed 100 characters")
        
        if not self.resource or not self.resource.strip():
            raise ValueError("Resource cannot be empty")
        
        if len(self.resource) > 50:
            raise ValueError("Resource cannot exceed 50 characters")
        
        if not self.action or not self.action.strip():
            raise ValueError("Action cannot be empty")
        
        if len(self.action) > 50:
            raise ValueError("Action cannot exceed 50 characters")
        
        if self.description and len(self.description) > 1000:
            raise ValueError("Permission description cannot exceed 1000 characters")
    
    def can_delete(self) -> bool:
        """Check if permission can be deleted."""
        return not self.is_system_permission and self.is_active and len(self.roles) == 0
    
    @property
    def role_count(self) -> int:
        """Get number of roles with this permission."""
        return len(self.roles) if self.roles else 0
    
    def __str__(self) -> str:
        """String representation of permission."""
        return self.name
    
    def __repr__(self) -> str:
        """Developer representation of permission."""
        return (
            f"Permission(id={self.id}, name='{self.name}', "
            f"resource='{self.resource}', action='{self.action}', "
            f"system={self.is_system_permission}, active={self.is_active})"
        )