from datetime import date, datetime
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.rental_return import (
    InitiateReturnRequest,
    ProcessPartialReturnRequest,
    CalculateLateFeeRequest,
    AssessDamageRequest,
    CompleteInspectionRequest,
    FinalizeReturnRequest,
    ReleaseDepositRequest,
    ReverseDepositReleaseRequest,
    RentalReturnResponse,
    RentalReturnListResponse,
    PartialReturnValidationResponse,
    LateFeeCalculationResponse,
    ProjectedLateFeeResponse,
    InspectionSummaryResponse,
    FinalizationPreviewResponse,
    DepositPreviewResponse,
    DepositReleaseResponse,
    DepositReversalResponse,
    RentalReturnFilters,
    InspectionReportResponse
)
from ....domain.value_objects.rental_return_type import ReturnStatus, ReturnType
from ....application.use_cases.rental_return import (
    InitiateReturnUseCase,
    CalculateLateFeeUseCase,
    ProcessPartialReturnUseCase,
    AssessDamageUseCase,
    FinalizeReturnUseCase,
    ReleaseDepositUseCase
)
from ....infrastructure.repositories.rental_return_repository import SQLAlchemyRentalReturnRepository
from ....infrastructure.repositories.rental_return_line_repository import SQLAlchemyRentalReturnLineRepository
from ....infrastructure.repositories.inspection_report_repository import SQLAlchemyInspectionReportRepository
from ....infrastructure.repositories.transaction_header_repository import SQLAlchemyTransactionHeaderRepository
from ....infrastructure.repositories.transaction_line_repository import SQLAlchemyTransactionLineRepository
from ....infrastructure.repositories.inventory_unit_repository import SQLAlchemyInventoryUnitRepository
from ....infrastructure.repositories.stock_level_repository import SQLAlchemyStockLevelRepository
from ....infrastructure.repositories.item_repository import ItemRepositoryImpl
from ..dependencies.database import get_db


router = APIRouter(prefix="/rental-returns", tags=["Rental Returns"])


# Dependency functions
def get_initiate_return_use_case(db: AsyncSession = Depends(get_db)) -> InitiateReturnUseCase:
    """Get InitiateReturnUseCase with dependencies."""
    return InitiateReturnUseCase(
        return_repository=SQLAlchemyRentalReturnRepository(db),
        line_repository=SQLAlchemyRentalReturnLineRepository(db),
        transaction_repository=SQLAlchemyTransactionHeaderRepository(db),
        transaction_line_repository=SQLAlchemyTransactionLineRepository(db),
        inventory_repository=SQLAlchemyInventoryUnitRepository(db)
    )


def get_calculate_late_fee_use_case(db: AsyncSession = Depends(get_db)) -> CalculateLateFeeUseCase:
    """Get CalculateLateFeeUseCase with dependencies."""
    return CalculateLateFeeUseCase(
        return_repository=SQLAlchemyRentalReturnRepository(db),
        line_repository=SQLAlchemyRentalReturnLineRepository(db),
        transaction_repository=SQLAlchemyTransactionHeaderRepository(db),
        item_repository=ItemRepositoryImpl(db)
    )


def get_process_partial_return_use_case(db: AsyncSession = Depends(get_db)) -> ProcessPartialReturnUseCase:
    """Get ProcessPartialReturnUseCase with dependencies."""
    return ProcessPartialReturnUseCase(
        return_repository=SQLAlchemyRentalReturnRepository(db),
        line_repository=SQLAlchemyRentalReturnLineRepository(db),
        inventory_repository=SQLAlchemyInventoryUnitRepository(db),
        stock_repository=SQLAlchemyStockLevelRepository(db)
    )


def get_assess_damage_use_case(db: AsyncSession = Depends(get_db)) -> AssessDamageUseCase:
    """Get AssessDamageUseCase with dependencies."""
    return AssessDamageUseCase(
        return_repository=SQLAlchemyRentalReturnRepository(db),
        line_repository=SQLAlchemyRentalReturnLineRepository(db),
        inspection_repository=SQLAlchemyInspectionReportRepository(db)
    )


def get_finalize_return_use_case(db: AsyncSession = Depends(get_db)) -> FinalizeReturnUseCase:
    """Get FinalizeReturnUseCase with dependencies."""
    return FinalizeReturnUseCase(
        return_repository=SQLAlchemyRentalReturnRepository(db),
        line_repository=SQLAlchemyRentalReturnLineRepository(db),
        transaction_repository=SQLAlchemyTransactionHeaderRepository(db),
        inventory_repository=SQLAlchemyInventoryUnitRepository(db),
        stock_repository=SQLAlchemyStockLevelRepository(db)
    )


def get_release_deposit_use_case(db: AsyncSession = Depends(get_db)) -> ReleaseDepositUseCase:
    """Get ReleaseDepositUseCase with dependencies."""
    return ReleaseDepositUseCase(
        return_repository=SQLAlchemyRentalReturnRepository(db),
        transaction_repository=SQLAlchemyTransactionHeaderRepository(db)
    )


# Endpoints
@router.post("/", response_model=RentalReturnResponse, status_code=status.HTTP_201_CREATED)
async def initiate_return(
    request: InitiateReturnRequest,
    use_case: InitiateReturnUseCase = Depends(get_initiate_return_use_case)
):
    """Initiate a new rental return."""
    try:
        rental_return = await use_case.execute(
            rental_transaction_id=request.rental_transaction_id,
            return_date=request.return_date,
            return_items=request.return_items,
            return_location_id=request.return_location_id,
            return_type=request.return_type,
            notes=request.notes,
            processed_by=request.processed_by
        )
        return RentalReturnResponse.model_validate(rental_return)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate return: {str(e)}")


@router.get("/", response_model=RentalReturnListResponse)
async def list_returns(
    transaction_id: UUID = Query(None),
    return_status: ReturnStatus = Query(None),
    return_type: ReturnType = Query(None),
    location_id: UUID = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List rental returns with filters and pagination."""
    try:
        repository = SQLAlchemyRentalReturnRepository(db)
        returns, total = await repository.list(
            skip=skip,
            limit=limit,
            transaction_id=transaction_id,
            return_status=return_status,
            return_type=return_type,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active
        )
        
        return RentalReturnListResponse(
            returns=[RentalReturnResponse.model_validate(ret) for ret in returns],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list returns: {str(e)}")


@router.get("/{return_id}", response_model=RentalReturnResponse)
async def get_return(
    return_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific rental return by ID."""
    try:
        repository = SQLAlchemyRentalReturnRepository(db)
        rental_return = await repository.get_by_id(return_id)
        
        if not rental_return:
            raise HTTPException(status_code=404, detail="Rental return not found")
            
        return RentalReturnResponse.model_validate(rental_return)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get return: {str(e)}")


@router.post("/{return_id}/process-partial", response_model=RentalReturnResponse)
async def process_partial_return(
    return_id: UUID,
    request: ProcessPartialReturnRequest,
    use_case: ProcessPartialReturnUseCase = Depends(get_process_partial_return_use_case)
):
    """Process a partial return with inventory updates."""
    try:
        rental_return = await use_case.execute(
            return_id=return_id,
            line_updates=request.line_updates,
            process_inventory=request.process_inventory,
            updated_by=request.updated_by
        )
        return RentalReturnResponse.model_validate(rental_return)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process partial return: {str(e)}")


@router.post("/{return_id}/validate-partial", response_model=PartialReturnValidationResponse)
async def validate_partial_return(
    return_id: UUID,
    proposed_quantities: dict,
    use_case: ProcessPartialReturnUseCase = Depends(get_process_partial_return_use_case)
):
    """Validate a proposed partial return without processing it."""
    try:
        # Convert string keys to UUIDs
        proposed_quantities_typed = {UUID(k): v for k, v in proposed_quantities.items()}
        
        validation_result = await use_case.validate_partial_return(
            return_id=return_id,
            proposed_quantities=proposed_quantities_typed
        )
        return PartialReturnValidationResponse(**validation_result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate partial return: {str(e)}")


@router.post("/{return_id}/calculate-late-fee", response_model=LateFeeCalculationResponse)
async def calculate_late_fee(
    return_id: UUID,
    request: CalculateLateFeeRequest,
    use_case: CalculateLateFeeUseCase = Depends(get_calculate_late_fee_use_case)
):
    """Calculate late fees for a return."""
    try:
        result = await use_case.execute(
            return_id=return_id,
            daily_late_fee_rate=request.daily_late_fee_rate,
            use_percentage_of_rental_rate=request.use_percentage_of_rental_rate,
            percentage_rate=request.percentage_rate,
            updated_by=request.updated_by
        )
        return LateFeeCalculationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate late fee: {str(e)}")


@router.post("/{return_id}/calculate-projected-late-fee", response_model=ProjectedLateFeeResponse)
async def calculate_projected_late_fee(
    return_id: UUID,
    projected_return_date: date,
    daily_late_fee_rate: float = Query(None),
    use_case: CalculateLateFeeUseCase = Depends(get_calculate_late_fee_use_case)
):
    """Calculate projected late fee for a future return date."""
    try:
        from decimal import Decimal
        rate = Decimal(str(daily_late_fee_rate)) if daily_late_fee_rate else None
        
        result = await use_case.calculate_projected_late_fee(
            return_id=return_id,
            projected_return_date=projected_return_date,
            daily_late_fee_rate=rate
        )
        return ProjectedLateFeeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate projected late fee: {str(e)}")


@router.post("/{return_id}/assess-damage", response_model=InspectionReportResponse)
async def assess_damage(
    return_id: UUID,
    request: AssessDamageRequest,
    use_case: AssessDamageUseCase = Depends(get_assess_damage_use_case)
):
    """Assess damage for returned items."""
    try:
        inspection_report = await use_case.execute(
            return_id=return_id,
            inspector_id=request.inspector_id,
            line_assessments=request.line_assessments,
            general_notes=request.general_notes,
            inspection_date=request.inspection_date
        )
        return InspectionReportResponse.model_validate(inspection_report)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assess damage: {str(e)}")


@router.post("/inspections/{inspection_id}/complete", response_model=InspectionReportResponse)
async def complete_inspection(
    inspection_id: UUID,
    request: CompleteInspectionRequest,
    use_case: AssessDamageUseCase = Depends(get_assess_damage_use_case)
):
    """Complete an inspection with approval/rejection."""
    try:
        inspection_report = await use_case.complete_inspection(
            inspection_report_id=inspection_id,
            approved=request.approved,
            approver_id=request.approver_id,
            approval_notes=request.approval_notes
        )
        return InspectionReportResponse.model_validate(inspection_report)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete inspection: {str(e)}")


@router.get("/{return_id}/inspection-summary", response_model=InspectionSummaryResponse)
async def get_inspection_summary(
    return_id: UUID,
    use_case: AssessDamageUseCase = Depends(get_assess_damage_use_case)
):
    """Get inspection summary for a return."""
    try:
        summary = await use_case.get_inspection_summary(return_id)
        return InspectionSummaryResponse(**summary)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get inspection summary: {str(e)}")


@router.post("/{return_id}/finalize", response_model=RentalReturnResponse)
async def finalize_return(
    return_id: UUID,
    request: FinalizeReturnRequest,
    use_case: FinalizeReturnUseCase = Depends(get_finalize_return_use_case)
):
    """Finalize a rental return."""
    try:
        rental_return = await use_case.execute(
            return_id=return_id,
            finalized_by=request.finalized_by,
            force_finalize=request.force_finalize,
            finalization_notes=request.finalization_notes
        )
        return RentalReturnResponse.model_validate(rental_return)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finalize return: {str(e)}")


@router.get("/{return_id}/finalization-preview", response_model=FinalizationPreviewResponse)
async def get_finalization_preview(
    return_id: UUID,
    use_case: FinalizeReturnUseCase = Depends(get_finalize_return_use_case)
):
    """Get a preview of what will happen when finalizing a return."""
    try:
        preview = await use_case.get_finalization_preview(return_id)
        return FinalizationPreviewResponse(**preview)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get finalization preview: {str(e)}")


@router.post("/{return_id}/release-deposit", response_model=DepositReleaseResponse)
async def release_deposit(
    return_id: UUID,
    request: ReleaseDepositRequest,
    use_case: ReleaseDepositUseCase = Depends(get_release_deposit_use_case)
):
    """Release security deposit for a completed return."""
    try:
        result = await use_case.execute(
            return_id=return_id,
            processed_by=request.processed_by,
            override_amount=request.override_amount,
            release_notes=request.release_notes
        )
        return DepositReleaseResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to release deposit: {str(e)}")


@router.get("/{return_id}/deposit-preview", response_model=DepositPreviewResponse)
async def get_deposit_preview(
    return_id: UUID,
    include_projections: bool = Query(False),
    use_case: ReleaseDepositUseCase = Depends(get_release_deposit_use_case)
):
    """Get deposit release preview without processing."""
    try:
        preview = await use_case.calculate_deposit_preview(
            return_id=return_id,
            include_projections=include_projections
        )
        return DepositPreviewResponse(**preview)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deposit preview: {str(e)}")


@router.post("/{return_id}/reverse-deposit-release", response_model=DepositReversalResponse)
async def reverse_deposit_release(
    return_id: UUID,
    request: ReverseDepositReleaseRequest,
    use_case: ReleaseDepositUseCase = Depends(get_release_deposit_use_case)
):
    """Reverse a deposit release for corrections."""
    try:
        result = await use_case.reverse_deposit_release(
            return_id=return_id,
            reason=request.reason,
            processed_by=request.processed_by
        )
        return DepositReversalResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reverse deposit release: {str(e)}")


# Utility endpoints
@router.get("/outstanding", response_model=RentalReturnListResponse)
async def get_outstanding_returns(
    customer_id: UUID = Query(None),
    location_id: UUID = Query(None),
    days_overdue: int = Query(None),  
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get outstanding returns (not completed)."""
    try:
        repository = SQLAlchemyRentalReturnRepository(db)
        returns = await repository.get_outstanding_returns(
            customer_id=customer_id,
            location_id=location_id,
            days_overdue=days_overdue
        )
        
        # Apply pagination manually since the repository method doesn't support it
        total = len(returns)
        paginated_returns = returns[skip:skip + limit]
        
        return RentalReturnListResponse(
            returns=[RentalReturnResponse.model_validate(ret) for ret in paginated_returns],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get outstanding returns: {str(e)}")


@router.get("/late", response_model=RentalReturnListResponse)
async def get_late_returns(
    as_of_date: date = Query(None),
    location_id: UUID = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get returns that are past due."""
    try:
        repository = SQLAlchemyRentalReturnRepository(db)
        returns = await repository.get_late_returns(
            as_of_date=as_of_date,
            location_id=location_id
        )
        
        # Apply pagination manually
        total = len(returns)
        paginated_returns = returns[skip:skip + limit]
        
        return RentalReturnListResponse(
            returns=[RentalReturnResponse.model_validate(ret) for ret in paginated_returns],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get late returns: {str(e)}")


@router.get("/needs-inspection", response_model=RentalReturnListResponse)
async def get_returns_needing_inspection(
    location_id: UUID = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get returns that need inspection."""
    try:
        repository = SQLAlchemyRentalReturnRepository(db)
        returns = await repository.get_returns_needing_inspection(location_id=location_id)
        
        # Apply pagination manually
        total = len(returns)
        paginated_returns = returns[skip:skip + limit]
        
        return RentalReturnListResponse(
            returns=[RentalReturnResponse.model_validate(ret) for ret in paginated_returns],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get returns needing inspection: {str(e)}")


@router.get("/statistics/status-counts")
async def get_return_status_counts(
    location_id: UUID = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get count of returns by status."""
    try:
        repository = SQLAlchemyRentalReturnRepository(db)
        counts = await repository.count_returns_by_status(
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
        return {"status_counts": counts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status counts: {str(e)}")


@router.get("/{return_id}/fees")
async def get_return_fees(
    return_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get calculated fees for a return."""
    try:
        repository = SQLAlchemyRentalReturnRepository(db)
        fees = await repository.calculate_total_fees(return_id)
        return {"return_id": str(return_id), "fees": fees}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get return fees: {str(e)}")