from typing import List, Optional, Tuple
from datetime import date, datetime
from uuid import UUID
from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.transaction_header import TransactionHeader
from ...domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ...domain.value_objects.transaction_type import TransactionType, TransactionStatus, PaymentStatus
from ..models.transaction_header_model import TransactionHeaderModel


class SQLAlchemyTransactionHeaderRepository(TransactionHeaderRepository):
    """SQLAlchemy implementation of TransactionHeaderRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, transaction: TransactionHeader) -> TransactionHeader:
        """Create a new transaction."""
        db_transaction = TransactionHeaderModel.from_entity(transaction)
        self.session.add(db_transaction)
        await self.session.flush()  # Flush to get the ID, but don't commit
        await self.session.refresh(db_transaction)
        return db_transaction.to_entity()
    
    async def get_by_id(self, transaction_id: UUID) -> Optional[TransactionHeader]:
        """Get transaction by ID."""
        query = select(TransactionHeaderModel).where(
            TransactionHeaderModel.id == transaction_id
        ).options(selectinload(TransactionHeaderModel.lines))
        
        result = await self.session.execute(query)
        db_transaction = result.scalar_one_or_none()
        
        if db_transaction:
            return db_transaction.to_entity()
        return None
    
    async def get_by_number(self, transaction_number: str) -> Optional[TransactionHeader]:
        """Get transaction by transaction number."""
        query = select(TransactionHeaderModel).where(
            TransactionHeaderModel.transaction_number == transaction_number
        ).options(selectinload(TransactionHeaderModel.lines))
        
        result = await self.session.execute(query)
        db_transaction = result.scalar_one_or_none()
        
        if db_transaction:
            return db_transaction.to_entity()
        return None
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        reference_transaction_id: Optional[UUID] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[TransactionHeader], int]:
        """List transactions with filters and pagination."""
        # Base query
        query = select(TransactionHeaderModel)
        count_query = select(func.count()).select_from(TransactionHeaderModel)
        
        # Apply filters
        filters = []
        
        if is_active is not None:
            filters.append(TransactionHeaderModel.is_active == is_active)
        
        if transaction_type:
            filters.append(TransactionHeaderModel.transaction_type == transaction_type)
        
        if status:
            filters.append(TransactionHeaderModel.status == status)
        
        if payment_status:
            filters.append(TransactionHeaderModel.payment_status == payment_status)
        
        if customer_id:
            filters.append(TransactionHeaderModel.customer_id == customer_id)
        
        if location_id:
            filters.append(TransactionHeaderModel.location_id == location_id)
        
        if start_date:
            filters.append(TransactionHeaderModel.transaction_date >= start_date)
        
        if end_date:
            filters.append(TransactionHeaderModel.transaction_date <= end_date)
        
        if reference_transaction_id:
            filters.append(TransactionHeaderModel.reference_transaction_id == reference_transaction_id)
        
        # Apply all filters
        if filters:
            where_clause = and_(*filters)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(TransactionHeaderModel.transaction_date.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return [trans.to_entity() for trans in transactions], total_count
    
    async def update(self, transaction_id: UUID, transaction: TransactionHeader) -> TransactionHeader:
        """Update existing transaction."""
        query = select(TransactionHeaderModel).where(
            TransactionHeaderModel.id == transaction_id
        )
        result = await self.session.execute(query)
        db_transaction = result.scalar_one_or_none()
        
        if not db_transaction:
            raise ValueError(f"Transaction with id {transaction_id} not found")
        
        # Update fields
        for key, value in transaction.__dict__.items():
            if not key.startswith('_') and hasattr(db_transaction, key):
                setattr(db_transaction, key, value)
        
        await self.session.commit()
        await self.session.refresh(db_transaction)
        
        return db_transaction.to_entity()
    
    async def delete(self, transaction_id: UUID) -> bool:
        """Soft delete transaction by setting is_active to False."""
        query = select(TransactionHeaderModel).where(
            TransactionHeaderModel.id == transaction_id
        )
        result = await self.session.execute(query)
        db_transaction = result.scalar_one_or_none()
        
        if not db_transaction:
            return False
        
        db_transaction.is_active = False
        await self.session.commit()
        
        return True
    
    async def get_customer_transactions(
        self,
        customer_id: UUID,
        transaction_type: Optional[TransactionType] = None,
        include_cancelled: bool = False
    ) -> List[TransactionHeader]:
        """Get all transactions for a customer."""
        query = select(TransactionHeaderModel).where(
            TransactionHeaderModel.customer_id == customer_id
        )
        
        if transaction_type:
            query = query.where(TransactionHeaderModel.transaction_type == transaction_type)
        
        if not include_cancelled:
            query = query.where(TransactionHeaderModel.status != TransactionStatus.CANCELLED)
        
        query = query.order_by(TransactionHeaderModel.transaction_date.desc())
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return [trans.to_entity() for trans in transactions]
    
    async def get_active_rentals(
        self,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        as_of_date: Optional[date] = None
    ) -> List[TransactionHeader]:
        """Get active rental transactions."""
        if not as_of_date:
            as_of_date = date.today()
        
        query = select(TransactionHeaderModel).where(
            and_(
                TransactionHeaderModel.transaction_type == TransactionType.RENTAL,
                TransactionHeaderModel.status == TransactionStatus.IN_PROGRESS,
                TransactionHeaderModel.rental_start_date <= as_of_date,
                or_(
                    TransactionHeaderModel.actual_return_date == None,
                    TransactionHeaderModel.actual_return_date > as_of_date
                )
            )
        )
        
        if customer_id:
            query = query.where(TransactionHeaderModel.customer_id == customer_id)
        
        if location_id:
            query = query.where(TransactionHeaderModel.location_id == location_id)
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return [trans.to_entity() for trans in transactions]
    
    async def get_overdue_rentals(
        self,
        location_id: Optional[UUID] = None,
        include_returned: bool = False,
        as_of_date: Optional[date] = None
    ) -> List[TransactionHeader]:
        """Get overdue rental transactions."""
        if not as_of_date:
            as_of_date = date.today()
            
        query = select(TransactionHeaderModel).where(
            and_(
                TransactionHeaderModel.transaction_type == TransactionType.RENTAL,
                TransactionHeaderModel.rental_end_date < as_of_date,
                TransactionHeaderModel.is_active == True
            )
        )
        
        if not include_returned:
            query = query.where(
                and_(
                    TransactionHeaderModel.status == TransactionStatus.IN_PROGRESS,
                    TransactionHeaderModel.actual_return_date == None
                )
            )
        
        if location_id:
            query = query.where(TransactionHeaderModel.location_id == location_id)
        
        query = query.order_by(TransactionHeaderModel.rental_end_date)
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return [trans.to_entity() for trans in transactions]
    
    async def get_pending_payments(
        self,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None
    ) -> List[TransactionHeader]:
        """Get transactions with pending payments."""
        query = select(TransactionHeaderModel).where(
            and_(
                TransactionHeaderModel.payment_status.in_([
                    PaymentStatus.PENDING,
                    PaymentStatus.PARTIALLY_PAID,
                    PaymentStatus.OVERDUE
                ]),
                TransactionHeaderModel.status != TransactionStatus.CANCELLED,
                TransactionHeaderModel.is_active == True
            )
        )
        
        if customer_id:
            query = query.where(TransactionHeaderModel.customer_id == customer_id)
        
        if location_id:
            query = query.where(TransactionHeaderModel.location_id == location_id)
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return [trans.to_entity() for trans in transactions]
    
    
    async def get_revenue_by_period(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
        group_by: str = "day"
    ) -> List[dict]:
        """Get revenue grouped by time period."""
        # Determine grouping - using SQLite-compatible functions
        if group_by == "day":
            date_format = func.date(TransactionHeaderModel.transaction_date)
        elif group_by == "week":
            # SQLite: Get the Monday of the week using strftime
            date_format = func.date(TransactionHeaderModel.transaction_date, 'weekday 1', '-6 days')
        elif group_by == "month":
            # SQLite: Get the first day of the month using strftime
            date_format = func.strftime('%Y-%m-01', TransactionHeaderModel.transaction_date)
        else:
            date_format = func.date(TransactionHeaderModel.transaction_date)
        
        # Build query
        query = select(
            date_format.label('period'),
            func.count().label('transaction_count'),
            func.sum(TransactionHeaderModel.total_amount).label('total_revenue'),
            func.sum(TransactionHeaderModel.paid_amount).label('total_paid')
        ).where(
            and_(
                TransactionHeaderModel.transaction_date >= start_date,
                TransactionHeaderModel.transaction_date <= end_date,
                TransactionHeaderModel.status != TransactionStatus.CANCELLED,
                TransactionHeaderModel.is_active == True
            )
        )
        
        if location_id:
            query = query.where(TransactionHeaderModel.location_id == location_id)
        
        query = query.group_by(date_format).order_by(date_format)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            {
                'period': row.period,
                'transaction_count': row.transaction_count,
                'total_revenue': float(row.total_revenue or 0),
                'total_paid': float(row.total_paid or 0),
                'outstanding': float((row.total_revenue or 0) - (row.total_paid or 0))
            }
            for row in rows
        ]
    
    async def get_customer_summary(self, customer_id: UUID) -> dict:
        """Get customer transaction summary."""
        # Count transactions by type
        type_counts = await self.session.execute(
            select(
                TransactionHeaderModel.transaction_type,
                func.count().label('count')
            ).where(
                and_(
                    TransactionHeaderModel.customer_id == customer_id,
                    TransactionHeaderModel.is_active == True
                )
            ).group_by(TransactionHeaderModel.transaction_type)
        )
        
        counts = {row.transaction_type.value: row.count for row in type_counts}
        
        # Get financial summary
        financial = await self.session.execute(
            select(
                func.count().label('total_transactions'),
                func.sum(TransactionHeaderModel.total_amount).label('total_revenue'),
                func.sum(TransactionHeaderModel.paid_amount).label('total_paid')
            ).where(
                and_(
                    TransactionHeaderModel.customer_id == customer_id,
                    TransactionHeaderModel.status != TransactionStatus.CANCELLED,
                    TransactionHeaderModel.is_active == True
                )
            )
        )
        
        summary = financial.one()
        
        # Count active and overdue rentals
        active_rentals = await self.session.execute(
            select(func.count()).where(
                and_(
                    TransactionHeaderModel.customer_id == customer_id,
                    TransactionHeaderModel.transaction_type == TransactionType.RENTAL,
                    TransactionHeaderModel.status == TransactionStatus.IN_PROGRESS,
                    TransactionHeaderModel.is_active == True
                )
            )
        )
        
        overdue_rentals = await self.session.execute(
            select(func.count()).where(
                and_(
                    TransactionHeaderModel.customer_id == customer_id,
                    TransactionHeaderModel.transaction_type == TransactionType.RENTAL,
                    TransactionHeaderModel.status == TransactionStatus.IN_PROGRESS,
                    TransactionHeaderModel.rental_end_date < date.today(),
                    TransactionHeaderModel.is_active == True
                )
            )
        )
        
        return {
            'total_transactions': summary.total_transactions or 0,
            'total_sales': counts.get('SALE', 0),
            'total_rentals': counts.get('RENTAL', 0),
            'total_revenue': float(summary.total_revenue or 0),
            'total_paid': float(summary.total_paid or 0),
            'total_outstanding': float((summary.total_revenue or 0) - (summary.total_paid or 0)),
            'active_rentals': active_rentals.scalar() or 0,
            'overdue_rentals': overdue_rentals.scalar() or 0
        }
    
    async def get_daily_summary(self, start_date: date, end_date: date, location_id: Optional[UUID] = None) -> List[dict]:
        """Get daily transaction summaries."""
        query = select(
            func.date(TransactionHeaderModel.transaction_date).label('date'),
            func.count().label('transaction_count'),
            func.sum(TransactionHeaderModel.total_amount).label('total_revenue'),
            func.sum(TransactionHeaderModel.paid_amount).label('total_paid'),
            func.sum(TransactionHeaderModel.discount_amount).label('total_discount'),
            func.sum(TransactionHeaderModel.tax_amount).label('total_tax')
        ).where(
            and_(
                func.date(TransactionHeaderModel.transaction_date) >= start_date,
                func.date(TransactionHeaderModel.transaction_date) <= end_date,
                TransactionHeaderModel.status != TransactionStatus.CANCELLED,
                TransactionHeaderModel.is_active == True
            )
        )
        
        if location_id:
            query = query.where(TransactionHeaderModel.location_id == location_id)
        
        query = query.group_by(func.date(TransactionHeaderModel.transaction_date)).order_by(
            func.date(TransactionHeaderModel.transaction_date)
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            {
                'date': row.date,
                'transaction_count': row.transaction_count,
                'total_revenue': float(row.total_revenue or 0),
                'total_paid': float(row.total_paid or 0),
                'total_discount': float(row.total_discount or 0),
                'total_tax': float(row.total_tax or 0),
                'outstanding_amount': float((row.total_revenue or 0) - (row.total_paid or 0))
            }
            for row in rows
        ]
    
    async def get_by_date(self, transaction_date: date, location_id: Optional[UUID] = None) -> List[TransactionHeader]:
        """Get transactions by date."""
        query = select(TransactionHeaderModel).where(
            and_(
                func.date(TransactionHeaderModel.transaction_date) == transaction_date,
                TransactionHeaderModel.is_active == True
            )
        )
        
        if location_id:
            query = query.where(TransactionHeaderModel.location_id == location_id)
        
        query = query.order_by(TransactionHeaderModel.transaction_date)
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return [trans.to_entity() for trans in transactions]
    
    async def get_revenue_report(
        self, start_date: date, end_date: date, group_by: str, location_id: Optional[UUID] = None
    ) -> List[dict]:
        """Get revenue report (alias for get_revenue_by_period)."""
        return await self.get_revenue_by_period(start_date, end_date, location_id, group_by)
    
    
    async def generate_transaction_number(
        self,
        transaction_type: TransactionType,
        location_id: UUID
    ) -> str:
        """Generate unique transaction number."""
        # Get location code (first 3 letters)
        from ..models.location_model import LocationModel
        location_query = select(LocationModel.location_code).where(
            LocationModel.id == location_id
        )
        location_result = await self.session.execute(location_query)
        location_code = location_result.scalar_one()[:3].upper()
        
        # Type prefix
        type_prefix = {
            TransactionType.SALE: "SAL",
            TransactionType.RENTAL: "RNT",
            TransactionType.RETURN: "RTN",
            TransactionType.EXCHANGE: "EXC",
            TransactionType.REFUND: "REF",
            TransactionType.ADJUSTMENT: "ADJ"
        }.get(transaction_type, "TRN")
        
        # Get current date
        today = datetime.now()
        date_part = today.strftime("%Y%m%d")
        
        # Get sequence number for today
        pattern = f"{location_code}-{type_prefix}-{date_part}-%"
        count_query = select(func.count()).select_from(TransactionHeaderModel).where(
            TransactionHeaderModel.transaction_number.like(pattern)
        )
        count_result = await self.session.execute(count_query)
        count = count_result.scalar_one()
        
        sequence = str(count + 1).zfill(4)
        
        return f"{location_code}-{type_prefix}-{date_part}-{sequence}"
    
    async def exists_by_number(self, transaction_number: str) -> bool:
        """Check if transaction with given number exists."""
        query = select(func.count()).select_from(TransactionHeaderModel).where(
            TransactionHeaderModel.transaction_number == transaction_number
        )
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def count_by_date(self, transaction_date: date) -> int:
        """Count transactions by date."""
        query = select(func.count()).select_from(TransactionHeaderModel).where(
            and_(
                func.date(TransactionHeaderModel.transaction_date) == transaction_date,
                TransactionHeaderModel.is_active == True
            )
        )
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count
    
    async def get_active_rentals_by_unit(self, unit_id: UUID) -> List[TransactionHeader]:
        """Get active rental transactions for a specific inventory unit."""
        # Join with transaction lines to find transactions containing the unit
        from ..models.transaction_line_model import TransactionLineModel
        
        query = select(TransactionHeaderModel).join(
            TransactionLineModel,
            TransactionHeaderModel.id == TransactionLineModel.transaction_id
        ).where(
            and_(
                TransactionLineModel.inventory_unit_id == unit_id,
                TransactionHeaderModel.transaction_type == TransactionType.RENTAL,
                TransactionHeaderModel.status.in_([
                    TransactionStatus.IN_PROGRESS,
                    TransactionStatus.PENDING,
                    TransactionStatus.CHECKED_OUT
                ]),
                TransactionHeaderModel.is_active == True
            )
        ).distinct()
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        return [trans.to_entity() for trans in transactions]