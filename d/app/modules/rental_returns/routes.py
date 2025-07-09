from typing import Optional, List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.modules.rental_returns.service import RentalReturnService
from app.modules.rental_returns.schemas import (
    RentalReturnCreate, RentalReturnUpdate, RentalReturnStatusUpdate, RentalReturnFinancialUpdate,
    RentalReturnLineUpdate, RentalReturnLineProcessing,
    RentalReturnResponse, RentalReturnWithLines, RentalReturnListResponse,
    RentalReturnLineResponse, RentalReturnLineSummary,
    RentalReturnSearchRequest, RentalReturnLineSearchRequest,
    RentalReturnBulkStatusUpdate, RentalReturnLineBulkProcessing,
    RentalReturnAnalytics, RentalReturnEstimate
)
from app.core.domain.value_objects.rental_return_type import ReturnStatus, ReturnType, DamageLevel
from app.core.domain.value_objects.item_type import ConditionGrade
from app.core.errors import NotFoundError, ValidationError
from app.shared.dependencies import get_rental_return_service


router = APIRouter(tags=["rental-returns"])


# Rental Return Operations
@router.post("/", response_model=RentalReturnWithLines, status_code=status.HTTP_201_CREATED)
async def create_rental_return(
    return_data: RentalReturnCreate,
    created_by: Optional[str] = Query(None, description="User creating the rental return"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Create a new rental return with lines."""
    try:
        return await service.create_rental_return(return_data, created_by)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/search", response_model=List[RentalReturnListResponse])
async def search_rental_returns(
    rental_transaction_id: Optional[UUID] = Query(None, description="Filter by rental transaction ID"),
    return_location_id: Optional[UUID] = Query(None, description="Filter by return location ID"),
    return_status: Optional[ReturnStatus] = Query(None, description="Filter by return status"),
    return_type: Optional[ReturnType] = Query(None, description="Filter by return type"),
    return_date_from: Optional[date] = Query(None, description="Filter by return date from"),
    return_date_to: Optional[date] = Query(None, description="Filter by return date to"),
    processed_by: Optional[str] = Query(None, description="Filter by processed by"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Search rental returns with filtering."""
    try:
        search_request = RentalReturnSearchRequest(
            rental_transaction_id=rental_transaction_id,
            return_location_id=return_location_id,
            return_status=return_status,
            return_type=return_type,
            return_date_from=return_date_from,
            return_date_to=return_date_to,
            processed_by=processed_by,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return await service.search_rental_returns(search_request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/by-transaction/{transaction_id}", response_model=List[RentalReturnListResponse])
async def get_rental_returns_by_transaction(
    transaction_id: UUID,
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get all rental returns for a transaction."""
    try:
        return await service.get_rental_returns_by_transaction(transaction_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/by-status/{status}", response_model=List[RentalReturnListResponse])
async def get_returns_by_status(
    status: ReturnStatus,
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get returns by status."""
    try:
        return await service.get_returns_by_status(status)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/overdue", response_model=List[RentalReturnListResponse])
async def get_overdue_returns(
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get overdue returns."""
    try:
        return await service.get_overdue_returns()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/analytics", response_model=RentalReturnAnalytics)
async def get_return_analytics(
    start_date: Optional[date] = Query(None, description="Analytics start date"),
    end_date: Optional[date] = Query(None, description="Analytics end date"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get comprehensive return analytics."""
    try:
        return await service.get_return_analytics(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/estimate", response_model=RentalReturnEstimate)
async def estimate_return_costs(
    return_data: RentalReturnCreate,
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Estimate costs for a potential return."""
    try:
        return await service.estimate_return_costs(return_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{return_id}", response_model=RentalReturnResponse)
async def get_rental_return(
    return_id: UUID,
    include_lines: bool = Query(False, description="Include return lines in response"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get rental return by ID."""
    try:
        return await service.get_rental_return_by_id(return_id, include_lines)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{return_id}/with-lines", response_model=RentalReturnWithLines)
async def get_rental_return_with_lines(
    return_id: UUID,
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get rental return by ID with all lines."""
    try:
        return await service.get_rental_return_by_id(return_id, include_lines=True)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{return_id}", response_model=RentalReturnResponse)
async def update_rental_return(
    return_id: UUID,
    update_data: RentalReturnUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the rental return"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Update rental return."""
    try:
        return await service.update_rental_return(return_id, update_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{return_id}/status", response_model=RentalReturnResponse)
async def update_rental_return_status(
    return_id: UUID,
    status_data: RentalReturnStatusUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the status"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Update rental return status."""
    try:
        return await service.update_rental_return_status(return_id, status_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{return_id}/financials", response_model=RentalReturnResponse)
async def update_rental_return_financials(
    return_id: UUID,
    financial_data: RentalReturnFinancialUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the financials"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Update rental return financial information."""
    try:
        return await service.update_rental_return_financials(return_id, financial_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{return_id}", response_model=dict)
async def delete_rental_return(
    return_id: UUID,
    deleted_by: Optional[str] = Query(None, description="User deleting the rental return"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Soft delete rental return."""
    try:
        success = await service.delete_rental_return(return_id, deleted_by)
        if success:
            return {"message": "Rental return deleted successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete rental return")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Rental Return Line Operations
@router.get("/{return_id}/lines", response_model=List[RentalReturnLineResponse])
async def get_rental_return_lines(
    return_id: UUID,
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get all lines for a rental return."""
    try:
        return await service.get_rental_return_lines_by_return(return_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/lines/search", response_model=List[RentalReturnLineResponse])
async def search_rental_return_lines(
    return_id: Optional[UUID] = Query(None, description="Filter by return ID"),
    inventory_unit_id: Optional[UUID] = Query(None, description="Filter by inventory unit ID"),
    condition_grade: Optional[ConditionGrade] = Query(None, description="Filter by condition grade"),
    damage_level: Optional[DamageLevel] = Query(None, description="Filter by damage level"),
    is_processed: Optional[bool] = Query(None, description="Filter by processed status"),
    processed_by: Optional[str] = Query(None, description="Filter by processed by"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Search rental return lines with filtering."""
    try:
        search_request = RentalReturnLineSearchRequest(
            return_id=return_id,
            inventory_unit_id=inventory_unit_id,
            condition_grade=condition_grade,
            damage_level=damage_level,
            is_processed=is_processed,
            processed_by=processed_by,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return await service.search_rental_return_lines(search_request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/lines/needing-processing", response_model=List[RentalReturnLineResponse])
async def get_lines_needing_processing(
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get return lines that need processing."""
    try:
        return await service.get_lines_needing_processing()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/lines/damaged", response_model=List[RentalReturnLineResponse])
async def get_damaged_returns(
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get return lines with damage."""
    try:
        return await service.get_damaged_returns()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/lines/{line_id}", response_model=RentalReturnLineResponse)
async def get_rental_return_line(
    line_id: UUID,
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Get rental return line by ID."""
    try:
        return await service.get_rental_return_line_by_id(line_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/lines/{line_id}", response_model=RentalReturnLineResponse)
async def update_rental_return_line(
    line_id: UUID,
    update_data: RentalReturnLineUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the return line"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Update rental return line."""
    try:
        return await service.update_rental_return_line(line_id, update_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/lines/{line_id}/process", response_model=RentalReturnLineResponse)
async def process_rental_return_line(
    line_id: UUID,
    processing_data: RentalReturnLineProcessing,
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Process a rental return line."""
    try:
        return await service.process_rental_return_line(line_id, processing_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Bulk Operations
@router.patch("/bulk/status", response_model=dict)
async def bulk_update_return_status(
    bulk_update: RentalReturnBulkStatusUpdate,
    updated_by: Optional[str] = Query(None, description="User performing the bulk update"),
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Bulk update status for multiple returns."""
    try:
        updated_count = await service.bulk_update_return_status(bulk_update, updated_by)
        return {"updated_count": updated_count, "requested_count": len(bulk_update.return_ids)}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/lines/bulk/process", response_model=dict)
async def bulk_process_return_lines(
    bulk_processing: RentalReturnLineBulkProcessing,
    service: RentalReturnService = Depends(get_rental_return_service)
):
    """Bulk process return lines."""
    try:
        updated_count = await service.bulk_process_return_lines(bulk_processing)
        return {"updated_count": updated_count, "requested_count": len(bulk_processing.line_ids)}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))