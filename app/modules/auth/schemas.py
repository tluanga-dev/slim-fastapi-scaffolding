from typing import Optional, List, Dict, Any
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


# Enhanced RBAC Schemas

class PermissionCategoryResponse(BaseModel):
    """Schema for permission category response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    name: str
    description: Optional[str]
    display_order: int
    icon: Optional[str]
    color: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class EnhancedPermissionResponse(BaseModel):
    """Schema for enhanced permission response with risk level and dependencies."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    name: str
    description: Optional[str]
    resource: str
    action: str
    category_id: Optional[UUID]
    risk_level: str
    requires_approval: bool
    is_system_permission: bool
    created_at: datetime
    updated_at: datetime
    is_active: bool
    category: Optional[PermissionCategoryResponse] = None


class PermissionDependencyResponse(BaseModel):
    """Schema for permission dependency response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    permission_id: UUID
    depends_on_id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    permission: Optional[EnhancedPermissionResponse] = None
    depends_on: Optional[EnhancedPermissionResponse] = None


class PermissionValidationRequest(BaseModel):
    """Schema for permission validation request."""
    permission_codes: List[str] = Field(..., description="List of permission codes to validate")


class PermissionValidationResponse(BaseModel):
    """Schema for permission validation response."""
    missing_dependencies: List[str] = Field(..., description="List of missing dependency permission codes")


class PermissionGrantRequest(BaseModel):
    """Schema for permission grant request."""
    grantee_id: UUID = Field(..., description="User ID to grant permission to")
    permission_code: str = Field(..., description="Permission code to grant")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration time")


class PermissionGrantResponse(BaseModel):
    """Schema for permission grant response."""
    success: bool = Field(..., description="Whether the grant was successful")
    message: str = Field(..., description="Response message")
    permission_id: Optional[UUID] = Field(None, description="Permission ID if successful")


class PermissionCanGrantRequest(BaseModel):
    """Schema for checking if permission can be granted."""
    grantee_id: UUID = Field(..., description="User ID to check grant for")
    permission_code: str = Field(..., description="Permission code to check")


class PermissionCanGrantResponse(BaseModel):
    """Schema for permission can grant response."""
    can_grant: bool = Field(..., description="Whether the permission can be granted")
    reason: str = Field(..., description="Reason for the decision")
    missing_dependencies: List[str] = Field(..., description="List of missing dependencies")


class PermissionRevokeRequest(BaseModel):
    """Schema for permission revoke request."""
    user_id: UUID = Field(..., description="User ID to revoke permission from")
    permission_code: str = Field(..., description="Permission code to revoke")


class PermissionRevokeResponse(BaseModel):
    """Schema for permission revoke response."""
    success: bool = Field(..., description="Whether the revoke was successful")
    message: str = Field(..., description="Response message")


class PermissionCheckRequest(BaseModel):
    """Schema for permission check request."""
    permission_code: str = Field(..., description="Permission code to check")
    require_dependencies: bool = Field(True, description="Whether to validate dependencies")


class PermissionCheckResponse(BaseModel):
    """Schema for permission check response."""
    has_permission: bool = Field(..., description="Whether user has the permission")
    risk_level: Optional[str] = Field(None, description="Risk level of the permission")
    requires_approval: bool = Field(..., description="Whether permission requires approval")
    missing_dependencies: List[str] = Field(..., description="List of missing dependencies")


class UserTypeElevationRequest(BaseModel):
    """Schema for user type elevation request."""
    target_user_id: UUID = Field(..., description="User ID to elevate")
    new_user_type: str = Field(..., description="New user type to assign")


class UserTypeElevationResponse(BaseModel):
    """Schema for user type elevation response."""
    success: bool = Field(..., description="Whether the elevation was successful")
    message: str = Field(..., description="Response message")
    previous_type: Optional[str] = Field(None, description="Previous user type")


class EnhancedUserResponse(BaseModel):
    """Schema for enhanced user response with additional RBAC fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    status: UserStatus
    role: UserRole  # Legacy field
    user_type: str  # New user type field
    is_superuser: bool
    is_verified: bool
    email_verified: bool
    last_login: Optional[datetime]
    account_locked_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class EnhancedRoleResponse(BaseModel):
    """Schema for enhanced role response with template and hierarchy fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str]
    template: Optional[str]
    parent_role_id: Optional[UUID]
    is_system_role: bool
    can_be_deleted: bool
    max_users: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class UserAllPermissionsResponse(BaseModel):
    """Schema for user all permissions response."""
    user: EnhancedUserResponse
    roles: List[EnhancedRoleResponse]
    permissions: List[EnhancedPermissionResponse]
    direct_permissions: List[EnhancedPermissionResponse]


class RBACauditlogResponse(BaseModel):
    """Schema for RBAC audit log response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: Optional[UUID]
    action: str
    entity_type: str
    entity_id: Optional[UUID]
    changes: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    success: bool
    error_message: Optional[str]
    session_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class RBACauditlogRequest(BaseModel):
    """Schema for RBAC audit log request."""
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    action: Optional[str] = Field(None, description="Filter by action")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")
    success: Optional[bool] = Field(None, description="Filter by success status")
    limit: int = Field(100, ge=1, le=1000, description="Limit results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


# Role hierarchy schemas

class RoleHierarchyRequest(BaseModel):
    """Schema for role hierarchy request."""
    parent_role_id: UUID = Field(..., description="Parent role ID")
    child_role_id: UUID = Field(..., description="Child role ID")
    inherit_permissions: bool = Field(True, description="Whether child role inherits permissions from parent")


class RoleHierarchyResponse(BaseModel):
    """Schema for role hierarchy response."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")


class RoleHierarchyInfo(BaseModel):
    """Schema for role hierarchy information."""
    current_role: Optional[EnhancedRoleResponse] = None
    parent_roles: List[EnhancedRoleResponse] = Field(default_factory=list, description="Parent roles")
    child_roles: List[EnhancedRoleResponse] = Field(default_factory=list, description="Child roles")


class RoleInheritedPermissionsResponse(BaseModel):
    """Schema for role inherited permissions response."""
    role_id: UUID = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    direct_permissions: List[EnhancedPermissionResponse] = Field(default_factory=list, description="Direct permissions")
    inherited_permissions: List[EnhancedPermissionResponse] = Field(default_factory=list, description="Inherited permissions")
    all_permissions: List[EnhancedPermissionResponse] = Field(default_factory=list, description="All permissions (direct + inherited)")


class PermissionSource(BaseModel):
    """Schema for permission source information."""
    permission: EnhancedPermissionResponse
    source: str = Field(..., description="Source type: 'direct' or 'role'")
    source_details: Optional[str] = Field(None, description="Additional source details")


class UserPermissionsWithHierarchyResponse(BaseModel):
    """Schema for user permissions with hierarchy response."""
    user_id: UUID = Field(..., description="User ID")
    direct_permissions: List[EnhancedPermissionResponse] = Field(default_factory=list, description="Direct permissions")
    role_permissions: Dict[str, List[EnhancedPermissionResponse]] = Field(default_factory=dict, description="Permissions by role")
    all_permissions: List[PermissionSource] = Field(default_factory=list, description="All permissions with source information")


# Temporary permissions schemas

class TemporaryPermissionRequest(BaseModel):
    """Schema for temporary permission request."""
    grantee_id: UUID = Field(..., description="User ID to grant permission to")
    permission_code: str = Field(..., description="Permission code to grant")
    expires_at: datetime = Field(..., description="Expiration time for the permission")
    reason: Optional[str] = Field(None, description="Reason for granting temporary permission")


class TemporaryPermissionResponse(BaseModel):
    """Schema for temporary permission response."""
    success: bool = Field(..., description="Whether the grant was successful")
    message: str = Field(..., description="Response message")
    permission_id: Optional[UUID] = Field(None, description="Permission ID if successful")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class TemporaryPermissionInfo(BaseModel):
    """Schema for temporary permission information."""
    permission: EnhancedPermissionResponse
    granted_by: Optional[UUID] = Field(None, description="User who granted the permission")
    granted_at: datetime = Field(..., description="When permission was granted")
    expires_at: datetime = Field(..., description="When permission expires")
    reason: Optional[str] = Field(None, description="Reason for granting")


class UserTemporaryPermissionsResponse(BaseModel):
    """Schema for user temporary permissions response."""
    user_id: UUID = Field(..., description="User ID")
    temporary_permissions: List[TemporaryPermissionInfo] = Field(default_factory=list, description="Temporary permissions")
    active_count: int = Field(..., description="Number of active temporary permissions")
    expired_count: int = Field(..., description="Number of expired temporary permissions")


# Bulk operation schemas

class BulkPermissionGrantRequest(BaseModel):
    """Schema for bulk permission grant request."""
    grantee_id: UUID = Field(..., description="User ID to grant permissions to")
    permission_codes: List[str] = Field(..., description="List of permission codes to grant")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration time for all permissions")


class BulkPermissionRevokeRequest(BaseModel):
    """Schema for bulk permission revoke request."""
    user_id: UUID = Field(..., description="User ID to revoke permissions from")
    permission_codes: List[str] = Field(..., description="List of permission codes to revoke")


class BulkRoleAssignRequest(BaseModel):
    """Schema for bulk role assignment request."""
    user_id: UUID = Field(..., description="User ID to assign roles to")
    role_ids: List[UUID] = Field(..., description="List of role IDs to assign")


class BulkRoleRemoveRequest(BaseModel):
    """Schema for bulk role removal request."""
    user_id: UUID = Field(..., description="User ID to remove roles from")
    role_ids: List[UUID] = Field(..., description="List of role IDs to remove")


class BulkRolePermissionAssignRequest(BaseModel):
    """Schema for bulk role permission assignment request."""
    role_id: UUID = Field(..., description="Role ID to assign permissions to")
    permission_codes: List[str] = Field(..., description="List of permission codes to assign")


class BulkOperationResult(BaseModel):
    """Schema for bulk operation result."""
    success: bool = Field(..., description="Whether the bulk operation was successful")
    total: int = Field(..., description="Total number of operations attempted")
    success_count: int = Field(..., description="Number of successful operations")
    failed_count: int = Field(..., description="Number of failed operations")
    successful_items: List[Dict[str, Any]] = Field(default_factory=list, description="List of successful operations")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="List of failed operations")
    message: str = Field(..., description="Summary message")


# Notification schemas

class NotificationPreferenceRequest(BaseModel):
    """Schema for notification preference request."""
    email_enabled: bool = Field(True, description="Enable email notifications")
    in_app_enabled: bool = Field(True, description="Enable in-app notifications")
    permission_expiry_days: List[int] = Field([7, 3, 1], description="Days before expiry to send notifications")
    high_risk_immediate: bool = Field(True, description="Send immediate notifications for high-risk permissions")
    digest_frequency: str = Field("daily", description="Digest frequency (daily, weekly, none)")
    quiet_hours_start: Optional[datetime] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[datetime] = Field(None, description="Quiet hours end time")


class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preference response."""
    user_id: UUID = Field(..., description="User ID")
    email_enabled: bool = Field(..., description="Email notifications enabled")
    in_app_enabled: bool = Field(..., description="In-app notifications enabled")
    permission_expiry_days: List[int] = Field(..., description="Days before expiry to send notifications")
    high_risk_immediate: bool = Field(..., description="Immediate notifications for high-risk permissions")
    digest_frequency: str = Field(..., description="Digest frequency")
    quiet_hours_start: Optional[datetime] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[datetime] = Field(None, description="Quiet hours end time")


class NotificationPreferenceUpdate(BaseModel):
    """Schema for notification preference update."""
    email_enabled: Optional[bool] = Field(None, description="Enable email notifications")
    in_app_enabled: Optional[bool] = Field(None, description="Enable in-app notifications")
    permission_expiry_days: Optional[List[int]] = Field(None, description="Days before expiry to send notifications")
    high_risk_immediate: Optional[bool] = Field(None, description="Send immediate notifications for high-risk permissions")
    digest_frequency: Optional[str] = Field(None, description="Digest frequency")
    quiet_hours_start: Optional[datetime] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[datetime] = Field(None, description="Quiet hours end time")


class NotificationHistoryResponse(BaseModel):
    """Schema for notification history response."""
    id: UUID = Field(..., description="Notification ID")
    notification_type: str = Field(..., description="Notification type")
    channel: str = Field(..., description="Notification channel")
    title: Optional[str] = Field(None, description="Notification title")
    message: Optional[str] = Field(None, description="Notification message")
    content: Optional[Dict[str, Any]] = Field(None, description="Full notification content")
    is_read: bool = Field(..., description="Read status")
    created_at: datetime = Field(..., description="Creation timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")


class NotificationMarkReadRequest(BaseModel):
    """Schema for marking notification as read."""
    notification_id: UUID = Field(..., description="Notification ID to mark as read")


class NotificationCheckRequest(BaseModel):
    """Schema for checking expiring permissions."""
    days_ahead: int = Field(7, ge=0, le=365, description="Days ahead to check for expiring permissions")


class NotificationCheckResponse(BaseModel):
    """Schema for expiring permissions check response."""
    total_expiring: int = Field(..., description="Total number of expiring permissions")
    expiring_permissions: List[Dict[str, Any]] = Field(..., description="List of expiring permissions")
    checked_at: datetime = Field(..., description="Check timestamp")


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics response."""
    total_processed: int = Field(..., description="Total notifications processed")
    total_notifications_sent: int = Field(..., description="Total notifications sent")
    notifications_by_channel: Dict[str, int] = Field(..., description="Notifications by channel")
    last_run: Optional[str] = Field(None, description="Last run timestamp")
    system_health: str = Field(..., description="System health status")


class NotificationDigestRequest(BaseModel):
    """Schema for notification digest request."""
    user_id: UUID = Field(..., description="User ID")
    digest_type: str = Field(..., description="Digest type (daily, weekly)")
    start_date: datetime = Field(..., description="Start date for digest")
    end_date: datetime = Field(..., description="End date for digest")


class NotificationDigestResponse(BaseModel):
    """Schema for notification digest response."""
    user_id: UUID = Field(..., description="User ID")
    digest_type: str = Field(..., description="Digest type")
    period: str = Field(..., description="Period covered")
    total_notifications: int = Field(..., description="Total notifications in period")
    unread_notifications: int = Field(..., description="Unread notifications in period")
    notifications_by_type: Dict[str, int] = Field(..., description="Notifications by type")
    summary: str = Field(..., description="Digest summary")


class NotificationChannelTestRequest(BaseModel):
    """Schema for testing notification channels."""
    channel: str = Field(..., description="Channel to test (email, in_app, sms)")
    message: str = Field(..., description="Test message")
    recipient: Optional[str] = Field(None, description="Recipient (for email/sms)")


class NotificationChannelTestResponse(BaseModel):
    """Schema for notification channel test response."""
    channel: str = Field(..., description="Tested channel")
    success: bool = Field(..., description="Test success status")
    message: str = Field(..., description="Test result message")
    delivery_time: Optional[float] = Field(None, description="Delivery time in seconds")


class NotificationBatchProcessResult(BaseModel):
    """Schema for notification batch processing result."""
    processed: int = Field(..., description="Number of notifications processed")
    notifications_sent: int = Field(..., description="Number of notifications sent")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Processing errors")
    notifications_by_type: Dict[str, int] = Field(default_factory=dict, description="Notifications by type")
    processing_time: float = Field(..., description="Processing time in seconds")
    success: bool = Field(..., description="Overall success status")