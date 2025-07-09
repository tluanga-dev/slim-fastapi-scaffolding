from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from uuid import UUID

from app.modules.auth.models import UserStatus, UserRole


class UserRegister(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    first_name: str = Field(..., max_length=100, description="First name")
    last_name: str = Field(..., max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    status: UserStatus
    role: UserRole
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class UserUpdate(BaseModel):
    """Schema for updating user."""
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class PasswordReset(BaseModel):
    """Schema for password reset."""
    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str = Field(..., description="Refresh token")


class RoleResponse(BaseModel):
    """Schema for role response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str]
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
    is_active: bool


class RoleCreate(BaseModel):
    """Schema for creating a role."""
    name: str = Field(..., max_length=50, description="Role name")
    description: Optional[str] = Field(None, max_length=200, description="Role description")
    is_system_role: bool = Field(False, description="Is system role")


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    name: Optional[str] = Field(None, max_length=50, description="Role name")
    description: Optional[str] = Field(None, max_length=200, description="Role description")


class PermissionResponse(BaseModel):
    """Schema for permission response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str]
    resource: str
    action: str
    is_system_permission: bool
    created_at: datetime
    updated_at: datetime
    is_active: bool


class PermissionCreate(BaseModel):
    """Schema for creating a permission."""
    name: str = Field(..., max_length=100, description="Permission name")
    description: Optional[str] = Field(None, max_length=200, description="Permission description")
    resource: str = Field(..., max_length=50, description="Resource name")
    action: str = Field(..., max_length=50, description="Action name")
    is_system_permission: bool = Field(False, description="Is system permission")


class PermissionUpdate(BaseModel):
    """Schema for updating a permission."""
    name: Optional[str] = Field(None, max_length=100, description="Permission name")
    description: Optional[str] = Field(None, max_length=200, description="Permission description")
    resource: Optional[str] = Field(None, max_length=50, description="Resource name")
    action: Optional[str] = Field(None, max_length=50, description="Action name")


class UserRoleAssignment(BaseModel):
    """Schema for user role assignment."""
    user_id: UUID = Field(..., description="User ID")
    role_id: UUID = Field(..., description="Role ID")


class RolePermissionAssignment(BaseModel):
    """Schema for role permission assignment."""
    role_id: UUID = Field(..., description="Role ID")
    permission_id: UUID = Field(..., description="Permission ID")


class UserPermissionsResponse(BaseModel):
    """Schema for user permissions response."""
    user: UserResponse
    roles: List[RoleResponse]
    permissions: List[PermissionResponse]


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request."""
    token: str = Field(..., description="Email verification token")


class ResendVerificationRequest(BaseModel):
    """Schema for resend verification request."""
    email: EmailStr = Field(..., description="Email address")