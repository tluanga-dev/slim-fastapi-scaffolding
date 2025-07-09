from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from app.modules.locations.models import Location
from app.core.domain.entities.location import LocationType


class LocationRepository:
    """Repository for location data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_location(self, location_data: dict) -> Location:
        """Create a new location."""
        location = Location(**location_data)
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location
    
    async def get_location_by_id(self, location_id: UUID) -> Optional[Location]:
        """Get location by ID."""
        result = await self.session.execute(
            select(Location).filter(Location.id == location_id)
        )
        return result.scalars().first()
    
    async def get_location_by_code(self, location_code: str) -> Optional[Location]:
        """Get location by location code."""
        result = await self.session.execute(
            select(Location).filter(Location.location_code == location_code)
        )
        return result.scalars().first()
    
    async def get_locations(
        self,
        skip: int = 0,
        limit: int = 100,
        location_type: Optional[LocationType] = None,
        is_active: Optional[bool] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Location]:
        """Get locations with optional filtering."""
        query = select(Location)
        
        # Apply filters
        conditions = []
        
        if location_type:
            conditions.append(Location.location_type == location_type)
        
        if is_active is not None:
            conditions.append(Location.is_active == is_active)
        
        if city:
            conditions.append(Location.city.ilike(f"%{city}%"))
        
        if state:
            conditions.append(Location.state.ilike(f"%{state}%"))
        
        if country:
            conditions.append(Location.country.ilike(f"%{country}%"))
        
        if search:
            search_conditions = [
                Location.location_name.ilike(f"%{search}%"),
                Location.location_code.ilike(f"%{search}%"),
                Location.address.ilike(f"%{search}%"),
                Location.city.ilike(f"%{search}%")
            ]
            conditions.append(func.or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        query = query.order_by(Location.location_name).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_locations(
        self,
        location_type: Optional[LocationType] = None,
        is_active: Optional[bool] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        """Count locations with optional filtering."""
        query = select(func.count(Location.id))
        
        # Apply same filters as get_locations
        conditions = []
        
        if location_type:
            conditions.append(Location.location_type == location_type)
        
        if is_active is not None:
            conditions.append(Location.is_active == is_active)
        
        if city:
            conditions.append(Location.city.ilike(f"%{city}%"))
        
        if state:
            conditions.append(Location.state.ilike(f"%{state}%"))
        
        if country:
            conditions.append(Location.country.ilike(f"%{country}%"))
        
        if search:
            search_conditions = [
                Location.location_name.ilike(f"%{search}%"),
                Location.location_code.ilike(f"%{search}%"),
                Location.address.ilike(f"%{search}%"),
                Location.city.ilike(f"%{search}%")
            ]
            conditions.append(func.or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def update_location(self, location_id: UUID, update_data: dict) -> Optional[Location]:
        """Update location by ID."""
        location = await self.get_location_by_id(location_id)
        if not location:
            return None
        
        for key, value in update_data.items():
            if hasattr(location, key):
                setattr(location, key, value)
        
        await self.session.commit()
        await self.session.refresh(location)
        return location
    
    async def delete_location(self, location_id: UUID) -> bool:
        """Delete location by ID (hard delete)."""
        location = await self.get_location_by_id(location_id)
        if not location:
            return False
        
        await self.session.delete(location)
        await self.session.commit()
        return True
    
    async def get_locations_by_manager(self, manager_user_id: UUID) -> List[Location]:
        """Get all locations managed by a specific user."""
        result = await self.session.execute(
            select(Location).filter(
                and_(
                    Location.manager_user_id == manager_user_id,
                    Location.is_active == True
                )
            ).order_by(Location.location_name)
        )
        return result.scalars().all()
    
    async def get_locations_by_type(self, location_type: LocationType) -> List[Location]:
        """Get all locations of a specific type."""
        result = await self.session.execute(
            select(Location).filter(
                and_(
                    Location.location_type == location_type,
                    Location.is_active == True
                )
            ).order_by(Location.location_name)
        )
        return result.scalars().all()
    
    async def location_code_exists(self, location_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if location code already exists."""
        query = select(Location).filter(Location.location_code == location_code)
        
        if exclude_id:
            query = query.filter(Location.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None