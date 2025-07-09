from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.unit_of_measurement import UnitOfMeasurement
from src.domain.repositories.base import BaseRepository


class UnitOfMeasurementRepository(BaseRepository[UnitOfMeasurement]):
    """Repository interface for UnitOfMeasurement entity."""
    
    @abstractmethod
    async def get_by_unit_id(self, unit_id: UUID) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by unit_id."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by name."""
        pass
    
    @abstractmethod
    async def get_by_abbreviation(self, abbreviation: str) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by abbreviation."""
        pass
    
    @abstractmethod
    async def search_by_name(self, name_pattern: str, skip: int = 0, limit: int = 100) -> List[UnitOfMeasurement]:
        """Search units of measurement by name pattern."""
        pass