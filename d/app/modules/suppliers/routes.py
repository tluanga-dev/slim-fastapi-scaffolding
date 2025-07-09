from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.modules.suppliers.service import SupplierService
from app.modules.suppliers.schemas import (
    SupplierCreate, SupplierUpdate, SupplierContactUpdate,
    SupplierPaymentUpdate, SupplierTierUpdate, SupplierStatusUpdate,
    SupplierPerformanceUpdate, SupplierResponse, SupplierListResponse,
    SupplierPerformanceResponse
)
from app.core.domain.value_objects.supplier_type import SupplierType, SupplierTier
from app.core.errors import NotFoundError, ValidationError
from app.shared.dependencies import get_supplier_service


router = APIRouter(tags=["suppliers"])


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Create a new supplier."""
    try:
        return await service.create_supplier(supplier_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=SupplierListResponse)
async def get_suppliers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    supplier_type: Optional[SupplierType] = Query(None, description="Filter by supplier type"),
    supplier_tier: Optional[SupplierTier] = Query(None, description="Filter by supplier tier"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name, code, contact person, and email"),
    service: SupplierService = Depends(get_supplier_service)
):
    """Get suppliers with filtering and pagination."""
    try:
        return await service.get_suppliers(
            page=page,
            page_size=page_size,
            supplier_type=supplier_type,
            supplier_tier=supplier_tier,
            is_active=is_active,
            search=search
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier_by_id(
    supplier_id: UUID,
    service: SupplierService = Depends(get_supplier_service)
):
    """Get supplier by ID."""
    try:
        return await service.get_supplier_by_id(supplier_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/code/{supplier_code}", response_model=SupplierResponse)
async def get_supplier_by_code(
    supplier_code: str,
    service: SupplierService = Depends(get_supplier_service)
):
    """Get supplier by supplier code."""
    try:
        return await service.get_supplier_by_code(supplier_code)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: UUID,
    update_data: SupplierUpdate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Update supplier business information."""
    try:
        return await service.update_supplier(supplier_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{supplier_id}/contact", response_model=SupplierResponse)
async def update_supplier_contact(
    supplier_id: UUID,
    contact_data: SupplierContactUpdate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Update supplier contact information."""
    try:
        return await service.update_contact_info(supplier_id, contact_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{supplier_id}/payment", response_model=SupplierResponse)
async def update_supplier_payment_terms(
    supplier_id: UUID,
    payment_data: SupplierPaymentUpdate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Update supplier payment terms and credit limit."""
    try:
        return await service.update_payment_terms(supplier_id, payment_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{supplier_id}/tier", response_model=SupplierResponse)
async def update_supplier_tier(
    supplier_id: UUID,
    tier_data: SupplierTierUpdate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Update supplier tier classification."""
    try:
        return await service.update_tier(supplier_id, tier_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{supplier_id}/status", response_model=SupplierResponse)
async def update_supplier_status(
    supplier_id: UUID,
    status_data: SupplierStatusUpdate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Update supplier status (activate/deactivate)."""
    try:
        return await service.update_status(supplier_id, status_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{supplier_id}/performance", response_model=SupplierResponse)
async def update_supplier_performance(
    supplier_id: UUID,
    performance_data: SupplierPerformanceUpdate,
    service: SupplierService = Depends(get_supplier_service)
):
    """Update supplier performance metrics."""
    try:
        return await service.update_performance_metrics(supplier_id, performance_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: UUID,
    service: SupplierService = Depends(get_supplier_service)
):
    """Delete supplier."""
    try:
        success = await service.delete_supplier(supplier_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/type/{supplier_type}", response_model=List[SupplierResponse])
async def get_suppliers_by_type(
    supplier_type: SupplierType,
    service: SupplierService = Depends(get_supplier_service)
):
    """Get all suppliers of a specific type."""
    try:
        return await service.get_suppliers_by_type(supplier_type)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/tier/{supplier_tier}", response_model=List[SupplierResponse])
async def get_suppliers_by_tier(
    supplier_tier: SupplierTier,
    service: SupplierService = Depends(get_supplier_service)
):
    """Get all suppliers of a specific tier."""
    try:
        return await service.get_suppliers_by_tier(supplier_tier)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/analytics/top-spend", response_model=List[SupplierResponse])
async def get_top_suppliers_by_spend(
    limit: int = Query(10, ge=1, le=50, description="Number of top suppliers to return"),
    service: SupplierService = Depends(get_supplier_service)
):
    """Get top suppliers by total spend."""
    try:
        return await service.get_top_suppliers_by_spend(limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/analytics/performance", response_model=List[SupplierPerformanceResponse])
async def get_supplier_performance_metrics(
    service: SupplierService = Depends(get_supplier_service)
):
    """Get performance metrics for all active suppliers."""
    try:
        return await service.get_supplier_performance_metrics()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))