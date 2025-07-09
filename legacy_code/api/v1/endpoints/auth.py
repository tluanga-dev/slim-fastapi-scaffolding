from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    TokenRequest, 
    TokenResponse,
    UserResponse,
    RoleResponse,
    PermissionResponse,
    EffectivePermissionsResponse
)
from src.api.v1.dependencies.auth import get_current_active_user
from src.infrastructure.database.session import get_db
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from src.domain.entities.user import User

router = APIRouter()


def _user_to_response(user: User) -> UserResponse:
    """Convert User entity to UserResponse."""
    role_response = None
    role_permissions = []
    
    if user.role:
        permissions_response = [
            PermissionResponse(
                id=perm.id,
                code=perm.code,
                name=perm.name,
                description=perm.description
            )
            for perm in user.role.permissions
        ]
        role_response = RoleResponse(
            id=user.role.id,
            name=user.role.name,
            description=user.role.description,
            permissions=permissions_response
        )
        role_permissions = [perm.code for perm in user.role.permissions]
    
    # Get effective permissions from user
    all_permissions = list(user.get_permissions())
    direct_permissions = list(user.direct_permissions)
    
    effective_permissions = EffectivePermissionsResponse(
        user_type=user.user_type.value,
        is_superuser=user.is_superuser,
        role_permissions=role_permissions,
        direct_permissions=direct_permissions,
        all_permissions=all_permissions
    )
    
    return UserResponse(
        id=user.id,
        email=user.email.value,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        name=user.name,
        user_type=user.user_type.value,
        is_superuser=user.is_superuser,
        role=role_response,
        location_id=user.location_id,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        direct_permissions=direct_permissions,
        effective_permissions=effective_permissions
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens."""
    user_repo = UserRepositoryImpl(db)
    
    # Create Email value object
    from src.domain.value_objects.email import Email
    email = Email(login_data.email)
    
    user = await user_repo.get_by_email(email)
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Skip updating last login for now to isolate the issue
    # TODO: Re-enable after fixing repository update method
    # try:
    #     user.update_last_login(datetime.utcnow())
    #     await user_repo.update(user)
    # except Exception as e:
    #     # Log error but continue with login
    #     print(f"Warning: Failed to update last login: {e}")
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Get user permissions for JWT token
    permissions = list(user.get_permissions())
    access_token_data = {
        "sub": user.email.value,
        "user_id": str(user.id),
        "permissions": permissions
    }
    access_token = create_access_token(
        data=access_token_data,
        expires_delta=access_token_expires
    )
    
    refresh_token_data = {
        "sub": user.email.value,
        "user_id": str(user.id)
    }
    refresh_token = create_refresh_token(data=refresh_token_data)
    
    return LoginResponse(
        user=_user_to_response(user),
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        payload = verify_token(token_data.refresh_token)
        token_type = payload.get("type")
        
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
            
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        # Get user and verify still active
        user_repo = UserRepositoryImpl(db)
        user = await user_repo.get_by_email(email)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        # Convert set to list for JSON serialization
        permissions = list(user.get_permissions())
        access_token_data = {
            "sub": user.email.value,
            "user_id": str(user.id),
            "permissions": permissions
        }
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return _user_to_response(current_user)


@router.post("/logout")
async def logout():
    """Logout user (client should remove tokens)."""
    return {"message": "Successfully logged out"}
