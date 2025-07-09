from typing import List, Optional
from uuid import UUID
from app.modules.units_of_measurement.repository import UnitOfMeasurementRepository
from app.modules.units_of_measurement.schemas import (
    UnitOfMeasurementCreate, UnitOfMeasurementUpdate, UnitOfMeasurementStatusUpdate,
    UnitOfMeasurementResponse, UnitOfMeasurementListResponse, UnitOfMeasurementSummary,
    UnitOfMeasurementValidationResponse
)
from app.core.domain.entities.unit_of_measurement import UnitOfMeasurement as UnitOfMeasurementEntity
from app.core.errors import NotFoundError, ValidationError
from app.modules.units_of_measurement.models import UnitOfMeasurement as UnitOfMeasurementModel


class UnitOfMeasurementService:
    """Service layer for unit of measurement business logic."""
    
    def __init__(self, repository: UnitOfMeasurementRepository):
        self.repository = repository
    
    def _model_to_entity(self, model: UnitOfMeasurementModel) -> UnitOfMeasurementEntity:
        """Convert SQLAlchemy model to domain entity."""
        return UnitOfMeasurementEntity(
            id=model.id,
            unit_id=model.unit_id,
            name=model.name,
            abbreviation=model.abbreviation,
            description=model.description,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
    
    def _entity_to_dict(self, entity: UnitOfMeasurementEntity) -> dict:
        """Convert domain entity to dictionary for database operations."""
        return {
            'id': entity.id,
            'unit_id': entity.unit_id,
            'name': entity.name,
            'abbreviation': entity.abbreviation,
            'description': entity.description,
            'is_active': entity.is_active,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'created_by': entity.created_by,
            'updated_by': entity.updated_by
        }
    
    async def create_unit(self, unit_data: UnitOfMeasurementCreate) -> UnitOfMeasurementResponse:
        """Create a new unit of measurement."""
        # Check if name already exists
        if await self.repository.name_exists(unit_data.name):
            raise ValidationError(f"Unit name '{unit_data.name}' already exists")
        
        # Check if abbreviation already exists (if provided)
        if unit_data.abbreviation and await self.repository.abbreviation_exists(unit_data.abbreviation):
            raise ValidationError(f"Unit abbreviation '{unit_data.abbreviation}' already exists")
        
        # Create domain entity to validate business rules
        try:
            entity = UnitOfMeasurementEntity(
                name=unit_data.name,
                abbreviation=unit_data.abbreviation,
                description=unit_data.description,
                created_by=unit_data.created_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Convert to dict for database creation
        create_data = self._entity_to_dict(entity)
        
        # Create in database
        unit_model = await self.repository.create_unit(create_data)
        
        return UnitOfMeasurementResponse.model_validate(unit_model)
    
    async def get_unit_by_id(self, unit_id: UUID) -> UnitOfMeasurementResponse:
        """Get unit of measurement by ID."""
        unit = await self.repository.get_unit_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit of measurement with ID {unit_id} not found")
        
        return UnitOfMeasurementResponse.model_validate(unit)
    
    async def get_unit_by_unit_id(self, unit_id: UUID) -> UnitOfMeasurementResponse:
        """Get unit of measurement by business unit_id."""
        unit = await self.repository.get_unit_by_unit_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit of measurement with unit_id {unit_id} not found")
        
        return UnitOfMeasurementResponse.model_validate(unit)
    
    async def get_unit_by_name(self, name: str) -> UnitOfMeasurementResponse:
        """Get unit of measurement by name."""
        unit = await self.repository.get_unit_by_name(name)
        if not unit:
            raise NotFoundError(f"Unit of measurement with name '{name}' not found")
        
        return UnitOfMeasurementResponse.model_validate(unit)
    
    async def get_units(
        self,
        page: int = 1,
        page_size: int = 50,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> UnitOfMeasurementListResponse:
        """Get units of measurement with filtering and pagination."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        if page_size > 100:
            page_size = 100
        
        skip = (page - 1) * page_size
        
        # Get units and total count
        units = await self.repository.get_units(
            skip=skip,
            limit=page_size,
            is_active=is_active,
            search=search
        )
        
        total = await self.repository.count_units(
            is_active=is_active,
            search=search
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return UnitOfMeasurementListResponse(
            units=[UnitOfMeasurementResponse.model_validate(unit) for unit in units],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_unit(self, unit_id: UUID, update_data: UnitOfMeasurementUpdate) -> UnitOfMeasurementResponse:
        """Update unit of measurement."""
        unit = await self.repository.get_unit_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit of measurement with ID {unit_id} not found")
        
        # Check for duplicate name (if being updated)
        if update_data.name and update_data.name != unit.name:
            if await self.repository.name_exists(update_data.name, exclude_id=unit_id):
                raise ValidationError(f"Unit name '{update_data.name}' already exists")
        
        # Check for duplicate abbreviation (if being updated)
        if (update_data.abbreviation is not None and 
            update_data.abbreviation != unit.abbreviation):
            if (update_data.abbreviation and 
                await self.repository.abbreviation_exists(update_data.abbreviation, exclude_id=unit_id)):
                raise ValidationError(f"Unit abbreviation '{update_data.abbreviation}' already exists")
        
        # Convert to domain entity for validation
        entity = self._model_to_entity(unit)
        
        # Update entity using domain method
        try:
            entity.update_details(
                name=update_data.name,
                abbreviation=update_data.abbreviation,
                description=update_data.description,
                updated_by=update_data.updated_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Prepare update data for database
        update_dict = {}
        if update_data.name is not None:
            update_dict['name'] = entity.name
        if update_data.abbreviation is not None:
            update_dict['abbreviation'] = entity.abbreviation
        if update_data.description is not None:
            update_dict['description'] = entity.description
        
        update_dict['updated_at'] = entity.updated_at
        if update_data.updated_by:
            update_dict['updated_by'] = update_data.updated_by
        
        # Update in database
        updated_unit = await self.repository.update_unit(unit_id, update_dict)
        
        return UnitOfMeasurementResponse.model_validate(updated_unit)
    
    async def update_status(self, unit_id: UUID, status_data: UnitOfMeasurementStatusUpdate) -> UnitOfMeasurementResponse:
        """Update unit of measurement status (activate/deactivate)."""
        unit = await self.repository.get_unit_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit of measurement with ID {unit_id} not found")
        
        # Convert to domain entity
        entity = self._model_to_entity(unit)
        
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
        
        updated_unit = await self.repository.update_unit(unit_id, update_dict)
        
        return UnitOfMeasurementResponse.model_validate(updated_unit)
    
    async def delete_unit(self, unit_id: UUID) -> bool:
        """Delete unit of measurement."""
        unit = await self.repository.get_unit_by_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit of measurement with ID {unit_id} not found")
        
        return await self.repository.delete_unit(unit_id)
    
    async def get_active_units(self) -> List[UnitOfMeasurementSummary]:
        """Get all active units of measurement (summary format)."""
        units = await self.repository.get_active_units()
        return [UnitOfMeasurementSummary.model_validate(unit) for unit in units]
    
    async def search_units(self, partial_name: str, limit: int = 10) -> List[UnitOfMeasurementSummary]:
        """Search units by partial name or abbreviation match."""
        if not partial_name or not partial_name.strip():
            return []
        
        units = await self.repository.search_units_by_partial_match(partial_name.strip(), limit)
        return [UnitOfMeasurementSummary.model_validate(unit) for unit in units]
    
    async def validate_units_for_use(self, unit_ids: List[UUID]) -> List[UnitOfMeasurementValidationResponse]:
        """Validate multiple units for use in inventory items."""
        if not unit_ids:
            return []
        
        units = await self.repository.get_units_for_validation(unit_ids)
        unit_dict = {unit.unit_id: unit for unit in units}
        
        validation_results = []
        for unit_id in unit_ids:
            if unit_id in unit_dict:
                unit = unit_dict[unit_id]
                entity = self._model_to_entity(unit)
                validation_errors = entity.validate_for_item_usage()
                
                validation_results.append(UnitOfMeasurementValidationResponse(
                    unit_id=unit.unit_id,
                    name=unit.name,
                    abbreviation=unit.abbreviation,
                    is_valid_for_use=len(validation_errors) == 0,
                    validation_errors=validation_errors,
                    display_name=entity.get_display_name()
                ))
            else:
                validation_results.append(UnitOfMeasurementValidationResponse(
                    unit_id=unit_id,
                    name="Unknown",
                    abbreviation=None,
                    is_valid_for_use=False,
                    validation_errors=[f"Unit with ID {unit_id} not found"],
                    display_name="Unknown Unit"
                ))
        
        return validation_results
    
    async def get_unit_conversion_info(self, unit_id: UUID) -> dict:
        """Get conversion information for a unit (future enhancement)."""
        unit = await self.repository.get_unit_by_unit_id(unit_id)
        if not unit:
            raise NotFoundError(f"Unit of measurement with unit_id {unit_id} not found")
        
        entity = self._model_to_entity(unit)
        return entity.get_conversion_info()