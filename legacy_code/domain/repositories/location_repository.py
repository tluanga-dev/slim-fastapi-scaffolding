from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.location import Location, LocationType


class LocationRepository(ABC):
    """Abstract repository interface for Location entity."""
    
    @abstractmethod
    async def create(self, location: Location) -> Location:
        """Create a new location."""
        pass
    
    @abstractmethod
    async def get_by_id(self, location_id: UUID) -> Optional[Location]:
        """Get location by ID."""
        pass
    
    @abstractmethod
    async def get_by_code(self, location_code: str) -> Optional[Location]:
        """Get location by location code."""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def update(self, location: Location) -> Location:
        """Update existing location."""
        pass
    
    @abstractmethod
    async def delete(self, location_id: UUID) -> bool:
        """Soft delete location by setting is_active to False."""
        pass
    
    @abstractmethod
    async def count(
        self,
        location_type: Optional[LocationType] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> int:
        """Count locations matching filters."""
        pass
    
    @abstractmethod
    async def get_by_manager(self, manager_user_id: UUID) -> List[Location]:
        """Get all locations managed by a specific user."""
        pass
    
    @abstractmethod
    async def exists_by_code(self, location_code: str) -> bool:
        """Check if a location with the given code exists."""
        pass