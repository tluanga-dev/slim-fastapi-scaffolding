from uuid import UUID

from ....domain.repositories.unit_of_measurement_repository import UnitOfMeasurementRepository


class DeleteUnitOfMeasurementUseCase:
    """Use case for deleting a unit of measurement."""
    
    def __init__(self, unit_repository: UnitOfMeasurementRepository):
        """Initialize use case with repository."""
        self.unit_repository = unit_repository
    
    async def execute(self, unit_id: UUID) -> bool:
        """Execute unit of measurement deletion (soft delete).
        
        Args:
            unit_id: ID of the unit to delete
            
        Returns:
            True if unit was deleted, False if not found
        """
        # Get existing unit
        unit = await self.unit_repository.get_by_unit_id(unit_id)
        if not unit:
            return False
        
        # Soft delete
        return await self.unit_repository.delete(unit.id)