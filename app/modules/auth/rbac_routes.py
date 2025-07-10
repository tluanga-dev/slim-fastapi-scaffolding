"""
Enhanced RBAC API Routes

This module provides API endpoints for advanced RBAC functionality including:
- Permission dependency validation
- User type management
- Risk-based permission checking
- Audit logging
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from uuid import UUID

from .rbac_service import RBACService
from .schemas import (
    PermissionCategoryResponse, EnhancedPermissionResponse, PermissionDependencyResponse,
    PermissionValidationRequest, PermissionValidationResponse,
    PermissionGrantRequest, PermissionGrantResponse,
    PermissionCanGrantRequest, PermissionCanGrantResponse,
    PermissionRevokeRequest, PermissionRevokeResponse,
    PermissionCheckRequest, PermissionCheckResponse,
    UserTypeElevationRequest, UserTypeElevationResponse,
    EnhancedUserResponse, EnhancedRoleResponse,
    UserAllPermissionsResponse, RBACauditlogResponse, RBACauditlogRequest,
    RoleHierarchyRequest, RoleHierarchyResponse, RoleHierarchyInfo,
    RoleInheritedPermissionsResponse, PermissionSource,
    UserPermissionsWithHierarchyResponse, TemporaryPermissionRequest,
    TemporaryPermissionResponse, TemporaryPermissionInfo,
    UserTemporaryPermissionsResponse, BulkPermissionGrantRequest,
    BulkPermissionRevokeRequest, BulkRoleAssignRequest, BulkRoleRemoveRequest,
    BulkRolePermissionAssignRequest, BulkOperationResult
)
from .constants import UserType
from app.shared.dependencies import get_rbac_service, get_current_user_data
from app.core.security import TokenData
from .rbac_cache import rbac_cache


router = APIRouter(prefix="/rbac", tags=["Enhanced RBAC"])


# Permission Dependencies
@router.get("/permission-categories", response_model=List[PermissionCategoryResponse])
async def get_permission_categories(
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permission categories."""
    categories = await rbac_service.get_permission_categories()
    return [PermissionCategoryResponse.model_validate(cat) for cat in categories]


@router.get("/permission-categories/{category_code}/permissions", response_model=List[EnhancedPermissionResponse])
async def get_permissions_by_category(
    category_code: str,
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get permissions by category code."""
    permissions = await rbac_service.get_permissions_by_category(category_code)
    return [EnhancedPermissionResponse.model_validate(perm) for perm in permissions]


@router.get("/permissions/{permission_id}/dependencies", response_model=List[EnhancedPermissionResponse])
async def get_permission_dependencies(
    permission_id: UUID,
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get dependencies for a permission."""
    dependencies = await rbac_service.get_permission_dependencies(permission_id)
    return [EnhancedPermissionResponse.model_validate(dep) for dep in dependencies]


@router.get("/permissions/{permission_id}/dependents", response_model=List[EnhancedPermissionResponse])
async def get_permission_dependents(
    permission_id: UUID,
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get permissions that depend on the given permission."""
    dependents = await rbac_service.get_permission_dependents(permission_id)
    return [EnhancedPermissionResponse.model_validate(dep) for dep in dependents]


# Permission Validation
@router.post("/validate-permissions", response_model=PermissionValidationResponse)
async def validate_permissions(
    request: PermissionValidationRequest,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Validate that current user has all required dependencies for given permissions."""
    user_id = UUID(current_user["user_id"])
    result = await rbac_service.validate_permission_dependencies(user_id, request.permission_codes)
    return PermissionValidationResponse(**result)


@router.post("/validate-permissions/{user_id}", response_model=PermissionValidationResponse)
async def validate_user_permissions(
    user_id: UUID,
    request: PermissionValidationRequest,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Validate that specified user has all required dependencies for given permissions."""
    # Check if current user can manage target user
    current_user_id = UUID(current_user["user_id"])
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.USER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to validate other user's permissions"
        )
    
    result = await rbac_service.validate_permission_dependencies(user_id, request.permission_codes)
    return PermissionValidationResponse(**result)


# Permission Management
@router.post("/can-grant-permission", response_model=PermissionCanGrantResponse)
async def can_grant_permission(
    request: PermissionCanGrantRequest,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Check if current user can grant a permission to another user."""
    granter_id = UUID(current_user["user_id"])
    result = await rbac_service.can_grant_permission(granter_id, request.grantee_id, request.permission_code)
    return PermissionCanGrantResponse(**result)


@router.post("/grant-permission", response_model=PermissionGrantResponse)
async def grant_permission(
    request: PermissionGrantRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Grant a permission to a user with validation."""
    granter_id = UUID(current_user["user_id"])
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.grant_permission_to_user(
        granter_id=granter_id,
        grantee_id=request.grantee_id,
        permission_code=request.permission_code,
        expires_at=request.expires_at
    )
    
    return PermissionGrantResponse(**result)


@router.post("/revoke-permission", response_model=PermissionRevokeResponse)
async def revoke_permission(
    request: PermissionRevokeRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Revoke a permission from a user with validation."""
    revoker_id = UUID(current_user["user_id"])
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.revoke_permission_from_user(
        revoker_id=revoker_id,
        user_id=request.user_id,
        permission_code=request.permission_code
    )
    
    return PermissionRevokeResponse(**result)


# Permission Checking
@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    request: PermissionCheckRequest,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Check if current user has permission with risk level validation."""
    user_id = UUID(current_user["user_id"])
    result = await rbac_service.check_permission_with_risk_level(
        user_id=user_id,
        permission_code=request.permission_code,
        require_dependencies=request.require_dependencies
    )
    return PermissionCheckResponse(**result)


@router.post("/check-permission/{user_id}", response_model=PermissionCheckResponse)
async def check_user_permission(
    user_id: UUID,
    request: PermissionCheckRequest,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Check if specified user has permission with risk level validation."""
    # Check if current user can manage target user
    current_user_id = UUID(current_user["user_id"])
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.USER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to check other user's permissions"
        )
    
    result = await rbac_service.check_permission_with_risk_level(
        user_id=user_id,
        permission_code=request.permission_code,
        require_dependencies=request.require_dependencies
    )
    return PermissionCheckResponse(**result)


# User Type Management
@router.post("/elevate-user-type", response_model=UserTypeElevationResponse)
async def elevate_user_type(
    request: UserTypeElevationRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Elevate user type with validation."""
    elevator_id = UUID(current_user["user_id"])
    
    # Validate new user type
    try:
        new_user_type = UserType(request.new_user_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user type: {request.new_user_type}"
        )
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.elevate_user_type(
        elevator_id=elevator_id,
        target_user_id=request.target_user_id,
        new_user_type=new_user_type
    )
    
    return UserTypeElevationResponse(**result)


# User Permissions
@router.get("/users/{user_id}/all-permissions", response_model=UserAllPermissionsResponse)
async def get_user_all_permissions(
    user_id: UUID,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions for a user (from roles and direct assignments)."""
    current_user_id = UUID(current_user["user_id"])
    
    # Check if user can view other user's permissions
    if current_user_id != user_id:
        if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.USER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view other user's permissions"
            )
    
    # Get user
    user = await rbac_service.repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get roles
    roles = await rbac_service.repository.get_user_roles(user_id)
    
    # Get all permissions
    all_permissions = await rbac_service.get_user_all_permissions(user_id)
    
    # Get direct permissions (not from roles)
    # This would require additional query to separate direct vs role permissions
    direct_permissions = []  # Simplified for now
    
    return UserAllPermissionsResponse(
        user=EnhancedUserResponse.model_validate(user),
        roles=[EnhancedRoleResponse.model_validate(role) for role in roles],
        permissions=[EnhancedPermissionResponse.model_validate(perm) for perm in all_permissions],
        direct_permissions=[EnhancedPermissionResponse.model_validate(perm) for perm in direct_permissions]
    )


@router.get("/users/me/all-permissions", response_model=UserAllPermissionsResponse)
async def get_current_user_all_permissions(
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions for the current user."""
    user_id = UUID(current_user["user_id"])
    return await get_user_all_permissions(user_id, current_user, rbac_service)


# Audit Logging
@router.post("/audit-logs", response_model=List[RBACauditlogResponse])
async def get_rbac_audit_logs(
    request: RBACauditlogRequest,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get RBAC audit logs with filtering."""
    current_user_id = UUID(current_user["user_id"])
    
    # Check if user can view audit logs (typically admin/superadmin only)
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit logs"
        )
    
    logs = await rbac_service.get_rbac_audit_logs(
        user_id=request.user_id,
        action=request.action,
        entity_type=request.entity_type,
        start_time=request.start_time,
        end_time=request.end_time,
        success=request.success,
        limit=request.limit,
        offset=request.offset
    )
    
    return [RBACauditlogResponse.model_validate(log) for log in logs]


@router.get("/audit-logs/me", response_model=List[RBACauditlogResponse])
async def get_current_user_audit_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get audit logs for the current user."""
    user_id = UUID(current_user["user_id"])
    
    logs = await rbac_service.get_rbac_audit_logs(
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    return [RBACauditlogResponse.model_validate(log) for log in logs]


# User Type Capabilities
@router.get("/user-types/can-manage/{target_user_type}")
async def can_manage_user_type(
    target_user_type: str,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Check if current user can manage the specified user type."""
    current_user_id = UUID(current_user["user_id"])
    
    try:
        target_type = UserType(target_user_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user type: {target_user_type}"
        )
    
    can_manage = await rbac_service.can_user_manage_user_type(current_user_id, target_type)
    
    return {
        "can_manage": can_manage,
        "current_user_type": current_user.get("user_type"),
        "target_user_type": target_user_type
    }


# Role Hierarchy Management
@router.get("/roles/{role_id}/hierarchy", response_model=RoleHierarchyInfo)
async def get_role_hierarchy(
    role_id: UUID,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get role hierarchy information including parent and child roles."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can manage roles
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view role hierarchy"
        )
    
    hierarchy_info = await rbac_service.get_role_hierarchy(role_id)
    
    return RoleHierarchyInfo(
        current_role=EnhancedRoleResponse.model_validate(hierarchy_info['current_role']) if hierarchy_info['current_role'] else None,
        parent_roles=[EnhancedRoleResponse.model_validate(role) for role in hierarchy_info['parent_roles']],
        child_roles=[EnhancedRoleResponse.model_validate(role) for role in hierarchy_info['child_roles']]
    )


@router.post("/roles/hierarchy", response_model=RoleHierarchyResponse)
async def add_role_hierarchy(
    request: RoleHierarchyRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Add a parent-child relationship between roles."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can manage roles
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage role hierarchy"
        )
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.add_role_hierarchy(
        parent_role_id=request.parent_role_id,
        child_role_id=request.child_role_id,
        inherit_permissions=request.inherit_permissions
    )
    
    # Log the action
    await rbac_service.log_rbac_action(
        user_id=current_user_id,
        action='ADD_ROLE_HIERARCHY',
        entity_type='ROLE_HIERARCHY',
        entity_id=request.child_role_id,
        changes={
            'parent_role_id': str(request.parent_role_id),
            'child_role_id': str(request.child_role_id),
            'inherit_permissions': request.inherit_permissions
        },
        ip_address=ip_address,
        user_agent=user_agent,
        success=result['success'],
        error_message=result['message'] if not result['success'] else None
    )
    
    return RoleHierarchyResponse(**result)


@router.delete("/roles/hierarchy", response_model=RoleHierarchyResponse)
async def remove_role_hierarchy(
    request: RoleHierarchyRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Remove a parent-child relationship between roles."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can manage roles
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage role hierarchy"
        )
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.remove_role_hierarchy(
        parent_role_id=request.parent_role_id,
        child_role_id=request.child_role_id
    )
    
    # Log the action
    await rbac_service.log_rbac_action(
        user_id=current_user_id,
        action='REMOVE_ROLE_HIERARCHY',
        entity_type='ROLE_HIERARCHY',
        entity_id=request.child_role_id,
        changes={
            'parent_role_id': str(request.parent_role_id),
            'child_role_id': str(request.child_role_id)
        },
        ip_address=ip_address,
        user_agent=user_agent,
        success=result['success'],
        error_message=result['message'] if not result['success'] else None
    )
    
    return RoleHierarchyResponse(**result)


@router.get("/roles/{role_id}/inherited-permissions", response_model=RoleInheritedPermissionsResponse)
async def get_role_inherited_permissions(
    role_id: UUID,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions for a role including inherited permissions from parent roles."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can manage roles
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view role permissions"
        )
    
    # Get role
    role = await rbac_service.repository.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Get direct permissions
    direct_permissions = await rbac_service.repository.get_role_permissions(role_id)
    
    # Get all permissions (including inherited)
    all_permissions = await rbac_service.get_role_inherited_permissions(role_id)
    
    # Calculate inherited permissions
    direct_permission_ids = {perm.id for perm in direct_permissions}
    inherited_permissions = [perm for perm in all_permissions if perm.id not in direct_permission_ids]
    
    return RoleInheritedPermissionsResponse(
        role_id=role_id,
        role_name=role.name,
        direct_permissions=[EnhancedPermissionResponse.model_validate(perm) for perm in direct_permissions],
        inherited_permissions=[EnhancedPermissionResponse.model_validate(perm) for perm in inherited_permissions],
        all_permissions=[EnhancedPermissionResponse.model_validate(perm) for perm in all_permissions]
    )


@router.get("/users/{user_id}/permissions-with-hierarchy", response_model=UserPermissionsWithHierarchyResponse)
async def get_user_permissions_with_hierarchy(
    user_id: UUID,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions for a user including role hierarchy inheritance."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can view other user's permissions
    if current_user_id != user_id:
        if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.USER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view other user's permissions"
            )
    
    # Get user permissions with hierarchy
    permissions_info = await rbac_service.get_user_all_permissions_with_hierarchy(user_id)
    
    # Convert to response format
    role_permissions = {}
    for role_name, perms in permissions_info['role_permissions'].items():
        role_permissions[role_name] = [EnhancedPermissionResponse.model_validate(perm) for perm in perms]
    
    all_permissions = []
    for perm_info in permissions_info['all_permissions']:
        all_permissions.append(PermissionSource(
            permission=EnhancedPermissionResponse.model_validate(perm_info['permission']),
            source=perm_info['source'],
            source_details=perm_info['source_details']
        ))
    
    return UserPermissionsWithHierarchyResponse(
        user_id=user_id,
        direct_permissions=[EnhancedPermissionResponse.model_validate(perm) for perm in permissions_info['direct_permissions']],
        role_permissions=role_permissions,
        all_permissions=all_permissions
    )


@router.get("/users/me/permissions-with-hierarchy", response_model=UserPermissionsWithHierarchyResponse)
async def get_current_user_permissions_with_hierarchy(
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all permissions for the current user including role hierarchy inheritance."""
    user_id = UUID(current_user.user_id)
    return await get_user_permissions_with_hierarchy(user_id, current_user, rbac_service)


# Temporary Permissions Management
@router.post("/temporary-permissions/grant", response_model=TemporaryPermissionResponse)
async def grant_temporary_permission(
    request: TemporaryPermissionRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Grant a temporary permission to a user with expiration."""
    granter_id = UUID(current_user.user_id)
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.grant_temporary_permission(
        granter_id=granter_id,
        grantee_id=request.grantee_id,
        permission_code=request.permission_code,
        expires_at=request.expires_at,
        reason=request.reason
    )
    
    return TemporaryPermissionResponse(**result)


@router.get("/users/{user_id}/temporary-permissions", response_model=UserTemporaryPermissionsResponse)
async def get_user_temporary_permissions(
    user_id: UUID,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all temporary permissions for a user."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can view other user's permissions
    if current_user_id != user_id:
        if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.USER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view other user's temporary permissions"
            )
    
    permissions_info = await rbac_service.get_user_temporary_permissions(user_id)
    
    # Convert to response format
    temporary_permissions = []
    for perm_info in permissions_info['temporary_permissions']:
        temporary_permissions.append(TemporaryPermissionInfo(
            permission=EnhancedPermissionResponse.model_validate(perm_info['permission']),
            granted_by=perm_info['granted_by'],
            granted_at=perm_info['granted_at'],
            expires_at=perm_info['expires_at'],
            reason=perm_info['reason']
        ))
    
    return UserTemporaryPermissionsResponse(
        user_id=user_id,
        temporary_permissions=temporary_permissions,
        active_count=permissions_info['active_count'],
        expired_count=permissions_info['expired_count']
    )


@router.get("/users/me/temporary-permissions", response_model=UserTemporaryPermissionsResponse)
async def get_current_user_temporary_permissions(
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get all temporary permissions for the current user."""
    user_id = UUID(current_user.user_id)
    return await get_user_temporary_permissions(user_id, current_user, rbac_service)


@router.post("/temporary-permissions/revoke", response_model=PermissionRevokeResponse)
async def revoke_temporary_permission(
    request: PermissionRevokeRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Revoke a temporary permission from a user."""
    revoker_id = UUID(current_user.user_id)
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.revoke_temporary_permission(
        revoker_id=revoker_id,
        user_id=request.user_id,
        permission_code=request.permission_code
    )
    
    return PermissionRevokeResponse(**result)


@router.post("/temporary-permissions/cleanup")
async def cleanup_expired_permissions(
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Clean up expired temporary permissions (admin only)."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can perform system operations
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to perform system cleanup"
        )
    
    result = await rbac_service.cleanup_expired_permissions()
    return result


@router.post("/temporary-permissions/extend")
async def extend_temporary_permission(
    user_id: UUID,
    permission_code: str,
    new_expires_at: datetime,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Extend the expiration time of a temporary permission."""
    extender_id = UUID(current_user.user_id)
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.extend_temporary_permission(
        extender_id=extender_id,
        user_id=user_id,
        permission_code=permission_code,
        new_expires_at=new_expires_at
    )
    
    return result


# Cache Management Endpoints
@router.get("/cache/stats")
async def get_cache_stats(
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get RBAC cache statistics (admin only)."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can view cache stats
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view cache statistics"
        )
    
    stats = await rbac_cache.get_cache_stats()
    return stats


@router.get("/cache/health")
async def get_cache_health(
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Get RBAC cache health status (admin only)."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can view cache health
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view cache health"
        )
    
    health = await rbac_cache.health_check()
    return health


@router.post("/cache/clear")
async def clear_cache(
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Clear all RBAC cache (admin only)."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can clear cache
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to clear cache"
        )
    
    result = await rbac_cache.clear_all_cache()
    
    # Log the action
    await rbac_service.log_rbac_action(
        user_id=current_user_id,
        action='CLEAR_RBAC_CACHE',
        entity_type='SYSTEM',
        entity_id=None,
        changes=result,
        success=result['success']
    )
    
    return result


@router.post("/cache/warm/user/{user_id}")
async def warm_user_cache(
    user_id: UUID,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Warm cache for a specific user (admin only)."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can warm cache
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to warm cache"
        )
    
    success = await rbac_cache.warm_user_permissions_cache(user_id, rbac_service)
    
    return {
        'success': success,
        'message': f'Cache warming for user {user_id} {"completed" if success else "failed"}',
        'user_id': str(user_id)
    }


@router.post("/cache/invalidate/user/{user_id}")
async def invalidate_user_cache(
    user_id: UUID,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Invalidate cache for a specific user (admin only)."""
    current_user_id = UUID(current_user.user_id)
    
    # Check if user can invalidate cache
    if not await rbac_service.can_user_manage_user_type(current_user_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to invalidate cache"
        )
    
    results = await rbac_cache.invalidate_user_related_cache(user_id)
    
    # Log the action
    await rbac_service.log_rbac_action(
        user_id=current_user_id,
        action='INVALIDATE_USER_CACHE',
        entity_type='USER',
        entity_id=user_id,
        changes=results,
        success=any(results.values())
    )
    
    return {
        'success': any(results.values()),
        'message': f'Cache invalidation for user {user_id} completed',
        'results': results,
        'user_id': str(user_id)
    }


# Bulk Operations
@router.post("/bulk/permissions/grant", response_model=BulkOperationResult)
async def bulk_grant_permissions(
    request: BulkPermissionGrantRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Grant multiple permissions to a user at once."""
    granter_id = UUID(current_user.user_id)
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.bulk_grant_permissions(
        granter_id=granter_id,
        grantee_id=request.grantee_id,
        permission_codes=request.permission_codes,
        expires_at=request.expires_at
    )
    
    return BulkOperationResult(
        success=result['success'],
        total=result['total'],
        success_count=result['granted_count'],
        failed_count=result['failed_count'],
        successful_items=result['granted'],
        failed_items=result['failed'],
        message=f"Bulk permission grant: {result['granted_count']} granted, {result['failed_count']} failed"
    )


@router.post("/bulk/permissions/revoke", response_model=BulkOperationResult)
async def bulk_revoke_permissions(
    request: BulkPermissionRevokeRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Revoke multiple permissions from a user at once."""
    revoker_id = UUID(current_user.user_id)
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.bulk_revoke_permissions(
        revoker_id=revoker_id,
        user_id=request.user_id,
        permission_codes=request.permission_codes
    )
    
    return BulkOperationResult(
        success=result['success'],
        total=result['total'],
        success_count=result['revoked_count'],
        failed_count=result['failed_count'],
        successful_items=result['revoked'],
        failed_items=result['failed'],
        message=f"Bulk permission revoke: {result['revoked_count']} revoked, {result['failed_count']} failed"
    )


@router.post("/bulk/roles/assign", response_model=BulkOperationResult)
async def bulk_assign_roles(
    request: BulkRoleAssignRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Assign multiple roles to a user at once."""
    assigner_id = UUID(current_user.user_id)
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.bulk_assign_roles_to_user(
        assigner_id=assigner_id,
        user_id=request.user_id,
        role_ids=request.role_ids
    )
    
    return BulkOperationResult(
        success=result['success'],
        total=result['total'],
        success_count=result['assigned_count'],
        failed_count=result['failed_count'],
        successful_items=result['assigned'],
        failed_items=result['failed'],
        message=f"Bulk role assignment: {result['assigned_count']} assigned, {result['failed_count']} failed"
    )


@router.post("/bulk/roles/remove", response_model=BulkOperationResult)
async def bulk_remove_roles(
    request: BulkRoleRemoveRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Remove multiple roles from a user at once."""
    remover_id = UUID(current_user.user_id)
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.bulk_remove_roles_from_user(
        remover_id=remover_id,
        user_id=request.user_id,
        role_ids=request.role_ids
    )
    
    return BulkOperationResult(
        success=result['success'],
        total=result['total'],
        success_count=result['removed_count'],
        failed_count=result['failed_count'],
        successful_items=result['removed'],
        failed_items=result['failed'],
        message=f"Bulk role removal: {result['removed_count']} removed, {result['failed_count']} failed"
    )


@router.post("/bulk/roles/permissions/assign", response_model=BulkOperationResult)
async def bulk_assign_permissions_to_role(
    request: BulkRolePermissionAssignRequest,
    http_request: Request,
    current_user: TokenData = Depends(get_current_user_data),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Assign multiple permissions to a role at once."""
    assigner_id = UUID(current_user.user_id)
    
    # Check if user can manage roles
    if not await rbac_service.can_user_manage_user_type(assigner_id, UserType.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to assign permissions to roles"
        )
    
    # Extract IP and user agent for audit logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    result = await rbac_service.bulk_assign_permissions_to_role(
        assigner_id=assigner_id,
        role_id=request.role_id,
        permission_codes=request.permission_codes
    )
    
    return BulkOperationResult(
        success=result['success'],
        total=result['total'],
        success_count=result['assigned_count'],
        failed_count=result['failed_count'],
        successful_items=result['assigned'],
        failed_items=result['failed'],
        message=f"Bulk role permission assignment: {result['assigned_count']} assigned, {result['failed_count']} failed"
    )