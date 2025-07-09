from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_access_token, TokenData
from src.infrastructure.database.session import get_db
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.domain.entities.user import User
from src.domain.value_objects.email import Email

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    token_data: TokenData = decode_access_token(token)
    
    user_repo = UserRepositoryImpl(db)
    email = Email(token_data.email)
    user = await user_repo.get_by_email(email)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_permissions(required_permissions: list[str]):
    """Create a dependency that requires specific permissions."""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.is_superuser:
            return current_user
            
        user_permissions = current_user.get_permissions()
        
        # Check if user has any of the required permissions
        has_permission = any(
            perm in user_permissions for perm in required_permissions
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(required_permissions)}"
            )
        
        return current_user
    
    return permission_checker


def require_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require superuser access."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return current_user
