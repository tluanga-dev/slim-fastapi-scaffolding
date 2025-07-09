from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import joinedload

from app.modules.inventory_units.models import InventoryUnitModel
from app.core.domain.value_objects.item_type import InventoryStatus, ConditionGrade


class InventoryUnitRepository:
    """Repository for inventory unit data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_inventory_unit(self, inventory_unit_data: dict) -> InventoryUnitModel:
        """Create a new inventory unit."""
        inventory_unit = InventoryUnitModel(**inventory_unit_data)
        self.session.add(inventory_unit)
        await self.session.commit()
        await self.session.refresh(inventory_unit)
        return inventory_unit
    
    async def get_inventory_unit_by_id(self, inventory_unit_id: UUID) -> Optional[InventoryUnitModel]:
        """Get inventory unit by ID with relationships."""
        result = await self.session.execute(
            select(InventoryUnitModel)
            .options(joinedload(InventoryUnitModel.item), joinedload(InventoryUnitModel.location))
            .filter(InventoryUnitModel.id == inventory_unit_id)
        )
        return result.scalars().first()
    
    async def get_inventory_unit_by_code(self, inventory_code: str) -> Optional[InventoryUnitModel]:
        """Get inventory unit by inventory code."""
        result = await self.session.execute(
            select(InventoryUnitModel)
            .options(joinedload(InventoryUnitModel.item), joinedload(InventoryUnitModel.location))
            .filter(InventoryUnitModel.inventory_code == inventory_code)
        )
        return result.scalars().first()
    
    async def get_inventory_unit_by_serial(self, serial_number: str) -> Optional[InventoryUnitModel]:
        """Get inventory unit by serial number."""
        result = await self.session.execute(
            select(InventoryUnitModel)
            .options(joinedload(InventoryUnitModel.item), joinedload(InventoryUnitModel.location))
            .filter(InventoryUnitModel.serial_number == serial_number)
        )
        return result.scalars().first()
    
    async def get_inventory_units(
        self,
        skip: int = 0,
        limit: int = 100,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[InventoryStatus] = None,
        condition_grade: Optional[ConditionGrade] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "inventory_code",
        sort_order: str = "asc"
    ) -> List[InventoryUnitModel]:
        """Get inventory units with optional filtering and sorting."""
        query = select(InventoryUnitModel).options(
            joinedload(InventoryUnitModel.item),
            joinedload(InventoryUnitModel.location)
        )
        
        # Apply filters
        conditions = []
        
        if item_id:
            conditions.append(InventoryUnitModel.item_id == item_id)
        
        if location_id:
            conditions.append(InventoryUnitModel.location_id == location_id)
        
        if status:
            conditions.append(InventoryUnitModel.current_status == status)
        
        if condition_grade:
            conditions.append(InventoryUnitModel.condition_grade == condition_grade)
        
        if is_active is not None:
            conditions.append(InventoryUnitModel.is_active == is_active)
        
        if search:
            search_conditions = [
                InventoryUnitModel.inventory_code.ilike(f"%{search}%"),
                InventoryUnitModel.serial_number.ilike(f"%{search}%"),
                InventoryUnitModel.notes.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Apply sorting
        if hasattr(InventoryUnitModel, sort_by):
            sort_column = getattr(InventoryUnitModel, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(InventoryUnitModel.inventory_code.asc())
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_inventory_units(
        self,
        item_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[InventoryStatus] = None,
        condition_grade: Optional[ConditionGrade] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """Count inventory units with optional filtering."""
        query = select(func.count(InventoryUnitModel.id))
        
        # Apply same filters as get_inventory_units
        conditions = []
        
        if item_id:
            conditions.append(InventoryUnitModel.item_id == item_id)
        
        if location_id:
            conditions.append(InventoryUnitModel.location_id == location_id)
        
        if status:
            conditions.append(InventoryUnitModel.current_status == status)
        
        if condition_grade:
            conditions.append(InventoryUnitModel.condition_grade == condition_grade)
        
        if is_active is not None:
            conditions.append(InventoryUnitModel.is_active == is_active)
        
        if search:
            search_conditions = [
                InventoryUnitModel.inventory_code.ilike(f"%{search}%"),
                InventoryUnitModel.serial_number.ilike(f"%{search}%"),
                InventoryUnitModel.notes.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def update_inventory_unit(self, inventory_unit_id: UUID, update_data: dict) -> Optional[InventoryUnitModel]:
        """Update inventory unit by ID."""
        inventory_unit = await self.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            return None
        
        for key, value in update_data.items():
            if hasattr(inventory_unit, key):
                setattr(inventory_unit, key, value)
        
        await self.session.commit()
        await self.session.refresh(inventory_unit)
        return inventory_unit
    
    async def delete_inventory_unit(self, inventory_unit_id: UUID) -> bool:
        """Delete inventory unit by ID (hard delete)."""
        inventory_unit = await self.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            return False
        
        await self.session.delete(inventory_unit)
        await self.session.commit()
        return True
    
    async def soft_delete_inventory_unit(self, inventory_unit_id: UUID, deleted_by: Optional[str] = None) -> Optional[InventoryUnitModel]:
        """Soft delete inventory unit by ID."""
        update_data = {
            'is_active': False,
            'updated_by': deleted_by
        }
        return await self.update_inventory_unit(inventory_unit_id, update_data)
    
    async def get_available_units_by_item(self, item_id: UUID) -> List[InventoryUnitModel]:
        """Get available inventory units for a specific item."""
        result = await self.session.execute(
            select(InventoryUnitModel)
            .options(joinedload(InventoryUnitModel.location))
            .filter(
                and_(
                    InventoryUnitModel.item_id == item_id,
                    InventoryUnitModel.is_active == True,
                    or_(
                        InventoryUnitModel.current_status == InventoryStatus.AVAILABLE_RENTAL,
                        InventoryUnitModel.current_status == InventoryStatus.AVAILABLE_SALE
                    )
                )
            )
            .order_by(InventoryUnitModel.condition_grade.asc(), InventoryUnitModel.created_at.asc())
        )
        return result.scalars().all()
    
    async def get_units_by_location(self, location_id: UUID, is_active: bool = True) -> List[InventoryUnitModel]:
        """Get inventory units at a specific location."""
        conditions = [InventoryUnitModel.location_id == location_id]
        if is_active is not None:
            conditions.append(InventoryUnitModel.is_active == is_active)
        
        result = await self.session.execute(
            select(InventoryUnitModel)
            .options(joinedload(InventoryUnitModel.item))
            .filter(and_(*conditions))
            .order_by(InventoryUnitModel.inventory_code.asc())
        )
        return result.scalars().all()
    
    async def get_units_needing_inspection(self, days_threshold: int = 90) -> List[InventoryUnitModel]:
        """Get units that need inspection (haven't been inspected in X days)."""
        threshold_date = date.today()
        
        result = await self.session.execute(
            select(InventoryUnitModel)
            .options(joinedload(InventoryUnitModel.item), joinedload(InventoryUnitModel.location))
            .filter(
                and_(
                    InventoryUnitModel.is_active == True,
                    or_(
                        InventoryUnitModel.last_inspection_date.is_(None),
                        InventoryUnitModel.last_inspection_date < threshold_date
                    )
                )
            )
            .order_by(InventoryUnitModel.last_inspection_date.asc().nullsfirst())
        )
        return result.scalars().all()
    
    async def get_units_by_status(self, status: InventoryStatus) -> List[InventoryUnitModel]:
        """Get inventory units by status."""
        result = await self.session.execute(
            select(InventoryUnitModel)
            .options(joinedload(InventoryUnitModel.item), joinedload(InventoryUnitModel.location))
            .filter(
                and_(
                    InventoryUnitModel.current_status == status,
                    InventoryUnitModel.is_active == True
                )
            )
            .order_by(InventoryUnitModel.inventory_code.asc())
        )
        return result.scalars().all()
    
    async def inventory_code_exists(self, inventory_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if inventory code already exists."""
        query = select(InventoryUnitModel).filter(InventoryUnitModel.inventory_code == inventory_code)
        
        if exclude_id:
            query = query.filter(InventoryUnitModel.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None
    
    async def serial_number_exists(self, serial_number: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if serial number already exists."""
        if not serial_number:
            return False
            
        query = select(InventoryUnitModel).filter(InventoryUnitModel.serial_number == serial_number)
        
        if exclude_id:
            query = query.filter(InventoryUnitModel.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None
    
    async def bulk_update_status(self, inventory_unit_ids: List[UUID], new_status: InventoryStatus, updated_by: Optional[str] = None) -> int:
        """Bulk update status for multiple inventory units."""
        from sqlalchemy import update
        
        stmt = (
            update(InventoryUnitModel)
            .where(InventoryUnitModel.id.in_(inventory_unit_ids))
            .values(current_status=new_status, updated_by=updated_by)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
    
    async def bulk_update_location(self, inventory_unit_ids: List[UUID], new_location_id: UUID, updated_by: Optional[str] = None) -> int:
        """Bulk update location for multiple inventory units."""
        from sqlalchemy import update
        
        stmt = (
            update(InventoryUnitModel)
            .where(InventoryUnitModel.id.in_(inventory_unit_ids))
            .values(location_id=new_location_id, updated_by=updated_by)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
    
    async def get_inventory_summary_by_status(self) -> dict:
        """Get inventory summary grouped by status."""
        result = await self.session.execute(
            select(
                InventoryUnitModel.current_status,
                func.count(InventoryUnitModel.id)
            )
            .filter(InventoryUnitModel.is_active == True)
            .group_by(InventoryUnitModel.current_status)
        )
        
        return {status.value: count for status, count in result.all()}
    
    async def get_inventory_summary_by_condition(self) -> dict:
        """Get inventory summary grouped by condition grade."""
        result = await self.session.execute(
            select(
                InventoryUnitModel.condition_grade,
                func.count(InventoryUnitModel.id)
            )
            .filter(InventoryUnitModel.is_active == True)
            .group_by(InventoryUnitModel.condition_grade)
        )
        
        return {condition.value: count for condition, count in result.all()}
    
    async def get_inventory_summary_by_location(self) -> List[dict]:
        """Get inventory summary grouped by location."""
        result = await self.session.execute(
            select(
                InventoryUnitModel.location_id,
                func.count(InventoryUnitModel.id)
            )
            .filter(InventoryUnitModel.is_active == True)
            .group_by(InventoryUnitModel.location_id)
        )
        
        return [{"location_id": str(location_id), "count": count} for location_id, count in result.all()]