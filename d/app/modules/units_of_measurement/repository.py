from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.modules.units_of_measurement.models import UnitOfMeasurement


class UnitOfMeasurementRepository:
    """Repository for unit of measurement data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_unit(self, unit_data: dict) -> UnitOfMeasurement:
        """Create a new unit of measurement."""
        unit = UnitOfMeasurement(**unit_data)
        self.session.add(unit)
        await self.session.commit()
        await self.session.refresh(unit)
        return unit
    
    async def get_unit_by_id(self, unit_id: UUID) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by primary key ID."""
        result = await self.session.execute(
            select(UnitOfMeasurement).filter(UnitOfMeasurement.id == unit_id)
        )
        return result.scalars().first()
    
    async def get_unit_by_unit_id(self, unit_id: UUID) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by business unit_id."""
        result = await self.session.execute(
            select(UnitOfMeasurement).filter(UnitOfMeasurement.unit_id == unit_id)
        )
        return result.scalars().first()
    
    async def get_unit_by_name(self, name: str) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by name (case-insensitive)."""
        result = await self.session.execute(
            select(UnitOfMeasurement).filter(
                func.lower(UnitOfMeasurement.name) == name.lower()
            )
        )
        return result.scalars().first()
    
    async def get_unit_by_abbreviation(self, abbreviation: str) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by abbreviation (case-insensitive)."""
        result = await self.session.execute(
            select(UnitOfMeasurement).filter(
                func.lower(UnitOfMeasurement.abbreviation) == abbreviation.lower()
            )
        )
        return result.scalars().first()
    
    async def get_units(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[UnitOfMeasurement]:
        """Get units of measurement with optional filtering."""
        query = select(UnitOfMeasurement)
        
        # Apply filters
        conditions = []
        
        if is_active is not None:
            conditions.append(UnitOfMeasurement.is_active == is_active)
        
        if search:
            search_conditions = [
                UnitOfMeasurement.name.ilike(f"%{search}%"),
                UnitOfMeasurement.abbreviation.ilike(f"%{search}%"),
                UnitOfMeasurement.description.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        query = query.order_by(UnitOfMeasurement.name).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_units(
        self,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """Count units of measurement with optional filtering."""
        query = select(func.count(UnitOfMeasurement.id))
        
        # Apply same filters as get_units
        conditions = []
        
        if is_active is not None:
            conditions.append(UnitOfMeasurement.is_active == is_active)
        
        if search:
            search_conditions = [
                UnitOfMeasurement.name.ilike(f"%{search}%"),
                UnitOfMeasurement.abbreviation.ilike(f"%{search}%"),
                UnitOfMeasurement.description.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def update_unit(self, unit_id: UUID, update_data: dict) -> Optional[UnitOfMeasurement]:
        """Update unit of measurement by ID."""
        unit = await self.get_unit_by_id(unit_id)
        if not unit:
            return None
        
        for key, value in update_data.items():
            if hasattr(unit, key):
                setattr(unit, key, value)
        
        await self.session.commit()
        await self.session.refresh(unit)
        return unit
    
    async def delete_unit(self, unit_id: UUID) -> bool:
        """Delete unit of measurement by ID (hard delete)."""
        unit = await self.get_unit_by_id(unit_id)
        if not unit:
            return False
        
        await self.session.delete(unit)
        await self.session.commit()
        return True
    
    async def get_active_units(self) -> List[UnitOfMeasurement]:
        """Get all active units of measurement."""
        result = await self.session.execute(
            select(UnitOfMeasurement).filter(
                UnitOfMeasurement.is_active == True
            ).order_by(UnitOfMeasurement.name)
        )
        return result.scalars().all()
    
    async def name_exists(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if unit name already exists (case-insensitive)."""
        query = select(UnitOfMeasurement).filter(
            func.lower(UnitOfMeasurement.name) == name.lower()
        )
        
        if exclude_id:
            query = query.filter(UnitOfMeasurement.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None
    
    async def abbreviation_exists(self, abbreviation: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if unit abbreviation already exists (case-insensitive)."""
        query = select(UnitOfMeasurement).filter(
            func.lower(UnitOfMeasurement.abbreviation) == abbreviation.lower()
        )
        
        if exclude_id:
            query = query.filter(UnitOfMeasurement.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None
    
    async def unit_id_exists(self, unit_id: UUID, exclude_id: Optional[UUID] = None) -> bool:
        """Check if unit_id already exists."""
        query = select(UnitOfMeasurement).filter(UnitOfMeasurement.unit_id == unit_id)
        
        if exclude_id:
            query = query.filter(UnitOfMeasurement.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None
    
    async def get_units_for_validation(self, unit_ids: List[UUID]) -> List[UnitOfMeasurement]:
        """Get multiple units by unit_id for validation purposes."""
        result = await self.session.execute(
            select(UnitOfMeasurement).filter(
                UnitOfMeasurement.unit_id.in_(unit_ids)
            )
        )
        return result.scalars().all()
    
    async def search_units_by_partial_match(self, partial_name: str, limit: int = 10) -> List[UnitOfMeasurement]:
        """Search units by partial name or abbreviation match."""
        result = await self.session.execute(
            select(UnitOfMeasurement).filter(
                and_(
                    UnitOfMeasurement.is_active == True,
                    or_(
                        UnitOfMeasurement.name.ilike(f"%{partial_name}%"),
                        UnitOfMeasurement.abbreviation.ilike(f"%{partial_name}%")
                    )
                )
            ).order_by(UnitOfMeasurement.name).limit(limit)
        )
        return result.scalars().all()