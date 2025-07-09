from typing import Optional
from uuid import UUID, uuid4

from ....domain.entities.unit_of_measurement import UnitOfMeasurement
from ....domain.repositories.unit_of_measurement_repository import UnitOfMeasurementRepository


class CreateUnitOfMeasurementUseCase:
    """Use case for creating a new unit of measurement."""
    
    def __init__(self, unit_repository: UnitOfMeasurementRepository):
        """Initialize use case with repository."""
        self.unit_repository = unit_repository
    
    async def execute(
        self,
        name: str,
        abbreviation: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> UnitOfMeasurement:
        """Execute unit of measurement creation.
        
        Args:
            name: Name of the unit of measurement
            abbreviation: Optional abbreviation
            description: Optional description
            created_by: ID of user creating the unit
            
        Returns:
            Created unit of measurement entity
            
        Raises:
            ValueError: If unit name already exists or abbreviation is not unique
        """
        # Check if unit name already exists
        if await self.unit_repository.get_by_name(name):
            raise ValueError(f"Unit of measurement with name '{name}' already exists")
        
        # Check if abbreviation already exists
        if abbreviation and await self.unit_repository.get_by_abbreviation(abbreviation):
            raise ValueError(f"Unit of measurement with abbreviation '{abbreviation}' already exists")
        
        # Create unit entity
        unit = UnitOfMeasurement(
            unit_id=uuid4(),
            name=name,
            abbreviation=abbreviation,
            description=description,
            created_by=created_by,
            updated_by=created_by
        )
        
        # Save to repository
        return await self.unit_repository.create(unit)