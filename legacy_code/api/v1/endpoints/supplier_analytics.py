from typing import Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....infrastructure.repositories.supplier_repository import SQLAlchemySupplierRepository
from ..dependencies.database import get_db
from ..schemas.supplier_schemas import SupplierAnalytics

router = APIRouter(prefix="/analytics", tags=["supplier-analytics"])


@router.get("/suppliers")
async def get_supplier_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics filtering"),
    end_date: Optional[date] = Query(None, description="End date for analytics filtering"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get supplier analytics data."""
    try:
        repository = SQLAlchemySupplierRepository(db)
        analytics = await repository.get_supplier_analytics(start_date, end_date)
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate supplier analytics: {str(e)}"
        )


@router.get("/suppliers/{supplier_id}/performance")
async def get_supplier_performance_history(
    supplier_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get supplier performance history and trends."""
    try:
        repository = SQLAlchemySupplierRepository(db)
        
        # Get the supplier
        from uuid import UUID
        supplier = await repository.get_by_id(UUID(supplier_id))
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with id {supplier_id} not found"
            )
        
        # Get real purchase transaction metrics (supplier data is now updated with real metrics)
        return {
            "supplier": {
                "id": str(supplier.id),
                "supplier_code": supplier.supplier_code,
                "company_name": supplier.company_name,
                "supplier_type": supplier.supplier_type.value,
                "supplier_tier": supplier.supplier_tier.value
            },
            "performance_metrics": {
                "total_orders": supplier.total_orders,
                "total_spend": float(supplier.total_spend),
                "average_delivery_days": supplier.average_delivery_days,
                "quality_rating": float(supplier.quality_rating),
                "performance_score": float(supplier.get_performance_score()),
                "last_order_date": supplier.last_order_date.isoformat() if supplier.last_order_date else None
            },
            "trends": {
                "delivery_trend": "stable",  # Would be calculated from historical data
                "quality_trend": "improving",  # Would be calculated from historical data
                "spend_trend": "increasing"  # Would be calculated from historical data
            },
            "recommendations": [
                "Consider increasing order frequency for better pricing",
                "Supplier shows consistent quality delivery",
                "Good candidate for preferred supplier status"
            ] if supplier.get_performance_score() > 70 else [
                "Monitor delivery performance closely",
                "Consider quality improvement discussions",
                "Evaluate alternative suppliers"
            ]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supplier performance data: {str(e)}"
        )


@router.get("/suppliers/{supplier_id}/purchases")
async def get_supplier_purchase_history(
    supplier_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get purchase transaction history for a supplier."""
    try:
        from ....infrastructure.repositories.transaction_header_repository import SQLAlchemyTransactionHeaderRepository
        from ....domain.value_objects.transaction_type import TransactionType
        from uuid import UUID
        
        # Verify supplier exists
        repository = SQLAlchemySupplierRepository(db)
        supplier = await repository.get_by_id(UUID(supplier_id))
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with id {supplier_id} not found"
            )
        
        # Get purchase transactions for this supplier
        # Note: In current architecture, suppliers are stored as customer_id in PURCHASE transactions
        transaction_repository = SQLAlchemyTransactionHeaderRepository(db)
        transactions, total = await transaction_repository.list(
            customer_id=UUID(supplier_id),
            transaction_type=TransactionType.PURCHASE,
            skip=skip,
            limit=limit,
            is_active=True
        )
        
        return {
            "supplier": {
                "id": str(supplier.id),
                "supplier_code": supplier.supplier_code,
                "company_name": supplier.company_name,
                "supplier_type": supplier.supplier_type.value,
                "supplier_tier": supplier.supplier_tier.value
            },
            "transactions": [
                {
                    "id": str(transaction.id),
                    "transaction_number": transaction.transaction_number,
                    "transaction_date": transaction.transaction_date.isoformat(),
                    "status": transaction.status.value,
                    "payment_status": transaction.payment_status.value,
                    "subtotal": float(transaction.subtotal),
                    "discount_amount": float(transaction.discount_amount),
                    "tax_amount": float(transaction.tax_amount),
                    "total_amount": float(transaction.total_amount),
                    "paid_amount": float(transaction.paid_amount),
                    "notes": transaction.notes,
                    "created_at": transaction.created_at.isoformat()
                }
                for transaction in transactions
            ],
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": skip + limit < total,
                "has_prev": skip > 0
            },
            "summary": {
                "total_transactions": total,
                "total_spend": float(supplier.total_spend),
                "average_order_value": float(supplier.total_spend / supplier.total_orders) if supplier.total_orders > 0 else 0,
                "last_order_date": supplier.last_order_date.isoformat() if supplier.last_order_date else None
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supplier purchase history: {str(e)}"
        )