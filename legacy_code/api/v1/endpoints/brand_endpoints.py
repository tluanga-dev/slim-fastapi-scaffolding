from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.brand import (
    CreateBrandUseCase,
    GetBrandUseCase,
    UpdateBrandUseCase,
    DeleteBrandUseCase,
    ListBrandsUseCase
)
from ....infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository
from ..schemas.brand_schemas import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BrandListResponse
)
from ..dependencies.database import get_db

router = APIRouter(tags=["brands"])


async def get_brand_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyBrandRepository:
    """Get brand repository instance."""
    return SQLAlchemyBrandRepository(db)


@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_data: BrandCreate,
    repository: SQLAlchemyBrandRepository = Depends(get_brand_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Create a new brand."""
    use_case = CreateBrandUseCase(repository)
    
    try:
        brand = await use_case.execute(
            brand_name=brand_data.brand_name,
            brand_code=brand_data.brand_code,
            description=brand_data.description,
            created_by=current_user_id
        )
        return BrandResponse.model_validate(brand)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    repository: SQLAlchemyBrandRepository = Depends(get_brand_repository)
):
    """Get a brand by ID."""
    use_case = GetBrandUseCase(repository)
    brand = await use_case.execute(brand_id)
    
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {brand_id} not found"
        )
    
    return BrandResponse.model_validate(brand)


@router.get("/by-name/{brand_name}", response_model=BrandResponse)
async def get_brand_by_name(
    brand_name: str,
    repository: SQLAlchemyBrandRepository = Depends(get_brand_repository)
):
    """Get a brand by name."""
    use_case = GetBrandUseCase(repository)
    brand = await use_case.get_by_name(brand_name)
    
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with name '{brand_name}' not found"
        )
    
    return BrandResponse.model_validate(brand)


@router.get("/by-code/{brand_code}", response_model=BrandResponse)
async def get_brand_by_code(
    brand_code: str,
    repository: SQLAlchemyBrandRepository = Depends(get_brand_repository)
):
    """Get a brand by code."""
    use_case = GetBrandUseCase(repository)
    brand = await use_case.get_by_code(brand_code.upper())
    
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with code '{brand_code}' not found"
        )
    
    return BrandResponse.model_validate(brand)


@router.get("/", response_model=BrandListResponse)
async def list_brands(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    search: Optional[str] = Query(None, description="Search in name, code, or description"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    repository: SQLAlchemyBrandRepository = Depends(get_brand_repository)
):
    """List brands with pagination and search."""
    use_case = ListBrandsUseCase(repository)
    brands, total_count = await use_case.execute(
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active
    )
    
    return BrandListResponse(
        items=[BrandResponse.model_validate(brand) for brand in brands],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    brand_data: BrandUpdate,
    repository: SQLAlchemyBrandRepository = Depends(get_brand_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update an existing brand."""
    use_case = UpdateBrandUseCase(repository)
    
    try:
        brand = await use_case.execute(
            brand_id=brand_id,
            brand_name=brand_data.brand_name,
            brand_code=brand_data.brand_code,
            description=brand_data.description,
            updated_by=current_user_id
        )
        return BrandResponse.model_validate(brand)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: UUID,
    repository: SQLAlchemyBrandRepository = Depends(get_brand_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Delete (deactivate) a brand."""
    use_case = DeleteBrandUseCase(repository)
    
    try:
        success = await use_case.execute(
            brand_id=brand_id,
            deleted_by=current_user_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand with id {brand_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )