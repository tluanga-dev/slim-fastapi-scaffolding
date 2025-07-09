from typing import Optional
from uuid import UUID

from ....domain.entities.unit_of_measurement import UnitOfMeasurement
from ....domain.repositories.unit_of_measurement_repository import UnitOfMeasurementRepository


class GetUnitOfMeasurementUseCase:
    """Use case for getting a unit of measurement."""
    
    def __init__(self, unit_repository: UnitOfMeasurementRepository):
        """Initialize use case with repository."""
        self.unit_repository = unit_repository
    
    async def execute(self, unit_id: UUID) -> Optional[UnitOfMeasurement]:
        """Execute unit of measurement retrieval.
        
        Args:
            unit_id: ID of the unit to retrieve
            
        Returns:
            Unit of measurement entity or None if not found
        """
        return await self.unit_repository.get_by_unit_id(unit_id)