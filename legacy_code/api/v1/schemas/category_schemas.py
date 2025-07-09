from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    """Base category schema."""
    category_name: str = Field(..., min_length=1, max_length=100, description="Category name")
    parent_category_id: Optional[UUID] = Field(None, description="Parent category ID (None for root)")
    display_order: int = Field(0, ge=0, description="Display order within parent")


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)


class CategoryMove(BaseModel):
    """Schema for moving a category to a new parent."""
    new_parent_id: Optional[UUID] = Field(None, description="New parent category ID (None for root)")


class CategoryResponse(CategoryBase):
    """Schema for category responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    category_path: str = Field(..., description="Full path like 'Electronics/Computers/Laptops'")
    category_level: int = Field(..., description="Hierarchy level (1=root)")
    is_leaf: bool = Field(..., description="Whether category has no children")
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool = True


class CategoryTreeNode(CategoryResponse):
    """Schema for category tree representation."""
    children: List["CategoryTreeNode"] = Field(default_factory=list)


class CategoryListResponse(BaseModel):
    """Schema for paginated category list."""
    items: List[CategoryResponse]
    total: int
    skip: int
    limit: int


class CategoryBreadcrumb(BaseModel):
    """Schema for category breadcrumb."""
    items: List[CategoryResponse] = Field(..., description="Categories from root to current")


class CategoryStatistics(BaseModel):
    """Schema for category statistics."""
    total_categories: int
    root_categories: int
    leaf_categories: int
    max_depth: int
    branch_categories: int


class CategoryFilter(BaseModel):
    """Schema for category filtering."""
    parent_id: Optional[UUID] = None
    is_leaf: Optional[bool] = None
    is_active: Optional[bool] = True


# Update forward references for recursive model
CategoryTreeNode.model_rebuild()