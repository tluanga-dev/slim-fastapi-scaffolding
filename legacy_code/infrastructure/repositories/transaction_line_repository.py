from typing import List, Optional, Tuple
from datetime import date
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.transaction_line import TransactionLine
from ...domain.repositories.transaction_line_repository import TransactionLineRepository
from ...domain.value_objects.transaction_type import LineItemType
from ..models.transaction_line_model import TransactionLineModel
from ..models.transaction_header_model import TransactionHeaderModel


class SQLAlchemyTransactionLineRepository(TransactionLineRepository):
    """SQLAlchemy implementation of TransactionLineRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, transaction_line: TransactionLine) -> TransactionLine:
        """Create a new transaction line."""
        db_line = TransactionLineModel.from_entity(transaction_line)
        self.session.add(db_line)
        await self.session.flush()  # Flush to get the ID, but don't commit
        await self.session.refresh(db_line)
        return db_line.to_entity()
    
    async def create_batch(self, transaction_lines: List[TransactionLine]) -> List[TransactionLine]:
        """Create multiple transaction lines in batch."""
        db_lines = [TransactionLineModel.from_entity(line) for line in transaction_lines]
        self.session.add_all(db_lines)
        await self.session.flush()  # Flush to get the IDs, but don't commit
        
        # Refresh all lines
        created_lines = []
        for db_line in db_lines:
            await self.session.refresh(db_line)
            created_lines.append(db_line.to_entity())
        
        return created_lines
    
    async def get_by_id(self, line_id: UUID) -> Optional[TransactionLine]:
        """Get transaction line by ID."""
        query = select(TransactionLineModel).where(
            TransactionLineModel.id == line_id
        )
        result = await self.session.execute(query)
        db_line = result.scalar_one_or_none()
        
        if db_line:
            return db_line.to_entity()
        return None
    
    async def get_by_transaction(
        self,
        transaction_id: UUID,
        line_type: Optional[LineItemType] = None,
        include_inactive: bool = False
    ) -> List[TransactionLine]:
        """Get all lines for a transaction."""
        query = select(TransactionLineModel).where(
            TransactionLineModel.transaction_id == transaction_id
        )
        
        if line_type:
            query = query.where(TransactionLineModel.line_type == line_type)
        
        if not include_inactive:
            query = query.where(TransactionLineModel.is_active == True)
        
        query = query.order_by(TransactionLineModel.line_number)
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        return [line.to_entity() for line in lines]
    
    async def get_by_sku(
        self,
        sku_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TransactionLine]:
        """Get all transaction lines for a SKU."""
        query = select(TransactionLineModel).where(
            and_(
                TransactionLineModel.sku_id == sku_id,
                TransactionLineModel.is_active == True
            )
        )
        
        if start_date or end_date:
            # Join with transaction header to filter by date
            query = query.join(TransactionHeaderModel)
            
            if start_date:
                query = query.where(TransactionHeaderModel.transaction_date >= start_date)
            
            if end_date:
                query = query.where(TransactionHeaderModel.transaction_date <= end_date)
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        return [line.to_entity() for line in lines]
    
    async def get_by_inventory_unit(
        self,
        inventory_unit_id: UUID,
        include_returned: bool = True
    ) -> List[TransactionLine]:
        """Get all transaction lines for an inventory unit."""
        query = select(TransactionLineModel).where(
            and_(
                TransactionLineModel.inventory_unit_id == inventory_unit_id,
                TransactionLineModel.is_active == True
            )
        )
        
        if not include_returned:
            query = query.where(TransactionLineModel.returned_quantity == 0)
        
        query = query.order_by(TransactionLineModel.created_at.desc())
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        return [line.to_entity() for line in lines]
    
    async def update(self, transaction_line: TransactionLine) -> TransactionLine:
        """Update existing transaction line."""
        query = select(TransactionLineModel).where(
            TransactionLineModel.id == transaction_line.id
        )
        result = await self.session.execute(query)
        db_line = result.scalar_one_or_none()
        
        if not db_line:
            raise ValueError(f"Transaction line with id {transaction_line.id} not found")
        
        # Update fields
        for key, value in transaction_line.__dict__.items():
            if not key.startswith('_') and hasattr(db_line, key):
                setattr(db_line, key, value)
        
        await self.session.commit()
        await self.session.refresh(db_line)
        
        return db_line.to_entity()
    
    async def update_batch(self, transaction_lines: List[TransactionLine]) -> List[TransactionLine]:
        """Update multiple transaction lines in batch."""
        updated_lines = []
        
        for line in transaction_lines:
            query = select(TransactionLineModel).where(
                TransactionLineModel.id == line.id
            )
            result = await self.session.execute(query)
            db_line = result.scalar_one_or_none()
            
            if db_line:
                for key, value in line.__dict__.items():
                    if not key.startswith('_') and hasattr(db_line, key):
                        setattr(db_line, key, value)
        
        await self.session.commit()
        
        # Refresh and return
        for line in transaction_lines:
            query = select(TransactionLineModel).where(
                TransactionLineModel.id == line.id
            )
            result = await self.session.execute(query)
            db_line = result.scalar_one_or_none()
            if db_line:
                updated_lines.append(db_line.to_entity())
        
        return updated_lines
    
    async def delete(self, line_id: UUID) -> bool:
        """Soft delete transaction line."""
        query = select(TransactionLineModel).where(
            TransactionLineModel.id == line_id
        )
        result = await self.session.execute(query)
        db_line = result.scalar_one_or_none()
        
        if not db_line:
            return False
        
        db_line.is_active = False
        await self.session.commit()
        
        return True
    
    async def delete_by_transaction(self, transaction_id: UUID) -> int:
        """Delete all lines for a transaction. Returns count of deleted lines."""
        # Count lines to delete
        count_query = select(func.count()).select_from(TransactionLineModel).where(
            and_(
                TransactionLineModel.transaction_id == transaction_id,
                TransactionLineModel.is_active == True
            )
        )
        count_result = await self.session.execute(count_query)
        count = count_result.scalar_one()
        
        # Soft delete all lines
        update_query = select(TransactionLineModel).where(
            and_(
                TransactionLineModel.transaction_id == transaction_id,
                TransactionLineModel.is_active == True
            )
        )
        result = await self.session.execute(update_query)
        lines = result.scalars().all()
        
        for line in lines:
            line.is_active = False
        
        await self.session.commit()
        
        return count
    
    async def get_unreturned_rentals(
        self,
        customer_id: Optional[UUID] = None,
        sku_id: Optional[UUID] = None,
        overdue_only: bool = False,
        as_of_date: Optional[date] = None
    ) -> List[TransactionLine]:
        """Get rental lines that haven't been fully returned."""
        if not as_of_date:
            as_of_date = date.today()
        
        # Base query for rental lines
        query = select(TransactionLineModel).join(
            TransactionHeaderModel
        ).where(
            and_(
                TransactionLineModel.line_type == LineItemType.PRODUCT,
                TransactionLineModel.quantity > TransactionLineModel.returned_quantity,
                TransactionLineModel.is_active == True,
                TransactionHeaderModel.transaction_type == 'RENTAL',
                TransactionHeaderModel.status.in_(['IN_PROGRESS', 'COMPLETED'])
            )
        )
        
        if customer_id:
            query = query.where(TransactionHeaderModel.customer_id == customer_id)
        
        if sku_id:
            query = query.where(TransactionLineModel.sku_id == sku_id)
        
        if overdue_only:
            query = query.where(TransactionLineModel.rental_end_date < as_of_date)
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        return [line.to_entity() for line in lines]
    
    async def get_rental_history(
        self,
        inventory_unit_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TransactionLine]:
        """Get rental history for an inventory unit."""
        query = select(TransactionLineModel).join(
            TransactionHeaderModel
        ).where(
            and_(
                TransactionLineModel.inventory_unit_id == inventory_unit_id,
                TransactionHeaderModel.transaction_type == 'RENTAL',
                TransactionLineModel.is_active == True
            )
        )
        
        if start_date:
            query = query.where(TransactionHeaderModel.transaction_date >= start_date)
        
        if end_date:
            query = query.where(TransactionHeaderModel.transaction_date <= end_date)
        
        query = query.order_by(TransactionHeaderModel.transaction_date.desc())
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        return [line.to_entity() for line in lines]
    
    async def calculate_line_totals(self, transaction_id: UUID) -> dict:
        """Calculate totals for all lines in a transaction."""
        # Get sum by line type
        query = select(
            TransactionLineModel.line_type,
            func.sum(TransactionLineModel.line_total).label('total')
        ).where(
            and_(
                TransactionLineModel.transaction_id == transaction_id,
                TransactionLineModel.is_active == True
            )
        ).group_by(TransactionLineModel.line_type)
        
        result = await self.session.execute(query)
        totals_by_type = {row.line_type: float(row.total) for row in result}
        
        # Calculate aggregates
        subtotal = (
            totals_by_type.get(LineItemType.PRODUCT, 0) +
            totals_by_type.get(LineItemType.SERVICE, 0)
        )
        
        return {
            'subtotal': subtotal,
            'discount': abs(totals_by_type.get(LineItemType.DISCOUNT, 0)),
            'tax': totals_by_type.get(LineItemType.TAX, 0),
            'fees': (
                totals_by_type.get(LineItemType.FEE, 0) +
                totals_by_type.get(LineItemType.LATE_FEE, 0) +
                totals_by_type.get(LineItemType.DAMAGE_FEE, 0)
            ),
            'deposit': totals_by_type.get(LineItemType.DEPOSIT, 0),
            'total': sum(totals_by_type.values())
        }
    
    async def get_sales_by_sku(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[dict]:
        """Get sales summary by SKU for a period."""
        query = select(
            TransactionLineModel.sku_id,
            func.count(TransactionLineModel.id).label('transaction_count'),
            func.sum(TransactionLineModel.quantity).label('total_quantity'),
            func.sum(TransactionLineModel.line_total).label('total_revenue')
        ).join(
            TransactionHeaderModel
        ).where(
            and_(
                TransactionHeaderModel.transaction_date >= start_date,
                TransactionHeaderModel.transaction_date <= end_date,
                TransactionHeaderModel.transaction_type == 'SALE',
                TransactionHeaderModel.status != 'CANCELLED',
                TransactionLineModel.line_type == LineItemType.PRODUCT,
                TransactionLineModel.is_active == True
            )
        )
        
        if location_id:
            query = query.where(TransactionHeaderModel.location_id == location_id)
        
        query = query.group_by(
            TransactionLineModel.sku_id
        ).order_by(
            func.sum(TransactionLineModel.line_total).desc()
        ).limit(limit)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            {
                'sku_id': str(row.sku_id),
                'transaction_count': row.transaction_count,
                'total_quantity': float(row.total_quantity),
                'total_revenue': float(row.total_revenue)
            }
            for row in rows
        ]
    
    async def get_rental_utilization(
        self,
        sku_id: UUID,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get rental utilization statistics for a SKU."""
        # Count rental transactions
        rental_query = select(
            func.count(TransactionLineModel.id).label('rental_count'),
            func.sum(TransactionLineModel.quantity).label('total_units_rented'),
            func.sum(TransactionLineModel.rental_period_value).label('total_rental_days')
        ).join(
            TransactionHeaderModel
        ).where(
            and_(
                TransactionLineModel.sku_id == sku_id,
                TransactionHeaderModel.transaction_date >= start_date,
                TransactionHeaderModel.transaction_date <= end_date,
                TransactionHeaderModel.transaction_type == 'RENTAL',
                TransactionHeaderModel.status != 'CANCELLED',
                TransactionLineModel.is_active == True
            )
        )
        
        result = await self.session.execute(rental_query)
        rental_stats = result.one()
        
        # Calculate period days
        period_days = (end_date - start_date).days + 1
        
        return {
            'sku_id': str(sku_id),
            'period_start': start_date,
            'period_end': end_date,
            'period_days': period_days,
            'rental_count': rental_stats.rental_count or 0,
            'total_units_rented': float(rental_stats.total_units_rented or 0),
            'total_rental_days': rental_stats.total_rental_days or 0,
            'average_rental_duration': (
                float(rental_stats.total_rental_days / rental_stats.rental_count)
                if rental_stats.rental_count else 0
            )
        }
    
    async def get_next_line_number(self, transaction_id: UUID) -> int:
        """Get next available line number for a transaction."""
        query = select(
            func.coalesce(func.max(TransactionLineModel.line_number), 0)
        ).where(
            TransactionLineModel.transaction_id == transaction_id
        )
        
        result = await self.session.execute(query)
        max_line_number = result.scalar_one()
        
        return max_line_number + 1