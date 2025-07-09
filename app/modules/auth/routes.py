from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError, AuthenticationError
from app.shared.dependencies import get_session, get_current_user_data, PermissionChecker, RoleChecker
from app.core.security import TokenData
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import (
    UserRegister, UserLogin, UserResponse, UserUpdate, PasswordChange,
    PasswordReset, PasswordResetConfirm, TokenResponse, RefreshTokenRequest,
    RoleCreate, RoleUpdate, RoleResponse, PermissionCreate, PermissionUpdate,
    PermissionResponse, UserRoleAssignment, RolePermissionAssignment,
    UserPermissionsResponse, EmailVerificationRequest, ResendVerificationRequest
)
from app.shared.pagination import Page


router = APIRouter(prefix="/auth", tags=["Authentication"])


# Dependency to get auth service
async def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session)


# Authentication endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        return await service.register_user(user_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    service: AuthService = Depends(get_auth_service)
):
    """Login user."""
    try:
        return await service.login_user(login_data)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/login/form", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    """Login user with form data (for OAuth2PasswordRequestForm compatibility)."""
    try:
        login_data = UserLogin(username=form_data.username, password=form_data.password)
        return await service.login_user(login_data)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service)
):
    """Refresh access token."""
    try:
        return await service.refresh_token(refresh_request)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: TokenData = Depends(get_current_user_data),
    service: AuthService = Depends(get_auth_service)
):
    """Get current user information."""
    try:
        return await service.get_current_user(UUID(current_user.user_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: TokenData = Depends(get_current_user_data),
    service: AuthService = Depends(get_auth_service)
):
    """Update current user information."""
    try:
        return await service.update_user(UUID(current_user.user_id), update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_change: PasswordChange,
    current_user: TokenData = Depends(get_current_user_data),
    service: AuthService = Depends(get_auth_service)
):
    """Change user password."""
    try:
        await service.change_password(UUID(current_user.user_id), password_change)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    reset_request: PasswordReset,
    service: AuthService = Depends(get_auth_service)
):
    """Request password reset."""
    await service.request_password_reset(reset_request)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    service: AuthService = Depends(get_auth_service)
):
    """Confirm password reset."""
    try:
        await service.confirm_password_reset(reset_confirm)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    verification_request: EmailVerificationRequest,
    service: AuthService = Depends(get_auth_service)
):
    """Verify email address."""
    try:
        await service.verify_email(verification_request)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
async def resend_verification(
    resend_request: ResendVerificationRequest,
    service: AuthService = Depends(get_auth_service)
):
    """Resend email verification."""
    await service.resend_verification(resend_request)


@router.get("/me/permissions", response_model=UserPermissionsResponse)
async def get_current_user_permissions(
    current_user: TokenData = Depends(get_current_user_data),
    service: AuthService = Depends(get_auth_service)
):
    """Get current user's roles and permissions."""
    try:
        return await service.get_user_permissions(UUID(current_user.user_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# User management endpoints (admin only)
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    search: Optional[str] = Query(None, description="Search term"),
    status: Optional[str] = Query(None, description="User status filter"),
    role: Optional[str] = Query(None, description="User role filter"),
    include_inactive: bool = Query(False, description="Include inactive users"),
    current_user: TokenData = Depends(PermissionChecker("users:read")),
    service: AuthService = Depends(get_auth_service)
):
    """List users (admin only)."""
    filters = {}
    if search:
        filters["search"] = search
    if status:
        filters["status"] = status
    if role:
        filters["role"] = role
    
    return await service.list_users(
        skip=skip,
        limit=limit,
        filters=filters,
        include_inactive=include_inactive
    )


@router.get("/users/paginated", response_model=Page[UserResponse])
async def get_paginated_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    status: Optional[str] = Query(None, description="User status filter"),
    role: Optional[str] = Query(None, description="User role filter"),
    include_inactive: bool = Query(False, description="Include inactive users"),
    current_user: TokenData = Depends(PermissionChecker("users:read")),
    service: AuthService = Depends(get_auth_service)
):
    """Get paginated users (admin only)."""
    filters = {}
    if search:
        filters["search"] = search
    if status:
        filters["status"] = status
    if role:
        filters["role"] = role
    
    return await service.get_paginated_users(
        page=page,
        page_size=page_size,
        filters=filters,
        include_inactive=include_inactive
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: TokenData = Depends(PermissionChecker("users:read")),
    service: AuthService = Depends(get_auth_service)
):
    """Get user by ID (admin only)."""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    update_data: UserUpdate,
    current_user: TokenData = Depends(PermissionChecker("users:update")),
    service: AuthService = Depends(get_auth_service)
):
    """Update user (admin only)."""
    try:
        return await service.update_user(user_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: TokenData = Depends(PermissionChecker("users:delete")),
    service: AuthService = Depends(get_auth_service)
):
    """Delete user (admin only)."""
    success = await service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: UUID,
    current_user: TokenData = Depends(PermissionChecker("users:read")),
    service: AuthService = Depends(get_auth_service)
):
    """Get user's roles and permissions (admin only)."""
    try:
        return await service.get_user_permissions(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Role management endpoints (admin only)
@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: TokenData = Depends(PermissionChecker("roles:create")),
    service: AuthService = Depends(get_auth_service)
):
    """Create a new role (admin only)."""
    try:
        return await service.create_role(role_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    include_inactive: bool = Query(False, description="Include inactive roles"),
    current_user: TokenData = Depends(PermissionChecker("roles:read")),
    service: AuthService = Depends(get_auth_service)
):
    """List roles (admin only)."""
    return await service.list_roles(
        skip=skip,
        limit=limit,
        include_inactive=include_inactive
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    current_user: TokenData = Depends(PermissionChecker("roles:read")),
    service: AuthService = Depends(get_auth_service)
):
    """Get role by ID (admin only)."""
    role = await service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    update_data: RoleUpdate,
    current_user: TokenData = Depends(PermissionChecker("roles:update")),
    service: AuthService = Depends(get_auth_service)
):
    """Update role (admin only)."""
    try:
        return await service.update_role(role_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    current_user: TokenData = Depends(PermissionChecker("roles:delete")),
    service: AuthService = Depends(get_auth_service)
):
    """Delete role (admin only)."""
    success = await service.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")


@router.get("/roles/{role_id}/permissions", response_model=List[PermissionResponse])
async def get_role_permissions(
    role_id: UUID,
    current_user: TokenData = Depends(PermissionChecker("roles:read")),
    service: AuthService = Depends(get_auth_service)
):
    """Get role permissions (admin only)."""
    try:
        return await service.get_role_permissions(role_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Permission management endpoints (admin only)
@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: TokenData = Depends(PermissionChecker("permissions:create")),
    service: AuthService = Depends(get_auth_service)
):
    """Create a new permission (admin only)."""
    try:
        return await service.create_permission(permission_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    include_inactive: bool = Query(False, description="Include inactive permissions"),
    current_user: TokenData = Depends(PermissionChecker("permissions:read")),
    service: AuthService = Depends(get_auth_service)
):
    """List permissions (admin only)."""
    return await service.list_permissions(
        skip=skip,
        limit=limit,
        include_inactive=include_inactive
    )


@router.get("/permissions/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: UUID,
    current_user: TokenData = Depends(PermissionChecker("permissions:read")),
    service: AuthService = Depends(get_auth_service)
):
    """Get permission by ID (admin only)."""
    permission = await service.get_permission(permission_id)
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    
    return permission


@router.put("/permissions/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: UUID,
    update_data: PermissionUpdate,
    current_user: TokenData = Depends(PermissionChecker("permissions:update")),
    service: AuthService = Depends(get_auth_service)
):
    """Update permission (admin only)."""
    try:
        return await service.update_permission(permission_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: UUID,
    current_user: TokenData = Depends(PermissionChecker("permissions:delete")),
    service: AuthService = Depends(get_auth_service)
):
    """Delete permission (admin only)."""
    success = await service.delete_permission(permission_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")


# User-Role assignment endpoints (admin only)
@router.post("/user-roles", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role_to_user(
    assignment: UserRoleAssignment,
    current_user: TokenData = Depends(PermissionChecker("users:update")),
    service: AuthService = Depends(get_auth_service)
):
    """Assign role to user (admin only)."""
    try:
        await service.assign_role_to_user(assignment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/user-roles", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    assignment: UserRoleAssignment,
    current_user: TokenData = Depends(PermissionChecker("users:update")),
    service: AuthService = Depends(get_auth_service)
):
    """Remove role from user (admin only)."""
    success = await service.remove_role_from_user(assignment)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")


# Role-Permission assignment endpoints (admin only)
@router.post("/role-permissions", status_code=status.HTTP_204_NO_CONTENT)
async def assign_permission_to_role(
    assignment: RolePermissionAssignment,
    current_user: TokenData = Depends(PermissionChecker("roles:update")),
    service: AuthService = Depends(get_auth_service)
):
    """Assign permission to role (admin only)."""
    try:
        await service.assign_permission_to_role(assignment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/role-permissions", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_role(
    assignment: RolePermissionAssignment,
    current_user: TokenData = Depends(PermissionChecker("roles:update")),
    service: AuthService = Depends(get_auth_service)
):
    """Remove permission from role (admin only)."""
    success = await service.remove_permission_from_role(assignment)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")


# Health check endpoint
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for authentication service."""
    return {"status": "healthy", "service": "authentication"}