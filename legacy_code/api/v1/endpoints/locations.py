from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.database import get_db
from ....application.use_cases.location_use_cases import LocationUseCases
from ....infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
from ....domain.entities.location import LocationType
from ..schemas.location_schemas import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationListResponse,
    LocationTypeEnum,
    AssignManagerRequest
)

router = APIRouter(tags=["locations"])


def get_location_use_cases(db: AsyncSession = Depends(get_db)) -> LocationUseCases:
    """Dependency injection for location use cases."""
    repository = SQLAlchemyLocationRepository(db)
    return LocationUseCases(repository)


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    use_cases: LocationUseCases = Depends(get_location_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Create a new location."""
    try:
        # Convert enum for domain
        location_type = LocationType(location_data.location_type.value)
        
        location = await use_cases.create_location(
            location_code=location_data.location_code,
            location_name=location_data.location_name,
            location_type=location_type,
            address=location_data.address,
            city=location_data.city,
            state=location_data.state,
            country=location_data.country,
            postal_code=location_data.postal_code,
            contact_number=location_data.contact_number,
            email=location_data.email,
            manager_user_id=location_data.manager_user_id,
            created_by="system"  # TODO: Use current_user
        )
        return location
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    use_cases: LocationUseCases = Depends(get_location_use_cases)
):
    """Get a location by ID."""
    try:
        location = await use_cases.get_location(location_id)
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/code/{location_code}", response_model=LocationResponse)
async def get_location_by_code(
    location_code: str,
    use_cases: LocationUseCases = Depends(get_location_use_cases)
):
    """Get a location by code."""
    try:
        location = await use_cases.get_location_by_code(location_code)
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=LocationListResponse)
async def list_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_type: Optional[LocationTypeEnum] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    use_cases: LocationUseCases = Depends(get_location_use_cases)
):
    """List locations with pagination and filters."""
    # Convert enum for domain if provided
    domain_location_type = LocationType(location_type.value) if location_type else None
    
    locations, total = await use_cases.list_locations(
        skip=skip,
        limit=limit,
        location_type=domain_location_type,
        city=city,
        state=state,
        is_active=is_active
    )
    
    return LocationListResponse(
        items=locations,
        total=total,
        skip=skip,
        limit=limit
    )


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    location_data: LocationUpdate,
    use_cases: LocationUseCases = Depends(get_location_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Update a location."""
    try:
        location = await use_cases.update_location(
            location_id=location_id,
            location_name=location_data.location_name,
            address=location_data.address,
            city=location_data.city,
            state=location_data.state,
            country=location_data.country,
            postal_code=location_data.postal_code,
            contact_number=location_data.contact_number,
            email=location_data.email,
            manager_user_id=location_data.manager_user_id,
            updated_by="system"  # TODO: Use current_user
        )
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{location_id}/deactivate", response_model=LocationResponse)
async def deactivate_location(
    location_id: UUID,
    use_cases: LocationUseCases = Depends(get_location_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Deactivate a location."""
    try:
        location = await use_cases.deactivate_location(
            location_id,
            updated_by="system"  # TODO: Use current_user
        )
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{location_id}/activate", response_model=LocationResponse)
async def activate_location(
    location_id: UUID,
    use_cases: LocationUseCases = Depends(get_location_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Activate a location."""
    try:
        location = await use_cases.activate_location(
            location_id,
            updated_by="system"  # TODO: Use current_user
        )
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    use_cases: LocationUseCases = Depends(get_location_use_cases)
):
    """Delete a location (soft delete)."""
    success = await use_cases.delete_location(location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")


@router.post("/{location_id}/assign-manager", response_model=LocationResponse)
async def assign_manager(
    location_id: UUID,
    request: AssignManagerRequest,
    use_cases: LocationUseCases = Depends(get_location_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Assign a manager to a location."""
    try:
        location = await use_cases.assign_manager_to_location(
            location_id,
            request.manager_user_id,
            updated_by="system"  # TODO: Use current_user
        )
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{location_id}/remove-manager", response_model=LocationResponse)
async def remove_manager(
    location_id: UUID,
    use_cases: LocationUseCases = Depends(get_location_use_cases),
    # current_user: str = Depends(get_current_user)  # TODO: Implement authentication
):
    """Remove manager from a location."""
    try:
        location = await use_cases.remove_manager_from_location(
            location_id,
            updated_by="system"  # TODO: Use current_user
        )
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/manager/{manager_user_id}/locations", response_model=list[LocationResponse])
async def get_locations_by_manager(
    manager_user_id: UUID,
    use_cases: LocationUseCases = Depends(get_location_use_cases)
):
    """Get all locations managed by a specific user."""
    locations = await use_cases.get_locations_by_manager(manager_user_id)
    return locations