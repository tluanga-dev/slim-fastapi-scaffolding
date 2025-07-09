from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List


class CategoryBase(BaseModel):
    """Base schema for category."""
    category_name: str = Field(..., min_length=1, max_length=100)
    parent_category_id: Optional[UUID] = None
    display_order: int = Field(default=0, ge=0)
    
    @field_validator('category_name')
    @classmethod
    def validate_category_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)
    
    @field_validator('category_name')
    @classmethod
    def validate_category_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Category name cannot be empty')
        return v.strip() if v else v


class CategoryResponse(CategoryBase):
    """Schema for category response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    category_path: str
    category_level: int
    is_leaf: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]


class CategoryTree(CategoryResponse):
    """Schema for category with children."""
    children: List["CategoryTree"] = []


class CategoryPath(BaseModel):
    """Value object for category path operations."""
    path: str
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        if not v:
            raise ValueError('Category path cannot be empty')
        return v.strip("/")
    
    def append(self, segment: str) -> "CategoryPath":
        """Append a segment to the path."""
        if not segment:
            raise ValueError("Path segment cannot be empty")
        return CategoryPath(path=f"{self.path}/{segment}")
    
    def parent_path(self) -> Optional["CategoryPath"]:
        """Get the parent path, or None if this is root."""
        segments = self.path.split("/")
        if len(segments) <= 1:
            return None
        return CategoryPath(path="/".join(segments[:-1]))
    
    def get_segments(self) -> List[str]:
        """Get path segments as a list."""
        return self.path.split("/")
    
    def get_level(self) -> int:
        """Get the level (depth) of this path."""
        return len(self.get_segments())


# This is needed for the self-referential type hint in CategoryTree
CategoryTree.model_rebuild()