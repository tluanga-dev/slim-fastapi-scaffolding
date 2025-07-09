from sqlalchemy import Column, String, Boolean, UUID, DateTime, ForeignKey, Table, Integer, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
import uuid

from src.infrastructure.database.database import Base
from src.infrastructure.models.base import BaseModel


# Association table for role-permission many-to-many relationship
role_permission_association = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID, ForeignKey('roles.id')),
    Column('permission_id', UUID, ForeignKey('permissions.id'))
)


class PermissionCategoryModel(BaseModel):
    __tablename__ = "permission_categories"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    permissions = relationship("PermissionModel", back_populates="category")


class PermissionModel(BaseModel):
    __tablename__ = "permissions"

    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    risk_level = Column(String(20), default="LOW", nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    permission_metadata = Column(JSON)
    
    # Foreign key to category
    category_id = Column(UUID, ForeignKey('permission_categories.id'), nullable=True)
    
    # Relationships
    category = relationship("PermissionCategoryModel", back_populates="permissions")


class RoleModel(BaseModel):
    __tablename__ = "roles"

    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String)
    template = Column(String(50))  # Role template (ADMIN, MANAGER, etc.)
    is_system = Column(Boolean, default=False, nullable=False)
    can_be_deleted = Column(Boolean, default=True, nullable=False)
    
    # Many-to-many relationship with permissions
    permissions = relationship(
        "PermissionModel",
        secondary=role_permission_association,
        backref="roles"
    )
    
    # One-to-many relationship with users
    users = relationship("UserModel", back_populates="role")
    
    # Role hierarchy relationships
    parent_roles = relationship(
        "RoleModel",
        secondary="role_hierarchy",
        primaryjoin="RoleModel.id==RoleHierarchyModel.child_role_id",
        secondaryjoin="RoleModel.id==RoleHierarchyModel.parent_role_id",
        backref="child_roles"
    )


# Update the existing user model to include role relationship
class UserModel(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    user_type = Column(String(20), default="USER", nullable=False)
    
    # Additional fields for JWT compatibility
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True, index=True)
    location_id = Column(UUID)
    last_login = Column(DateTime)
    
    # Foreign key to role
    role_id = Column(UUID, ForeignKey('roles.id'), nullable=True)
    
    # Relationships
    role = relationship("RoleModel", back_populates="users")
    direct_permissions = relationship("UserPermissionModel", back_populates="user", foreign_keys="UserPermissionModel.user_id")
    audit_logs = relationship("RBACauditLogModel", back_populates="user")


# User direct permissions
class UserPermissionModel(BaseModel):
    __tablename__ = "user_permissions"
    
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    permission_code = Column(String(100), nullable=False)
    granted_by = Column(UUID, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    granted_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    reason = Column(Text)
    
    # Relationships
    user = relationship("UserModel", back_populates="direct_permissions", foreign_keys=[user_id])
    granter = relationship("UserModel", foreign_keys=[granted_by])
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_code', name='uq_user_permission'),
    )


# Role hierarchy
class RoleHierarchyModel(BaseModel):
    __tablename__ = "role_hierarchy"
    
    parent_role_id = Column(UUID, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    child_role_id = Column(UUID, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    inherit_permissions = Column(Boolean, default=True, nullable=False)
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('parent_role_id', 'child_role_id', name='uq_role_hierarchy'),
    )


# RBAC Audit Log
class RBACauditLogModel(BaseModel):
    __tablename__ = "rbac_audit_logs"
    
    user_id = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID, nullable=True)
    entity_name = Column(String(255), nullable=True)
    changes = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    reason = Column(Text)
    
    # Relationships
    user = relationship("UserModel", back_populates="audit_logs")


# Permission dependencies
class PermissionDependencyModel(BaseModel):
    __tablename__ = "permission_dependencies"
    
    permission_code = Column(String(100), nullable=False)
    depends_on_code = Column(String(100), nullable=False)
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('permission_code', 'depends_on_code', name='uq_permission_dependency'),
    )
