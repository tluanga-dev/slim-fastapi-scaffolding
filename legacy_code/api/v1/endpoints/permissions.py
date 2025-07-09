from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.role import (
    PermissionResponse,
    PermissionCreate, 
    PermissionUpdate,
    PermissionListResponse
)
from src.api.v1.dependencies.auth import get_current_active_user, require_permissions
from src.infrastructure.database.session import get_db
from src.infrastructure.repositories.permission_repository import PermissionRepositoryImpl
from src.domain.entities.user import User

router = APIRouter()


def _permission_to_response(permission) -> PermissionResponse:
    """Convert Permission entity to PermissionResponse"""
    return PermissionResponse(
        id=permission.id,
        code=permission.code,
        name=permission.name,
        description=permission.description,
        is_active=permission.is_active,
        created_at=permission.created_at,
        updated_at=permission.updated_at
    )


@router.get("/", response_model=PermissionListResponse)
async def list_permissions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(True, description="Only return active permissions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["USER_VIEW", "SETTINGS_VIEW"]))
):
    """List all permissions"""
    try:
        permission_repo = PermissionRepositoryImpl(db)
        
        permissions = await permission_repo.list(skip=skip, limit=limit)
        
        if active_only:
            permissions = [p for p in permissions if p.is_active]
        
        permission_responses = [_permission_to_response(permission) for permission in permissions]
        
        return PermissionListResponse(
            permissions=permission_responses,
            total=len(permission_responses),
            page=skip // limit + 1,
            per_page=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve permissions")


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["USER_VIEW", "SETTINGS_VIEW"]))
):
    """Get a specific permission by ID"""
    try:
        permission_repo = PermissionRepositoryImpl(db)
        
        permission = await permission_repo.get(permission_id)
        if not permission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
        
        return _permission_to_response(permission)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve permission")


@router.get("/code/{permission_code}", response_model=PermissionResponse)
async def get_permission_by_code(
    permission_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["USER_VIEW", "SETTINGS_VIEW"]))
):
    """Get a specific permission by code"""
    try:
        permission_repo = PermissionRepositoryImpl(db)
        
        permission = await permission_repo.get_by_code(permission_code)
        if not permission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Permission with code '{permission_code}' not found")
        
        return _permission_to_response(permission)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve permission")