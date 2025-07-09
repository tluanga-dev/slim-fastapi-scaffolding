from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    code: str = Field(..., description="Permission code")
    name: str = Field(..., description="Permission name")
    description: Optional[str] = Field(None, description="Permission description")


class PermissionResponse(PermissionBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str = Field(..., description="Role name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Role description", max_length=500)


class RoleCreate(RoleBase):
    permission_codes: Optional[List[str]] = Field(default=[], description="List of permission codes to assign to the role")


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Role name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Role description", max_length=500)
    permission_codes: Optional[List[str]] = Field(None, description="List of permission codes to assign to the role")
    is_active: Optional[bool] = Field(None, description="Whether the role is active")


class RoleResponse(RoleBase):
    id: UUID
    permissions: List[PermissionResponse] = Field(default=[], description="Permissions assigned to this role")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total: int
    page: int
    per_page: int


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Permission name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Permission description", max_length=500)
    is_active: Optional[bool] = Field(None, description="Whether the permission is active")


class PermissionListResponse(BaseModel):
    permissions: List[PermissionResponse]
    total: int
    page: int
    per_page: int