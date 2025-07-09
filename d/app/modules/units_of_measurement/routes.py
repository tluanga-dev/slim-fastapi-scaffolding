from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.modules.units_of_measurement.service import UnitOfMeasurementService
from app.modules.units_of_measurement.schemas import (
    UnitOfMeasurementCreate, UnitOfMeasurementUpdate, UnitOfMeasurementStatusUpdate,
    UnitOfMeasurementResponse, UnitOfMeasurementListResponse, UnitOfMeasurementSummary,
    UnitOfMeasurementValidationResponse
)
from app.core.errors import NotFoundError, ValidationError
from app.shared.dependencies import get_unit_of_measurement_service


router = APIRouter(tags=["units-of-measurement"])


@router.post("/", response_model=UnitOfMeasurementResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_of_measurement(
    unit_data: UnitOfMeasurementCreate,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Create a new unit of measurement."""
    try:
        return await service.create_unit(unit_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=UnitOfMeasurementListResponse)
async def get_units_of_measurement(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name, abbreviation, and description"),
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get units of measurement with filtering and pagination."""
    try:
        return await service.get_units(
            page=page,
            page_size=page_size,
            is_active=is_active,
            search=search
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/active", response_model=List[UnitOfMeasurementSummary])
async def get_active_units_of_measurement(
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get all active units of measurement (summary format)."""
    try:
        return await service.get_active_units()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/search", response_model=List[UnitOfMeasurementSummary])
async def search_units_of_measurement(
    q: str = Query(..., min_length=1, description="Search query for name or abbreviation"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Search units of measurement by partial name or abbreviation match."""
    try:
        return await service.search_units(q, limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{unit_id}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement_by_id(
    unit_id: UUID,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get unit of measurement by ID."""
    try:
        return await service.get_unit_by_id(unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/unit-id/{unit_id}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement_by_unit_id(
    unit_id: UUID,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get unit of measurement by business unit_id."""
    try:
        return await service.get_unit_by_unit_id(unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/name/{name}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement_by_name(
    name: str,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get unit of measurement by name."""
    try:
        return await service.get_unit_by_name(name)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{unit_id}", response_model=UnitOfMeasurementResponse)
async def update_unit_of_measurement(
    unit_id: UUID,
    update_data: UnitOfMeasurementUpdate,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Update unit of measurement."""
    try:
        return await service.update_unit(unit_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{unit_id}/status", response_model=UnitOfMeasurementResponse)
async def update_unit_of_measurement_status(
    unit_id: UUID,
    status_data: UnitOfMeasurementStatusUpdate,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Update unit of measurement status (activate/deactivate)."""
    try:
        return await service.update_status(unit_id, status_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit_of_measurement(
    unit_id: UUID,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Delete unit of measurement."""
    try:
        success = await service.delete_unit(unit_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit of measurement not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/validate", response_model=List[UnitOfMeasurementValidationResponse])
async def validate_units_for_use(
    unit_ids: List[UUID],
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Validate multiple units for use in inventory items."""
    try:
        return await service.validate_units_for_use(unit_ids)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/unit-id/{unit_id}/conversion-info")
async def get_unit_conversion_info(
    unit_id: UUID,
    service: UnitOfMeasurementService = Depends(get_unit_of_measurement_service)
):
    """Get conversion information for a unit (future enhancement)."""
    try:
        return await service.get_unit_conversion_info(unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))