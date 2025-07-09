from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from datetime import datetime, timedelta

from ....infrastructure.repositories.customer_repository import SQLAlchemyCustomerRepository
from ....infrastructure.models.customer_model import CustomerModel
from ....domain.value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus
from ..dependencies.database import get_db
from ..schemas.customer_schemas import CustomerResponse

router = APIRouter(prefix="/analytics", tags=["customer-analytics"])


@router.get("/customers")
async def get_customer_analytics(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get customer analytics data."""
    try:
        # Get basic customer counts
        total_customers_result = await db.execute(
            text("SELECT COUNT(*) FROM customers WHERE is_active = true")
        )
        total_customers = total_customers_result.scalar() or 0
        
        active_customers_result = await db.execute(
            text("SELECT COUNT(*) FROM customers WHERE is_active = true")
        )
        active_customers = active_customers_result.scalar() or 0
        
        blacklisted_customers_result = await db.execute(
            text("SELECT COUNT(*) FROM customers WHERE blacklist_status = 'BLACKLISTED' AND is_active = true")
        )
        blacklisted_customers = blacklisted_customers_result.scalar() or 0
        
        # Get tier distribution
        tier_distribution = {
            "bronze": 0,
            "silver": 0,
            "gold": 0,
            "platinum": 0
        }
        
        tier_result = await db.execute(
            text("SELECT customer_tier, COUNT(*) FROM customers WHERE is_active = true GROUP BY customer_tier")
        )
        
        for tier, count in tier_result.fetchall():
            if tier:
                tier_distribution[tier.lower()] = count
        
        # Get customer types
        customer_types = {"individual": 0, "business": 0}
        
        types_result = await db.execute(
            text("SELECT customer_type, COUNT(*) FROM customers WHERE is_active = true GROUP BY customer_type")
        )
        
        for customer_type, count in types_result.fetchall():
            if customer_type:
                customer_types[customer_type.lower()] = count
        
        # Get top customers by lifetime value
        repository = SQLAlchemyCustomerRepository(db)
        customers, _ = await repository.list(skip=0, limit=10)
        
        top_customers_by_value = []
        for customer in sorted(customers, key=lambda c: c.lifetime_value, reverse=True)[:10]:
            top_customers_by_value.append({
                "customer": CustomerResponse.from_entity(customer),
                "lifetime_value": float(customer.lifetime_value)
            })
        
        # Monthly growth data (last 12 months)
        monthly_new_customers = []
        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
            month_end = month_start.replace(day=28) + timedelta(days=4)  # End of month
            month_end = month_end - timedelta(days=month_end.day)
            
            count_result = await db.execute(
                text("SELECT COUNT(*) FROM customers WHERE created_at >= :start AND created_at < :end"),
                {"start": month_start, "end": month_end}
            )
            count = count_result.scalar() or 0
            
            monthly_new_customers.append({
                "month": month_start.strftime("%Y-%m"),
                "count": count
            })
        
        monthly_new_customers.reverse()  # Show oldest first
        
        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "blacklisted_customers": blacklisted_customers,
            "tier_distribution": tier_distribution,
            "monthly_new_customers": monthly_new_customers,
            "top_customers_by_value": top_customers_by_value,
            "customer_types": customer_types
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )


@router.get("/customers/{customer_id}/transactions")
async def get_customer_transaction_history(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get customer transaction history."""
    # For now, return mock data until transaction system is fully implemented
    repository = SQLAlchemyCustomerRepository(db)
    customer = await repository.get_by_id(customer_id)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    return {
        "customer": CustomerResponse.from_entity(customer),
        "transactions": [],  # Will be populated when transaction system is ready
        "summary": {
            "total_transactions": 0,
            "total_spent": 0.0,
            "average_transaction": 0.0,
            "last_transaction_date": customer.last_transaction_date,
            "favorite_items": []
        }
    }