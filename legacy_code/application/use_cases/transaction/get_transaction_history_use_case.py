from typing import List, Optional, Tuple, Dict
from datetime import date
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.value_objects.transaction_type import TransactionType, TransactionStatus, PaymentStatus


class GetTransactionHistoryUseCase:
    """Use case for retrieving transaction history."""
    
    def __init__(
        self,
        transaction_repository: TransactionHeaderRepository,
        customer_repository: CustomerRepository
    ):
        """Initialize use case with repositories."""
        self.transaction_repository = transaction_repository
        self.customer_repository = customer_repository
    
    async def execute(
        self,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
        include_cancelled: bool = False
    ) -> Tuple[List[TransactionHeader], int]:
        """Execute the use case to get transaction history."""
        # If customer_id provided, validate customer exists
        if customer_id:
            customer = await self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with id {customer_id} not found")
        
        # Get transactions with filters
        transactions, total_count = await self.transaction_repository.list(
            skip=skip,
            limit=limit,
            transaction_type=transaction_type,
            status=status,
            payment_status=payment_status,
            customer_id=customer_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date,
            is_active=None if include_cancelled else True
        )
        
        return transactions, total_count
    
    async def get_customer_summary(
        self,
        customer_id: UUID,
        include_cancelled: bool = False
    ) -> Dict:
        """Get transaction summary for a customer."""
        # Validate customer
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")
        
        # Get all customer transactions
        transactions = await self.transaction_repository.get_customer_transactions(
            customer_id=customer_id,
            include_cancelled=include_cancelled
        )
        
        # Calculate summary
        total_transactions = len(transactions)
        total_sales = sum(1 for t in transactions if t.is_sale)
        total_rentals = sum(1 for t in transactions if t.is_rental)
        
        # Calculate financial summary
        total_revenue = sum(t.total_amount for t in transactions if t.status != TransactionStatus.CANCELLED)
        total_paid = sum(t.paid_amount for t in transactions)
        total_outstanding = sum(t.balance_due for t in transactions)
        
        # Get active rentals
        active_rentals = await self.transaction_repository.get_active_rentals(
            customer_id=customer_id
        )
        
        # Get overdue items
        overdue_rentals = [
            r for r in active_rentals
            if r.rental_end_date and r.rental_end_date < date.today()
        ]
        
        return {
            'customer_id': str(customer_id),
            'customer_name': customer.company_name or f"{customer.first_name} {customer.last_name}",
            'total_transactions': total_transactions,
            'total_sales': total_sales,
            'total_rentals': total_rentals,
            'total_revenue': float(total_revenue),
            'total_paid': float(total_paid),
            'total_outstanding': float(total_outstanding),
            'active_rentals': len(active_rentals),
            'overdue_rentals': len(overdue_rentals),
            'customer_since': customer.created_at,
            'customer_tier': customer.customer_tier.value if customer.customer_tier else None
        }
    
    async def get_daily_transactions(
        self,
        transaction_date: date,
        location_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None
    ) -> Dict:
        """Get transactions and summary for a specific date."""
        # Get transactions for the date
        transactions, _ = await self.transaction_repository.list(
            start_date=transaction_date,
            end_date=transaction_date,
            location_id=location_id,
            transaction_type=transaction_type,
            limit=1000  # Get all transactions for the day
        )
        
        # Get daily summary
        summary = await self.transaction_repository.get_daily_summary(
            summary_date=transaction_date,
            location_id=location_id,
            transaction_type=transaction_type
        )
        
        # Add transaction list to summary
        summary['transactions'] = transactions
        
        return summary
    
    async def get_revenue_report(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
        group_by: str = "day"
    ) -> List[Dict]:
        """Get revenue report for a period."""
        return await self.transaction_repository.get_revenue_by_period(
            start_date=start_date,
            end_date=end_date,
            location_id=location_id,
            group_by=group_by
        )