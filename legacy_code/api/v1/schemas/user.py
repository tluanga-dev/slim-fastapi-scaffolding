from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_superuser: Optional[bool] = None


class UserInDB(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    created_by: Optional[str]
    updated_by: Optional[str]

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    pass