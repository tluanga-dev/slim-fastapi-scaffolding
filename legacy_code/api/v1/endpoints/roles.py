from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.role import (
    RoleResponse, 
    RoleCreate, 
    RoleUpdate,
    RoleListResponse
)
from src.api.v1.dependencies.auth import get_current_active_user, require_permissions
from src.infrastructure.database.session import get_db
from src.infrastructure.repositories.role_repository import RoleRepositoryImpl
from src.infrastructure.repositories.permission_repository import PermissionRepositoryImpl
from src.application.use_cases.role.create_role import CreateRoleUseCase
from src.application.use_cases.role.update_role import UpdateRoleUseCase
from src.application.use_cases.role.get_role import GetRoleUseCase
from src.application.use_cases.role.list_roles import ListRolesUseCase
from src.application.use_cases.role.delete_role import DeleteRoleUseCase
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.domain.entities.user import User

router = APIRouter()


def _role_to_response(role) -> RoleResponse:
    """Convert Role entity to RoleResponse"""
    from src.api.v1.schemas.role import PermissionResponse
    
    permissions = [
        PermissionResponse(
            id=perm.id,
            code=perm.code,
            name=perm.name,
            description=perm.description,
            is_active=perm.is_active,
            created_at=perm.created_at,
            updated_at=perm.updated_at
        )
        for perm in (role.permissions or [])
    ]
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=permissions,
        is_active=role.is_active,
        created_at=role.created_at,
        updated_at=role.updated_at
    )


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["USER_CREATE", "SETTINGS_UPDATE"]))
):
    """Create a new role"""
    try:
        role_repo = RoleRepositoryImpl(db)
        permission_repo = PermissionRepositoryImpl(db)
        use_case = CreateRoleUseCase(role_repo, permission_repo)
        
        role = await use_case.execute(
            name=role_data.name,
            description=role_data.description,
            permission_codes=role_data.permission_codes
        )
        
        return _role_to_response(role)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create role")


@router.get("/", response_model=RoleListResponse)
async def list_roles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(True, description="Only return active roles"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["USER_VIEW", "SETTINGS_VIEW"]))
):
    """List all roles"""
    try:
        role_repo = RoleRepositoryImpl(db)
        use_case = ListRolesUseCase(role_repo)
        
        roles = await use_case.execute(skip=skip, limit=limit, active_only=active_only)
        
        role_responses = [_role_to_response(role) for role in roles]
        
        return RoleListResponse(
            roles=role_responses,
            total=len(role_responses),
            page=skip // limit + 1,
            per_page=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve roles")


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["USER_VIEW", "SETTINGS_VIEW"]))
):
    """Get a specific role by ID"""
    try:
        role_repo = RoleRepositoryImpl(db)
        use_case = GetRoleUseCase(role_repo)
        
        role = await use_case.execute(role_id)
        return _role_to_response(role)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve role")


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["USER_UPDATE", "SETTINGS_UPDATE"]))
):
    """Update a role"""
    try:
        role_repo = RoleRepositoryImpl(db)
        permission_repo = PermissionRepositoryImpl(db)
        use_case = UpdateRoleUseCase(role_repo, permission_repo)
        
        role = await use_case.execute(
            role_id=role_id,
            name=role_data.name,
            description=role_data.description,
            permission_codes=role_data.permission_codes,
            is_active=role_data.is_active
        )
        
        return _role_to_response(role)
        
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update role")


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["USER_DELETE", "SETTINGS_UPDATE"]))
):
    """Delete a role (soft delete)"""
    try:
        role_repo = RoleRepositoryImpl(db)
        user_repo = UserRepositoryImpl(db)
        use_case = DeleteRoleUseCase(role_repo, user_repo)
        
        success = await use_case.execute(role_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete role")