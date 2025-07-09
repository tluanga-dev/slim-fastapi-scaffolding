from typing import List

from ....domain.entities.unit_of_measurement import UnitOfMeasurement
from ....domain.repositories.unit_of_measurement_repository import UnitOfMeasurementRepository


class ListUnitsOfMeasurementUseCase:
    """Use case for listing units of measurement."""
    
    def __init__(self, unit_repository: UnitOfMeasurementRepository):
        """Initialize use case with repository."""
        self.unit_repository = unit_repository
    
    async def execute(self, skip: int = 0, limit: int = 100) -> List[UnitOfMeasurement]:
        """Execute units of measurement listing.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active unit of measurement entities
        """
        return await self.unit_repository.get_active(skip=skip, limit=limit)