from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.database import get_db
from ....infrastructure.repositories.inventory_unit_repository import SQLAlchemyInventoryUnitRepository
from ....infrastructure.repositories.stock_level_repository import SQLAlchemyStockLevelRepository
from ....infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
from ....infrastructure.repositories.item_repository import ItemRepositoryImpl

from ....application.use_cases.inventory import (
    CreateInventoryUnitUseCase,
    UpdateInventoryStatusUseCase,
    InspectInventoryUseCase,
    TransferInventoryUseCase,
    CheckStockAvailabilityUseCase,
    UpdateStockLevelsUseCase
)

from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade

from ..schemas.inventory import (
    InventoryUnitCreate,
    InventoryUnitUpdate,
    InventoryUnitResponse,
    InventoryUnitListResponse,
    StockLevelCreate,
    StockLevelUpdate,
    StockLevelResponse,
    StockLevelListResponse,
    InventoryStatusUpdate,
    InventoryInspection,
    InventoryTransfer,
    BulkInventoryTransfer,
    SkuInventoryTransfer,
    StockOperation,
    StockReconciliation,
    BulkReceive,
    StockAvailabilityQuery,
    MultiSkuAvailabilityQuery,
    StockAvailabilityResponse,
    LowStockAlert,
    OverstockReport,
    StockValuation,
    InventoryStatusCount,
    InventoryConditionCount
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


# Inventory Unit Endpoints
@router.post("/units", response_model=InventoryUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_unit(
    unit_data: InventoryUnitCreate,
    db: AsyncSession = Depends(get_db)
) -> InventoryUnitResponse:
    """Create a new inventory unit."""
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    
    use_case = CreateInventoryUnitUseCase(inventory_repo, stock_repo, item_repo)
    
    try:
        unit = await use_case.execute(
            inventory_code=unit_data.inventory_code,
            item_id=unit_data.item_id,
            location_id=unit_data.location_id,
            serial_number=unit_data.serial_number,
            current_status=unit_data.current_status,
            condition_grade=unit_data.condition_grade,
            purchase_date=unit_data.purchase_date,
            purchase_cost=unit_data.purchase_cost,
            notes=unit_data.notes
        )
        return InventoryUnitResponse.model_validate(unit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Specific inventory unit endpoints (must come before parameterized routes)
@router.get("/units/needing-inspection", response_model=List[InventoryUnitResponse])
async def get_units_needing_inspection(
    days_since_last: int = Query(30, ge=1),
    location_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> List[InventoryUnitResponse]:
    """Get inventory units needing inspection."""
    repo = SQLAlchemyInventoryUnitRepository(db)
    units = await repo.get_units_needing_inspection(days_since_last, location_id)
    return [InventoryUnitResponse.model_validate(unit) for unit in units]


@router.get("/units/status-count", response_model=InventoryStatusCount)
async def get_inventory_status_count(
    location_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> InventoryStatusCount:
    """Get count of inventory units by status."""
    repo = SQLAlchemyInventoryUnitRepository(db)
    counts = await repo.count_by_status(location_id)
    return InventoryStatusCount(status_counts=counts)


@router.get("/units/condition-count", response_model=InventoryConditionCount)
async def get_inventory_condition_count(
    location_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> InventoryConditionCount:
    """Get count of inventory units by condition."""
    repo = SQLAlchemyInventoryUnitRepository(db)
    counts = await repo.count_by_condition(location_id)
    return InventoryConditionCount(condition_counts=counts)


# Parameterized inventory unit endpoints
@router.get("/units/{unit_id}", response_model=InventoryUnitResponse)
async def get_inventory_unit(
    unit_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> InventoryUnitResponse:
    """Get inventory unit by ID."""
    repo = SQLAlchemyInventoryUnitRepository(db)
    unit = await repo.get_by_id(unit_id)
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory unit with id {unit_id} not found"
        )
    
    return InventoryUnitResponse.model_validate(unit)


@router.get("/units/code/{inventory_code}", response_model=InventoryUnitResponse)
async def get_inventory_unit_by_code(
    inventory_code: str,
    db: AsyncSession = Depends(get_db)
) -> InventoryUnitResponse:
    """Get inventory unit by code."""
    repo = SQLAlchemyInventoryUnitRepository(db)
    unit = await repo.get_by_code(inventory_code)
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory unit with code {inventory_code} not found"
        )
    
    return InventoryUnitResponse.model_validate(unit)


@router.get("/units", response_model=InventoryUnitListResponse)
async def list_inventory_units(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    status: Optional[InventoryStatus] = None,
    condition_grade: Optional[ConditionGrade] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db)
) -> InventoryUnitListResponse:
    """List inventory units with filters."""
    repo = SQLAlchemyInventoryUnitRepository(db)
    
    units, total = await repo.list(
        skip=skip,
        limit=limit,
        item_id=item_id,
        location_id=location_id,
        status=status,
        condition_grade=condition_grade,
        is_active=is_active
    )
    
    return InventoryUnitListResponse(
        items=[InventoryUnitResponse.model_validate(unit) for unit in units],
        total=total,
        skip=skip,
        limit=limit
    )


@router.put("/units/{unit_id}/status", response_model=InventoryUnitResponse)
async def update_inventory_status(
    unit_id: UUID,
    status_update: InventoryStatusUpdate,
    db: AsyncSession = Depends(get_db)
) -> InventoryUnitResponse:
    """Update inventory unit status."""
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)
    
    use_case = UpdateInventoryStatusUseCase(inventory_repo, stock_repo)
    
    try:
        unit = await use_case.execute(
            inventory_id=unit_id,
            new_status=status_update.new_status,
            reason=status_update.reason
        )
        return InventoryUnitResponse.model_validate(unit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/units/{unit_id}/inspect", response_model=InventoryUnitResponse)
async def inspect_inventory_unit(
    unit_id: UUID,
    inspection: InventoryInspection,
    db: AsyncSession = Depends(get_db)
) -> InventoryUnitResponse:
    """Inspect an inventory unit."""
    repo = SQLAlchemyInventoryUnitRepository(db)
    use_case = InspectInventoryUseCase(repo)
    
    try:
        unit = await use_case.execute(
            inventory_id=unit_id,
            condition_grade=inspection.condition_grade,
            inspection_notes=inspection.inspection_notes,
            passed_inspection=inspection.passed_inspection,
            photos=inspection.photos
        )
        return InventoryUnitResponse.model_validate(unit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/units/{unit_id}/transfer", response_model=InventoryUnitResponse)
async def transfer_inventory_unit(
    unit_id: UUID,
    transfer: InventoryTransfer,
    db: AsyncSession = Depends(get_db)
) -> InventoryUnitResponse:
    """Transfer inventory unit to another location."""
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = TransferInventoryUseCase(inventory_repo, stock_repo, location_repo)
    
    try:
        unit = await use_case.execute(
            inventory_id=unit_id,
            to_location_id=transfer.to_location_id,
            transfer_reason=transfer.transfer_reason
        )
        return InventoryUnitResponse.model_validate(unit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/units/transfer/bulk", response_model=dict)
async def bulk_transfer_inventory(
    transfer: BulkInventoryTransfer,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Transfer multiple inventory units."""
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = TransferInventoryUseCase(inventory_repo, stock_repo, location_repo)
    
    try:
        transferred_units, errors = await use_case.bulk_transfer(
            inventory_ids=transfer.inventory_ids,
            to_location_id=transfer.to_location_id,
            transfer_reason=transfer.transfer_reason
        )
        
        return {
            "transferred": [InventoryUnitResponse.model_validate(unit) for unit in transferred_units],
            "errors": errors
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/units/transfer/by-sku", response_model=List[InventoryUnitResponse])
async def transfer_by_sku(
    transfer: SkuInventoryTransfer,
    db: AsyncSession = Depends(get_db)
) -> List[InventoryUnitResponse]:
    """Transfer inventory by SKU."""
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = TransferInventoryUseCase(inventory_repo, stock_repo, location_repo)
    
    try:
        units = await use_case.transfer_by_sku(
            item_id=transfer.item_id,
            from_location_id=transfer.from_location_id,
            to_location_id=transfer.to_location_id,
            quantity=transfer.quantity,
            transfer_reason=transfer.transfer_reason,
            condition_grade=transfer.condition_grade
        )
        return [InventoryUnitResponse.model_validate(unit) for unit in units]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



# Stock Level Endpoints
@router.post("/stock-levels", response_model=StockLevelResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_level(
    stock_data: StockLevelCreate,
    db: AsyncSession = Depends(get_db)
) -> StockLevelResponse:
    """Create a new stock level record."""
    repo = SQLAlchemyStockLevelRepository(db)
    
    # Check if stock level already exists
    existing = await repo.get_by_item_location(stock_data.item_id, stock_data.location_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock level already exists for Item {stock_data.item_id} at location {stock_data.location_id}"
        )
    
    from ....domain.entities.stock_level import StockLevel
    stock_level = StockLevel(
        item_id=stock_data.item_id,
        location_id=stock_data.location_id,
        quantity_on_hand=stock_data.quantity_on_hand,
        quantity_available=stock_data.quantity_on_hand,
        quantity_reserved=0,
        quantity_in_transit=0,
        quantity_damaged=0,
        reorder_point=stock_data.reorder_point,
        reorder_quantity=stock_data.reorder_quantity,
        maximum_stock=stock_data.maximum_stock
    )
    
    created = await repo.create(stock_level)
    return StockLevelResponse.model_validate(created)


@router.get("/stock-levels", response_model=StockLevelListResponse)
async def list_stock_levels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_id: Optional[UUID] = None,
    item_id: Optional[UUID] = None,
    low_stock_only: bool = False,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db)
) -> StockLevelListResponse:
    """List stock levels with filters."""
    repo = SQLAlchemyStockLevelRepository(db)
    
    items, total = await repo.list(
        skip=skip,
        limit=limit,
        location_id=location_id,
        item_id=item_id,
        low_stock_only=low_stock_only,
        is_active=is_active
    )
    
    return StockLevelListResponse(
        items=[StockLevelResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit
    )


# Specific stock-levels endpoints (must come before parameterized routes)
@router.get("/stock-levels/low-stock/alerts", response_model=List[LowStockAlert])
async def get_low_stock_alerts(
    location_id: Optional[UUID] = None,
    include_zero_stock: bool = True,
    db: AsyncSession = Depends(get_db)
) -> List[LowStockAlert]:
    """Get low stock alerts."""
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = CheckStockAvailabilityUseCase(inventory_repo, stock_repo, item_repo, location_repo)
    
    alerts = await use_case.get_low_stock_alerts(location_id, include_zero_stock)
    return [LowStockAlert(**alert) for alert in alerts]


@router.get("/stock-levels/overstock/report", response_model=List[OverstockReport])
async def get_overstock_report(
    location_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> List[OverstockReport]:
    """Get overstock report."""
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = UpdateStockLevelsUseCase(stock_repo, item_repo, location_repo)
    
    report = await use_case.get_overstock_report(location_id)
    return [OverstockReport(**item) for item in report]


@router.get("/stock-levels/valuation", response_model=StockValuation)
async def get_stock_valuation(
    location_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> StockValuation:
    """Get stock valuation summary."""
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = UpdateStockLevelsUseCase(stock_repo, item_repo, location_repo)
    
    valuation = await use_case.get_stock_valuation(location_id)
    return StockValuation(**valuation)


# Parameterized stock-levels endpoints
@router.get("/stock-levels/{item_id}/{location_id}", response_model=StockLevelResponse)
async def get_stock_level(
    item_id: UUID,
    location_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> StockLevelResponse:
    """Get stock level for Item at location."""
    repo = SQLAlchemyStockLevelRepository(db)
    stock_level = await repo.get_by_item_location(item_id, location_id)
    
    if not stock_level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock level not found for Item {item_id} at location {location_id}"
        )
    
    return StockLevelResponse.model_validate(stock_level)


@router.put("/stock-levels/{item_id}/{location_id}/operation", response_model=StockLevelResponse)
async def perform_stock_operation(
    item_id: UUID,
    location_id: UUID,
    operation: StockOperation,
    db: AsyncSession = Depends(get_db)
) -> StockLevelResponse:
    """Perform stock operation."""
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = UpdateStockLevelsUseCase(stock_repo, item_repo, location_repo)
    
    try:
        stock_level = await use_case.execute(
            item_id=item_id,
            location_id=location_id,
            operation=operation.operation,
            quantity=operation.quantity,
            reason=operation.reason
        )
        return StockLevelResponse.model_validate(stock_level)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/stock-levels/{item_id}/{location_id}/parameters", response_model=StockLevelResponse)
async def update_stock_parameters(
    item_id: UUID,
    location_id: UUID,
    params: StockLevelUpdate,
    db: AsyncSession = Depends(get_db)
) -> StockLevelResponse:
    """Update stock level reorder parameters."""
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = UpdateStockLevelsUseCase(stock_repo, item_repo, location_repo)
    
    try:
        stock_level = await use_case.set_reorder_parameters(
            item_id=item_id,
            location_id=location_id,
            reorder_point=params.reorder_point or 0,
            reorder_quantity=params.reorder_quantity or 1,
            maximum_stock=params.maximum_stock
        )
        return StockLevelResponse.model_validate(stock_level)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/stock-levels/{location_id}/bulk-receive", response_model=List[StockLevelResponse])
async def bulk_receive_stock(
    location_id: UUID,
    receive_data: BulkReceive,
    db: AsyncSession = Depends(get_db)
) -> List[StockLevelResponse]:
    """Bulk receive stock."""
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = UpdateStockLevelsUseCase(stock_repo, item_repo, location_repo)
    
    try:
        stock_levels = await use_case.bulk_receive(
            items=[item.model_dump() for item in receive_data.items],
            location_id=location_id,
            reference_number=receive_data.reference_number
        )
        return [StockLevelResponse.model_validate(level) for level in stock_levels]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/stock-levels/{item_id}/{location_id}/reconcile", response_model=StockLevelResponse)
async def reconcile_stock(
    item_id: UUID,
    location_id: UUID,
    reconciliation: StockReconciliation,
    db: AsyncSession = Depends(get_db)
) -> StockLevelResponse:
    """Reconcile stock to match physical count."""
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = UpdateStockLevelsUseCase(stock_repo, item_repo, location_repo)
    
    try:
        stock_level = await use_case.reconcile_stock(
            item_id=item_id,
            location_id=location_id,
            physical_count=reconciliation.physical_count,
            reason=reconciliation.reason
        )
        return StockLevelResponse.model_validate(stock_level)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Stock Analysis Endpoints
@router.post("/availability/check", response_model=StockAvailabilityResponse)
async def check_stock_availability(
    query: StockAvailabilityQuery,
    db: AsyncSession = Depends(get_db)
) -> StockAvailabilityResponse:
    """Check stock availability."""
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = CheckStockAvailabilityUseCase(inventory_repo, stock_repo, item_repo, location_repo)
    
    try:
        result = await use_case.execute(
            item_id=query.item_id,
            quantity=query.quantity,
            location_id=query.location_id,
            for_sale=query.for_sale,
            min_condition_grade=query.min_condition_grade
        )
        return StockAvailabilityResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/availability/check-multiple", response_model=dict)
async def check_multiple_stock_availability(
    query: MultiSkuAvailabilityQuery,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Check availability for multiple SKUs."""
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)
    item_repo = ItemRepositoryImpl(db)
    location_repo = SQLAlchemyLocationRepository(db)
    
    use_case = CheckStockAvailabilityUseCase(inventory_repo, stock_repo, item_repo, location_repo)
    
    try:
        results = await use_case.check_multiple_skus(
            items=query.items,
            location_id=query.location_id,
            for_sale=query.for_sale
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


