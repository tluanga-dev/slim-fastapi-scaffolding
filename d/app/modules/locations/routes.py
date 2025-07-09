from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.modules.locations.service import LocationService
from app.modules.locations.schemas import (
    LocationCreate, LocationUpdate, LocationContactUpdate,
    LocationManagerUpdate, LocationStatusUpdate, LocationResponse,
    LocationListResponse
)
from app.core.domain.entities.location import LocationType
from app.core.errors import NotFoundError, ValidationError
from app.shared.dependencies import get_location_service


router = APIRouter(tags=["locations"])


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    service: LocationService = Depends(get_location_service)
):
    """Create a new location."""
    try:
        return await service.create_location(location_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=LocationListResponse)
async def get_locations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    location_type: Optional[LocationType] = Query(None, description="Filter by location type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    country: Optional[str] = Query(None, description="Filter by country"),
    search: Optional[str] = Query(None, description="Search in name, code, address, and city"),
    service: LocationService = Depends(get_location_service)
):
    """Get locations with filtering and pagination."""
    try:
        return await service.get_locations(
            page=page,
            page_size=page_size,
            location_type=location_type,
            is_active=is_active,
            city=city,
            state=state,
            country=country,
            search=search
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location_by_id(
    location_id: UUID,
    service: LocationService = Depends(get_location_service)
):
    """Get location by ID."""
    try:
        return await service.get_location_by_id(location_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/code/{location_code}", response_model=LocationResponse)
async def get_location_by_code(
    location_code: str,
    service: LocationService = Depends(get_location_service)
):
    """Get location by location code."""
    try:
        return await service.get_location_by_code(location_code)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    update_data: LocationUpdate,
    service: LocationService = Depends(get_location_service)
):
    """Update location details."""
    try:
        return await service.update_location(location_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{location_id}/contact", response_model=LocationResponse)
async def update_location_contact(
    location_id: UUID,
    contact_data: LocationContactUpdate,
    service: LocationService = Depends(get_location_service)
):
    """Update location contact information."""
    try:
        return await service.update_contact_info(location_id, contact_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{location_id}/manager", response_model=LocationResponse)
async def update_location_manager(
    location_id: UUID,
    manager_data: LocationManagerUpdate,
    service: LocationService = Depends(get_location_service)
):
    """Update location manager."""
    try:
        return await service.update_manager(location_id, manager_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{location_id}/status", response_model=LocationResponse)
async def update_location_status(
    location_id: UUID,
    status_data: LocationStatusUpdate,
    service: LocationService = Depends(get_location_service)
):
    """Update location status (activate/deactivate)."""
    try:
        return await service.update_status(location_id, status_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    service: LocationService = Depends(get_location_service)
):
    """Delete location."""
    try:
        success = await service.delete_location(location_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/manager/{manager_user_id}", response_model=List[LocationResponse])
async def get_locations_by_manager(
    manager_user_id: UUID,
    service: LocationService = Depends(get_location_service)
):
    """Get all locations managed by a specific user."""
    try:
        return await service.get_locations_by_manager(manager_user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/type/{location_type}", response_model=List[LocationResponse])
async def get_locations_by_type(
    location_type: LocationType,
    service: LocationService = Depends(get_location_service)
):
    """Get all locations of a specific type."""
    try:
        return await service.get_locations_by_type(location_type)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))