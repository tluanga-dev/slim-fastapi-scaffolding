from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.modules.inventory_units.repository import InventoryUnitRepository
from app.modules.inventory_units.schemas import (
    InventoryUnitCreate, InventoryUnitUpdate, InventoryUnitLocationUpdate,
    InventoryUnitStatusUpdate, InventoryUnitConditionUpdate, InventoryUnitRentalUpdate,
    InventoryUnitResponse, InventoryUnitListResponse, InventoryUnitSummary,
    InventoryUnitMetrics, InventoryUnitSearchRequest,
    InventoryUnitBulkStatusUpdate, InventoryUnitBulkLocationUpdate
)
from app.core.domain.entities.inventory_unit import InventoryUnit as InventoryUnitEntity
from app.core.domain.value_objects.item_type import InventoryStatus, ConditionGrade
from app.core.errors import NotFoundError, ValidationError
from app.modules.inventory_units.models import InventoryUnitModel


class InventoryUnitService:
    """Service layer for inventory unit business logic."""
    
    def __init__(self, repository: InventoryUnitRepository):
        self.repository = repository
    
    def _model_to_entity(self, model: InventoryUnitModel) -> InventoryUnitEntity:
        """Convert SQLAlchemy model to domain entity."""
        return InventoryUnitEntity(
            id=model.id,
            inventory_code=model.inventory_code,
            item_id=model.item_id,
            location_id=model.location_id,
            serial_number=model.serial_number,
            current_status=model.current_status,
            condition_grade=model.condition_grade,
            purchase_date=model.purchase_date,
            purchase_cost=Decimal(str(model.purchase_cost)) if model.purchase_cost else None,
            current_value=Decimal(str(model.current_value)) if model.current_value else None,
            last_inspection_date=model.last_inspection_date,
            total_rental_days=model.total_rental_days,
            rental_count=model.rental_count,
            notes=model.notes,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
    
    def _entity_to_dict(self, entity: InventoryUnitEntity) -> dict:
        """Convert domain entity to dictionary for database operations."""
        return {
            'id': entity.id,
            'inventory_code': entity.inventory_code,
            'item_id': entity.item_id,
            'location_id': entity.location_id,
            'serial_number': entity.serial_number,
            'current_status': entity.current_status,
            'condition_grade': entity.condition_grade,
            'purchase_date': entity.purchase_date,
            'purchase_cost': float(entity.purchase_cost) if entity.purchase_cost else None,
            'current_value': float(entity.current_value) if entity.current_value else None,
            'last_inspection_date': entity.last_inspection_date,
            'total_rental_days': entity.total_rental_days,
            'rental_count': entity.rental_count,
            'notes': entity.notes,
            'is_active': entity.is_active,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'created_by': entity.created_by,
            'updated_by': entity.updated_by
        }
    
    async def create_inventory_unit(self, inventory_unit_data: InventoryUnitCreate, created_by: Optional[str] = None) -> InventoryUnitResponse:
        """Create a new inventory unit."""
        # Check if inventory code already exists
        existing_code = await self.repository.inventory_code_exists(inventory_unit_data.inventory_code)
        if existing_code:
            raise ValidationError(f"Inventory code '{inventory_unit_data.inventory_code}' already exists")
        
        # Check if serial number already exists (if provided)
        if inventory_unit_data.serial_number:
            existing_serial = await self.repository.serial_number_exists(inventory_unit_data.serial_number)
            if existing_serial:
                raise ValidationError(f"Serial number '{inventory_unit_data.serial_number}' already exists")
        
        # Create domain entity to validate business rules
        try:
            entity = InventoryUnitEntity(
                inventory_code=inventory_unit_data.inventory_code,
                item_id=inventory_unit_data.item_id,
                location_id=inventory_unit_data.location_id,
                serial_number=inventory_unit_data.serial_number,
                current_status=inventory_unit_data.current_status,
                condition_grade=inventory_unit_data.condition_grade,
                purchase_date=inventory_unit_data.purchase_date,
                purchase_cost=inventory_unit_data.purchase_cost,
                current_value=inventory_unit_data.current_value,
                last_inspection_date=inventory_unit_data.last_inspection_date,
                notes=inventory_unit_data.notes,
                created_by=created_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Convert to dict for database creation
        create_data = self._entity_to_dict(entity)
        
        # Create in database
        inventory_unit_model = await self.repository.create_inventory_unit(create_data)
        
        return InventoryUnitResponse.model_validate(inventory_unit_model)
    
    async def get_inventory_unit_by_id(self, inventory_unit_id: UUID) -> InventoryUnitResponse:
        """Get inventory unit by ID."""
        inventory_unit = await self.repository.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
        
        return InventoryUnitResponse.model_validate(inventory_unit)
    
    async def get_inventory_unit_by_code(self, inventory_code: str) -> InventoryUnitResponse:
        """Get inventory unit by inventory code."""
        inventory_unit = await self.repository.get_inventory_unit_by_code(inventory_code)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with code '{inventory_code}' not found")
        
        return InventoryUnitResponse.model_validate(inventory_unit)
    
    async def get_inventory_unit_by_serial(self, serial_number: str) -> InventoryUnitResponse:
        """Get inventory unit by serial number."""
        inventory_unit = await self.repository.get_inventory_unit_by_serial(serial_number)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with serial number '{serial_number}' not found")
        
        return InventoryUnitResponse.model_validate(inventory_unit)
    
    async def search_inventory_units(self, search_request: InventoryUnitSearchRequest) -> List[InventoryUnitListResponse]:
        """Search inventory units with filtering."""
        inventory_units = await self.repository.get_inventory_units(
            skip=search_request.offset,
            limit=search_request.limit,
            item_id=search_request.item_id,
            location_id=search_request.location_id,
            status=search_request.status,
            condition_grade=search_request.condition_grade,
            is_active=search_request.is_active,
            search=search_request.inventory_code or search_request.serial_number
        )
        
        return [InventoryUnitListResponse.model_validate(unit) for unit in inventory_units]
    
    async def update_inventory_unit(self, inventory_unit_id: UUID, update_data: InventoryUnitUpdate, updated_by: Optional[str] = None) -> InventoryUnitResponse:
        """Update inventory unit information."""
        inventory_unit = await self.repository.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
        
        # Convert to domain entity for validation
        entity = self._model_to_entity(inventory_unit)
        
        # Check for duplicate serial number (if being updated)
        if update_data.serial_number is not None and update_data.serial_number != inventory_unit.serial_number:
            if update_data.serial_number:  # Only check if new serial number is not empty
                existing_serial = await self.repository.serial_number_exists(update_data.serial_number, exclude_id=inventory_unit_id)
                if existing_serial:
                    raise ValidationError(f"Serial number '{update_data.serial_number}' already exists")
        
        # Update entity using domain methods
        try:
            if update_data.current_status is not None:
                entity.update_status(update_data.current_status, updated_by)
            
            if update_data.condition_grade is not None:
                entity.update_condition(update_data.condition_grade, updated_by)
            
            if update_data.current_value is not None:
                entity.update_value(update_data.current_value, updated_by)
            
            if update_data.last_inspection_date is not None:
                entity.update_inspection_date(update_data.last_inspection_date, updated_by)
            
            if update_data.notes is not None:
                entity.update_notes(update_data.notes, updated_by)
            
            # Update serial number directly if provided
            if update_data.serial_number is not None:
                entity.serial_number = update_data.serial_number
                entity.update_timestamp(updated_by)
                
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Prepare update data for database
        update_dict = {}
        if update_data.serial_number is not None:
            update_dict['serial_number'] = entity.serial_number
        if update_data.current_status is not None:
            update_dict['current_status'] = entity.current_status
        if update_data.condition_grade is not None:
            update_dict['condition_grade'] = entity.condition_grade
        if update_data.current_value is not None:
            update_dict['current_value'] = float(entity.current_value) if entity.current_value else None
        if update_data.last_inspection_date is not None:
            update_dict['last_inspection_date'] = entity.last_inspection_date
        if update_data.notes is not None:
            update_dict['notes'] = entity.notes
        
        update_dict['updated_at'] = entity.updated_at
        update_dict['rental_count'] = entity.rental_count  # In case status update incremented this
        if updated_by:
            update_dict['updated_by'] = entity.updated_by
        
        # Update in database
        updated_inventory_unit = await self.repository.update_inventory_unit(inventory_unit_id, update_dict)
        
        return InventoryUnitResponse.model_validate(updated_inventory_unit)
    
    async def update_inventory_unit_location(self, inventory_unit_id: UUID, location_data: InventoryUnitLocationUpdate, updated_by: Optional[str] = None) -> InventoryUnitResponse:
        """Update inventory unit location."""
        inventory_unit = await self.repository.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
        
        # Convert to domain entity and update location
        entity = self._model_to_entity(inventory_unit)
        
        try:
            entity.update_location(location_data.location_id, updated_by)
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Update in database
        update_dict = {
            'location_id': entity.location_id,
            'updated_at': entity.updated_at,
            'updated_by': entity.updated_by
        }
        
        updated_inventory_unit = await self.repository.update_inventory_unit(inventory_unit_id, update_dict)
        return InventoryUnitResponse.model_validate(updated_inventory_unit)
    
    async def update_inventory_unit_status(self, inventory_unit_id: UUID, status_data: InventoryUnitStatusUpdate, updated_by: Optional[str] = None) -> InventoryUnitResponse:
        """Update inventory unit status."""
        inventory_unit = await self.repository.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
        
        entity = self._model_to_entity(inventory_unit)
        
        try:
            entity.update_status(status_data.current_status, updated_by)
        except ValueError as e:
            raise ValidationError(str(e))
        
        update_dict = {
            'current_status': entity.current_status,
            'rental_count': entity.rental_count,  # May have been incremented
            'updated_at': entity.updated_at,
            'updated_by': entity.updated_by
        }
        
        updated_inventory_unit = await self.repository.update_inventory_unit(inventory_unit_id, update_dict)
        return InventoryUnitResponse.model_validate(updated_inventory_unit)
    
    async def update_inventory_unit_condition(self, inventory_unit_id: UUID, condition_data: InventoryUnitConditionUpdate, updated_by: Optional[str] = None) -> InventoryUnitResponse:
        """Update inventory unit condition."""
        inventory_unit = await self.repository.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
        
        entity = self._model_to_entity(inventory_unit)
        
        try:
            entity.update_condition(condition_data.condition_grade, updated_by)
        except ValueError as e:
            raise ValidationError(str(e))
        
        update_dict = {
            'condition_grade': entity.condition_grade,
            'updated_at': entity.updated_at,
            'updated_by': entity.updated_by
        }
        
        updated_inventory_unit = await self.repository.update_inventory_unit(inventory_unit_id, update_dict)
        return InventoryUnitResponse.model_validate(updated_inventory_unit)
    
    async def add_rental_days(self, inventory_unit_id: UUID, rental_data: InventoryUnitRentalUpdate, updated_by: Optional[str] = None) -> InventoryUnitResponse:
        """Add rental days to inventory unit."""
        inventory_unit = await self.repository.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
        
        entity = self._model_to_entity(inventory_unit)
        
        try:
            entity.add_rental_days(rental_data.rental_days, updated_by)
        except ValueError as e:
            raise ValidationError(str(e))
        
        update_dict = {
            'total_rental_days': entity.total_rental_days,
            'updated_at': entity.updated_at,
            'updated_by': entity.updated_by
        }
        
        updated_inventory_unit = await self.repository.update_inventory_unit(inventory_unit_id, update_dict)
        return InventoryUnitResponse.model_validate(updated_inventory_unit)
    
    async def get_available_units_by_item(self, item_id: UUID) -> List[InventoryUnitListResponse]:
        """Get available inventory units for a specific item."""
        inventory_units = await self.repository.get_available_units_by_item(item_id)
        return [InventoryUnitListResponse.model_validate(unit) for unit in inventory_units]
    
    async def get_units_by_location(self, location_id: UUID, is_active: bool = True) -> List[InventoryUnitListResponse]:
        """Get inventory units at a specific location."""
        inventory_units = await self.repository.get_units_by_location(location_id, is_active)
        return [InventoryUnitListResponse.model_validate(unit) for unit in inventory_units]
    
    async def get_units_needing_inspection(self, days_threshold: int = 90) -> List[InventoryUnitResponse]:
        """Get units that need inspection."""
        inventory_units = await self.repository.get_units_needing_inspection(days_threshold)
        return [InventoryUnitResponse.model_validate(unit) for unit in inventory_units]
    
    async def get_units_by_status(self, status: InventoryStatus) -> List[InventoryUnitListResponse]:
        """Get inventory units by status."""
        inventory_units = await self.repository.get_units_by_status(status)
        return [InventoryUnitListResponse.model_validate(unit) for unit in inventory_units]
    
    async def get_inventory_unit_metrics(self, inventory_unit_id: UUID) -> InventoryUnitMetrics:
        """Get inventory unit metrics."""
        inventory_unit = await self.repository.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
        
        entity = self._model_to_entity(inventory_unit)
        
        return InventoryUnitMetrics(
            inventory_unit_id=inventory_unit_id,
            depreciation_rate=entity.get_depreciation_rate(),
            utilization_rate=entity.get_utilization_rate(),
            rental_frequency=entity.get_rental_frequency()
        )
    
    async def bulk_update_status(self, bulk_update: InventoryUnitBulkStatusUpdate, updated_by: Optional[str] = None) -> int:
        """Bulk update status for multiple inventory units."""
        # Validate that all inventory units exist
        for unit_id in bulk_update.inventory_unit_ids:
            unit = await self.repository.get_inventory_unit_by_id(unit_id)
            if not unit:
                raise NotFoundError(f"Inventory unit with ID {unit_id} not found")
        
        # Perform bulk update
        updated_count = await self.repository.bulk_update_status(
            bulk_update.inventory_unit_ids,
            bulk_update.new_status,
            updated_by
        )
        
        return updated_count
    
    async def bulk_update_location(self, bulk_update: InventoryUnitBulkLocationUpdate, updated_by: Optional[str] = None) -> int:
        """Bulk update location for multiple inventory units."""
        # Validate that all inventory units exist
        for unit_id in bulk_update.inventory_unit_ids:
            unit = await self.repository.get_inventory_unit_by_id(unit_id)
            if not unit:
                raise NotFoundError(f"Inventory unit with ID {unit_id} not found")
        
        # Perform bulk update
        updated_count = await self.repository.bulk_update_location(
            bulk_update.inventory_unit_ids,
            bulk_update.new_location_id,
            updated_by
        )
        
        return updated_count
    
    async def delete_inventory_unit(self, inventory_unit_id: UUID, deleted_by: Optional[str] = None) -> bool:
        """Soft delete inventory unit."""
        inventory_unit = await self.repository.get_inventory_unit_by_id(inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
        
        # Perform soft delete
        deleted_unit = await self.repository.soft_delete_inventory_unit(inventory_unit_id, deleted_by)
        return deleted_unit is not None
    
    async def get_inventory_summary(self) -> dict:
        """Get comprehensive inventory summary."""
        status_summary = await self.repository.get_inventory_summary_by_status()
        condition_summary = await self.repository.get_inventory_summary_by_condition()
        location_summary = await self.repository.get_inventory_summary_by_location()
        
        return {
            "by_status": status_summary,
            "by_condition": condition_summary,
            "by_location": location_summary
        }
    
    async def check_inventory_code_availability(self, inventory_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if inventory code is available."""
        if not inventory_code or not inventory_code.strip():
            return False
        
        exists = await self.repository.inventory_code_exists(inventory_code.strip(), exclude_id)
        return not exists
    
    async def check_serial_number_availability(self, serial_number: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if serial number is available."""
        if not serial_number or not serial_number.strip():
            return True  # Empty serial numbers are allowed
        
        exists = await self.repository.serial_number_exists(serial_number.strip(), exclude_id)
        return not exists