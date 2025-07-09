from typing import Optional
from uuid import UUID

from ....domain.entities.unit_of_measurement import UnitOfMeasurement
from ....domain.repositories.unit_of_measurement_repository import UnitOfMeasurementRepository


class UpdateUnitOfMeasurementUseCase:
    """Use case for updating a unit of measurement."""
    
    def __init__(self, unit_repository: UnitOfMeasurementRepository):
        """Initialize use case with repository."""
        self.unit_repository = unit_repository
    
    async def execute(
        self,
        unit_id: UUID,
        name: Optional[str] = None,
        abbreviation: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> UnitOfMeasurement:
        """Execute unit of measurement update.
        
        Args:
            unit_id: ID of the unit to update
            name: Optional new name
            abbreviation: Optional new abbreviation
            description: Optional new description
            updated_by: ID of user updating the unit
            
        Returns:
            Updated unit of measurement entity
            
        Raises:
            ValueError: If unit not found or name/abbreviation conflicts
        """
        # Get existing unit
        unit = await self.unit_repository.get_by_unit_id(unit_id)
        if not unit:
            raise ValueError(f"Unit of measurement with ID '{unit_id}' not found")
        
        # Check if new name already exists (exclude current unit)
        if name and name != unit.name:
            existing_unit = await self.unit_repository.get_by_name(name)
            if existing_unit and existing_unit.unit_id != unit_id:
                raise ValueError(f"Unit of measurement with name '{name}' already exists")
        
        # Check if new abbreviation already exists (exclude current unit)
        if abbreviation and abbreviation != unit.abbreviation:
            existing_unit = await self.unit_repository.get_by_abbreviation(abbreviation)
            if existing_unit and existing_unit.unit_id != unit_id:
                raise ValueError(f"Unit of measurement with abbreviation '{abbreviation}' already exists")
        
        # Update unit details
        unit.update_details(
            name=name,
            abbreviation=abbreviation,
            description=description,
            updated_by=updated_by
        )
        
        # Save to repository
        return await self.unit_repository.update(unit)