from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import AuthRepository
from .models import User, Role, Permission, UserStatus, UserRole
from .schemas import (
    UserRegister, UserLogin, UserResponse, UserUpdate, PasswordChange,
    PasswordReset, PasswordResetConfirm, TokenResponse, RefreshTokenRequest,
    RoleCreate, RoleUpdate, RoleResponse, PermissionCreate, PermissionUpdate,
    PermissionResponse, UserRoleAssignment, RolePermissionAssignment,
    UserPermissionsResponse, EmailVerificationRequest, ResendVerificationRequest
)
from app.core.security import (
    verify_password, get_password_hash, validate_password,
    create_access_token, create_refresh_token, verify_token, 
    create_password_reset_token, verify_password_reset_token,
    create_email_verification_token, verify_email_verification_token
)
from app.core.errors import ValidationError, NotFoundError, ConflictError, AuthenticationError
from app.shared.pagination import Page


class AuthService:
    """Authentication service."""
    
    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.repository = AuthRepository(session)
    
    # User management
    async def register_user(self, user_data: UserRegister) -> UserResponse:
        """Register a new user."""
        # Validate password
        try:
            validate_password(user_data.password)
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Check if username already exists
        if await self.repository.exists_by_username(user_data.username):
            raise ConflictError(f"Username '{user_data.username}' is already taken")
        
        # Check if email already exists
        if await self.repository.exists_by_email(user_data.email):
            raise ConflictError(f"Email '{user_data.email}' is already registered")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user data
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": hashed_password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "phone": user_data.phone,
            "status": UserStatus.ACTIVE,
            "role": UserRole.USER,
            "is_verified": False,
            "is_active": True
        }
        
        # Create user
        user = await self.repository.create_user(user_dict)
        
        # TODO: Send verification email
        
        return UserResponse.model_validate(user)
    
    async def login_user(self, login_data: UserLogin) -> TokenResponse:
        """Login user and return tokens."""
        # Get user by username or email
        user = await self.repository.get_user_by_username_or_email(login_data.username)
        
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise AuthenticationError("Invalid username or password")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        
        # Check if user is verified (optional - depends on requirements)
        # if not user.is_verified:
        #     raise AuthenticationError("Please verify your email address")
        
        # Update last login
        await self.repository.update_user(user.id, {"last_login": datetime.utcnow()})
        
        # Get user permissions
        permissions = await self.repository.get_user_permissions(user.id)
        permission_names = [f"{perm.resource}:{perm.action}" for perm in permissions]
        
        # Create tokens
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "permissions": permission_names,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour
            user=UserResponse.model_validate(user)
        )
    
    async def refresh_token(self, refresh_request: RefreshTokenRequest) -> TokenResponse:
        """Refresh access token using refresh token."""
        try:
            payload = verify_token(refresh_request.refresh_token, expected_type="refresh")
        except Exception:
            raise AuthenticationError("Invalid refresh token")
        
        # Get user
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        user = await self.repository.get_user_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Get user permissions
        permissions = await self.repository.get_user_permissions(user.id)
        permission_names = [f"{perm.resource}:{perm.action}" for perm in permissions]
        
        # Create new tokens
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "permissions": permission_names,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour
            user=UserResponse.model_validate(user)
        )
    
    async def get_user(self, user_id: UUID) -> Optional[UserResponse]:
        """Get user by ID."""
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    async def get_current_user(self, user_id: UUID) -> UserResponse:
        """Get current user."""
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        return UserResponse.model_validate(user)
    
    async def update_user(self, user_id: UUID, update_data: UserUpdate) -> UserResponse:
        """Update user information."""
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Check email uniqueness if updating email
        if update_data.email and update_data.email != user.email:
            if await self.repository.exists_by_email(update_data.email, exclude_id=user_id):
                raise ConflictError(f"Email '{update_data.email}' is already registered")
        
        # Update user
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_user = await self.repository.update_user(user_id, update_dict)
        
        return UserResponse.model_validate(updated_user)
    
    async def change_password(self, user_id: UUID, password_change: PasswordChange) -> bool:
        """Change user password."""
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Verify current password
        if not verify_password(password_change.current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password
        try:
            validate_password(password_change.new_password)
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Hash new password
        new_password_hash = get_password_hash(password_change.new_password)
        
        # Update password
        await self.repository.update_user(user_id, {"password_hash": new_password_hash})
        
        return True
    
    async def request_password_reset(self, reset_request: PasswordReset) -> bool:
        """Request password reset."""
        user = await self.repository.get_user_by_email(reset_request.email)
        if not user:
            # Don't reveal if email exists or not
            return True
        
        # Generate reset token
        reset_token = create_password_reset_token(user.email)
        
        # TODO: Send reset email with token
        # In a real implementation, you would send an email here
        
        return True
    
    async def confirm_password_reset(self, reset_confirm: PasswordResetConfirm) -> bool:
        """Confirm password reset with token."""
        # Verify token
        email = verify_password_reset_token(reset_confirm.token)
        if not email:
            raise AuthenticationError("Invalid or expired reset token")
        
        # Get user
        user = await self.repository.get_user_by_email(email)
        if not user:
            raise NotFoundError("User not found")
        
        # Validate new password
        try:
            validate_password(reset_confirm.new_password)
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Hash new password
        new_password_hash = get_password_hash(reset_confirm.new_password)
        
        # Update password
        await self.repository.update_user(user.id, {"password_hash": new_password_hash})
        
        return True
    
    async def verify_email(self, verification_request: EmailVerificationRequest) -> bool:
        """Verify user email."""
        # Verify token
        email = verify_email_verification_token(verification_request.token)
        if not email:
            raise AuthenticationError("Invalid or expired verification token")
        
        # Get user
        user = await self.repository.get_user_by_email(email)
        if not user:
            raise NotFoundError("User not found")
        
        # Update verification status
        await self.repository.update_user(user.id, {"is_verified": True})
        
        return True
    
    async def resend_verification(self, resend_request: ResendVerificationRequest) -> bool:
        """Resend email verification."""
        user = await self.repository.get_user_by_email(resend_request.email)
        if not user:
            # Don't reveal if email exists or not
            return True
        
        if user.is_verified:
            return True  # Already verified
        
        # Generate verification token
        verification_token = create_email_verification_token(user.email)
        
        # TODO: Send verification email with token
        # In a real implementation, you would send an email here
        
        return True
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_inactive: bool = False
    ) -> List[UserResponse]:
        """List users with filtering and sorting."""
        users = await self.repository.list_users(
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            include_inactive=include_inactive
        )
        
        return [UserResponse.model_validate(user) for user in users]
    
    async def get_paginated_users(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_inactive: bool = False
    ) -> Page[UserResponse]:
        """Get paginated users."""
        page_result = await self.repository.get_paginated_users(
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            include_inactive=include_inactive
        )
        
        # Convert users to response models
        user_responses = [UserResponse.model_validate(user) for user in page_result.items]
        
        return Page(
            items=user_responses,
            page_info=page_result.page_info
        )
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user."""
        return await self.repository.delete_user(user_id)
    
    # Role management
    async def create_role(self, role_data: RoleCreate) -> RoleResponse:
        """Create a new role."""
        # Check if role name already exists
        if await self.repository.get_role_by_name(role_data.name):
            raise ConflictError(f"Role '{role_data.name}' already exists")
        
        # Create role
        role_dict = role_data.model_dump()
        role = await self.repository.create_role(role_dict)
        
        return RoleResponse.model_validate(role)
    
    async def get_role(self, role_id: UUID) -> Optional[RoleResponse]:
        """Get role by ID."""
        role = await self.repository.get_role_by_id(role_id)
        if not role:
            return None
        
        return RoleResponse.model_validate(role)
    
    async def list_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[RoleResponse]:
        """List roles."""
        roles = await self.repository.list_roles(
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
        
        return [RoleResponse.model_validate(role) for role in roles]
    
    async def update_role(self, role_id: UUID, update_data: RoleUpdate) -> RoleResponse:
        """Update role."""
        role = await self.repository.get_role_by_id(role_id)
        if not role:
            raise NotFoundError("Role not found")
        
        # Check name uniqueness if updating name
        if update_data.name and update_data.name != role.name:
            if await self.repository.get_role_by_name(update_data.name):
                raise ConflictError(f"Role '{update_data.name}' already exists")
        
        # Update role
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_role = await self.repository.update_role(role_id, update_dict)
        
        return RoleResponse.model_validate(updated_role)
    
    async def delete_role(self, role_id: UUID) -> bool:
        """Delete role."""
        return await self.repository.delete_role(role_id)
    
    # Permission management
    async def create_permission(self, permission_data: PermissionCreate) -> PermissionResponse:
        """Create a new permission."""
        # Check if permission already exists
        if await self.repository.get_permission_by_resource_action(
            permission_data.resource, permission_data.action
        ):
            raise ConflictError(
                f"Permission '{permission_data.resource}:{permission_data.action}' already exists"
            )
        
        # Create permission
        permission_dict = permission_data.model_dump()
        permission = await self.repository.create_permission(permission_dict)
        
        return PermissionResponse.model_validate(permission)
    
    async def get_permission(self, permission_id: UUID) -> Optional[PermissionResponse]:
        """Get permission by ID."""
        permission = await self.repository.get_permission_by_id(permission_id)
        if not permission:
            return None
        
        return PermissionResponse.model_validate(permission)
    
    async def list_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[PermissionResponse]:
        """List permissions."""
        permissions = await self.repository.list_permissions(
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
        
        return [PermissionResponse.model_validate(perm) for perm in permissions]
    
    async def update_permission(self, permission_id: UUID, update_data: PermissionUpdate) -> PermissionResponse:
        """Update permission."""
        permission = await self.repository.get_permission_by_id(permission_id)
        if not permission:
            raise NotFoundError("Permission not found")
        
        # Check uniqueness if updating resource or action
        if (update_data.resource and update_data.resource != permission.resource) or \
           (update_data.action and update_data.action != permission.action):
            resource = update_data.resource or permission.resource
            action = update_data.action or permission.action
            
            if await self.repository.get_permission_by_resource_action(resource, action):
                raise ConflictError(f"Permission '{resource}:{action}' already exists")
        
        # Update permission
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_permission = await self.repository.update_permission(permission_id, update_dict)
        
        return PermissionResponse.model_validate(updated_permission)
    
    async def delete_permission(self, permission_id: UUID) -> bool:
        """Delete permission."""
        return await self.repository.delete_permission(permission_id)
    
    # User-Role management
    async def assign_role_to_user(self, assignment: UserRoleAssignment) -> bool:
        """Assign role to user."""
        # Verify user exists
        user = await self.repository.get_user_by_id(assignment.user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Verify role exists
        role = await self.repository.get_role_by_id(assignment.role_id)
        if not role:
            raise NotFoundError("Role not found")
        
        # Assign role
        success = await self.repository.assign_role_to_user(assignment.user_id, assignment.role_id)
        if not success:
            raise ConflictError("Role is already assigned to user")
        
        return True
    
    async def remove_role_from_user(self, assignment: UserRoleAssignment) -> bool:
        """Remove role from user."""
        return await self.repository.remove_role_from_user(assignment.user_id, assignment.role_id)
    
    async def get_user_permissions(self, user_id: UUID) -> UserPermissionsResponse:
        """Get user with their roles and permissions."""
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        roles = await self.repository.get_user_roles(user_id)
        permissions = await self.repository.get_user_permissions(user_id)
        
        return UserPermissionsResponse(
            user=UserResponse.model_validate(user),
            roles=[RoleResponse.model_validate(role) for role in roles],
            permissions=[PermissionResponse.model_validate(perm) for perm in permissions]
        )
    
    # Role-Permission management
    async def assign_permission_to_role(self, assignment: RolePermissionAssignment) -> bool:
        """Assign permission to role."""
        # Verify role exists
        role = await self.repository.get_role_by_id(assignment.role_id)
        if not role:
            raise NotFoundError("Role not found")
        
        # Verify permission exists
        permission = await self.repository.get_permission_by_id(assignment.permission_id)
        if not permission:
            raise NotFoundError("Permission not found")
        
        # Assign permission
        success = await self.repository.assign_permission_to_role(
            assignment.role_id, assignment.permission_id
        )
        if not success:
            raise ConflictError("Permission is already assigned to role")
        
        return True
    
    async def remove_permission_from_role(self, assignment: RolePermissionAssignment) -> bool:
        """Remove permission from role."""
        return await self.repository.remove_permission_from_role(
            assignment.role_id, assignment.permission_id
        )
    
    async def get_role_permissions(self, role_id: UUID) -> List[PermissionResponse]:
        """Get permissions for a role."""
        role = await self.repository.get_role_by_id(role_id)
        if not role:
            raise NotFoundError("Role not found")
        
        permissions = await self.repository.get_role_permissions(role_id)
        return [PermissionResponse.model_validate(perm) for perm in permissions]