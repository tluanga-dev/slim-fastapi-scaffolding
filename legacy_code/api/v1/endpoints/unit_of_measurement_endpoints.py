from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.unit_of_measurement import (
    CreateUnitOfMeasurementUseCase,
    GetUnitOfMeasurementUseCase,
    UpdateUnitOfMeasurementUseCase,
    DeleteUnitOfMeasurementUseCase,
    ListUnitsOfMeasurementUseCase
)
from ....infrastructure.repositories.unit_of_measurement_repository import UnitOfMeasurementRepositoryImpl
from ..schemas.unit_of_measurement_schemas import (
    UnitOfMeasurementCreate,
    UnitOfMeasurementUpdate,
    UnitOfMeasurementResponse,
    UnitOfMeasurementListResponse
)
from ..dependencies.database import get_db

router = APIRouter(tags=["units-of-measurement"])


async def get_unit_repository(db: AsyncSession = Depends(get_db)) -> UnitOfMeasurementRepositoryImpl:
    """Get unit of measurement repository instance."""
    return UnitOfMeasurementRepositoryImpl(db)


@router.post("/", response_model=UnitOfMeasurementResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_of_measurement(
    unit_data: UnitOfMeasurementCreate,
    repository: UnitOfMeasurementRepositoryImpl = Depends(get_unit_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Create a new unit of measurement."""
    use_case = CreateUnitOfMeasurementUseCase(repository)
    
    try:
        unit = await use_case.execute(
            name=unit_data.name,
            abbreviation=unit_data.abbreviation,
            description=unit_data.description,
            created_by=current_user_id
        )
        return UnitOfMeasurementResponse.model_validate(unit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{unit_id}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement(
    unit_id: UUID,
    repository: UnitOfMeasurementRepositoryImpl = Depends(get_unit_repository)
):
    """Get a unit of measurement by ID."""
    use_case = GetUnitOfMeasurementUseCase(repository)
    unit = await use_case.execute(unit_id)
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit of measurement with id {unit_id} not found"
        )
    
    return UnitOfMeasurementResponse.model_validate(unit)


@router.get("/by-name/{name}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement_by_name(
    name: str,
    repository: UnitOfMeasurementRepositoryImpl = Depends(get_unit_repository)
):
    """Get a unit of measurement by name."""
    unit = await repository.get_by_name(name)
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit of measurement with name '{name}' not found"
        )
    
    return UnitOfMeasurementResponse.model_validate(unit)


@router.get("/by-abbreviation/{abbreviation}", response_model=UnitOfMeasurementResponse)
async def get_unit_of_measurement_by_abbreviation(
    abbreviation: str,
    repository: UnitOfMeasurementRepositoryImpl = Depends(get_unit_repository)
):
    """Get a unit of measurement by abbreviation."""
    unit = await repository.get_by_abbreviation(abbreviation.upper())
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit of measurement with abbreviation '{abbreviation}' not found"
        )
    
    return UnitOfMeasurementResponse.model_validate(unit)


@router.get("/", response_model=UnitOfMeasurementListResponse)
async def list_units_of_measurement(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    search: Optional[str] = Query(None, description="Search in name or abbreviation"),
    repository: UnitOfMeasurementRepositoryImpl = Depends(get_unit_repository)
):
    """List units of measurement with pagination and search."""
    use_case = ListUnitsOfMeasurementUseCase(repository)
    
    if search:
        # Search by name pattern
        units = await repository.search_by_name(search, skip=skip, limit=limit)
        # Note: For simplicity, we're not implementing total count for search
        # In a real app, you'd want to implement a separate count query
        total_count = len(units)
    else:
        units = await use_case.execute(skip=skip, limit=limit)
        # Note: For simplicity, we're not implementing total count
        # In a real app, you'd want to implement a separate count query
        total_count = len(units)
    
    return UnitOfMeasurementListResponse(
        items=[UnitOfMeasurementResponse.model_validate(unit) for unit in units],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.put("/{unit_id}", response_model=UnitOfMeasurementResponse)
async def update_unit_of_measurement(
    unit_id: UUID,
    unit_data: UnitOfMeasurementUpdate,
    repository: UnitOfMeasurementRepositoryImpl = Depends(get_unit_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update an existing unit of measurement."""
    use_case = UpdateUnitOfMeasurementUseCase(repository)
    
    try:
        unit = await use_case.execute(
            unit_id=unit_id,
            name=unit_data.name,
            abbreviation=unit_data.abbreviation,
            description=unit_data.description,
            updated_by=current_user_id
        )
        return UnitOfMeasurementResponse.model_validate(unit)
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


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit_of_measurement(
    unit_id: UUID,
    repository: UnitOfMeasurementRepositoryImpl = Depends(get_unit_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Delete (deactivate) a unit of measurement."""
    use_case = DeleteUnitOfMeasurementUseCase(repository)
    
    success = await use_case.execute(unit_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit of measurement with id {unit_id} not found"
        )