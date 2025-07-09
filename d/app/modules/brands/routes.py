from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.modules.brands.service import BrandService
from app.modules.brands.schemas import (
    BrandCreate, BrandUpdate, BrandStatusUpdate,
    BrandResponse, BrandListResponse, BrandSearchResponse
)
from app.core.errors import NotFoundError, ValidationError
from app.shared.dependencies import get_brand_service


router = APIRouter(tags=["brands"])


@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_data: BrandCreate,
    service: BrandService = Depends(get_brand_service)
):
    """Create a new brand."""
    try:
        return await service.create_brand(brand_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=BrandListResponse)
async def get_brands(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in brand name, code, and description"),
    sort_by: str = Query("brand_name", description="Sort by field (brand_name, brand_code, created_at, updated_at)"),
    sort_order: str = Query("asc", description="Sort order (asc, desc)"),
    service: BrandService = Depends(get_brand_service)
):
    """Get brands with filtering, pagination, and sorting."""
    try:
        return await service.get_brands(
            page=page,
            page_size=page_size,
            is_active=is_active,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/active", response_model=List[BrandResponse])
async def get_active_brands(
    service: BrandService = Depends(get_brand_service)
):
    """Get all active brands."""
    try:
        return await service.get_active_brands()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/search", response_model=List[BrandSearchResponse])
async def search_brands(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    service: BrandService = Depends(get_brand_service)
):
    """Search brands by name or code."""
    try:
        return await service.search_brands(q, limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/prefix/{prefix}", response_model=List[BrandSearchResponse])
async def get_brands_by_prefix(
    prefix: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    service: BrandService = Depends(get_brand_service)
):
    """Get brands that start with the given prefix."""
    try:
        return await service.get_brands_by_prefix(prefix, limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/check-name-availability", response_model=dict)
async def check_brand_name_availability(
    name: str = Query(..., min_length=1, description="Brand name to check"),
    exclude_id: Optional[UUID] = Query(None, description="Brand ID to exclude from check"),
    service: BrandService = Depends(get_brand_service)
):
    """Check if brand name is available."""
    try:
        available = await service.check_brand_name_availability(name, exclude_id)
        return {"available": available, "name": name}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/check-code-availability", response_model=dict)
async def check_brand_code_availability(
    code: str = Query(..., min_length=1, description="Brand code to check"),
    exclude_id: Optional[UUID] = Query(None, description="Brand ID to exclude from check"),
    service: BrandService = Depends(get_brand_service)
):
    """Check if brand code is available."""
    try:
        available = await service.check_brand_code_availability(code, exclude_id)
        return {"available": available, "code": code}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand_by_id(
    brand_id: UUID,
    service: BrandService = Depends(get_brand_service)
):
    """Get brand by ID."""
    try:
        return await service.get_brand_by_id(brand_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/name/{brand_name}", response_model=BrandResponse)
async def get_brand_by_name(
    brand_name: str,
    service: BrandService = Depends(get_brand_service)
):
    """Get brand by name."""
    try:
        return await service.get_brand_by_name(brand_name)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/code/{brand_code}", response_model=BrandResponse)
async def get_brand_by_code(
    brand_code: str,
    service: BrandService = Depends(get_brand_service)
):
    """Get brand by code."""
    try:
        return await service.get_brand_by_code(brand_code)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    update_data: BrandUpdate,
    service: BrandService = Depends(get_brand_service)
):
    """Update brand information."""
    try:
        return await service.update_brand(brand_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{brand_id}/status", response_model=BrandResponse)
async def update_brand_status(
    brand_id: UUID,
    status_data: BrandStatusUpdate,
    service: BrandService = Depends(get_brand_service)
):
    """Update brand active status."""
    try:
        return await service.update_brand_status(brand_id, status_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: UUID,
    deleted_by: Optional[str] = Query(None, description="User performing the deletion"),
    service: BrandService = Depends(get_brand_service)
):
    """Soft delete brand."""
    try:
        success = await service.delete_brand(brand_id, deleted_by)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))