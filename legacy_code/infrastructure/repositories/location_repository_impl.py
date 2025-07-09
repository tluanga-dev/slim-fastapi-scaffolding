from typing import List, Optional
from uuid import UUID
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.location import Location, LocationType
from ...domain.repositories.location_repository import LocationRepository
from ..models.location_model import LocationModel


class SQLAlchemyLocationRepository(LocationRepository):
    """SQLAlchemy implementation of LocationRepository."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db
    
    async def create(self, location: Location) -> Location:
        """Create a new location."""
        db_location = LocationModel.from_entity(location)
        self.db.add(db_location)
        await self.db.commit()
        await self.db.refresh(db_location)
        return db_location.to_entity()
    
    async def get_by_id(self, location_id: UUID) -> Optional[Location]:
        """Get location by ID."""
        from sqlalchemy import select
        
        query = select(LocationModel).where(
            and_(
                LocationModel.id == location_id,
                LocationModel.is_active == True
            )
        )
        result = await self.db.execute(query)
        db_location = result.scalar_one_or_none()
        return db_location.to_entity() if db_location else None
    
    async def get_by_code(self, location_code: str) -> Optional[Location]:
        """Get location by location code."""
        from sqlalchemy import select
        
        query = select(LocationModel).where(
            and_(
                LocationModel.location_code == location_code,
                LocationModel.is_active == True
            )
        )
        result = await self.db.execute(query)
        db_location = result.scalar_one_or_none()
        return db_location.to_entity() if db_location else None
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        location_type: Optional[LocationType] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[Location]:
        """List locations with optional filters."""
        from sqlalchemy import select
        
        query = select(LocationModel)
        
        # Apply filters
        filters = []
        if is_active is not None:
            filters.append(LocationModel.is_active == is_active)
        if location_type:
            filters.append(LocationModel.location_type == location_type)
        if city:
            filters.append(LocationModel.city.ilike(f"%{city}%"))
        if state:
            filters.append(LocationModel.state.ilike(f"%{state}%"))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        db_locations = result.scalars().all()
        return [db_location.to_entity() for db_location in db_locations]
    
    async def update(self, location: Location) -> Location:
        """Update existing location."""
        from sqlalchemy import select
        
        query = select(LocationModel).where(LocationModel.id == location.id)
        result = await self.db.execute(query)
        db_location = result.scalar_one_or_none()
        
        if not db_location:
            raise ValueError(f"Location with ID {location.id} not found")
        
        # Update all fields
        db_location.location_code = location.location_code
        db_location.location_name = location.location_name
        db_location.location_type = location.location_type
        db_location.address = location.address
        db_location.city = location.city
        db_location.state = location.state
        db_location.country = location.country
        db_location.postal_code = location.postal_code
        db_location.contact_number = location.contact_number
        db_location.email = location.email
        db_location.manager_user_id = location.manager_user_id
        db_location.updated_at = location.updated_at
        db_location.updated_by = location.updated_by
        db_location.is_active = location.is_active
        
        await self.db.commit()
        await self.db.refresh(db_location)
        return db_location.to_entity()
    
    async def delete(self, location_id: UUID) -> bool:
        """Soft delete location by setting is_active to False."""
        from sqlalchemy import select
        
        query = select(LocationModel).where(LocationModel.id == location_id)
        result = await self.db.execute(query)
        db_location = result.scalar_one_or_none()
        
        if not db_location:
            return False
        
        db_location.is_active = False
        await self.db.commit()
        return True
    
    async def count(
        self,
        location_type: Optional[LocationType] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> int:
        """Count locations matching filters."""
        from sqlalchemy import select, func
        
        query = select(func.count()).select_from(LocationModel)
        
        # Apply same filters as list method
        filters = []
        if is_active is not None:
            filters.append(LocationModel.is_active == is_active)
        if location_type:
            filters.append(LocationModel.location_type == location_type)
        if city:
            filters.append(LocationModel.city.ilike(f"%{city}%"))
        if state:
            filters.append(LocationModel.state.ilike(f"%{state}%"))
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def get_by_manager(self, manager_user_id: UUID) -> List[Location]:
        """Get all locations managed by a specific user."""
        from sqlalchemy import select
        
        query = select(LocationModel).where(
            and_(
                LocationModel.manager_user_id == manager_user_id,
                LocationModel.is_active == True
            )
        )
        result = await self.db.execute(query)
        db_locations = result.scalars().all()
        return [db_location.to_entity() for db_location in db_locations]
    
    async def exists_by_code(self, location_code: str) -> bool:
        """Check if a location with the given code exists."""
        from sqlalchemy import select, func
        
        query = select(func.count()).select_from(LocationModel).where(
            LocationModel.location_code == location_code
        )
        result = await self.db.execute(query)
        count = result.scalar_one()
        return count > 0