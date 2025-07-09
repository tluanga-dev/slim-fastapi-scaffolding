from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.modules.inventory_units.service import InventoryUnitService
from app.modules.inventory_units.schemas import (
    InventoryUnitCreate, InventoryUnitUpdate, InventoryUnitLocationUpdate,
    InventoryUnitStatusUpdate, InventoryUnitConditionUpdate, InventoryUnitRentalUpdate,
    InventoryUnitResponse, InventoryUnitListResponse, InventoryUnitSummary,
    InventoryUnitMetrics, InventoryUnitSearchRequest,
    InventoryUnitBulkStatusUpdate, InventoryUnitBulkLocationUpdate
)
from app.core.domain.value_objects.item_type import InventoryStatus, ConditionGrade
from app.core.errors import NotFoundError, ValidationError
from app.shared.dependencies import get_inventory_unit_service


router = APIRouter(tags=["inventory-units"])


@router.post("/", response_model=InventoryUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_unit(
    inventory_unit_data: InventoryUnitCreate,
    created_by: Optional[str] = Query(None, description="User creating the inventory unit"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Create a new inventory unit."""
    try:
        return await service.create_inventory_unit(inventory_unit_data, created_by)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/search", response_model=List[InventoryUnitListResponse])
async def search_inventory_units(
    item_id: Optional[UUID] = Query(None, description="Filter by item ID"),
    location_id: Optional[UUID] = Query(None, description="Filter by location ID"),
    status: Optional[InventoryStatus] = Query(None, description="Filter by status"),
    condition_grade: Optional[ConditionGrade] = Query(None, description="Filter by condition grade"),
    inventory_code: Optional[str] = Query(None, description="Search by inventory code"),
    serial_number: Optional[str] = Query(None, description="Search by serial number"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Search inventory units with filtering."""
    try:
        search_request = InventoryUnitSearchRequest(
            item_id=item_id,
            location_id=location_id,
            status=status,
            condition_grade=condition_grade,
            inventory_code=inventory_code,
            serial_number=serial_number,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return await service.search_inventory_units(search_request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/by-item/{item_id}/available", response_model=List[InventoryUnitListResponse])
async def get_available_units_by_item(
    item_id: UUID,
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get available inventory units for a specific item."""
    try:
        return await service.get_available_units_by_item(item_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/by-location/{location_id}", response_model=List[InventoryUnitListResponse])
async def get_units_by_location(
    location_id: UUID,
    is_active: bool = Query(True, description="Filter by active status"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get inventory units at a specific location."""
    try:
        return await service.get_units_by_location(location_id, is_active)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/by-status/{status}", response_model=List[InventoryUnitListResponse])
async def get_units_by_status(
    status: InventoryStatus,
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get inventory units by status."""
    try:
        return await service.get_units_by_status(status)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/inspection/needed", response_model=List[InventoryUnitResponse])
async def get_units_needing_inspection(
    days_threshold: int = Query(90, ge=1, description="Days since last inspection"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get units that need inspection."""
    try:
        return await service.get_units_needing_inspection(days_threshold)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/summary", response_model=dict)
async def get_inventory_summary(
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get comprehensive inventory summary."""
    try:
        return await service.get_inventory_summary()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/code/{inventory_code}", response_model=InventoryUnitResponse)
async def get_inventory_unit_by_code(
    inventory_code: str,
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get inventory unit by inventory code."""
    try:
        return await service.get_inventory_unit_by_code(inventory_code)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/serial/{serial_number}", response_model=InventoryUnitResponse)
async def get_inventory_unit_by_serial(
    serial_number: str,
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get inventory unit by serial number."""
    try:
        return await service.get_inventory_unit_by_serial(serial_number)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{inventory_unit_id}", response_model=InventoryUnitResponse)
async def get_inventory_unit(
    inventory_unit_id: UUID,
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get inventory unit by ID."""
    try:
        return await service.get_inventory_unit_by_id(inventory_unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{inventory_unit_id}/metrics", response_model=InventoryUnitMetrics)
async def get_inventory_unit_metrics(
    inventory_unit_id: UUID,
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Get inventory unit metrics."""
    try:
        return await service.get_inventory_unit_metrics(inventory_unit_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{inventory_unit_id}", response_model=InventoryUnitResponse)
async def update_inventory_unit(
    inventory_unit_id: UUID,
    update_data: InventoryUnitUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the inventory unit"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Update inventory unit."""
    try:
        return await service.update_inventory_unit(inventory_unit_id, update_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{inventory_unit_id}/location", response_model=InventoryUnitResponse)
async def update_inventory_unit_location(
    inventory_unit_id: UUID,
    location_data: InventoryUnitLocationUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the location"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Update inventory unit location."""
    try:
        return await service.update_inventory_unit_location(inventory_unit_id, location_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{inventory_unit_id}/status", response_model=InventoryUnitResponse)
async def update_inventory_unit_status(
    inventory_unit_id: UUID,
    status_data: InventoryUnitStatusUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the status"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Update inventory unit status."""
    try:
        return await service.update_inventory_unit_status(inventory_unit_id, status_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{inventory_unit_id}/condition", response_model=InventoryUnitResponse)
async def update_inventory_unit_condition(
    inventory_unit_id: UUID,
    condition_data: InventoryUnitConditionUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the condition"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Update inventory unit condition."""
    try:
        return await service.update_inventory_unit_condition(inventory_unit_id, condition_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{inventory_unit_id}/rental-days", response_model=InventoryUnitResponse)
async def add_rental_days(
    inventory_unit_id: UUID,
    rental_data: InventoryUnitRentalUpdate,
    updated_by: Optional[str] = Query(None, description="User updating the rental days"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Add rental days to inventory unit."""
    try:
        return await service.add_rental_days(inventory_unit_id, rental_data, updated_by)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/bulk/status", response_model=dict)
async def bulk_update_status(
    bulk_update: InventoryUnitBulkStatusUpdate,
    updated_by: Optional[str] = Query(None, description="User performing the bulk update"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Bulk update status for multiple inventory units."""
    try:
        updated_count = await service.bulk_update_status(bulk_update, updated_by)
        return {"updated_count": updated_count, "requested_count": len(bulk_update.inventory_unit_ids)}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/bulk/location", response_model=dict)
async def bulk_update_location(
    bulk_update: InventoryUnitBulkLocationUpdate,
    updated_by: Optional[str] = Query(None, description="User performing the bulk update"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Bulk update location for multiple inventory units."""
    try:
        updated_count = await service.bulk_update_location(bulk_update, updated_by)
        return {"updated_count": updated_count, "requested_count": len(bulk_update.inventory_unit_ids)}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{inventory_unit_id}", response_model=dict)
async def delete_inventory_unit(
    inventory_unit_id: UUID,
    deleted_by: Optional[str] = Query(None, description="User deleting the inventory unit"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Soft delete inventory unit."""
    try:
        success = await service.delete_inventory_unit(inventory_unit_id, deleted_by)
        if success:
            return {"message": "Inventory unit deleted successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete inventory unit")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Utility endpoints
@router.get("/check/code/{inventory_code}/availability", response_model=dict)
async def check_inventory_code_availability(
    inventory_code: str,
    exclude_id: Optional[UUID] = Query(None, description="Exclude this ID from the check"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Check if inventory code is available."""
    try:
        is_available = await service.check_inventory_code_availability(inventory_code, exclude_id)
        return {"inventory_code": inventory_code, "is_available": is_available}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/check/serial/{serial_number}/availability", response_model=dict)
async def check_serial_number_availability(
    serial_number: str,
    exclude_id: Optional[UUID] = Query(None, description="Exclude this ID from the check"),
    service: InventoryUnitService = Depends(get_inventory_unit_service)
):
    """Check if serial number is available."""
    try:
        is_available = await service.check_serial_number_availability(serial_number, exclude_id)
        return {"serial_number": serial_number, "is_available": is_available}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))