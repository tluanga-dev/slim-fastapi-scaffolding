from typing import List, Optional, Tuple
from uuid import UUID
from datetime import date, datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.inventory_unit import InventoryUnit
from src.domain.repositories.inventory_unit_repository import InventoryUnitRepository
from src.domain.value_objects.item_type import InventoryStatus, ConditionGrade
from src.infrastructure.models.inventory_unit_model import InventoryUnitModel


class SQLAlchemyInventoryUnitRepository(InventoryUnitRepository):
    """SQLAlchemy implementation of InventoryUnitRepository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, inventory_unit: InventoryUnit) -> InventoryUnit:
        """Create a new inventory unit."""
        db_unit = InventoryUnitModel.from_entity(inventory_unit)
        self.session.add(db_unit)
        await self.session.flush()  # Flush to persist changes, but don't commit
        await self.session.refresh(db_unit)
        return db_unit.to_entity()
    
    async def get_by_id(self, inventory_id: UUID) -> Optional[InventoryUnit]:
        """Get inventory unit by ID."""
        query = select(InventoryUnitModel).where(InventoryUnitModel.id == inventory_id)
        result = await self.session.execute(query)
        db_unit = result.scalar_one_or_none()
        return db_unit.to_entity() if db_unit else None
    
    async def get_by_code(self, inventory_code: str) -> Optional[InventoryUnit]:
        """Get inventory unit by inventory code."""
        query = select(InventoryUnitModel).where(
            InventoryUnitModel.inventory_code == inventory_code
        )
        result = await self.session.execute(query)
        db_unit = result.scalar_one_or_none()
        return db_unit.to_entity() if db_unit else None
    
    async def get_by_serial_number(self, serial_number: str) -> Optional[InventoryUnit]:
        """Get inventory unit by serial number."""
        query = select(InventoryUnitModel).where(
            InventoryUnitModel.serial_number == serial_number
        )
        result = await self.session.execute(query)
        db_unit = result.scalar_one_or_none()
        return db_unit.to_entity() if db_unit else None
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[InventoryStatus] = None,
        condition_grade: Optional[ConditionGrade] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[InventoryUnit], int]:
        """List inventory units with filters and pagination."""
        query = select(InventoryUnitModel)
        count_query = select(func.count()).select_from(InventoryUnitModel)
        
        # Build filters
        filters = []
        if is_active is not None:
            filters.append(InventoryUnitModel.is_active == is_active)
        if item_id:
            filters.append(InventoryUnitModel.item_id == item_id)
        if location_id:
            filters.append(InventoryUnitModel.location_id == location_id)
        if status:
            filters.append(InventoryUnitModel.current_status == status)
        if condition_grade:
            filters.append(InventoryUnitModel.condition_grade == condition_grade)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply pagination
        query = query.order_by(InventoryUnitModel.inventory_code).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        return [unit.to_entity() for unit in units], total_count
    
    async def update(self, inventory_id: UUID, inventory_unit: InventoryUnit) -> InventoryUnit:
        """Update existing inventory unit."""
        query = select(InventoryUnitModel).where(InventoryUnitModel.id == inventory_id)
        result = await self.session.execute(query)
        db_unit = result.scalar_one_or_none()
        
        if not db_unit:
            raise ValueError(f"Inventory unit with id {inventory_id} not found")
        
        # Update fields
        db_unit.inventory_code = inventory_unit.inventory_code
        db_unit.item_id = inventory_unit.item_id
        db_unit.location_id = inventory_unit.location_id
        db_unit.serial_number = inventory_unit.serial_number
        db_unit.current_status = inventory_unit.current_status
        db_unit.condition_grade = inventory_unit.condition_grade
        db_unit.purchase_date = inventory_unit.purchase_date
        db_unit.purchase_cost = inventory_unit.purchase_cost
        db_unit.current_value = inventory_unit.current_value
        db_unit.last_inspection_date = inventory_unit.last_inspection_date
        db_unit.total_rental_days = inventory_unit.total_rental_days
        db_unit.rental_count = inventory_unit.rental_count
        db_unit.notes = inventory_unit.notes
        db_unit.is_active = inventory_unit.is_active
        db_unit.updated_by = inventory_unit.updated_by
        db_unit.updated_at = datetime.utcnow()
        
        await self.session.flush()  # Flush to persist changes, but don't commit
        await self.session.refresh(db_unit)
        return db_unit.to_entity()
    
    async def delete(self, inventory_id: UUID) -> bool:
        """Soft delete inventory unit."""
        query = select(InventoryUnitModel).where(InventoryUnitModel.id == inventory_id)
        result = await self.session.execute(query)
        db_unit = result.scalar_one_or_none()
        
        if not db_unit:
            return False
        
        db_unit.is_active = False
        db_unit.updated_at = datetime.utcnow()
        await self.session.flush()  # Flush to persist changes, but don't commit
        return True
    
    async def exists_by_code(self, inventory_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if an inventory unit with the given code exists."""
        query = select(InventoryUnitModel).where(
            InventoryUnitModel.inventory_code == inventory_code
        )
        
        if exclude_id:
            query = query.where(InventoryUnitModel.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def exists_by_serial(self, serial_number: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if an inventory unit with the given serial number exists."""
        query = select(InventoryUnitModel).where(
            InventoryUnitModel.serial_number == serial_number
        )
        
        if exclude_id:
            query = query.where(InventoryUnitModel.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_available_units(
        self,
        item_id: UUID,
        location_id: Optional[UUID] = None,
        condition_grade: Optional[ConditionGrade] = None
    ) -> List[InventoryUnit]:
        """Get available units for a SKU."""
        query = select(InventoryUnitModel).where(
            and_(
                InventoryUnitModel.item_id == item_id,
                InventoryUnitModel.is_active == True,
                or_(
                    InventoryUnitModel.current_status == InventoryStatus.AVAILABLE_SALE,
                    InventoryUnitModel.current_status == InventoryStatus.AVAILABLE_RENT
                )
            )
        )
        
        if location_id:
            query = query.where(InventoryUnitModel.location_id == location_id)
        
        if condition_grade:
            query = query.where(InventoryUnitModel.condition_grade == condition_grade)
        
        # Order by condition grade (best first)
        query = query.order_by(InventoryUnitModel.condition_grade)
        
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        return [unit.to_entity() for unit in units]
    
    async def get_units_by_status(
        self,
        status: InventoryStatus,
        location_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[InventoryUnit], int]:
        """Get inventory units by status."""
        query = select(InventoryUnitModel).where(
            and_(
                InventoryUnitModel.current_status == status,
                InventoryUnitModel.is_active == True
            )
        )
        count_query = select(func.count()).select_from(InventoryUnitModel).where(
            and_(
                InventoryUnitModel.current_status == status,
                InventoryUnitModel.is_active == True
            )
        )
        
        if location_id:
            query = query.where(InventoryUnitModel.location_id == location_id)
            count_query = count_query.where(InventoryUnitModel.location_id == location_id)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply pagination
        query = query.order_by(InventoryUnitModel.inventory_code).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        return [unit.to_entity() for unit in units], total_count
    
    async def get_units_needing_inspection(
        self,
        days_since_last: int = 30,
        location_id: Optional[UUID] = None
    ) -> List[InventoryUnit]:
        """Get units that need inspection."""
        cutoff_date = date.today() - timedelta(days=days_since_last)
        
        query = select(InventoryUnitModel).where(
            and_(
                InventoryUnitModel.is_active == True,
                or_(
                    InventoryUnitModel.last_inspection_date == None,
                    InventoryUnitModel.last_inspection_date < cutoff_date
                )
            )
        )
        
        if location_id:
            query = query.where(InventoryUnitModel.location_id == location_id)
        
        # Order by last inspection date (oldest first)
        query = query.order_by(InventoryUnitModel.last_inspection_date.asc().nullsfirst())
        
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        return [unit.to_entity() for unit in units]
    
    async def get_rental_history(
        self,
        inventory_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[dict]:
        """Get rental history for an inventory unit."""
        # This would typically join with transaction tables
        # For now, return empty list as transaction history is not yet implemented
        return []
    
    async def count_by_status(self, location_id: Optional[UUID] = None) -> dict:
        """Get count of inventory units by status."""
        base_query = select(
            InventoryUnitModel.current_status,
            func.count(InventoryUnitModel.id).label('count')
        ).where(
            InventoryUnitModel.is_active == True
        )
        
        if location_id:
            base_query = base_query.where(InventoryUnitModel.location_id == location_id)
        
        query = base_query.group_by(InventoryUnitModel.current_status)
        
        result = await self.session.execute(query)
        counts = result.all()
        
        return {status.value: count for status, count in counts}
    
    async def count_by_condition(self, location_id: Optional[UUID] = None) -> dict:
        """Get count of inventory units by condition grade."""
        base_query = select(
            InventoryUnitModel.condition_grade,
            func.count(InventoryUnitModel.id).label('count')
        ).where(
            InventoryUnitModel.is_active == True
        )
        
        if location_id:
            base_query = base_query.where(InventoryUnitModel.location_id == location_id)
        
        query = base_query.group_by(InventoryUnitModel.condition_grade)
        
        result = await self.session.execute(query)
        counts = result.all()
        
        return {grade.value: count for grade, count in counts}
    
    async def get_high_value_units(
        self,
        min_value: float,
        location_id: Optional[UUID] = None
    ) -> List[InventoryUnit]:
        """Get high value inventory units."""
        query = select(InventoryUnitModel).where(
            and_(
                InventoryUnitModel.is_active == True,
                InventoryUnitModel.current_value >= min_value
            )
        )
        
        if location_id:
            query = query.where(InventoryUnitModel.location_id == location_id)
        
        # Order by value descending
        query = query.order_by(InventoryUnitModel.current_value.desc())
        
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        return [unit.to_entity() for unit in units]
    
    async def get_by_sku_and_location(
        self,
        item_id: UUID,
        location_id: UUID
    ) -> List[InventoryUnit]:
        """Get all inventory units for a SKU at a specific location."""
        query = select(InventoryUnitModel).where(
            and_(
                InventoryUnitModel.item_id == item_id,
                InventoryUnitModel.location_id == location_id,
                InventoryUnitModel.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        return [unit.to_entity() for unit in units]
    
    async def get_by_status_and_sku(
        self,
        status: InventoryStatus,
        item_id: UUID
    ) -> List[InventoryUnit]:
        """Get inventory units by status and SKU."""
        query = select(InventoryUnitModel).where(
            and_(
                InventoryUnitModel.current_status == status,
                InventoryUnitModel.item_id == item_id,
                InventoryUnitModel.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        return [unit.to_entity() for unit in units]