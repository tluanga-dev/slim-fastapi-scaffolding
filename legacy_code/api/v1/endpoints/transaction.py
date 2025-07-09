from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.transaction import (
    CancelTransactionUseCase,
    CreateRentalTransactionUseCase,
    CreateSaleTransactionUseCase,
    GetTransactionHistoryUseCase,
    ProcessPaymentUseCase,
)
from ....application.use_cases.transaction.create_purchase_transaction_use_case import (
    CreatePurchaseTransactionUseCase,
)
from ....application.use_cases.transaction.receive_goods_use_case import (
    ReceiveGoodsUseCase,
)
from ....application.use_cases.transaction.record_completed_purchase_return_use_case import (
    RecordCompletedPurchaseReturnUseCase,
)
from ....application.use_cases.transaction.record_completed_purchase_use_case import (
    RecordCompletedPurchaseUseCase,
)
from ....application.use_cases.transaction.record_completed_sale_return_use_case import (
    RecordCompletedSaleReturnUseCase,
)
from ....application.use_cases.transaction.record_completed_sale_use_case import (
    RecordCompletedSaleUseCase,
)
from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.value_objects.transaction_type import (
    LineItemType,
    PaymentMethod,
    PaymentStatus,
    RentalPeriodUnit,
    TransactionStatus,
    TransactionType,
)
from ....domain.value_objects.customer_type import CustomerType
from ....infrastructure.repositories.supplier_repository import (
    SQLAlchemySupplierRepository,
)
from ....infrastructure.repositories.customer_repository import (
    SQLAlchemyCustomerRepository,
)
from ....infrastructure.repositories.inventory_unit_repository import (
    SQLAlchemyInventoryUnitRepository,
)
from ....infrastructure.repositories.location_repository_impl import (
    SQLAlchemyLocationRepository,
)
from ....infrastructure.repositories.item_repository import ItemRepositoryImpl
from ....infrastructure.repositories.stock_level_repository import (
    SQLAlchemyStockLevelRepository,
)
from ....infrastructure.repositories.transaction_header_repository import (
    SQLAlchemyTransactionHeaderRepository,
)
from ....infrastructure.repositories.transaction_line_repository import (
    SQLAlchemyTransactionLineRepository,
)
from ..dependencies.database import get_db
from ..schemas.purchase_transaction import (  # Legacy/deprecated imports:
    CompletedPurchaseItemRecord,
    CompletedPurchaseRecord,
    GoodsReceiptRequest,
    PurchaseOrderApprovalRequest,
    PurchaseTransactionCreate,
)
from ..schemas.return_transaction import (
    CompletedPurchaseReturnRecord,
    CompletedReturnItemRecord,
    CompletedSaleReturnRecord,
    ReturnValidationRequest,
    ReturnValidationResponse,
)
from ..schemas.sale_transaction import CompletedSaleItemRecord, CompletedSaleRecord
from ..schemas.sale_transaction import (
    SaleTransactionCreate as LegacySaleTransactionCreate,
)
from ..schemas.transaction import (
    CancelTransactionRequest,
    CompleteRentalReturnRequest,
    CustomerTransactionSummary,
    DailyTransactionSummary,
    OverdueRental,
    PaymentRequest,
    ProcessPartialReturnRequest,
    ProcessReturnLineRequest,
    RefundRequest,
    RentalTransactionCreate,
    RevenueReport,
    SaleTransactionCreate,
    TransactionFilterParams,
    TransactionHeaderResponse,
    TransactionHeaderUpdate,
    TransactionLineResponse,
    TransactionListResponse,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


# Transaction Creation Endpoints
@router.post(
    "/sales/completed",
    response_model=TransactionHeaderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_completed_sale(
    transaction_data: CompletedSaleRecord, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """Record a completed sale transaction and process inventory."""
    try:
        # Create repository instances
        transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
        line_repo = SQLAlchemyTransactionLineRepository(db)
        customer_repo = SQLAlchemyCustomerRepository(db)
        item_repo = ItemRepositoryImpl(db)
        inventory_repo = SQLAlchemyInventoryUnitRepository(db)
        stock_repo = SQLAlchemyStockLevelRepository(db)

        use_case = RecordCompletedSaleUseCase(
            transaction_repo, line_repo, item_repo, customer_repo, inventory_repo, stock_repo
        )

        # Convert items to the expected format
        items = []
        for item in transaction_data.items:
            items.append(
                {
                    "item_id": item.item_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "discount_percentage": item.discount_percentage,
                    "serial_numbers": item.serial_numbers,
                    "condition_notes": item.condition_notes,
                    "notes": item.notes,
                }
            )

        transaction = await use_case.execute(
            customer_id=transaction_data.customer_id,
            location_id=transaction_data.location_id,
            items=items,
            sale_date=transaction_data.sale_date,
            tax_rate=transaction_data.tax_rate,
            discount_amount=transaction_data.discount_amount,
            receipt_number=transaction_data.receipt_number,
            receipt_date=transaction_data.receipt_date,
            notes=transaction_data.notes,
            sales_person_id=transaction_data.sales_person_id,
        )
        
        # Ensure all changes are committed
        await db.commit()

        # Create response without loading lines for now (to debug the issue)
        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = []  # Empty lines for now

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Legacy endpoint for backward compatibility
@router.post(
    "/sales",
    response_model=TransactionHeaderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sale_transaction_legacy(
    transaction_data: LegacySaleTransactionCreate, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """DEPRECATED: Create a new sale transaction. Use /sales/completed endpoint instead."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)
    item_repo = ItemRepositoryImpl(db)
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)

    use_case = CreateSaleTransactionUseCase(
        transaction_repo, line_repo, item_repo, inventory_repo, stock_repo, customer_repo
    )

    try:
        transaction = await use_case.execute(
            customer_id=transaction_data.customer_id,
            location_id=transaction_data.location_id,
            sales_person_id=transaction_data.sales_person_id,
            items=transaction_data.items,
            discount_amount=transaction_data.discount_amount,
            tax_rate=transaction_data.tax_rate,
            notes=transaction_data.notes,
            auto_reserve=transaction_data.auto_reserve,
        )

        # Load lines for response
        lines = await line_repo.get_by_transaction(transaction.id)

        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/rentals",
    response_model=TransactionHeaderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rental_transaction(
    transaction_data: RentalTransactionCreate, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """Create a new rental transaction."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)
    location_repo = SQLAlchemyLocationRepository(db)
    item_repo = ItemRepositoryImpl(db)
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)

    use_case = CreateRentalTransactionUseCase(
        transaction_repo, line_repo, item_repo, inventory_repo, customer_repo
    )

    try:
        transaction = await use_case.execute(
            customer_id=transaction_data.customer_id,
            location_id=transaction_data.location_id,
            sales_person_id=transaction_data.sales_person_id,
            rental_start_date=transaction_data.rental_start_date,
            rental_end_date=transaction_data.rental_end_date,
            items=transaction_data.items,
            deposit_amount=transaction_data.deposit_amount,
            discount_amount=transaction_data.discount_amount,
            tax_rate=transaction_data.tax_rate,
            notes=transaction_data.notes,
            auto_reserve=transaction_data.auto_reserve,
        )

        # Load lines for response
        lines = await line_repo.get_by_transaction(transaction.id)

        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Transaction Retrieval Endpoints
@router.get("/{transaction_id}", response_model=TransactionHeaderResponse)
async def get_transaction(
    transaction_id: UUID,
    include_lines: bool = Query(True, description="Include transaction lines"),
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """Get transaction by ID."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )

    response = TransactionHeaderResponse.model_validate(transaction)

    if include_lines:
        lines = await line_repo.get_by_transaction(transaction_id)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

    return response


@router.get("/number/{transaction_number}", response_model=TransactionHeaderResponse)
async def get_transaction_by_number(
    transaction_number: str,
    include_lines: bool = Query(True, description="Include transaction lines"),
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """Get transaction by transaction number."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    transaction = await transaction_repo.get_by_number(transaction_number)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with number {transaction_number} not found",
        )

    response = TransactionHeaderResponse.model_validate(transaction)

    if include_lines:
        lines = await line_repo.get_by_transaction(transaction.id)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

    return response


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    customer_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_cancelled: bool = False,
    include_lines: bool = False,
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """List transactions with filters."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    # Handle include_cancelled by adjusting status filter
    is_active = None if include_cancelled else True

    transactions, total = await transaction_repo.list(
        skip=skip,
        limit=limit,
        transaction_type=transaction_type,
        status=status,
        payment_status=payment_status,
        customer_id=customer_id,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
        is_active=is_active,
    )

    items = []
    for transaction in transactions:
        response = TransactionHeaderResponse.model_validate(transaction)
        if include_lines:
            lines = await line_repo.get_by_transaction(transaction.id)
            response.lines = [
                TransactionLineResponse.model_validate(line) for line in lines
            ]
        items.append(response)

    return TransactionListResponse(items=items, total=total, skip=skip, limit=limit)


# Transaction Operations Endpoints
@router.post("/{transaction_id}/payment", response_model=TransactionHeaderResponse)
async def process_payment(
    transaction_id: UUID, payment: PaymentRequest, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """Process payment for a transaction."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)

    use_case = ProcessPaymentUseCase(transaction_repo, inventory_repo, stock_repo)

    try:
        transaction = await use_case.execute(
            transaction_id=transaction_id,
            payment_amount=payment.payment_amount,
            payment_method=payment.payment_method,
            payment_reference=payment.payment_reference,
            process_inventory=payment.process_inventory,
        )

        # Load lines for response
        lines = await line_repo.get_by_transaction(transaction.id)

        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{transaction_id}/refund", response_model=TransactionHeaderResponse)
async def process_refund(
    transaction_id: UUID, refund: RefundRequest, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """Process refund for a transaction."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )

    try:
        transaction.process_refund(
            refund_amount=refund.refund_amount,
            reason=refund.reason,
            refunded_by="api_user",  # Should come from auth context
        )

        updated = await transaction_repo.update(transaction_id, transaction)

        # Load lines for response
        lines = await line_repo.get_by_transaction(updated.id)

        response = TransactionHeaderResponse.model_validate(updated)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{transaction_id}/cancel", response_model=TransactionHeaderResponse)
async def cancel_transaction(
    transaction_id: UUID,
    cancel_request: CancelTransactionRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """Cancel a transaction."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)

    use_case = CancelTransactionUseCase(
        transaction_repo, line_repo, inventory_repo, stock_repo
    )

    try:
        transaction = await use_case.execute(
            transaction_id=transaction_id,
            cancellation_reason=cancel_request.cancellation_reason,
            release_inventory=cancel_request.release_inventory,
        )

        # Load lines for response
        lines = await line_repo.get_by_transaction(transaction.id)

        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{transaction_id}/complete-return", response_model=TransactionHeaderResponse
)
async def complete_rental_return(
    transaction_id: UUID,
    return_request: CompleteRentalReturnRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """Complete rental return."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )

    try:
        transaction.complete_rental_return(
            return_date=return_request.actual_return_date,
            updated_by="api_user",  # Should come from auth context
        )

        # Update notes if provided
        if return_request.condition_notes:
            transaction.notes = (
                transaction.notes or ""
            ) + f"\n[RETURN CONDITION] {return_request.condition_notes}"

        updated = await transaction_repo.update(transaction_id, transaction)

        # Load lines for response
        lines = await line_repo.get_by_transaction(updated.id)

        response = TransactionHeaderResponse.model_validate(updated)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Partial Return Endpoints
@router.post(
    "/{transaction_id}/partial-return", response_model=TransactionHeaderResponse
)
async def process_partial_return(
    transaction_id: UUID,
    return_request: ProcessPartialReturnRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """Process partial return for transaction lines."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )

    try:
        # Process each line return
        for line_return in return_request.lines:
            line = await line_repo.get_by_id(line_return.line_id)
            if not line or line.transaction_id != transaction_id:
                raise ValueError(f"Line {line_return.line_id} not found in transaction")

            line.process_return(
                return_quantity=line_return.return_quantity,
                return_date=date.today(),
                return_reason=line_return.return_reason,
                updated_by="api_user",
            )

            await line_repo.update(line.id, line)

        # Update transaction if all lines are returned
        lines = await line_repo.get_by_transaction(transaction_id)
        all_returned = all(line.is_fully_returned for line in lines)

        if all_returned and transaction.status == TransactionStatus.IN_PROGRESS:
            transaction.update_status(TransactionStatus.COMPLETED, "api_user")
            await transaction_repo.update(transaction_id, transaction)

        # Process refund if requested
        if return_request.process_refund:
            # Calculate refund amount based on returned items
            refund_amount = sum(
                line.effective_unit_price * line_return.return_quantity
                for line_return in return_request.lines
                for line in lines
                if line.id == line_return.line_id
            )

            transaction.process_refund(
                refund_amount=refund_amount,
                reason="Partial return refund",
                refunded_by="api_user",
            )
            await transaction_repo.update(transaction_id, transaction)

        # Load updated transaction and lines
        updated = await transaction_repo.get_by_id(transaction_id)
        lines = await line_repo.get_by_transaction(transaction_id)

        response = TransactionHeaderResponse.model_validate(updated)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Update Endpoints
@router.patch("/{transaction_id}", response_model=TransactionHeaderResponse)
async def update_transaction(
    transaction_id: UUID,
    update_data: TransactionHeaderUpdate,
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """Update transaction header details."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )

    # Only allow updates on draft or pending transactions
    if transaction.status not in [TransactionStatus.DRAFT, TransactionStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update draft or pending transactions",
        )

    # Update fields
    if update_data.sales_person_id is not None:
        transaction.sales_person_id = update_data.sales_person_id

    if update_data.notes is not None:
        transaction.notes = update_data.notes

    if update_data.rental_end_date is not None and transaction.is_rental:
        if update_data.rental_end_date < transaction.rental_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rental end date must be after start date",
            )
        transaction.rental_end_date = update_data.rental_end_date

    transaction.update_timestamp("api_user")

    updated = await transaction_repo.update(transaction_id, transaction)

    # Load lines for response
    lines = await line_repo.get_by_transaction(updated.id)

    response = TransactionHeaderResponse.model_validate(updated)
    response.lines = [TransactionLineResponse.model_validate(line) for line in lines]

    return response


# Transaction History and Reports
@router.get("/customer/{customer_id}/history", response_model=TransactionListResponse)
async def get_customer_transaction_history(
    customer_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_lines: bool = False,
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """Get transaction history for a customer."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    use_case = GetTransactionHistoryUseCase(transaction_repo)

    transactions, total = await use_case.execute(
        customer_id=customer_id, skip=skip, limit=limit
    )

    items = []
    for transaction in transactions:
        response = TransactionHeaderResponse.model_validate(transaction)
        if include_lines:
            lines = await line_repo.get_by_transaction(transaction.id)
            response.lines = [
                TransactionLineResponse.model_validate(line) for line in lines
            ]
        items.append(response)

    return TransactionListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/customer/{customer_id}/summary", response_model=CustomerTransactionSummary
)
async def get_customer_transaction_summary(
    customer_id: UUID, db: AsyncSession = Depends(get_db)
) -> CustomerTransactionSummary:
    """Get transaction summary for a customer."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)

    customer = await customer_repo.get_by_id(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found",
        )

    summary = await transaction_repo.get_customer_summary(customer_id)

    return CustomerTransactionSummary(
        customer_id=str(customer_id),
        customer_name=f"{customer.first_name} {customer.last_name}",
        total_transactions=summary["total_transactions"],
        total_sales=summary["total_sales"],
        total_rentals=summary["total_rentals"],
        total_revenue=float(summary["total_revenue"]),
        total_paid=float(summary["total_paid"]),
        total_outstanding=float(summary["total_outstanding"]),
        active_rentals=summary["active_rentals"],
        overdue_rentals=summary["overdue_rentals"],
        customer_since=customer.created_at,
        customer_tier=customer.customer_tier.value if customer.customer_tier else None,
    )


@router.get("/reports/daily", response_model=List[DailyTransactionSummary])
async def get_daily_transaction_summary(
    start_date: date = Query(..., description="Start date for report"),
    end_date: date = Query(..., description="End date for report"),
    location_id: Optional[UUID] = None,
    include_transactions: bool = False,
    db: AsyncSession = Depends(get_db),
) -> List[DailyTransactionSummary]:
    """Get daily transaction summary report."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)

    summaries = await transaction_repo.get_daily_summary(
        start_date, end_date, location_id
    )

    result = []
    for summary in summaries:
        daily = DailyTransactionSummary(
            date=summary["date"],
            transaction_count=summary["transaction_count"],
            total_revenue=float(summary["total_revenue"]),
            total_paid=float(summary["total_paid"]),
            total_discount=float(summary["total_discount"]),
            total_tax=float(summary["total_tax"]),
            outstanding_amount=float(summary["outstanding_amount"]),
        )

        if include_transactions:
            transactions = await transaction_repo.get_by_date(
                summary["date"], location_id
            )
            daily.transactions = [
                TransactionHeaderResponse.model_validate(t) for t in transactions
            ]

        result.append(daily)

    return result


@router.get("/reports/revenue", response_model=List[RevenueReport])
async def get_revenue_report(
    start_date: date = Query(..., description="Start date for report"),
    end_date: date = Query(..., description="End date for report"),
    group_by: str = Query("day", description="Group by: day, week, month"),
    location_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> List[RevenueReport]:
    """Get revenue report."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)

    report = await transaction_repo.get_revenue_report(
        start_date, end_date, group_by, location_id
    )

    return [
        RevenueReport(
            period=item["period"],
            transaction_count=item["transaction_count"],
            total_revenue=float(item["total_revenue"]),
            total_paid=float(item["total_paid"]),
            outstanding=float(item["outstanding"]),
        )
        for item in report
    ]


@router.get("/rentals/overdue", response_model=List[OverdueRental])
async def get_overdue_rentals(
    location_id: Optional[UUID] = None,
    include_returned: bool = False,
    db: AsyncSession = Depends(get_db),
) -> List[OverdueRental]:
    """Get overdue rental transactions."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)

    overdue_transactions = await transaction_repo.get_overdue_rentals(
        location_id, include_returned
    )

    result = []
    for transaction in overdue_transactions:
        customer = await customer_repo.get_by_id(transaction.customer_id)
        lines = await line_repo.get_by_transaction(transaction.id)

        days_overdue = (date.today() - transaction.rental_end_date).days

        result.append(
            OverdueRental(
                transaction_id=transaction.id,
                transaction_number=transaction.transaction_number,
                customer_id=transaction.customer_id,
                customer_name=f"{customer.first_name} {customer.last_name}",
                rental_end_date=transaction.rental_end_date,
                days_overdue=days_overdue,
                total_amount=transaction.total_amount,
                balance_due=transaction.balance_due,
                items=[
                    line.description
                    for line in lines
                    if line.line_type == LineItemType.PRODUCT
                ],
            )
        )

    return result


# Soft Delete Endpoint
@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_transaction(
    transaction_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Soft delete a transaction (set is_active to False)."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)

    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )

    # Only allow deletion of draft or cancelled transactions
    if transaction.status not in [TransactionStatus.DRAFT, TransactionStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete draft or cancelled transactions",
        )

    await transaction_repo.delete(transaction_id)


# Purchase Transaction Endpoints
@router.post(
    "/purchases",
    response_model=TransactionHeaderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_completed_purchase(
    transaction_data: CompletedPurchaseRecord, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """Record a completed purchase transaction and create inventory records."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    supplier_repo = SQLAlchemySupplierRepository(db)
    item_repo = ItemRepositoryImpl(db)
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)

    use_case = RecordCompletedPurchaseUseCase(
        transaction_repo, line_repo, item_repo, supplier_repo, inventory_repo, stock_repo
    )

    try:
        # Convert items to the expected format
        items = []
        for item in transaction_data.items:
            items.append(
                {
                    "item_id": item.item_id,
                    "quantity": item.quantity,
                    "unit_cost": item.unit_cost,
                    "tax_rate": item.tax_rate,
                    "tax_amount": item.tax_amount,
                    "discount_amount": item.discount_amount,
                    "serial_numbers": item.serial_numbers,
                    "condition_notes": item.condition_notes,
                    "notes": item.notes,
                }
            )

        transaction = await use_case.execute(
            supplier_id=transaction_data.supplier_id,
            location_id=transaction_data.location_id,
            items=items,
            purchase_date=transaction_data.purchase_date,
            tax_rate=transaction_data.tax_rate,
            tax_amount=transaction_data.tax_amount,
            discount_amount=transaction_data.discount_amount,
            invoice_number=transaction_data.invoice_number,
            invoice_date=transaction_data.invoice_date,
            notes=transaction_data.notes,
        )

        # Commit the transaction to ensure data is persisted
        await db.commit()
        
        # Load lines for response
        lines = await line_repo.get_by_transaction(transaction.id)

        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )



# Legacy endpoint for backward compatibility
@router.post(
    "/purchases/legacy",
    response_model=TransactionHeaderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_purchase_transaction_legacy(
    transaction_data: PurchaseTransactionCreate, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """DEPRECATED: Create a new purchase order. Use /purchases endpoint instead."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)
    item_repo = ItemRepositoryImpl(db)
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)

    use_case = CreatePurchaseTransactionUseCase(
        transaction_repo, line_repo, item_repo, customer_repo, inventory_repo, stock_repo
    )

    try:
        # Convert items to the expected format
        items = []
        for item in transaction_data.items:
            items.append(
                {
                    "item_id": item.item_id,
                    "quantity": item.quantity,
                    "unit_cost": item.unit_cost,
                    "notes": item.notes,
                }
            )

        transaction = await use_case.execute(
            supplier_id=transaction_data.supplier_id,
            location_id=transaction_data.location_id,
            items=items,
            expected_delivery_date=transaction_data.expected_delivery_date,
            tax_rate=transaction_data.tax_rate,
            notes=transaction_data.notes,
        )

        # Load lines for response
        lines = await line_repo.get_by_transaction(transaction.id)

        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/purchases/list", response_model=TransactionListResponse)
async def list_purchase_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[TransactionStatus] = Query(None, alias="status"),
    supplier_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_lines: bool = False,
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """List purchase orders with filters."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)

    transactions, total = await transaction_repo.list(
        skip=skip,
        limit=limit,
        transaction_type=TransactionType.PURCHASE,
        status=status_filter,
        customer_id=supplier_id,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
    )

    items = []
    for transaction in transactions:
        response = TransactionHeaderResponse.model_validate(transaction)
        
        # For purchase transactions, include supplier (customer) details
        if transaction.customer_id:
            supplier = await customer_repo.get_by_id(transaction.customer_id)
            if supplier:
                from ..schemas.transaction import SupplierSummary
                
                response.supplier = SupplierSummary(
                    id=str(supplier.id),
                    company_name=supplier.business_name or "",
                    supplier_code=supplier.customer_code or "",
                    display_name=supplier.get_display_name(),
                    contact_person=f"{supplier.first_name or ''} {supplier.last_name or ''}".strip() if supplier.customer_type == CustomerType.BUSINESS else None,
                    supplier_type=supplier.customer_type.value if supplier.customer_type else "BUSINESS",
                    supplier_tier=supplier.customer_tier.value if supplier.customer_tier else "BRONZE",
                    is_active=supplier.is_active,
                    contacts=[],
                    addresses=[],
                    primary_email=None,
                    primary_phone=None
                )
        
        if include_lines:
            lines = await line_repo.get_by_transaction(transaction.id)
            response.lines = [
                TransactionLineResponse.model_validate(line) for line in lines
            ]
        items.append(response)

    return TransactionListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/purchases/{transaction_id}", response_model=TransactionHeaderResponse)
async def get_purchase_transaction(
    transaction_id: UUID,
    include_lines: bool = Query(True, description="Include transaction lines"),
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """Get purchase order by ID."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    supplier_repo = SQLAlchemySupplierRepository(db)

    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )

    if transaction.transaction_type != TransactionType.PURCHASE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction is not a purchase order",
        )

    response = TransactionHeaderResponse.model_validate(transaction)

    # For purchase transactions, include supplier details
    # Note: customer_id field contains supplier_id for purchase transactions
    if transaction.customer_id:
        supplier = await supplier_repo.get_by_id(transaction.customer_id)
        if supplier:
            from ..schemas.transaction import SupplierSummary, SupplierContact, SupplierAddress
            
            # Build supplier summary from supplier entity
            contacts = []
            addresses = []
            
            # Add primary contact if available
            if supplier.email:
                contacts.append(SupplierContact(
                    contact_type="EMAIL",
                    contact_value=supplier.email,
                    contact_label="Primary",
                    is_primary=True
                ))
            
            if supplier.phone:
                contacts.append(SupplierContact(
                    contact_type="PHONE", 
                    contact_value=supplier.phone,
                    contact_label="Primary",
                    is_primary=True
                ))
            
            # Add address if available
            if supplier.address:
                addresses.append(SupplierAddress(
                    street=supplier.address,
                    address_line2=None,
                    city=None,
                    state=None,
                    country=None,
                    postal_code=None
                ))
            
            response.supplier = SupplierSummary(
                id=str(supplier.id),
                company_name=supplier.company_name,
                supplier_code=supplier.supplier_code,
                display_name=supplier.company_name,
                contact_person=supplier.contact_person,
                supplier_type=supplier.supplier_type.value if supplier.supplier_type else "DISTRIBUTOR",
                supplier_tier=supplier.supplier_tier.value if supplier.supplier_tier else "STANDARD",
                is_active=supplier.is_active,
                contacts=contacts,
                addresses=addresses,
                primary_email=supplier.email,
                primary_phone=supplier.phone
            )

    if include_lines:
        lines = await line_repo.get_by_transaction(transaction_id)
        item_repo = ItemRepositoryImpl(db)
        
        # Enhanced line responses with item details
        enhanced_lines = []
        for line in lines:
            line_response = TransactionLineResponse.model_validate(line)
            
            # Get item details if item_id is present
            if line.item_id:
                item = await item_repo.get_by_id(line.item_id)
                if item:
                    # Add item information to the response
                    line_response.item_name = item.item_name
                    line_response.item_sku = item.sku
                    # Note: category and brand would need separate repository calls
                    # For now, we'll leave them as None to avoid additional complexity
                    line_response.item_category = None
                    line_response.item_brand = None
            
            enhanced_lines.append(line_response)
        
        response.lines = enhanced_lines
        
        # Calculate total items from lines
        total_items = sum(int(line.quantity) for line in lines)
        response.total_items = total_items
    else:
        # If lines are not included, we need to get the count separately
        lines = await line_repo.get_by_transaction(transaction_id)
        total_items = sum(int(line.quantity) for line in lines)
        response.total_items = total_items

    return response


# DEPRECATED ENDPOINTS: These are no longer needed in the new purchase flow
# They are kept for backward compatibility but will return appropriate errors


@router.post(
    "/purchases/{transaction_id}/receive", response_model=TransactionHeaderResponse
)
async def receive_goods_deprecated(
    transaction_id: UUID,
    receipt_data: GoodsReceiptRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """
    DEPRECATED: Process goods receipt for a purchase order.

    This endpoint is no longer supported in the new purchase flow where inventory
    is created immediately when recording a completed purchase.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "This endpoint is deprecated. In the new purchase flow, inventory is created "
            "immediately when recording a completed purchase via POST /transactions/purchases. "
            "There is no separate goods receipt process."
        ),
    )


@router.post(
    "/purchases/{transaction_id}/approve", response_model=TransactionHeaderResponse
)
async def approve_purchase_order_deprecated(
    transaction_id: UUID,
    approval_data: PurchaseOrderApprovalRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """
    DEPRECATED: Approve a purchase order.

    This endpoint is no longer supported in the new purchase flow where purchases
    are recorded as already completed transactions.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "This endpoint is deprecated. In the new purchase flow, purchases are recorded "
            "as already completed transactions via POST /transactions/purchases. "
            "There is no approval workflow."
        ),
    )


# Return Transaction Endpoints
@router.post(
    "/purchase-returns",
    response_model=TransactionHeaderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_completed_purchase_return(
    transaction_data: CompletedPurchaseReturnRecord, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """Record a completed purchase return transaction (returning items to supplier)."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)
    item_repo = ItemRepositoryImpl(db)
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)

    use_case = RecordCompletedPurchaseReturnUseCase(
        transaction_repo, line_repo, item_repo, customer_repo, inventory_repo, stock_repo
    )

    try:
        # Convert items to the expected format
        items = []
        for item in transaction_data.items:
            items.append(
                {
                    "item_id": item.item_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "serial_numbers": item.serial_numbers,
                    "condition_notes": item.condition_notes,
                    "return_reason": item.return_reason,
                    "notes": item.notes,
                }
            )

        transaction = await use_case.execute(
            supplier_id=transaction_data.supplier_id,
            location_id=transaction_data.location_id,
            original_purchase_id=transaction_data.original_purchase_id,
            items=items,
            return_date=transaction_data.return_date,
            refund_amount=transaction_data.refund_amount,
            return_authorization=transaction_data.return_authorization,
            return_reason=transaction_data.return_reason,
            notes=transaction_data.notes,
        )

        # Load lines for response
        lines = await line_repo.get_by_transaction(transaction.id)

        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/sale-returns",
    response_model=TransactionHeaderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_completed_sale_return(
    transaction_data: CompletedSaleReturnRecord, db: AsyncSession = Depends(get_db)
) -> TransactionHeaderResponse:
    """Record a completed sale return transaction (customer returning purchased items)."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)
    item_repo = ItemRepositoryImpl(db)
    inventory_repo = SQLAlchemyInventoryUnitRepository(db)
    stock_repo = SQLAlchemyStockLevelRepository(db)

    use_case = RecordCompletedSaleReturnUseCase(
        transaction_repo, line_repo, item_repo, customer_repo, inventory_repo, stock_repo
    )

    try:
        # Convert items to the expected format
        items = []
        for item in transaction_data.items:
            items.append(
                {
                    "item_id": item.item_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "serial_numbers": item.serial_numbers,
                    "condition_notes": item.condition_notes,
                    "return_reason": item.return_reason,
                    "notes": item.notes,
                }
            )

        transaction = await use_case.execute(
            customer_id=transaction_data.customer_id,
            location_id=transaction_data.location_id,
            original_sale_id=transaction_data.original_sale_id,
            items=items,
            return_date=transaction_data.return_date,
            refund_amount=transaction_data.refund_amount,
            refund_method=transaction_data.refund_method,
            return_reason=transaction_data.return_reason,
            restocking_fee=transaction_data.restocking_fee,
            notes=transaction_data.notes,
        )

        # Load lines for response
        lines = await line_repo.get_by_transaction(transaction.id)

        response = TransactionHeaderResponse.model_validate(transaction)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/returns", response_model=TransactionListResponse)
async def list_return_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[TransactionStatus] = Query(None, alias="status"),
    customer_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_lines: bool = False,
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """List return transactions with filters."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    transactions, total = await transaction_repo.list(
        skip=skip,
        limit=limit,
        transaction_type=TransactionType.RETURN,
        status=status_filter,
        customer_id=customer_id,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
    )

    items = []
    for transaction in transactions:
        response = TransactionHeaderResponse.model_validate(transaction)
        if include_lines:
            lines = await line_repo.get_by_transaction(transaction.id)
            response.lines = [
                TransactionLineResponse.model_validate(line) for line in lines
            ]
        items.append(response)

    return TransactionListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/returns/{transaction_id}", response_model=TransactionHeaderResponse)
async def get_return_transaction(
    transaction_id: UUID,
    include_lines: bool = Query(True, description="Include transaction lines"),
    db: AsyncSession = Depends(get_db),
) -> TransactionHeaderResponse:
    """Get return transaction by ID."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    transaction = await transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )

    if transaction.transaction_type != TransactionType.RETURN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction is not a return transaction",
        )

    response = TransactionHeaderResponse.model_validate(transaction)

    if include_lines:
        lines = await line_repo.get_by_transaction(transaction_id)
        response.lines = [
            TransactionLineResponse.model_validate(line) for line in lines
        ]

    return response


@router.get("/purchase-returns/purchase/{purchase_id}", response_model=TransactionListResponse)
async def get_purchase_returns_by_purchase(
    purchase_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_lines: bool = Query(False, description="Include transaction lines"),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """Get all purchase return transactions for a specific purchase."""
    transaction_repo = SQLAlchemyTransactionHeaderRepository(db)
    line_repo = SQLAlchemyTransactionLineRepository(db)

    # First verify the original purchase exists
    original_purchase = await transaction_repo.get_by_id(purchase_id)
    if not original_purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase transaction with id {purchase_id} not found",
        )

    if original_purchase.transaction_type != TransactionType.PURCHASE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction is not a purchase transaction",
        )

    # Get all return transactions that reference this purchase
    transactions, total = await transaction_repo.list(
        skip=skip,
        limit=limit,
        transaction_type=TransactionType.RETURN,
        reference_transaction_id=purchase_id,
        is_active=True,
    )

    items = []
    for transaction in transactions:
        response = TransactionHeaderResponse.model_validate(transaction)
        if include_lines:
            lines = await line_repo.get_by_transaction(transaction.id)
            response.lines = [
                TransactionLineResponse.model_validate(line) for line in lines
            ]
        items.append(response)

    return TransactionListResponse(items=items, total=total, skip=skip, limit=limit)
