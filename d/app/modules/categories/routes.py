from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from app.modules.categories import schemas
from app.shared.dependencies import get_category_service


router = APIRouter(tags=["Categories"])


@router.post("/", response_model=schemas.CategoryResponse)
async def create_category(
    category: schemas.CategoryCreate,
    service=Depends(get_category_service),
    created_by: Optional[str] = Query(None, description="User creating the category")
):
    """Create a new category."""
    try:
        return await service.create_category(category, created_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.CategoryResponse])
async def get_categories(
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category ID"),
    level: Optional[int] = Query(None, description="Filter by category level"),
    leaf_only: bool = Query(False, description="Return only leaf categories"),
    service=Depends(get_category_service)
):
    """Get categories based on filters."""
    if leaf_only:
        return await service.get_leaf_categories()
    elif parent_id is not None or parent_id == "root":
        # Handle both UUID and "root" for getting root categories
        parent_uuid = None if parent_id == "root" else parent_id
        return await service.get_categories_by_parent(parent_uuid)
    elif level is not None:
        return await service.repo.get_categories_by_level(level)
    else:
        # Default: return root categories
        return await service.get_categories_by_parent(None)


@router.get("/tree", response_model=List[schemas.CategoryTree])
async def get_category_tree(
    root_id: Optional[UUID] = Query(None, description="Start tree from specific category"),
    service=Depends(get_category_service)
):
    """Get category tree structure."""
    categories = await service.get_category_tree(root_id)
    
    # Convert to tree structure
    if root_id:
        return categories
    else:
        # Build tree from root categories
        tree = []
        for cat in categories:
            tree_node = await _build_tree_node(cat, service)
            tree.append(tree_node)
        return tree


@router.get("/{category_id}", response_model=schemas.CategoryResponse)
async def get_category(
    category_id: UUID,
    service=Depends(get_category_service)
):
    """Get a specific category by ID."""
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.get("/{category_id}/children", response_model=List[schemas.CategoryResponse])
async def get_category_children(
    category_id: UUID,
    service=Depends(get_category_service)
):
    """Get direct children of a category."""
    # Verify category exists
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return await service.get_categories_by_parent(category_id)


@router.put("/{category_id}", response_model=schemas.CategoryResponse)
async def update_category(
    category_id: UUID,
    category_update: schemas.CategoryUpdate,
    service=Depends(get_category_service),
    updated_by: Optional[str] = Query(None, description="User updating the category")
):
    """Update a category."""
    try:
        category = await service.update_category(category_id, category_update, updated_by)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}")
async def delete_category(
    category_id: UUID,
    service=Depends(get_category_service),
    deleted_by: Optional[str] = Query(None, description="User deleting the category")
):
    """Soft delete a category and all its descendants."""
    success = await service.delete_category(category_id, deleted_by)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


@router.post("/{category_id}/move")
async def move_category(
    category_id: UUID,
    new_parent_id: Optional[UUID] = Query(None, description="New parent category ID (None for root)"),
    service=Depends(get_category_service),
    updated_by: Optional[str] = Query(None, description="User moving the category")
):
    """Move a category to a new parent."""
    try:
        category = await service.move_category(category_id, new_parent_id, updated_by)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _build_tree_node(category, service) -> schemas.CategoryTree:
    """Build a tree node with children."""
    # Get children
    children = await service.get_categories_by_parent(category.id)
    
    # Convert to CategoryTree
    tree_node = schemas.CategoryTree.model_validate(category)
    
    # Recursively build children
    for child in children:
        child_node = await _build_tree_node(child, service)
        tree_node.children.append(child_node)
    
    return tree_node