from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from src.infrastructure.database.session import get_db
from src.infrastructure.repositories.user_repository import UserRepositoryImpl
from src.domain.value_objects.email import Email
from src.core.security import verify_password, create_access_token

router = APIRouter()


class SimpleLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SimpleLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str
    user_name: str


@router.post("/login-simple", response_model=SimpleLoginResponse)
async def login_simple(
    login_data: SimpleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Simple login endpoint for testing."""
    try:
        # Get user
        user_repo = UserRepositoryImpl(db)
        email = Email(login_data.email)
        user = await user_repo.get_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Create simple token
        access_token_data = {
            "sub": user.email.value,
            "user_id": str(user.id)
        }
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(minutes=30)
        )
        
        return SimpleLoginResponse(
            access_token=access_token,
            user_email=user.email.value,
            user_name=user.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )