from typing import List, Optional, Tuple
from uuid import UUID

from ...domain.entities.location import Location, LocationType
from ...domain.repositories.location_repository import LocationRepository


class LocationUseCases:
    """Location use cases for CRUD operations."""
    
    def __init__(self, location_repository: LocationRepository):
        """Initialize with location repository."""
        self.location_repository = location_repository
    
    async def create_location(
        self,
        location_code: str,
        location_name: str,
        location_type: LocationType,
        address: str,
        city: str,
        state: str,
        country: str,
        postal_code: Optional[str] = None,
        contact_number: Optional[str] = None,
        email: Optional[str] = None,
        manager_user_id: Optional[UUID] = None,
        created_by: Optional[str] = None
    ) -> Location:
        """Create a new location."""
        # Check if location code already exists
        if await self.location_repository.exists_by_code(location_code):
            raise ValueError(f"Location with code {location_code} already exists")
        
        # Create domain entity
        location = Location(
            location_code=location_code,
            location_name=location_name,
            location_type=location_type,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            contact_number=contact_number,
            email=email,
            manager_user_id=manager_user_id,
            created_by=created_by
        )
        
        # Persist
        return await self.location_repository.create(location)
    
    async def get_location(self, location_id: UUID) -> Location:
        """Get location by ID."""
        location = await self.location_repository.get_by_id(location_id)
        if not location:
            raise ValueError(f"Location with ID {location_id} not found")
        return location
    
    async def get_location_by_code(self, location_code: str) -> Location:
        """Get location by code."""
        location = await self.location_repository.get_by_code(location_code)
        if not location:
            raise ValueError(f"Location with code {location_code} not found")
        return location
    
    async def list_locations(
        self,
        skip: int = 0,
        limit: int = 100,
        location_type: Optional[LocationType] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[Location], int]:
        """List locations with pagination and filters."""
        locations = await self.location_repository.list(
            skip=skip,
            limit=limit,
            location_type=location_type,
            city=city,
            state=state,
            is_active=is_active
        )
        total = await self.location_repository.count(
            location_type=location_type,
            city=city,
            state=state,
            is_active=is_active
        )
        return locations, total
    
    async def update_location(
        self,
        location_id: UUID,
        location_name: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        contact_number: Optional[str] = None,
        email: Optional[str] = None,
        manager_user_id: Optional[UUID] = None,
        updated_by: Optional[str] = None
    ) -> Location:
        """Update existing location."""
        # Get existing location
        location = await self.get_location(location_id)
        
        # Update details if provided
        if any([location_name, address, city, state, country, postal_code is not None]):
            location.update_details(
                location_name=location_name,
                address=address,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
                updated_by=updated_by
            )
        
        # Update contact info if provided
        if contact_number is not None or email is not None:
            location.update_contact_info(
                contact_number=contact_number,
                email=email,
                updated_by=updated_by
            )
        
        # Update manager if provided
        if manager_user_id is not None:
            if manager_user_id:
                location.assign_manager(manager_user_id, updated_by)
            else:
                location.remove_manager(updated_by)
        
        # Persist changes
        return await self.location_repository.update(location)
    
    async def deactivate_location(self, location_id: UUID, updated_by: Optional[str] = None) -> Location:
        """Deactivate a location."""
        location = await self.get_location(location_id)
        location.deactivate(updated_by)
        return await self.location_repository.update(location)
    
    async def activate_location(self, location_id: UUID, updated_by: Optional[str] = None) -> Location:
        """Activate a location."""
        location = await self.get_location(location_id)
        location.activate(updated_by)
        return await self.location_repository.update(location)
    
    async def delete_location(self, location_id: UUID) -> bool:
        """Soft delete a location."""
        return await self.location_repository.delete(location_id)
    
    async def get_locations_by_manager(self, manager_user_id: UUID) -> List[Location]:
        """Get all locations managed by a specific user."""
        return await self.location_repository.get_by_manager(manager_user_id)
    
    async def assign_manager_to_location(
        self,
        location_id: UUID,
        manager_user_id: UUID,
        updated_by: Optional[str] = None
    ) -> Location:
        """Assign a manager to a location."""
        location = await self.get_location(location_id)
        location.assign_manager(manager_user_id, updated_by)
        return await self.location_repository.update(location)
    
    async def remove_manager_from_location(
        self,
        location_id: UUID,
        updated_by: Optional[str] = None
    ) -> Location:
        """Remove manager from a location."""
        location = await self.get_location(location_id)
        location.remove_manager(updated_by)
        return await self.location_repository.update(location)