from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.modules.locations.repository import LocationRepository
from app.modules.locations.schemas import (
    LocationCreate, LocationUpdate, LocationContactUpdate,
    LocationManagerUpdate, LocationStatusUpdate, LocationResponse,
    LocationListResponse
)
from app.core.domain.entities.location import Location as LocationEntity, LocationType
from app.core.errors import NotFoundError, ValidationError
from app.modules.locations.models import Location as LocationModel


class LocationService:
    """Service layer for location business logic."""
    
    def __init__(self, repository: LocationRepository):
        self.repository = repository
    
    def _model_to_entity(self, model: LocationModel) -> LocationEntity:
        """Convert SQLAlchemy model to domain entity."""
        return LocationEntity(
            id=model.id,
            location_code=model.location_code,
            location_name=model.location_name,
            location_type=model.location_type,
            address=model.address,
            city=model.city,
            state=model.state,
            country=model.country,
            postal_code=model.postal_code,
            contact_number=model.contact_number,
            email=model.email,
            manager_user_id=model.manager_user_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
    
    def _entity_to_dict(self, entity: LocationEntity) -> dict:
        """Convert domain entity to dictionary for database operations."""
        return {
            'id': entity.id,
            'location_code': entity.location_code,
            'location_name': entity.location_name,
            'location_type': entity.location_type,
            'address': entity.address,
            'city': entity.city,
            'state': entity.state,
            'country': entity.country,
            'postal_code': entity.postal_code,
            'contact_number': entity.contact_number,
            'email': entity.email,
            'manager_user_id': entity.manager_user_id,
            'is_active': entity.is_active,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'created_by': entity.created_by,
            'updated_by': entity.updated_by
        }
    
    async def create_location(self, location_data: LocationCreate) -> LocationResponse:
        """Create a new location."""
        # Check if location code already exists
        existing = await self.repository.get_location_by_code(location_data.location_code)
        if existing:
            raise ValidationError(f"Location code '{location_data.location_code}' already exists")
        
        # Create domain entity to validate business rules
        entity = LocationEntity(
            location_code=location_data.location_code,
            location_name=location_data.location_name,
            location_type=location_data.location_type,
            address=location_data.address,
            city=location_data.city,
            state=location_data.state,
            country=location_data.country,
            postal_code=location_data.postal_code,
            contact_number=location_data.contact_number,
            email=location_data.email,
            manager_user_id=location_data.manager_user_id,
            created_by=location_data.created_by
        )
        
        # Convert to dict for database creation
        create_data = self._entity_to_dict(entity)
        
        # Create in database
        location_model = await self.repository.create_location(create_data)
        
        return LocationResponse.model_validate(location_model)
    
    async def get_location_by_id(self, location_id: UUID) -> LocationResponse:
        """Get location by ID."""
        location = await self.repository.get_location_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location with ID {location_id} not found")
        
        return LocationResponse.model_validate(location)
    
    async def get_location_by_code(self, location_code: str) -> LocationResponse:
        """Get location by location code."""
        location = await self.repository.get_location_by_code(location_code)
        if not location:
            raise NotFoundError(f"Location with code '{location_code}' not found")
        
        return LocationResponse.model_validate(location)
    
    async def get_locations(
        self,
        page: int = 1,
        page_size: int = 50,
        location_type: Optional[LocationType] = None,
        is_active: Optional[bool] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None
    ) -> LocationListResponse:
        """Get locations with filtering and pagination."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        if page_size > 100:
            page_size = 100
        
        skip = (page - 1) * page_size
        
        # Get locations and total count
        locations = await self.repository.get_locations(
            skip=skip,
            limit=page_size,
            location_type=location_type,
            is_active=is_active,
            city=city,
            state=state,
            country=country,
            search=search
        )
        
        total = await self.repository.count_locations(
            location_type=location_type,
            is_active=is_active,
            city=city,
            state=state,
            country=country,
            search=search
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return LocationListResponse(
            locations=[LocationResponse.model_validate(loc) for loc in locations],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_location(self, location_id: UUID, update_data: LocationUpdate) -> LocationResponse:
        """Update location details."""
        location = await self.repository.get_location_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location with ID {location_id} not found")
        
        # Convert to domain entity for validation
        entity = self._model_to_entity(location)
        
        # Update entity using domain method
        entity.update_details(
            location_name=update_data.location_name,
            address=update_data.address,
            city=update_data.city,
            state=update_data.state,
            country=update_data.country,
            postal_code=update_data.postal_code,
            updated_by=update_data.updated_by
        )
        
        # Prepare update data for database
        update_dict = {}
        if update_data.location_name is not None:
            update_dict['location_name'] = entity.location_name
        if update_data.address is not None:
            update_dict['address'] = entity.address
        if update_data.city is not None:
            update_dict['city'] = entity.city
        if update_data.state is not None:
            update_dict['state'] = entity.state
        if update_data.country is not None:
            update_dict['country'] = entity.country
        if update_data.postal_code is not None:
            update_dict['postal_code'] = entity.postal_code
        
        update_dict['updated_at'] = entity.updated_at
        if update_data.updated_by:
            update_dict['updated_by'] = update_data.updated_by
        
        # Update in database
        updated_location = await self.repository.update_location(location_id, update_dict)
        
        return LocationResponse.model_validate(updated_location)
    
    async def update_contact_info(self, location_id: UUID, contact_data: LocationContactUpdate) -> LocationResponse:
        """Update location contact information."""
        location = await self.repository.get_location_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location with ID {location_id} not found")
        
        # Convert to domain entity for validation
        entity = self._model_to_entity(location)
        
        # Update entity using domain method
        entity.update_contact_info(
            contact_number=contact_data.contact_number,
            email=contact_data.email,
            updated_by=contact_data.updated_by
        )
        
        # Update in database
        update_dict = {
            'contact_number': entity.contact_number,
            'email': entity.email,
            'updated_at': entity.updated_at
        }
        if contact_data.updated_by:
            update_dict['updated_by'] = contact_data.updated_by
        
        updated_location = await self.repository.update_location(location_id, update_dict)
        
        return LocationResponse.model_validate(updated_location)
    
    async def update_manager(self, location_id: UUID, manager_data: LocationManagerUpdate) -> LocationResponse:
        """Update location manager."""
        location = await self.repository.get_location_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location with ID {location_id} not found")
        
        # Convert to domain entity
        entity = self._model_to_entity(location)
        
        # Update entity using domain method
        if manager_data.manager_user_id:
            entity.assign_manager(manager_data.manager_user_id, manager_data.updated_by)
        else:
            entity.remove_manager(manager_data.updated_by)
        
        # Update in database
        update_dict = {
            'manager_user_id': entity.manager_user_id,
            'updated_at': entity.updated_at
        }
        if manager_data.updated_by:
            update_dict['updated_by'] = manager_data.updated_by
        
        updated_location = await self.repository.update_location(location_id, update_dict)
        
        return LocationResponse.model_validate(updated_location)
    
    async def update_status(self, location_id: UUID, status_data: LocationStatusUpdate) -> LocationResponse:
        """Update location status (activate/deactivate)."""
        location = await self.repository.get_location_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location with ID {location_id} not found")
        
        # Convert to domain entity
        entity = self._model_to_entity(location)
        
        # Update entity using domain method
        if status_data.is_active:
            entity.activate(status_data.updated_by)
        else:
            entity.deactivate(status_data.updated_by)
        
        # Update in database
        update_dict = {
            'is_active': entity.is_active,
            'updated_at': entity.updated_at
        }
        if status_data.updated_by:
            update_dict['updated_by'] = status_data.updated_by
        
        updated_location = await self.repository.update_location(location_id, update_dict)
        
        return LocationResponse.model_validate(updated_location)
    
    async def delete_location(self, location_id: UUID) -> bool:
        """Delete location."""
        location = await self.repository.get_location_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location with ID {location_id} not found")
        
        return await self.repository.delete_location(location_id)
    
    async def get_locations_by_manager(self, manager_user_id: UUID) -> List[LocationResponse]:
        """Get all locations managed by a specific user."""
        locations = await self.repository.get_locations_by_manager(manager_user_id)
        return [LocationResponse.model_validate(loc) for loc in locations]
    
    async def get_locations_by_type(self, location_type: LocationType) -> List[LocationResponse]:
        """Get all locations of a specific type."""
        locations = await self.repository.get_locations_by_type(location_type)
        return [LocationResponse.model_validate(loc) for loc in locations]