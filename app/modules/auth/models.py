from enum import Enum
from typing import Optional, List, Set, TYPE_CHECKING
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Table, Index, Integer
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
import bcrypt
from datetime import timedelta

from app.db.base import BaseModel, UUIDType
from app.modules.auth.constants import (
    UserType, PermissionRiskLevel, RoleTemplate, PermissionCategory as PermissionCategoryEnum,
    get_permission_risk_level, get_permission_dependencies,
    can_user_type_manage, validate_permission_dependencies
)

if TYPE_CHECKING:
    from app.modules.master_data.locations.models import Location


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    LOCKED = "LOCKED"


class UserRole(str, Enum):
    """Legacy user role enumeration - deprecated, use Role model instead."""
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

# Association table for user direct permissions
user_permissions_table = Table(
    'user_permissions',
    BaseModel.metadata,
    Column('user_id', UUIDType(), ForeignKey('users.id'), primary_key=True),
    Column('permission_id', UUIDType(), ForeignKey('permissions.id'), primary_key=True),
    Column('granted_by', UUIDType(), ForeignKey('users.id'), nullable=True),
    Column('granted_at', DateTime, nullable=False, default=datetime.utcnow),
    Column('expires_at', DateTime, nullable=True),
    Index('idx_user_permissions_user', 'user_id'),
    Index('idx_user_permissions_permission', 'permission_id'),
    Index('idx_user_permissions_expires', 'expires_at'),
)

# Association table for role hierarchy
role_hierarchy_table = Table(
    'role_hierarchy',
    BaseModel.metadata,
    Column('parent_role_id', UUIDType(), ForeignKey('roles.id'), primary_key=True),
    Column('child_role_id', UUIDType(), ForeignKey('roles.id'), primary_key=True),
    Column('inherit_permissions', Boolean, nullable=False, default=True),
    Index('idx_role_hierarchy_parent', 'parent_role_id'),
    Index('idx_role_hierarchy_child', 'child_role_id'),
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
    user_type = Column(String(20), nullable=False, default=UserType.USER.value, comment="User type hierarchy")
    last_login = Column(DateTime, nullable=True, comment="Last login timestamp")
    failed_login_attempts = Column(String(10), nullable=False, default="0", comment="Failed login attempts")
    account_locked_until = Column(DateTime, nullable=True, comment="Account locked until timestamp")
    password_reset_token = Column(String(255), nullable=True, comment="Password reset token")
    password_reset_expires = Column(DateTime, nullable=True, comment="Password reset token expiration")
    email_verified = Column(Boolean, nullable=False, default=False, comment="Email verification status")
    email_verification_token = Column(String(255), nullable=True, comment="Email verification token")
    is_superuser = Column(Boolean, nullable=False, default=False, comment="Superuser flag")
    
    # Relationships
    roles = relationship("Role", secondary=user_roles_table, back_populates="users", lazy="select")
    direct_permissions = relationship(
        "Permission", 
        secondary=user_permissions_table, 
        primaryjoin="User.id == user_permissions.c.user_id",
        secondaryjoin="Permission.id == user_permissions.c.permission_id",
        lazy="select"
    )
    audit_logs = relationship("RBACauditlog", back_populates="user", lazy="select")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False)
    notifications = relationship("PermissionNotification", foreign_keys="PermissionNotification.user_id", back_populates="user")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_status', 'status'),
        Index('idx_user_user_type', 'user_type'),
        Index('idx_user_last_login', 'last_login'),
        Index('idx_user_superuser', 'is_superuser'),
        Index('idx_user_email_verified', 'email_verified'),
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
        user_type: UserType = UserType.USER,
        is_superuser: bool = False,
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
        self.user_type = user_type.value if isinstance(user_type, UserType) else user_type
        self.failed_login_attempts = "0"
        self.is_superuser = is_superuser
        self.email_verified = False
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
        # Superusers have all permissions
        if self.is_superuser:
            return True
            
        # Check direct permissions
        for permission in self.direct_permissions:
            if permission.name == permission_name:
                return True
                
        # Check role permissions
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False
    
    def get_permissions(self) -> List[str]:
        """Get all permissions for the user."""
        permissions = set()
        
        # Add direct permissions
        for permission in self.direct_permissions:
            permissions.add(permission.name)
            
        # Add role permissions
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
    
    def get_user_type(self) -> UserType:
        """Get user type enum."""
        return UserType(self.user_type)
    
    def can_manage_user_type(self, target_type: UserType) -> bool:
        """Check if user can manage another user type."""
        if self.is_superuser:
            return True
        return can_user_type_manage(self.get_user_type(), target_type)
    
    def has_direct_permission(self, permission_name: str) -> bool:
        """Check if user has a direct permission."""
        return any(perm.name == permission_name for perm in self.direct_permissions)
    
    def get_direct_permissions(self) -> List[str]:
        """Get all direct permissions for the user."""
        return [perm.name for perm in self.direct_permissions]
    
    def get_role_permissions(self) -> List[str]:
        """Get all permissions from roles."""
        permissions = set()
        for role in self.roles:
            permissions.update(role.get_permissions())
        return list(permissions)
    
    def is_account_locked(self) -> bool:
        """Check if account is temporarily locked."""
        if self.account_locked_until is None:
            return False
        return datetime.utcnow() < self.account_locked_until
    
    def set_account_lock(self, lock_duration_minutes: int = 30):
        """Lock account for specified duration."""
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=lock_duration_minutes)
        self.status = UserStatus.LOCKED.value
    
    def unlock_account_time(self):
        """Unlock account from time-based lock."""
        self.account_locked_until = None
        if self.status == UserStatus.LOCKED.value:
            self.status = UserStatus.ACTIVE.value
    
    def verify_email(self):
        """Mark email as verified."""
        self.email_verified = True
        self.email_verification_token = None
    
    def set_email_verification_token(self, token: str):
        """Set email verification token."""
        self.email_verification_token = token
    
    def make_superuser(self, updated_by: Optional[str] = None):
        """Make user a superuser."""
        self.is_superuser = True
        self.updated_by = updated_by
    
    def revoke_superuser(self, updated_by: Optional[str] = None):
        """Revoke superuser status."""
        self.is_superuser = False
        self.updated_by = updated_by
    
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
    template = Column(String(50), nullable=True, comment="Role template type")
    parent_role_id = Column(UUIDType(), ForeignKey('roles.id'), nullable=True, comment="Parent role for hierarchy")
    can_be_deleted = Column(Boolean, nullable=False, default=True, comment="Can be deleted flag")
    max_users = Column(Integer, nullable=True, comment="Maximum users allowed")
    
    # Relationships
    permissions = relationship("Permission", secondary=role_permissions_table, back_populates="roles", lazy="select")
    users = relationship("User", secondary=user_roles_table, back_populates="roles", lazy="select")
    parent_role = relationship("Role", remote_side="Role.id", back_populates="child_roles")
    child_roles = relationship("Role", back_populates="parent_role")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_role_name', 'name'),
        Index('idx_role_system', 'is_system_role'),
        Index('idx_role_template', 'template'),
        Index('idx_role_parent', 'parent_role_id'),
        Index('idx_role_can_delete', 'can_be_deleted'),
    )
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        is_system_role: bool = False,
        template: Optional[RoleTemplate] = None,
        parent_role_id: Optional[str] = None,
        can_be_deleted: bool = True,
        max_users: Optional[int] = None,
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
        self.template = template.value if isinstance(template, RoleTemplate) else template
        self.parent_role_id = parent_role_id
        self.can_be_deleted = can_be_deleted
        self.max_users = max_users
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
        """Get all permission names for this role including inherited permissions."""
        permissions = set()
        
        # Add direct permissions
        for perm in self.permissions:
            permissions.add(perm.name)
            
        # Add inherited permissions from parent roles
        if self.parent_role:
            permissions.update(self.parent_role.get_permissions())
            
        return list(permissions)
    
    def can_delete(self) -> bool:
        """Check if role can be deleted."""
        return (
            not self.is_system_role 
            and self.can_be_deleted 
            and self.is_active 
            and len(self.users) == 0
            and len(self.child_roles) == 0
        )
    
    @property
    def user_count(self) -> int:
        """Get number of users with this role."""
        return len(self.users) if self.users else 0
    
    @property
    def permission_count(self) -> int:
        """Get number of direct permissions for this role."""
        return len(self.permissions) if self.permissions else 0
    
    @property
    def total_permission_count(self) -> int:
        """Get total number of permissions including inherited ones."""
        return len(self.get_permissions())
    
    def get_template(self) -> Optional[RoleTemplate]:
        """Get role template enum."""
        return RoleTemplate(self.template) if self.template else None
    
    def has_parent(self) -> bool:
        """Check if role has a parent role."""
        return self.parent_role_id is not None
    
    def has_children(self) -> bool:
        """Check if role has child roles."""
        return len(self.child_roles) > 0
    
    def get_hierarchy_depth(self) -> int:
        """Get the depth of this role in the hierarchy."""
        if not self.parent_role:
            return 0
        return 1 + self.parent_role.get_hierarchy_depth()
    
    def get_all_child_roles(self) -> List['Role']:
        """Get all child roles recursively."""
        children = []
        for child in self.child_roles:
            children.append(child)
            children.extend(child.get_all_child_roles())
        return children
    
    def get_all_parent_roles(self) -> List['Role']:
        """Get all parent roles recursively."""
        parents = []
        if self.parent_role:
            parents.append(self.parent_role)
            parents.extend(self.parent_role.get_all_parent_roles())
        return parents
    
    def can_assign_to_user_count(self, additional_users: int = 1) -> bool:
        """Check if role can be assigned to additional users."""
        if self.max_users is None:
            return True
        return (self.user_count + additional_users) <= self.max_users
    
    def validate_permission_dependencies(self) -> List[str]:
        """Validate that all permission dependencies are satisfied."""
        permission_names = [perm.name for perm in self.permissions]
        return validate_permission_dependencies(permission_names)
    
    def has_permission_recursive(self, permission_name: str) -> bool:
        """Check if role has permission including inherited ones."""
        return permission_name in self.get_permissions()
    
    def __str__(self) -> str:
        """String representation of role."""
        return self.name
    
    def __repr__(self) -> str:
        """Developer representation of role."""
        return (
            f"Role(id={self.id}, name='{self.name}', "
            f"template='{self.template}', system={self.is_system_role}, "
            f"active={self.is_active})"
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
    category_id = Column(UUIDType(), ForeignKey('permission_categories.id'), nullable=True, comment="Permission category")
    risk_level = Column(String(20), nullable=False, default=PermissionRiskLevel.LOW.value, comment="Risk level")
    requires_approval = Column(Boolean, nullable=False, default=False, comment="Requires approval flag")
    code = Column(String(100), nullable=False, unique=True, index=True, comment="Permission code")
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions_table, back_populates="permissions", lazy="select")
    category = relationship("PermissionCategory", back_populates="permissions")
    dependencies = relationship("PermissionDependency", foreign_keys="PermissionDependency.permission_id", back_populates="permission")
    dependents = relationship("PermissionDependency", foreign_keys="PermissionDependency.depends_on_id", back_populates="depends_on")
    notifications = relationship("PermissionNotification", back_populates="permission")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_permission_name', 'name'),
        Index('idx_permission_code', 'code'),
        Index('idx_permission_resource', 'resource'),
        Index('idx_permission_action', 'action'),
        Index('idx_permission_system', 'is_system_permission'),
        Index('idx_permission_category', 'category_id'),
        Index('idx_permission_risk_level', 'risk_level'),
        Index('idx_permission_requires_approval', 'requires_approval'),
        Index('idx_permission_resource_action', 'resource', 'action'),
    )
    
    def __init__(
        self,
        name: str,
        resource: str,
        action: str,
        code: Optional[str] = None,
        description: Optional[str] = None,
        is_system_permission: bool = False,
        category_id: Optional[str] = None,
        risk_level: PermissionRiskLevel = PermissionRiskLevel.LOW,
        requires_approval: bool = False,
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
        self.code = code or name  # Use name as code if not provided
        self.description = description
        self.is_system_permission = is_system_permission
        self.category_id = category_id
        self.risk_level = risk_level.value if isinstance(risk_level, PermissionRiskLevel) else risk_level
        self.requires_approval = requires_approval
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
    
    def get_risk_level(self) -> PermissionRiskLevel:
        """Get risk level enum."""
        return PermissionRiskLevel(self.risk_level)
    
    def get_dependencies(self) -> List[str]:
        """Get list of permission codes this permission depends on."""
        return [dep.depends_on.code for dep in self.dependencies]
    
    def get_dependents(self) -> List[str]:
        """Get list of permission codes that depend on this permission."""
        return [dep.permission.code for dep in self.dependents]
    
    def is_high_risk(self) -> bool:
        """Check if permission is high or critical risk."""
        return self.get_risk_level() in [PermissionRiskLevel.HIGH, PermissionRiskLevel.CRITICAL]
    
    def is_critical_risk(self) -> bool:
        """Check if permission is critical risk."""
        return self.get_risk_level() == PermissionRiskLevel.CRITICAL
    
    def needs_approval(self) -> bool:
        """Check if permission requires approval."""
        return self.requires_approval or self.is_high_risk()
    
    def validate_dependencies(self, available_permissions: List[str]) -> List[str]:
        """Validate that all dependencies are available."""
        missing_deps = []
        for dep in self.get_dependencies():
            if dep not in available_permissions:
                missing_deps.append(dep)
        return missing_deps
    
    def __str__(self) -> str:
        """String representation of permission."""
        return self.name
    
    def __repr__(self) -> str:
        """Developer representation of permission."""
        return (
            f"Permission(id={self.id}, name='{self.name}', "
            f"code='{self.code}', resource='{self.resource}', action='{self.action}', "
            f"risk='{self.risk_level}', system={self.is_system_permission}, active={self.is_active})"
        )


class PermissionCategory(BaseModel):
    """Permission category model for organizing permissions."""
    
    __tablename__ = "permission_categories"
    
    code = Column(String(50), nullable=False, unique=True, index=True, comment="Category code")
    name = Column(String(100), nullable=False, comment="Category name")
    description = Column(Text, nullable=True, comment="Category description")
    display_order = Column(Integer, nullable=False, default=0, comment="Display order")
    icon = Column(String(50), nullable=True, comment="Icon name")
    color = Column(String(20), nullable=True, comment="Display color")
    
    # Relationships
    permissions = relationship("Permission", back_populates="category")
    
    # Indexes
    __table_args__ = (
        Index('idx_permission_category_code', 'code'),
        Index('idx_permission_category_name', 'name'),
        Index('idx_permission_category_order', 'display_order'),
    )
    
    def __init__(
        self,
        code: str,
        name: str,
        description: Optional[str] = None,
        display_order: int = 0,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.code = code
        self.name = name
        self.description = description
        self.display_order = display_order
        self.icon = icon
        self.color = color
        self._validate()
    
    def _validate(self):
        """Validate category business rules."""
        if not self.code or not self.code.strip():
            raise ValueError("Category code cannot be empty")
        
        if len(self.code) > 50:
            raise ValueError("Category code cannot exceed 50 characters")
        
        if not self.name or not self.name.strip():
            raise ValueError("Category name cannot be empty")
        
        if len(self.name) > 100:
            raise ValueError("Category name cannot exceed 100 characters")
    
    @property
    def permission_count(self) -> int:
        """Get number of permissions in this category."""
        return len(self.permissions) if self.permissions else 0
    
    def get_category_enum(self) -> Optional[PermissionCategoryEnum]:
        """Get category enum from code."""
        try:
            return PermissionCategoryEnum(self.code)
        except ValueError:
            return None
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f"PermissionCategory(id={self.id}, code='{self.code}', name='{self.name}')"


class PermissionDependency(BaseModel):
    """Permission dependency model for defining permission prerequisites."""
    
    __tablename__ = "permission_dependencies"
    
    permission_id = Column(UUIDType(), ForeignKey('permissions.id'), nullable=False, comment="Permission ID")
    depends_on_id = Column(UUIDType(), ForeignKey('permissions.id'), nullable=False, comment="Depends on permission ID")
    
    # Relationships
    permission = relationship("Permission", foreign_keys=[permission_id], back_populates="dependencies")
    depends_on = relationship("Permission", foreign_keys=[depends_on_id], back_populates="dependents")
    
    # Indexes
    __table_args__ = (
        Index('idx_permission_deps_perm', 'permission_id'),
        Index('idx_permission_deps_depends', 'depends_on_id'),
    )
    
    def __init__(self, permission_id: str, depends_on_id: str, **kwargs):
        super().__init__(**kwargs)
        self.permission_id = permission_id
        self.depends_on_id = depends_on_id
    
    def __repr__(self) -> str:
        return f"PermissionDependency(permission_id={self.permission_id}, depends_on_id={self.depends_on_id})"


class RBACauditlog(BaseModel):
    """RBAC audit log model for tracking all authentication and authorization events."""
    
    __tablename__ = "rbac_audit_logs"
    
    user_id = Column(UUIDType(), ForeignKey('users.id'), nullable=True, comment="User ID")
    action = Column(String(50), nullable=False, comment="Action performed")
    entity_type = Column(String(50), nullable=False, comment="Entity type")
    entity_id = Column(UUIDType(), nullable=True, comment="Entity ID")
    changes = Column(Text, nullable=True, comment="Changes made (JSON)")
    ip_address = Column(String(45), nullable=True, comment="Client IP address")
    user_agent = Column(String(500), nullable=True, comment="Client user agent")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Event timestamp")
    success = Column(Boolean, nullable=False, default=True, comment="Success flag")
    error_message = Column(Text, nullable=True, comment="Error message if failed")
    session_id = Column(String(255), nullable=True, comment="Session ID")
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_rbac_audit_user', 'user_id'),
        Index('idx_rbac_audit_action', 'action'),
        Index('idx_rbac_audit_entity_type', 'entity_type'),
        Index('idx_rbac_audit_entity_id', 'entity_id'),
        Index('idx_rbac_audit_timestamp', 'timestamp'),
        Index('idx_rbac_audit_success', 'success'),
        Index('idx_rbac_audit_ip', 'ip_address'),
    )
    
    def __init__(
        self,
        action: str,
        entity_type: str,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        changes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.changes = changes
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.success = success
        self.error_message = error_message
        self.session_id = session_id
        self.timestamp = datetime.utcnow()
    
    def __repr__(self) -> str:
        return (
            f"RBACauditlog(id={self.id}, user_id={self.user_id}, "
            f"action='{self.action}', entity_type='{self.entity_type}', "
            f"success={self.success}, timestamp={self.timestamp})"
        )


class NotificationPreference(BaseModel):
    """
    User notification preference model for RBAC notifications.
    
    Attributes:
        user_id: User ID
        email_enabled: Whether email notifications are enabled
        in_app_enabled: Whether in-app notifications are enabled
        permission_expiry_days: Days before expiry to send notifications
        high_risk_immediate: Whether to send immediate notifications for high-risk permissions
        digest_frequency: Frequency of digest notifications (daily, weekly, none)
        quiet_hours_start: Start time for quiet hours
        quiet_hours_end: End time for quiet hours
    """
    
    __tablename__ = "notification_preferences"
    
    user_id = Column(UUIDType(), ForeignKey('users.id'), nullable=False, unique=True, comment="User ID")
    email_enabled = Column(Boolean, nullable=False, default=True, comment="Email notifications enabled")
    in_app_enabled = Column(Boolean, nullable=False, default=True, comment="In-app notifications enabled")
    permission_expiry_days = Column(String(50), nullable=True, comment="Days before expiry to notify (JSON array)")
    high_risk_immediate = Column(Boolean, nullable=False, default=True, comment="Immediate notifications for high-risk permissions")
    digest_frequency = Column(String(20), nullable=False, default='daily', comment="Digest frequency")
    quiet_hours_start = Column(DateTime, nullable=True, comment="Quiet hours start time")
    quiet_hours_end = Column(DateTime, nullable=True, comment="Quiet hours end time")
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_prefs_user', 'user_id'),
        Index('idx_notification_prefs_email', 'email_enabled'),
        Index('idx_notification_prefs_in_app', 'in_app_enabled'),
        Index('idx_notification_prefs_digest', 'digest_frequency'),
    )
    
    def __init__(
        self,
        user_id: str,
        email_enabled: bool = True,
        in_app_enabled: bool = True,
        permission_expiry_days: Optional[str] = None,
        high_risk_immediate: bool = True,
        digest_frequency: str = 'daily',
        quiet_hours_start: Optional[datetime] = None,
        quiet_hours_end: Optional[datetime] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.email_enabled = email_enabled
        self.in_app_enabled = in_app_enabled
        self.permission_expiry_days = permission_expiry_days
        self.high_risk_immediate = high_risk_immediate
        self.digest_frequency = digest_frequency
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end
    
    def __repr__(self) -> str:
        return (
            f"NotificationPreference(id={self.id}, user_id={self.user_id}, "
            f"email={self.email_enabled}, in_app={self.in_app_enabled}, "
            f"digest={self.digest_frequency})"
        )


class PermissionNotification(BaseModel):
    """
    Permission notification model for tracking sent notifications.
    
    Attributes:
        user_id: User ID receiving the notification
        permission_id: Permission ID related to the notification
        notification_type: Type of notification (e.g., PERMISSION_EXPIRING, ADMIN_ALERT)
        channel: Notification channel (email, in_app, etc.)
        title: Notification title
        message: Notification message
        content: Full notification content (JSON)
        days_ahead: Days ahead when notification was sent
        is_read: Whether notification has been read (for in-app notifications)
        read_at: When notification was read
        related_user_id: Related user ID (for admin notifications)
    """
    
    __tablename__ = "permission_notifications"
    
    user_id = Column(UUIDType(), ForeignKey('users.id'), nullable=False, comment="User ID")
    permission_id = Column(UUIDType(), ForeignKey('permissions.id'), nullable=False, comment="Permission ID")
    notification_type = Column(String(50), nullable=False, comment="Notification type")
    channel = Column(String(20), nullable=False, comment="Notification channel")
    title = Column(String(200), nullable=True, comment="Notification title")
    message = Column(Text, nullable=True, comment="Notification message")
    content = Column(Text, nullable=True, comment="Full notification content (JSON)")
    days_ahead = Column(Integer, nullable=True, comment="Days ahead when sent")
    is_read = Column(Boolean, nullable=False, default=False, comment="Read status")
    read_at = Column(DateTime, nullable=True, comment="Read timestamp")
    related_user_id = Column(UUIDType(), ForeignKey('users.id'), nullable=True, comment="Related user ID")
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    permission = relationship("Permission", back_populates="notifications")
    related_user = relationship("User", foreign_keys=[related_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_permission_notifications_user', 'user_id'),
        Index('idx_permission_notifications_permission', 'permission_id'),
        Index('idx_permission_notifications_type', 'notification_type'),
        Index('idx_permission_notifications_channel', 'channel'),
        Index('idx_permission_notifications_read', 'is_read'),
        Index('idx_permission_notifications_created', 'created_at'),
        Index('idx_permission_notifications_days_ahead', 'days_ahead'),
        Index('idx_permission_notifications_related_user', 'related_user_id'),
    )
    
    def __init__(
        self,
        user_id: str,
        permission_id: str,
        notification_type: str,
        channel: str,
        title: Optional[str] = None,
        message: Optional[str] = None,
        content: Optional[str] = None,
        days_ahead: Optional[int] = None,
        related_user_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.permission_id = permission_id
        self.notification_type = notification_type
        self.channel = channel
        self.title = title
        self.message = message
        self.content = content
        self.days_ahead = days_ahead
        self.related_user_id = related_user_id
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return (
            f"PermissionNotification(id={self.id}, user_id={self.user_id}, "
            f"permission_id={self.permission_id}, type='{self.notification_type}', "
            f"channel='{self.channel}', read={self.is_read})"
        )