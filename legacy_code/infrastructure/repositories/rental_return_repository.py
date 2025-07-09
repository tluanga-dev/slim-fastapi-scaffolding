from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.rental_return import RentalReturn
from ...domain.repositories.rental_return_repository import RentalReturnRepository
from ...domain.value_objects.rental_return_type import ReturnStatus, ReturnType
from ..models.rental_return_model import RentalReturnModel


class SQLAlchemyRentalReturnRepository(RentalReturnRepository):
    """SQLAlchemy implementation of RentalReturnRepository."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db
    
    async def create(self, rental_return: RentalReturn) -> RentalReturn:
        """Create a new rental return."""
        db_return = RentalReturnModel.from_entity(rental_return)
        self.db.add(db_return)
        await self.db.commit()
        await self.db.refresh(db_return)
        return db_return.to_entity()
    
    async def get_by_id(self, return_id: UUID) -> Optional[RentalReturn]:
        """Get rental return by ID."""
        query = select(RentalReturnModel).where(
            and_(
                RentalReturnModel.id == return_id,
                RentalReturnModel.is_active == True
            )
        ).options(
            selectinload(RentalReturnModel.lines),
            selectinload(RentalReturnModel.inspection_reports)
        )
        
        result = await self.db.execute(query)
        db_return = result.scalar_one_or_none()
        
        if db_return:
            entity = db_return.to_entity()
            # Load related entities
            if db_return.lines:
                entity._lines = [line.to_entity() for line in db_return.lines]
            if db_return.inspection_reports:
                entity._inspection_reports = [report.to_entity() for report in db_return.inspection_reports]
            return entity
        return None
    
    async def get_by_transaction_id(self, transaction_id: UUID) -> List[RentalReturn]:
        """Get all returns for a rental transaction."""
        query = select(RentalReturnModel).where(
            and_(
                RentalReturnModel.rental_transaction_id == transaction_id,
                RentalReturnModel.is_active == True
            )
        ).options(
            selectinload(RentalReturnModel.lines),
            selectinload(RentalReturnModel.inspection_reports)
        ).order_by(RentalReturnModel.return_date.desc())
        
        result = await self.db.execute(query)
        db_returns = result.scalars().all()
        
        returns = []
        for db_return in db_returns:
            entity = db_return.to_entity()
            if db_return.lines:
                entity._lines = [line.to_entity() for line in db_return.lines]
            if db_return.inspection_reports:
                entity._inspection_reports = [report.to_entity() for report in db_return.inspection_reports]
            returns.append(entity)
        
        return returns
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_id: Optional[UUID] = None,
        return_status: Optional[ReturnStatus] = None,
        return_type: Optional[ReturnType] = None,
        location_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[RentalReturn], int]:
        """List rental returns with filters and pagination."""
        # Base query
        query = select(RentalReturnModel)
        count_query = select(func.count()).select_from(RentalReturnModel)
        
        # Apply filters
        filters = []
        
        if is_active is not None:
            filters.append(RentalReturnModel.is_active == is_active)
        
        if transaction_id:
            filters.append(RentalReturnModel.rental_transaction_id == transaction_id)
        
        if return_status:
            filters.append(RentalReturnModel.return_status == return_status.value)
        
        if return_type:
            filters.append(RentalReturnModel.return_type == return_type.value)
        
        if location_id:
            filters.append(RentalReturnModel.return_location_id == location_id)
        
        if start_date:
            filters.append(RentalReturnModel.return_date >= start_date)
        
        if end_date:
            filters.append(RentalReturnModel.return_date <= end_date)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Execute count query
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        # Execute main query with pagination
        query = query.options(
            selectinload(RentalReturnModel.lines),
            selectinload(RentalReturnModel.inspection_reports)
        ).order_by(RentalReturnModel.return_date.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        db_returns = result.scalars().all()
        
        returns = []
        for db_return in db_returns:
            entity = db_return.to_entity()
            if db_return.lines:
                entity._lines = [line.to_entity() for line in db_return.lines]
            if db_return.inspection_reports:
                entity._inspection_reports = [report.to_entity() for report in db_return.inspection_reports]
            returns.append(entity)
        
        return returns, total
    
    async def update(self, rental_return: RentalReturn) -> RentalReturn:
        """Update an existing rental return."""
        query = select(RentalReturnModel).where(RentalReturnModel.id == rental_return.id)
        result = await self.db.execute(query)
        db_return = result.scalar_one_or_none()
        
        if not db_return:
            raise ValueError(f"Rental return with ID {rental_return.id} not found")
        
        db_return.update_from_entity(rental_return)
        await self.db.commit()
        await self.db.refresh(db_return)
        return db_return.to_entity()
    
    async def delete(self, return_id: UUID) -> bool:
        """Soft delete a rental return."""
        query = select(RentalReturnModel).where(RentalReturnModel.id == return_id)
        result = await self.db.execute(query)
        db_return = result.scalar_one_or_none()
        
        if not db_return:
            return False
        
        db_return.is_active = False
        await self.db.commit()
        return True
    
    async def get_outstanding_returns(
        self,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        days_overdue: Optional[int] = None
    ) -> List[RentalReturn]:
        """Get outstanding returns (not completed)."""
        from ..models.transaction_header_model import TransactionHeaderModel
        
        query = select(RentalReturnModel).join(
            TransactionHeaderModel,
            RentalReturnModel.rental_transaction_id == TransactionHeaderModel.id
        ).where(
            and_(
                RentalReturnModel.return_status != ReturnStatus.COMPLETED.value,
                RentalReturnModel.return_status != ReturnStatus.CANCELLED.value,
                RentalReturnModel.is_active == True
            )
        )
        
        if customer_id:
            query = query.where(TransactionHeaderModel.customer_id == customer_id)
        
        if location_id:
            query = query.where(RentalReturnModel.return_location_id == location_id)
        
        if days_overdue is not None:
            overdue_date = date.today() - timedelta(days=days_overdue)
            query = query.where(RentalReturnModel.expected_return_date < overdue_date)
        
        query = query.options(
            selectinload(RentalReturnModel.lines)
        ).order_by(RentalReturnModel.expected_return_date.asc())
        
        result = await self.db.execute(query)
        db_returns = result.scalars().all()
        
        returns = []
        for db_return in db_returns:
            entity = db_return.to_entity()
            if db_return.lines:
                entity._lines = [line.to_entity() for line in db_return.lines]
            returns.append(entity)
        
        return returns
    
    async def get_returns_by_customer(
        self,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[RentalReturn], int]:
        """Get all returns for a specific customer."""
        from ..models.transaction_header_model import TransactionHeaderModel
        
        # Base query
        query = select(RentalReturnModel).join(
            TransactionHeaderModel,
            RentalReturnModel.rental_transaction_id == TransactionHeaderModel.id
        ).where(
            and_(
                TransactionHeaderModel.customer_id == customer_id,
                RentalReturnModel.is_active == True
            )
        )
        
        count_query = select(func.count()).select_from(RentalReturnModel).join(
            TransactionHeaderModel,
            RentalReturnModel.rental_transaction_id == TransactionHeaderModel.id
        ).where(
            and_(
                TransactionHeaderModel.customer_id == customer_id,
                RentalReturnModel.is_active == True
            )
        )
        
        # Execute count query
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        # Execute main query with pagination
        query = query.options(
            selectinload(RentalReturnModel.lines)
        ).order_by(RentalReturnModel.return_date.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        db_returns = result.scalars().all()
        
        returns = []
        for db_return in db_returns:
            entity = db_return.to_entity()
            if db_return.lines:
                entity._lines = [line.to_entity() for line in db_return.lines]
            returns.append(entity)
        
        return returns, total
    
    async def get_late_returns(
        self,
        as_of_date: Optional[date] = None,
        location_id: Optional[UUID] = None
    ) -> List[RentalReturn]:
        """Get returns that are past due."""
        if not as_of_date:
            as_of_date = date.today()
        
        query = select(RentalReturnModel).where(
            and_(
                RentalReturnModel.expected_return_date < as_of_date,
                RentalReturnModel.return_status != ReturnStatus.COMPLETED.value,
                RentalReturnModel.return_status != ReturnStatus.CANCELLED.value,
                RentalReturnModel.is_active == True
            )
        )
        
        if location_id:
            query = query.where(RentalReturnModel.return_location_id == location_id)
        
        query = query.options(
            selectinload(RentalReturnModel.lines)
        ).order_by(RentalReturnModel.expected_return_date.asc())
        
        result = await self.db.execute(query)
        db_returns = result.scalars().all()
        
        returns = []
        for db_return in db_returns:
            entity = db_return.to_entity()
            if db_return.lines:
                entity._lines = [line.to_entity() for line in db_return.lines]
            returns.append(entity)
        
        return returns
    
    async def get_returns_needing_inspection(
        self,
        location_id: Optional[UUID] = None
    ) -> List[RentalReturn]:
        """Get returns that need inspection."""
        query = select(RentalReturnModel).where(
            and_(
                RentalReturnModel.return_status == ReturnStatus.IN_INSPECTION.value,
                RentalReturnModel.is_active == True
            )
        )
        
        if location_id:
            query = query.where(RentalReturnModel.return_location_id == location_id)
        
        query = query.options(
            selectinload(RentalReturnModel.lines),
            selectinload(RentalReturnModel.inspection_reports)
        ).order_by(RentalReturnModel.return_date.asc())
        
        result = await self.db.execute(query)
        db_returns = result.scalars().all()
        
        returns = []
        for db_return in db_returns:
            entity = db_return.to_entity()
            if db_return.lines:
                entity._lines = [line.to_entity() for line in db_return.lines]
            if db_return.inspection_reports:
                entity._inspection_reports = [report.to_entity() for report in db_return.inspection_reports]
            returns.append(entity)
        
        return returns
    
    async def count_returns_by_status(
        self,
        location_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """Count returns by status."""
        query = select(
            RentalReturnModel.return_status,
            func.count(RentalReturnModel.id).label('count')
        ).where(RentalReturnModel.is_active == True)
        
        if location_id:
            query = query.where(RentalReturnModel.return_location_id == location_id)
        
        if start_date:
            query = query.where(RentalReturnModel.return_date >= start_date)
        
        if end_date:
            query = query.where(RentalReturnModel.return_date <= end_date)
        
        query = query.group_by(RentalReturnModel.return_status)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        return {row.return_status: row.count for row in rows}
    
    async def calculate_total_fees(self, return_id: UUID) -> dict:
        """Calculate total fees for a return."""
        from ..models.rental_return_line_model import RentalReturnLineModel
        
        query = select(
            func.sum(RentalReturnLineModel.late_fee).label('total_late_fee'),
            func.sum(RentalReturnLineModel.damage_fee).label('total_damage_fee'),
            func.sum(RentalReturnLineModel.cleaning_fee).label('total_cleaning_fee'),
            func.sum(RentalReturnLineModel.replacement_fee).label('total_replacement_fee')
        ).where(
            and_(
                RentalReturnLineModel.return_id == return_id,
                RentalReturnLineModel.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        row = result.fetchone()
        
        return {
            'total_late_fee': float(row.total_late_fee or 0),
            'total_damage_fee': float(row.total_damage_fee or 0),
            'total_cleaning_fee': float(row.total_cleaning_fee or 0),
            'total_replacement_fee': float(row.total_replacement_fee or 0),
            'total_fees': float((row.total_late_fee or 0) + (row.total_damage_fee or 0) + 
                              (row.total_cleaning_fee or 0) + (row.total_replacement_fee or 0))
        }