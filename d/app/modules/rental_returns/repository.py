from typing import List, Optional, Tuple
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, update
from sqlalchemy.orm import joinedload

from app.modules.rental_returns.models import RentalReturnModel, RentalReturnLineModel
from app.core.domain.value_objects.rental_return_type import ReturnStatus, ReturnType, DamageLevel
from app.core.domain.value_objects.item_type import ConditionGrade


class RentalReturnRepository:
    """Repository for rental return data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # RentalReturn CRUD Operations
    async def create_rental_return(self, return_data: dict) -> RentalReturnModel:
        """Create a new rental return."""
        rental_return = RentalReturnModel(**return_data)
        self.session.add(rental_return)
        await self.session.commit()
        await self.session.refresh(rental_return)
        return rental_return
    
    async def get_rental_return_by_id(self, return_id: UUID) -> Optional[RentalReturnModel]:
        """Get rental return by ID with relationships."""
        result = await self.session.execute(
            select(RentalReturnModel)
            .options(
                joinedload(RentalReturnModel.return_location),
                joinedload(RentalReturnModel.lines).joinedload(RentalReturnLineModel.inventory_unit)
            )
            .filter(RentalReturnModel.id == return_id)
        )
        return result.scalars().first()
    
    async def get_rental_returns_by_transaction(self, transaction_id: UUID) -> List[RentalReturnModel]:
        """Get all rental returns for a transaction."""
        result = await self.session.execute(
            select(RentalReturnModel)
            .options(
                joinedload(RentalReturnModel.return_location),
                joinedload(RentalReturnModel.lines)
            )
            .filter(RentalReturnModel.rental_transaction_id == transaction_id)
            .order_by(RentalReturnModel.return_date.desc())
        )
        return result.scalars().all()
    
    async def get_rental_returns(
        self,
        skip: int = 0,
        limit: int = 100,
        rental_transaction_id: Optional[UUID] = None,
        return_location_id: Optional[UUID] = None,
        return_status: Optional[ReturnStatus] = None,
        return_type: Optional[ReturnType] = None,
        return_date_from: Optional[date] = None,
        return_date_to: Optional[date] = None,
        processed_by: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "return_date",
        sort_order: str = "desc"
    ) -> List[RentalReturnModel]:
        """Get rental returns with optional filtering and sorting."""
        query = select(RentalReturnModel).options(
            joinedload(RentalReturnModel.return_location)
        )
        
        # Apply filters
        conditions = []
        
        if rental_transaction_id:
            conditions.append(RentalReturnModel.rental_transaction_id == rental_transaction_id)
        
        if return_location_id:
            conditions.append(RentalReturnModel.return_location_id == return_location_id)
        
        if return_status:
            conditions.append(RentalReturnModel.return_status == return_status.value)
        
        if return_type:
            conditions.append(RentalReturnModel.return_type == return_type.value)
        
        if return_date_from:
            conditions.append(RentalReturnModel.return_date >= return_date_from)
        
        if return_date_to:
            conditions.append(RentalReturnModel.return_date <= return_date_to)
        
        if processed_by:
            conditions.append(RentalReturnModel.processed_by.ilike(f"%{processed_by}%"))
        
        if is_active is not None:
            conditions.append(RentalReturnModel.is_active == is_active)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Apply sorting
        if hasattr(RentalReturnModel, sort_by):
            sort_column = getattr(RentalReturnModel, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(RentalReturnModel.return_date.desc())
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_rental_returns(
        self,
        rental_transaction_id: Optional[UUID] = None,
        return_location_id: Optional[UUID] = None,
        return_status: Optional[ReturnStatus] = None,
        return_type: Optional[ReturnType] = None,
        return_date_from: Optional[date] = None,
        return_date_to: Optional[date] = None,
        processed_by: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Count rental returns with optional filtering."""
        query = select(func.count(RentalReturnModel.id))
        
        # Apply same filters as get_rental_returns
        conditions = []
        
        if rental_transaction_id:
            conditions.append(RentalReturnModel.rental_transaction_id == rental_transaction_id)
        
        if return_location_id:
            conditions.append(RentalReturnModel.return_location_id == return_location_id)
        
        if return_status:
            conditions.append(RentalReturnModel.return_status == return_status.value)
        
        if return_type:
            conditions.append(RentalReturnModel.return_type == return_type.value)
        
        if return_date_from:
            conditions.append(RentalReturnModel.return_date >= return_date_from)
        
        if return_date_to:
            conditions.append(RentalReturnModel.return_date <= return_date_to)
        
        if processed_by:
            conditions.append(RentalReturnModel.processed_by.ilike(f"%{processed_by}%"))
        
        if is_active is not None:
            conditions.append(RentalReturnModel.is_active == is_active)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def update_rental_return(self, return_id: UUID, update_data: dict) -> Optional[RentalReturnModel]:
        """Update rental return by ID."""
        rental_return = await self.get_rental_return_by_id(return_id)
        if not rental_return:
            return None
        
        for key, value in update_data.items():
            if hasattr(rental_return, key):
                setattr(rental_return, key, value)
        
        await self.session.commit()
        await self.session.refresh(rental_return)
        return rental_return
    
    async def delete_rental_return(self, return_id: UUID) -> bool:
        """Delete rental return by ID (hard delete)."""
        rental_return = await self.get_rental_return_by_id(return_id)
        if not rental_return:
            return False
        
        await self.session.delete(rental_return)
        await self.session.commit()
        return True
    
    async def soft_delete_rental_return(self, return_id: UUID, deleted_by: Optional[str] = None) -> Optional[RentalReturnModel]:
        """Soft delete rental return by ID."""
        update_data = {
            'is_active': False,
            'updated_by': deleted_by
        }
        return await self.update_rental_return(return_id, update_data)
    
    # RentalReturnLine CRUD Operations
    async def create_rental_return_line(self, line_data: dict) -> RentalReturnLineModel:
        """Create a new rental return line."""
        return_line = RentalReturnLineModel(**line_data)
        self.session.add(return_line)
        await self.session.commit()
        await self.session.refresh(return_line)
        return return_line
    
    async def get_rental_return_line_by_id(self, line_id: UUID) -> Optional[RentalReturnLineModel]:
        """Get rental return line by ID with relationships."""
        result = await self.session.execute(
            select(RentalReturnLineModel)
            .options(
                joinedload(RentalReturnLineModel.rental_return),
                joinedload(RentalReturnLineModel.inventory_unit)
            )
            .filter(RentalReturnLineModel.id == line_id)
        )
        return result.scalars().first()
    
    async def get_rental_return_lines_by_return(self, return_id: UUID) -> List[RentalReturnLineModel]:
        """Get all lines for a rental return."""
        result = await self.session.execute(
            select(RentalReturnLineModel)
            .options(joinedload(RentalReturnLineModel.inventory_unit))
            .filter(RentalReturnLineModel.return_id == return_id)
            .order_by(RentalReturnLineModel.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_rental_return_lines(
        self,
        skip: int = 0,
        limit: int = 100,
        return_id: Optional[UUID] = None,
        inventory_unit_id: Optional[UUID] = None,
        condition_grade: Optional[ConditionGrade] = None,
        damage_level: Optional[DamageLevel] = None,
        is_processed: Optional[bool] = None,
        processed_by: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "asc"
    ) -> List[RentalReturnLineModel]:
        """Get rental return lines with optional filtering and sorting."""
        query = select(RentalReturnLineModel).options(
            joinedload(RentalReturnLineModel.rental_return),
            joinedload(RentalReturnLineModel.inventory_unit)
        )
        
        # Apply filters
        conditions = []
        
        if return_id:
            conditions.append(RentalReturnLineModel.return_id == return_id)
        
        if inventory_unit_id:
            conditions.append(RentalReturnLineModel.inventory_unit_id == inventory_unit_id)
        
        if condition_grade:
            conditions.append(RentalReturnLineModel.condition_grade == condition_grade.value)
        
        if damage_level:
            conditions.append(RentalReturnLineModel.damage_level == damage_level.value)
        
        if is_processed is not None:
            conditions.append(RentalReturnLineModel.is_processed == is_processed)
        
        if processed_by:
            conditions.append(RentalReturnLineModel.processed_by.ilike(f"%{processed_by}%"))
        
        if is_active is not None:
            conditions.append(RentalReturnLineModel.is_active == is_active)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Apply sorting
        if hasattr(RentalReturnLineModel, sort_by):
            sort_column = getattr(RentalReturnLineModel, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(RentalReturnLineModel.created_at.asc())
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_rental_return_line(self, line_id: UUID, update_data: dict) -> Optional[RentalReturnLineModel]:
        """Update rental return line by ID."""
        return_line = await self.get_rental_return_line_by_id(line_id)
        if not return_line:
            return None
        
        for key, value in update_data.items():
            if hasattr(return_line, key):
                setattr(return_line, key, value)
        
        await self.session.commit()
        await self.session.refresh(return_line)
        return return_line
    
    # Specialized Query Methods
    async def get_returns_by_status(self, status: ReturnStatus) -> List[RentalReturnModel]:
        """Get returns by status."""
        result = await self.session.execute(
            select(RentalReturnModel)
            .options(joinedload(RentalReturnModel.return_location))
            .filter(
                and_(
                    RentalReturnModel.return_status == status.value,
                    RentalReturnModel.is_active == True
                )
            )
            .order_by(RentalReturnModel.return_date.desc())
        )
        return result.scalars().all()
    
    async def get_overdue_returns(self, days_threshold: int = 0) -> List[RentalReturnModel]:
        """Get returns that are overdue."""
        today = date.today()
        
        result = await self.session.execute(
            select(RentalReturnModel)
            .options(joinedload(RentalReturnModel.return_location))
            .filter(
                and_(
                    RentalReturnModel.is_active == True,
                    RentalReturnModel.expected_return_date.isnot(None),
                    RentalReturnModel.return_date > RentalReturnModel.expected_return_date,
                    RentalReturnModel.return_status.in_([
                        ReturnStatus.PENDING.value,
                        ReturnStatus.INITIATED.value,
                        ReturnStatus.IN_INSPECTION.value,
                        ReturnStatus.PARTIALLY_COMPLETED.value
                    ])
                )
            )
            .order_by(RentalReturnModel.expected_return_date.asc())
        )
        return result.scalars().all()
    
    async def get_lines_needing_processing(self) -> List[RentalReturnLineModel]:
        """Get return lines that need processing."""
        result = await self.session.execute(
            select(RentalReturnLineModel)
            .options(
                joinedload(RentalReturnLineModel.rental_return),
                joinedload(RentalReturnLineModel.inventory_unit)
            )
            .filter(
                and_(
                    RentalReturnLineModel.is_processed == False,
                    RentalReturnLineModel.is_active == True,
                    RentalReturnLineModel.returned_quantity > 0
                )
            )
            .order_by(RentalReturnLineModel.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_damaged_returns(self) -> List[RentalReturnLineModel]:
        """Get return lines with damage."""
        result = await self.session.execute(
            select(RentalReturnLineModel)
            .options(
                joinedload(RentalReturnLineModel.rental_return),
                joinedload(RentalReturnLineModel.inventory_unit)
            )
            .filter(
                and_(
                    RentalReturnLineModel.damage_level != DamageLevel.NONE.value,
                    RentalReturnLineModel.is_active == True
                )
            )
            .order_by(RentalReturnLineModel.created_at.desc())
        )
        return result.scalars().all()
    
    # Bulk Operations
    async def bulk_update_return_status(self, return_ids: List[UUID], new_status: ReturnStatus, updated_by: Optional[str] = None) -> int:
        """Bulk update status for multiple returns."""
        stmt = (
            update(RentalReturnModel)
            .where(RentalReturnModel.id.in_(return_ids))
            .values(return_status=new_status.value, updated_by=updated_by)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_process_return_lines(self, line_ids: List[UUID], processed_by: str) -> int:
        """Bulk process return lines."""
        from datetime import datetime
        
        stmt = (
            update(RentalReturnLineModel)
            .where(RentalReturnLineModel.id.in_(line_ids))
            .values(
                is_processed=True,
                processed_at=datetime.utcnow(),
                processed_by=processed_by,
                updated_by=processed_by
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
    
    # Analytics and Reporting
    async def get_return_summary_by_status(self) -> dict:
        """Get return summary grouped by status."""
        result = await self.session.execute(
            select(
                RentalReturnModel.return_status,
                func.count(RentalReturnModel.id)
            )
            .filter(RentalReturnModel.is_active == True)
            .group_by(RentalReturnModel.return_status)
        )
        
        return {status: count for status, count in result.all()}
    
    async def get_damage_summary(self) -> dict:
        """Get damage summary grouped by damage level."""
        result = await self.session.execute(
            select(
                RentalReturnLineModel.damage_level,
                func.count(RentalReturnLineModel.id),
                func.sum(RentalReturnLineModel.damage_fee + RentalReturnLineModel.cleaning_fee + RentalReturnLineModel.replacement_fee)
            )
            .filter(RentalReturnLineModel.is_active == True)
            .group_by(RentalReturnLineModel.damage_level)
        )
        
        return {
            damage_level: {"count": count, "total_fees": float(total_fees or 0)}
            for damage_level, count, total_fees in result.all()
        }
    
    async def get_return_metrics(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> dict:
        """Get return metrics for a date range."""
        query = select(
            func.count(RentalReturnModel.id).label('total_returns'),
            func.count(
                func.nullif(RentalReturnModel.return_status != ReturnStatus.COMPLETED.value, False)
            ).label('completed_returns'),
            func.sum(RentalReturnModel.total_late_fee + RentalReturnModel.total_damage_fee).label('total_fees'),
            func.sum(RentalReturnModel.total_refund_amount).label('total_refunds')
        ).filter(RentalReturnModel.is_active == True)
        
        if start_date:
            query = query.filter(RentalReturnModel.return_date >= start_date)
        
        if end_date:
            query = query.filter(RentalReturnModel.return_date <= end_date)
        
        result = await self.session.execute(query)
        row = result.first()
        
        return {
            "total_returns": row.total_returns or 0,
            "completed_returns": row.completed_returns or 0,
            "total_fees": float(row.total_fees or 0),
            "total_refunds": float(row.total_refunds or 0)
        }