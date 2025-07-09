from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.supplier import (
    CreateSupplierUseCase,
    GetSupplierUseCase,
    UpdateSupplierUseCase,
    ListSuppliersUseCase
)
from ....infrastructure.repositories.supplier_repository import SQLAlchemySupplierRepository
from ....domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms
from ..schemas.supplier_schemas import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse,
    SupplierPerformanceUpdate,
    SupplierStatusUpdate
)
from ..dependencies.database import get_db

router = APIRouter(tags=["suppliers"])


async def get_supplier_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemySupplierRepository:
    """Get supplier repository instance."""
    return SQLAlchemySupplierRepository(db)


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Create a new supplier."""
    use_case = CreateSupplierUseCase(repository)
    
    try:
        supplier = await use_case.execute(
            supplier_code=supplier_data.supplier_code,
            company_name=supplier_data.company_name,
            supplier_type=supplier_data.supplier_type,
            contact_person=supplier_data.contact_person,
            email=supplier_data.email,
            phone=supplier_data.phone,
            address=supplier_data.address,
            tax_id=supplier_data.tax_id,
            payment_terms=supplier_data.payment_terms,
            credit_limit=supplier_data.credit_limit,
            supplier_tier=supplier_data.supplier_tier,
            created_by=current_user_id
        )
        return SupplierResponse.from_entity(supplier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: UUID,
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository)
):
    """Get a supplier by ID."""
    use_case = GetSupplierUseCase(repository)
    supplier = await use_case.execute(supplier_id)
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    return SupplierResponse.from_entity(supplier)


@router.get("/code/{supplier_code}", response_model=SupplierResponse)
async def get_supplier_by_code(
    supplier_code: str,
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository)
):
    """Get a supplier by code."""
    use_case = GetSupplierUseCase(repository)
    supplier = await use_case.get_by_code(supplier_code)
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with code '{supplier_code}' not found"
        )
    
    return SupplierResponse.from_entity(supplier)


@router.get("/", response_model=SupplierListResponse)
async def list_suppliers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    supplier_type: Optional[SupplierType] = Query(None, description="Filter by supplier type"),
    supplier_tier: Optional[SupplierTier] = Query(None, description="Filter by supplier tier"),
    payment_terms: Optional[PaymentTerms] = Query(None, description="Filter by payment terms"),
    search: Optional[str] = Query(None, description="Search in code, name, or contact info"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository)
):
    """List suppliers with pagination and filters."""
    use_case = ListSuppliersUseCase(repository)
    suppliers, total_count = await use_case.execute(
        skip=skip,
        limit=limit,
        supplier_type=supplier_type,
        supplier_tier=supplier_tier,
        payment_terms=payment_terms,
        search=search,
        is_active=is_active
    )
    
    return SupplierListResponse(
        items=[SupplierResponse.from_entity(supplier) for supplier in suppliers],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update supplier information."""
    use_case = UpdateSupplierUseCase(repository)
    
    try:
        # Get existing supplier
        get_use_case = GetSupplierUseCase(repository)
        supplier = await get_use_case.execute(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with id {supplier_id} not found"
            )
        
        # Update supplier fields
        updated_supplier = await use_case.execute(
            supplier_id=supplier_id,
            company_name=supplier_data.company_name,
            supplier_type=supplier_data.supplier_type,
            contact_person=supplier_data.contact_person,
            email=supplier_data.email,
            phone=supplier_data.phone,
            address=supplier_data.address,
            tax_id=supplier_data.tax_id,
            payment_terms=supplier_data.payment_terms,
            credit_limit=supplier_data.credit_limit,
            supplier_tier=supplier_data.supplier_tier,
            updated_by=current_user_id
        )
        
        return SupplierResponse.from_entity(updated_supplier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{supplier_id}/status", response_model=SupplierResponse)
async def update_supplier_status(
    supplier_id: UUID,
    status_update: SupplierStatusUpdate,
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update supplier active status."""
    get_use_case = GetSupplierUseCase(repository)
    supplier = await get_use_case.execute(supplier_id)
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    try:
        if status_update.is_active:
            supplier.activate(updated_by=current_user_id)
        else:
            supplier.deactivate(updated_by=current_user_id)
        
        updated_supplier = await repository.update(supplier)
        return SupplierResponse.from_entity(updated_supplier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{supplier_id}/performance", response_model=SupplierResponse)
async def update_supplier_performance(
    supplier_id: UUID,
    performance_data: SupplierPerformanceUpdate,
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository)
):
    """Update supplier performance metrics."""
    get_use_case = GetSupplierUseCase(repository)
    supplier = await get_use_case.execute(supplier_id)
    
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    try:
        supplier.update_performance_metrics(
            total_orders=performance_data.total_orders,
            total_spend=performance_data.total_spend,
            average_delivery_days=performance_data.average_delivery_days,
            quality_rating=performance_data.quality_rating
        )
        
        updated_supplier = await repository.update(supplier)
        return SupplierResponse.from_entity(updated_supplier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: UUID,
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Soft delete a supplier."""
    success = await repository.delete(supplier_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )


@router.get("/search/name", response_model=List[SupplierResponse])
async def search_suppliers_by_name(
    name: str = Query(..., min_length=2, description="Name to search for"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository)
):
    """Search suppliers by company name."""
    suppliers = await repository.search_by_name(name, limit)
    return [SupplierResponse.from_entity(supplier) for supplier in suppliers]


@router.get("/tier/{tier}", response_model=SupplierListResponse)
async def get_suppliers_by_tier(
    tier: SupplierTier,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository)
):
    """Get suppliers by tier."""
    suppliers, total_count = await repository.get_by_tier(tier, skip, limit)
    
    return SupplierListResponse(
        items=[SupplierResponse.from_entity(supplier) for supplier in suppliers],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/top/by-spend", response_model=List[SupplierResponse])
async def get_top_suppliers_by_spend(
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    repository: SQLAlchemySupplierRepository = Depends(get_supplier_repository)
):
    """Get top suppliers by total spend."""
    suppliers = await repository.get_top_suppliers_by_spend(limit)
    return [SupplierResponse.from_entity(supplier) for supplier in suppliers]