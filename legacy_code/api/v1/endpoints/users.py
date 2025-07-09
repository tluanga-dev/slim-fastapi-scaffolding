from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.schemas.user import UserCreate, UserUpdate, UserResponse
from src.api.v1.dependencies.repositories import get_user_repository
from src.api.v1.dependencies.auth import require_permissions
from src.domain.entities.user import User
from src.application.use_cases.user import (
    CreateUserUseCase,
    GetUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    ListUsersUseCase,
)
from src.core.security import get_password_hash
from src.domain.repositories.user_repository import UserRepository

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(require_permissions(["USER_CREATE"]))
):
    use_case = CreateUserUseCase(user_repo)
    try:
        user = await use_case.execute(
            email=user_data.email,
            name=user_data.name,
            hashed_password=get_password_hash(user_data.password),
            is_superuser=user_data.is_superuser,
        )
        return UserResponse(
            id=user.id,
            email=user.email.value,
            name=user.name,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(require_permissions(["USER_VIEW"]))
):
    use_case = GetUserUseCase(user_repo)
    user = await use_case.execute_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email.value,
        name=user.name,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_active=user.is_active,
        created_by=user.created_by,
        updated_by=user.updated_by,
    )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(require_permissions(["USER_VIEW"]))
):
    use_case = ListUsersUseCase(user_repo)
    users = await use_case.execute(skip=skip, limit=limit, active_only=active_only)
    
    return [
        UserResponse(
            id=user.id,
            email=user.email.value,
            name=user.name,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
        for user in users
    ]


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(require_permissions(["USER_UPDATE"]))
):
    use_case = UpdateUserUseCase(user_repo)
    try:
        user = await use_case.execute(
            user_id=user_id,
            email=user_data.email,
            name=user_data.name,
            hashed_password=get_password_hash(user_data.password) if user_data.password else None,
            is_superuser=user_data.is_superuser,
        )
        return UserResponse(
            id=user.id,
            email=user.email.value,
            name=user.name,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(require_permissions(["USER_DELETE"]))
):
    use_case = DeleteUserUseCase(user_repo)
    try:
        await use_case.execute(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))