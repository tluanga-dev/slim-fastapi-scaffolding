from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.item.get_rentable_items_with_availability import (
    GetRentableItemsWithAvailabilityUseCase
)
from ....infrastructure.repositories.item_repository import ItemRepositoryImpl
from ....infrastructure.repositories.stock_level_repository import SQLAlchemyStockLevelRepository
from ....infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
from ....infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
from ....infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository
from ..schemas.rentable_item_schemas import (
    RentableItemListResponse,
    RentableItemSearchParams
)
from ..dependencies.database import get_db

router = APIRouter(tags=["rentable-items"])


async def get_rentable_items_dependencies(db: AsyncSession = Depends(get_db)):
    """Get all repositories needed for rentable items use case."""
    return {
        'item_repository': ItemRepositoryImpl(db),
        'stock_repository': SQLAlchemyStockLevelRepository(db),
        'location_repository': SQLAlchemyLocationRepository(db),
        'category_repository': SQLAlchemyCategoryRepository(db),
        'brand_repository': SQLAlchemyBrandRepository(db)
    }


@router.get("/available", response_model=RentableItemListResponse)
async def get_rentable_items_with_availability(
    search: Optional[str] = Query(None, description="Search term for item name or SKU"),
    location_id: Optional[str] = Query(None, description="Location ID filter"),
    category_id: Optional[str] = Query(None, description="Category ID filter"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    dependencies = Depends(get_rentable_items_dependencies)
):
    """
    Get rentable items with availability information.
    
    This endpoint returns items that are:
    - Marked as rentable (is_rentable=True)
    - Have available stock (quantity_available > 0)
    
    Returns detailed information including:
    - Item details (name, SKU, category, brand)
    - Rental pricing and constraints
    - Availability by location
    - Additional item metadata
    """
    try:
        # Convert string UUIDs to UUID objects if provided
        location_uuid = UUID(location_id) if location_id else None
        category_uuid = UUID(category_id) if category_id else None
        
        # Initialize use case
        use_case = GetRentableItemsWithAvailabilityUseCase(
            item_repository=dependencies['item_repository'],
            stock_repository=dependencies['stock_repository'],
            location_repository=dependencies['location_repository'],
            category_repository=dependencies['category_repository'],
            brand_repository=dependencies['brand_repository']
        )
        
        # Execute use case
        items, total_count = await use_case.execute(
            search=search,
            location_id=location_uuid,
            category_id=category_uuid,
            skip=skip,
            limit=limit
        )
        
        return RentableItemListResponse(
            items=items,
            total=total_count,
            skip=skip,
            limit=limit
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching rentable items: {str(e)}"
        )


@router.get("/search", response_model=RentableItemListResponse)
async def search_rentable_items(
    q: str = Query(..., min_length=1, max_length=255, description="Search query"),
    location_id: Optional[str] = Query(None, description="Location ID filter"),
    category_id: Optional[str] = Query(None, description="Category ID filter"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    dependencies = Depends(get_rentable_items_dependencies)
):
    """
    Search rentable items by name or SKU.
    
    This is a convenience endpoint for searching rentable items.
    It's equivalent to calling /available with a search parameter.
    """
    try:
        # Convert string UUIDs to UUID objects if provided
        location_uuid = UUID(location_id) if location_id else None
        category_uuid = UUID(category_id) if category_id else None
        
        # Initialize use case
        use_case = GetRentableItemsWithAvailabilityUseCase(
            item_repository=dependencies['item_repository'],
            stock_repository=dependencies['stock_repository'],
            location_repository=dependencies['location_repository'],
            category_repository=dependencies['category_repository'],
            brand_repository=dependencies['brand_repository']
        )
        
        # Execute use case with search
        items, total_count = await use_case.execute(
            search=q,
            location_id=location_uuid,
            category_id=category_uuid,
            skip=skip,
            limit=limit
        )
        
        return RentableItemListResponse(
            items=items,
            total=total_count,
            skip=skip,
            limit=limit
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while searching rentable items: {str(e)}"
        )