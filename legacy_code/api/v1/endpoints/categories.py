from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.database import get_db
from ....application.use_cases.category_use_cases import CategoryUseCases
from ....infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
from ..schemas.category_schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryMove,
    CategoryResponse,
    CategoryListResponse,
    CategoryTreeNode,
    CategoryBreadcrumb,
    CategoryStatistics
)

router = APIRouter(tags=["categories"])


def get_category_use_cases(db: AsyncSession = Depends(get_db)) -> CategoryUseCases:
    """Dependency injection for category use cases."""
    repository = SQLAlchemyCategoryRepository(db)
    return CategoryUseCases(repository)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    use_cases: CategoryUseCases = Depends(get_category_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Create a new category."""
    try:
        category = await use_cases.create_category(
            category_name=category_data.category_name,
            parent_category_id=category_data.parent_category_id,
            display_order=category_data.display_order,
            created_by="system"  # TODO: Use current_user
        )
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """Get a category by ID."""
    try:
        category = await use_cases.get_category(category_id)
        return category
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/path/{category_path:path}", response_model=CategoryResponse)
async def get_category_by_path(
    category_path: str,
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """Get a category by its full path (e.g., 'Electronics/Computers/Laptops')."""
    try:
        category = await use_cases.get_category_by_path(category_path)
        return category
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    parent_id: Optional[UUID] = Query(None),
    is_leaf: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """List categories with pagination and filters."""
    categories, total = await use_cases.list_categories(
        skip=skip,
        limit=limit,
        parent_id=parent_id,
        is_leaf=is_leaf,
        is_active=is_active
    )
    
    return CategoryListResponse(
        items=categories,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/tree/", response_model=List[CategoryResponse])
async def get_category_tree(
    root_id: Optional[UUID] = Query(None, description="Root category ID to start from"),
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """Get category tree structure."""
    tree = await use_cases.get_category_tree(root_id)
    return tree


@router.get("/{category_id}/breadcrumb", response_model=CategoryBreadcrumb)
async def get_category_breadcrumb(
    category_id: UUID,
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """Get breadcrumb trail from root to category."""
    try:
        breadcrumb = await use_cases.get_category_breadcrumb(category_id)
        return CategoryBreadcrumb(items=breadcrumb)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{category_id}/children", response_model=List[CategoryResponse])
async def get_category_children(
    category_id: UUID,
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """Get direct children of a category."""
    repository = use_cases.category_repository
    children = await repository.get_children(category_id)
    return children


@router.get("/leaf/all", response_model=List[CategoryResponse])
async def get_leaf_categories(
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """Get all leaf categories (categories that can have products)."""
    categories = await use_cases.get_leaf_categories()
    return categories


@router.get("/statistics/summary", response_model=CategoryStatistics)
async def get_category_statistics(
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """Get category hierarchy statistics."""
    stats = await use_cases.get_category_statistics()
    return CategoryStatistics(**stats)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    use_cases: CategoryUseCases = Depends(get_category_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Update a category."""
    try:
        category = await use_cases.update_category(
            category_id=category_id,
            category_name=category_data.category_name,
            display_order=category_data.display_order,
            updated_by="system"  # TODO: Use current_user
        )
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{category_id}/move", response_model=CategoryResponse)
async def move_category(
    category_id: UUID,
    move_data: CategoryMove,
    use_cases: CategoryUseCases = Depends(get_category_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Move a category to a new parent."""
    try:
        category = await use_cases.move_category(
            category_id=category_id,
            new_parent_id=move_data.new_parent_id,
            updated_by="system"  # TODO: Use current_user
        )
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    use_cases: CategoryUseCases = Depends(get_category_use_cases)
):
    """Delete a category (soft delete).
    
    Note: Category must have no children or products assigned.
    """
    try:
        success = await use_cases.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))