from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse

from .service import TransactionHeaderService
from .schemas import (
    TransactionHeaderCreate,
    TransactionHeaderUpdate,
    TransactionHeaderResponse,
    TransactionHeaderWithDetails,
    TransactionHeaderListResponse
)
from .enums import TransactionType, TransactionStatus, PaymentStatus
from app.core.errors import NotFoundError, ValidationError

router = APIRouter()


async def get_transaction_service() -> TransactionHeaderService:
    """Dependency to get TransactionHeaderService."""
    # This would be implemented with proper dependency injection
    # For now, it's a placeholder that would be connected to the DI system
    raise NotImplementedError("Service dependency injection not implemented")


@router.post("/", response_model=TransactionHeaderResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionHeaderCreate,
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Create a new transaction header."""
    try:
        return await service.create_transaction(transaction_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction"
        )


@router.get("/{transaction_id}", response_model=TransactionHeaderResponse)
async def get_transaction(
    transaction_id: UUID,
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Get transaction header by ID."""
    try:
        return await service.get_transaction(transaction_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{transaction_id}/details", response_model=TransactionHeaderWithDetails)
async def get_transaction_with_details(
    transaction_id: UUID,
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Get transaction header with all related details."""
    try:
        return await service.get_transaction_with_details(transaction_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/number/{transaction_number}", response_model=TransactionHeaderResponse)
async def get_transaction_by_number(
    transaction_number: str,
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Get transaction header by transaction number."""
    try:
        return await service.get_transaction_by_number(transaction_number)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=TransactionHeaderListResponse)
async def get_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    transaction_type: Optional[TransactionType] = Query(None),
    status: Optional[TransactionStatus] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Get paginated list of transaction headers with filtering."""
    try:
        return await service.get_transactions(
            page=page,
            size=size,
            transaction_type=transaction_type,
            status=status,
            payment_status=payment_status,
            customer_id=customer_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions"
        )


@router.put("/{transaction_id}", response_model=TransactionHeaderResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction_data: TransactionHeaderUpdate,
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Update a transaction header."""
    try:
        return await service.update_transaction(transaction_id, transaction_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Delete (soft delete) a transaction header."""
    try:
        success = await service.delete_transaction(transaction_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/customer/{customer_id}", response_model=list[TransactionHeaderResponse])
async def get_customer_transactions(
    customer_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Get all transactions for a specific customer."""
    try:
        return await service.get_customer_transactions(customer_id, page, size)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer transactions"
        )


@router.get("/pending-payments/", response_model=list[TransactionHeaderResponse])
async def get_pending_payments(
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Get all transactions with pending payments."""
    try:
        return await service.get_pending_payments()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending payments"
        )


@router.post("/{transaction_id}/payment", response_model=TransactionHeaderResponse)
async def process_payment(
    transaction_id: UUID,
    payment_amount: Decimal,
    payment_method: Optional[str] = None,
    payment_reference: Optional[str] = None,
    service: TransactionHeaderService = Depends(get_transaction_service)
):
    """Process a payment for a transaction."""
    try:
        return await service.process_payment(
            transaction_id=transaction_id,
            payment_amount=payment_amount,
            payment_method=payment_method,
            payment_reference=payment_reference
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )