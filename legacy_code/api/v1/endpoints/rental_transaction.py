from typing import List, Optional
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.database import get_db
from ..schemas.rental_transaction import (
    CreateRentalBookingRequest,
    CheckoutRentalRequest,
    ProcessRentalPickupRequest,
    CompleteRentalReturnRequest,
    ExtendRentalPeriodRequest,
    CancelRentalBookingRequest,
    RentalBookingResponse,
    RentalCheckoutResponse,
    RentalPickupResponse,
    RentalReturnResponse,
    RentalExtensionResponse,
    RentalCancellationResponse,
    RentalTransactionResponse,
    RentalTransactionFilter,
    RentalAvailabilityCheckRequest,
    RentalAvailabilityResponse
)

from ....infrastructure.repositories.transaction_header_repository import (
    SQLAlchemyTransactionHeaderRepository
)
from ....infrastructure.repositories.transaction_line_repository import (
    SQLAlchemyTransactionLineRepository
)
from ....infrastructure.repositories.customer_repository import (
    SQLAlchemyCustomerRepository
)
from ....infrastructure.repositories.inventory_unit_repository import (
    SQLAlchemyInventoryUnitRepository
)
from ....infrastructure.repositories.item_repository import (
    ItemRepositoryImpl
)
from ....infrastructure.repositories.stock_level_repository import (
    SQLAlchemyStockLevelRepository
)
from ....infrastructure.repositories.rental_return_repository import (
    SQLAlchemyRentalReturnRepository
)
from ....infrastructure.repositories.rental_return_line_repository import (
    SQLAlchemyRentalReturnLineRepository
)
from ....infrastructure.repositories.inspection_report_repository import (
    SQLAlchemyInspectionReportRepository
)

from ....application.use_cases.rental_transaction.create_rental_booking_use_case import (
    CreateRentalBookingUseCase, RentalBookingItem
)
from ....application.use_cases.rental_transaction.checkout_rental_use_case import (
    CheckoutRentalUseCase
)
from ....application.use_cases.rental_transaction.process_rental_pickup_use_case import (
    ProcessRentalPickupUseCase, RentalPickupItem
)
from ....application.use_cases.rental_transaction.complete_rental_return_use_case import (
    CompleteRentalReturnUseCase, ReturnItem
)
from ....application.use_cases.rental_transaction.extend_rental_period_use_case import (
    ExtendRentalPeriodUseCase
)
from ....application.use_cases.rental_transaction.cancel_rental_booking_use_case import (
    CancelRentalBookingUseCase
)

router = APIRouter(prefix="/rental-transactions", tags=["rental-transactions"])


@router.post("/bookings", response_model=RentalBookingResponse, status_code=status.HTTP_201_CREATED)
async def create_rental_booking(
    request: CreateRentalBookingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"  # TODO: Get from auth
):
    """Create a new rental booking."""
    # Initialize repositories
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    transaction_line_repo = SQLAlchemyTransactionLineRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)
    inventory_unit_repo = SQLAlchemyInventoryUnitRepository(db)
    item_repo = ItemRepositoryImpl(db)
    stock_level_repo = SQLAlchemyStockLevelRepository(db)
    
    # Initialize use case
    use_case = CreateRentalBookingUseCase(
        transaction_repo=transaction_repo,
        transaction_line_repo=transaction_line_repo,
        customer_repo=customer_repo,
        inventory_unit_repo=inventory_unit_repo,
        item_repo=item_repo,
        stock_level_repo=stock_level_repo
    )
    
    try:
        # Convert request items to use case DTOs
        booking_items = [
            RentalBookingItem(
                item_id=item.item_id,
                quantity=item.quantity,
                rental_start_date=item.rental_start_date,
                rental_end_date=item.rental_end_date,
                inventory_unit_ids=item.inventory_unit_ids,
                custom_price=item.custom_price,
                discount_percentage=item.discount_percentage,
                notes=item.notes
            )
            for item in request.items
        ]
        
        # Execute use case
        transaction = await use_case.execute(
            customer_id=request.customer_id,
            location_id=request.location_id,
            items=booking_items,
            deposit_percentage=request.deposit_percentage,
            tax_rate=request.tax_rate,
            sales_person_id=request.sales_person_id,
            notes=request.notes,
            created_by=current_user
        )
        
        # Load lines for response
        lines = await transaction_line_repo.get_by_transaction_id(transaction.id)
        transaction._lines = lines
        
        return RentalBookingResponse(
            transaction=RentalTransactionResponse.model_validate(transaction),
            message="Rental booking created successfully",
            booking_summary={
                "booking_number": transaction.transaction_number,
                "rental_period": {
                    "start": transaction.rental_start_date,
                    "end": transaction.rental_end_date,
                    "days": transaction.rental_days
                },
                "items_count": len([l for l in lines if l.line_type == "PRODUCT"]),
                "total_amount": transaction.total_amount,
                "deposit_required": transaction.deposit_amount
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{transaction_id}/checkout", response_model=RentalCheckoutResponse)
async def checkout_rental(
    transaction_id: UUID,
    request: CheckoutRentalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"
):
    """Process rental checkout - confirm booking and process payment."""
    # Initialize repositories
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    transaction_line_repo = SQLAlchemyTransactionLineRepository(db)
    inventory_unit_repo = SQLAlchemyInventoryUnitRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)
    
    # Initialize use case
    use_case = CheckoutRentalUseCase(
        transaction_repo=transaction_repo,
        transaction_line_repo=transaction_line_repo,
        inventory_unit_repo=inventory_unit_repo,
        customer_repo=customer_repo
    )
    
    try:
        # Execute use case
        transaction = await use_case.execute(
            transaction_id=transaction_id,
            payment_amount=request.payment_amount,
            payment_method=request.payment_method,
            payment_reference=request.payment_reference,
            collect_full_payment=request.collect_full_payment,
            additional_notes=request.additional_notes,
            processed_by=current_user
        )
        
        # Load lines for response
        lines = await transaction_line_repo.get_by_transaction_id(transaction.id)
        transaction._lines = lines
        
        return RentalCheckoutResponse(
            transaction=RentalTransactionResponse.model_validate(transaction),
            message="Rental checkout completed successfully",
            payment_summary={
                "payment_method": request.payment_method.value,
                "amount_paid": request.payment_amount,
                "total_paid": transaction.paid_amount,
                "balance_due": transaction.balance_due,
                "payment_status": transaction.payment_status.value
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{transaction_id}/pickup", response_model=RentalPickupResponse)
async def process_rental_pickup(
    transaction_id: UUID,
    request: ProcessRentalPickupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"
):
    """Process rental pickup when customer collects items."""
    # Initialize repositories
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    transaction_line_repo = SQLAlchemyTransactionLineRepository(db)
    inventory_unit_repo = SQLAlchemyInventoryUnitRepository(db)
    inspection_repo = SQLAlchemyInspectionReportRepository(db)
    
    # Initialize use case
    use_case = ProcessRentalPickupUseCase(
        transaction_repo=transaction_repo,
        transaction_line_repo=transaction_line_repo,
        inventory_unit_repo=inventory_unit_repo,
        inspection_repo=inspection_repo
    )
    
    try:
        # Convert request items
        pickup_items = [
            RentalPickupItem(
                inventory_unit_id=item.inventory_unit_id,
                serial_number=item.serial_number,
                condition_notes=item.condition_notes,
                photos=item.photos,
                accessories_included=item.accessories_included
            )
            for item in request.pickup_items
        ]
        
        # Execute use case
        result = await use_case.execute(
            transaction_id=transaction_id,
            pickup_items=pickup_items,
            pickup_person_name=request.pickup_person_name,
            pickup_person_id=request.pickup_person_id,
            pickup_notes=request.pickup_notes,
            processed_by=current_user
        )
        
        # Load lines for response
        lines = await transaction_line_repo.get_by_transaction_id(transaction_id)
        result["transaction"]._lines = lines
        
        return RentalPickupResponse(
            transaction=RentalTransactionResponse.model_validate(result["transaction"]),
            inspection_reports=[
                {
                    "id": str(report.id),
                    "inspection_date": report.inspection_date,
                    "condition_grade": report.condition_grade.value,
                    "notes": report.notes
                }
                for report in result["inspection_reports"]
            ],
            pickup_summary=result["pickup_summary"],
            message="Rental pickup processed successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{transaction_id}/return", response_model=RentalReturnResponse)
async def complete_rental_return(
    transaction_id: UUID,
    request: CompleteRentalReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"
):
    """Complete rental return process."""
    # Initialize repositories
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    transaction_line_repo = SQLAlchemyTransactionLineRepository(db)
    rental_return_repo = SQLAlchemyRentalReturnRepository(db)
    rental_return_line_repo = SQLAlchemyRentalReturnLineRepository(db)
    inventory_unit_repo = SQLAlchemyInventoryUnitRepository(db)
    inspection_repo = SQLAlchemyInspectionReportRepository(db)
    
    # Initialize use case
    use_case = CompleteRentalReturnUseCase(
        transaction_repo=transaction_repo,
        transaction_line_repo=transaction_line_repo,
        rental_return_repo=rental_return_repo,
        rental_return_line_repo=rental_return_line_repo,
        inventory_unit_repo=inventory_unit_repo,
        inspection_repo=inspection_repo
    )
    
    try:
        # Convert request items
        return_items = [
            ReturnItem(
                inventory_unit_id=item.inventory_unit_id,
                condition_grade=item.condition_grade,
                is_damaged=item.is_damaged,
                damage_description=item.damage_description,
                damage_photos=item.damage_photos,
                missing_accessories=item.missing_accessories,
                cleaning_required=item.cleaning_required
            )
            for item in request.return_items
        ]
        
        # Execute use case
        result = await use_case.execute(
            transaction_id=transaction_id,
            return_items=return_items,
            is_partial_return=request.is_partial_return,
            late_fee_waived=request.late_fee_waived,
            damage_fee_percentage=request.damage_fee_percentage,
            process_refund=request.process_refund,
            refund_method=request.refund_method,
            return_notes=request.return_notes,
            processed_by=current_user
        )
        
        # Load lines for response
        lines = await transaction_line_repo.get_by_transaction_id(transaction_id)
        result["transaction"]._lines = lines
        
        return RentalReturnResponse(
            transaction=RentalTransactionResponse.model_validate(result["transaction"]),
            rental_return={
                "id": str(result["rental_return"].id),
                "return_number": result["rental_return"].return_number,
                "return_date": result["rental_return"].return_date,
                "status": result["rental_return"].status.value
            },
            return_summary=result["summary"],
            message="Rental return processed successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{transaction_id}/extend", response_model=RentalExtensionResponse)
async def extend_rental_period(
    transaction_id: UUID,
    request: ExtendRentalPeriodRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"
):
    """Extend an active rental period."""
    # Initialize repositories
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    transaction_line_repo = SQLAlchemyTransactionLineRepository(db)
    inventory_unit_repo = SQLAlchemyInventoryUnitRepository(db)
    item_repo = ItemRepositoryImpl(db)
    
    # Initialize use case
    use_case = ExtendRentalPeriodUseCase(
        transaction_repo=transaction_repo,
        transaction_line_repo=transaction_line_repo,
        inventory_unit_repo=inventory_unit_repo,
        item_repo=item_repo
    )
    
    try:
        # Execute use case
        transaction = await use_case.execute(
            transaction_id=transaction_id,
            new_end_date=request.new_end_date,
            payment_amount=request.payment_amount,
            payment_method=request.payment_method,
            payment_reference=request.payment_reference,
            apply_discount_percentage=request.apply_discount_percentage,
            extension_notes=request.extension_notes,
            processed_by=current_user
        )
        
        # Load lines for response
        lines = await transaction_line_repo.get_by_transaction_id(transaction.id)
        transaction._lines = lines
        
        # Calculate extension details
        original_end_date = transaction.rental_end_date
        extension_days = (request.new_end_date - original_end_date).days
        
        return RentalExtensionResponse(
            transaction=RentalTransactionResponse.model_validate(transaction),
            extension_summary={
                "original_end_date": original_end_date,
                "new_end_date": request.new_end_date,
                "extension_days": extension_days,
                "new_total_days": transaction.rental_days,
                "extension_charge": sum(
                    line.line_total for line in lines 
                    if "Extension" in line.description
                )
            },
            message="Rental period extended successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{transaction_id}/cancel", response_model=RentalCancellationResponse)
async def cancel_rental_booking(
    transaction_id: UUID,
    request: CancelRentalBookingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"
):
    """Cancel a rental booking."""
    # Initialize repositories
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    transaction_line_repo = SQLAlchemyTransactionLineRepository(db)
    inventory_unit_repo = SQLAlchemyInventoryUnitRepository(db)
    
    # Initialize use case
    use_case = CancelRentalBookingUseCase(
        transaction_repo=transaction_repo,
        transaction_line_repo=transaction_line_repo,
        inventory_unit_repo=inventory_unit_repo
    )
    
    try:
        # Execute use case
        transaction = await use_case.execute(
            transaction_id=transaction_id,
            cancellation_reason=request.cancellation_reason,
            refund_percentage=request.refund_percentage,
            cancellation_fee=request.cancellation_fee,
            refund_method=request.refund_method,
            refund_reference=request.refund_reference,
            cancelled_by=current_user
        )
        
        # Load lines for response
        lines = await transaction_line_repo.get_by_transaction_id(transaction.id)
        transaction._lines = lines
        
        # Calculate refund details
        refund_amount = None
        if transaction.payment_status == "REFUNDED":
            # Calculate from notes or payment history
            refund_amount = transaction.total_amount - transaction.paid_amount
        
        return RentalCancellationResponse(
            transaction=RentalTransactionResponse.model_validate(transaction),
            refund_summary={
                "cancellation_reason": request.cancellation_reason,
                "refund_percentage": request.refund_percentage,
                "refund_amount": refund_amount,
                "cancellation_fee": request.cancellation_fee,
                "refund_method": request.refund_method.value if request.refund_method else None
            },
            message="Rental booking cancelled successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{transaction_id}", response_model=RentalTransactionResponse)
async def get_rental_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get rental transaction by ID."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    transaction_line_repo = SQLAlchemyTransactionLineRepository(db)
    
    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.transaction_type != "RENTAL":
        raise HTTPException(status_code=400, detail="Not a rental transaction")
    
    # Load lines
    lines = await transaction_line_repo.get_by_transaction_id(transaction.id)
    transaction._lines = lines
    
    return RentalTransactionResponse.model_validate(transaction)


@router.get("/", response_model=List[RentalTransactionResponse])
async def list_rental_transactions(
    filter_params: RentalTransactionFilter = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List rental transactions with filtering."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    
    # This would need custom repository method for filtering
    # For now, return all rentals
    transactions = await transaction_repo.list(skip=skip, limit=limit)
    
    # Filter for rentals only
    rental_transactions = [t for t in transactions if t.transaction_type == "RENTAL"]
    
    return [RentalTransactionResponse.model_validate(t) for t in rental_transactions]


@router.post("/availability/check", response_model=RentalAvailabilityResponse)
async def check_rental_availability(
    request: RentalAvailabilityCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """Check rental availability for specific SKU and period."""
    inventory_unit_repo = SQLAlchemyInventoryUnitRepository(db)
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    
    try:
        # Get all units for SKU at location
        all_units = await inventory_unit_repo.get_by_sku_and_location(
            request.item_id, request.location_id
        )
        
        # Filter available units
        available_units = []
        conflicting_rentals = []
        
        for unit in all_units:
            if unit.current_status != "AVAILABLE_RENT":
                continue
            
            # Check for conflicts
            transactions = await transaction_repo.get_active_rentals_by_unit(unit.id)
            
            has_conflict = False
            for trans in transactions:
                if (trans.rental_start_date <= request.rental_end_date and 
                    trans.rental_end_date >= request.rental_start_date):
                    has_conflict = True
                    conflicting_rentals.append({
                        "transaction_id": str(trans.id),
                        "transaction_number": trans.transaction_number,
                        "rental_period": {
                            "start": trans.rental_start_date,
                            "end": trans.rental_end_date
                        }
                    })
            
            if not has_conflict:
                available_units.append({
                    "unit_id": str(unit.id),
                    "serial_number": unit.serial_number,
                    "condition_grade": unit.condition_grade.value
                })
        
        return RentalAvailabilityResponse(
            item_id=request.item_id,
            location_id=request.location_id,
            rental_period={
                "start": request.rental_start_date,
                "end": request.rental_end_date
            },
            requested_quantity=request.quantity,
            available_quantity=len(available_units),
            is_available=len(available_units) >= request.quantity,
            available_units=available_units[:request.quantity],
            conflicting_rentals=conflicting_rentals
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")