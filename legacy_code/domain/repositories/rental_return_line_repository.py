from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities.rental_return_line import RentalReturnLine
from ..value_objects.inspection_type import DamageLevel
from ..value_objects.item_type import ConditionGrade


class RentalReturnLineRepository(ABC):
    """Abstract repository for rental return lines."""
    
    @abstractmethod
    async def create(self, line: RentalReturnLine) -> RentalReturnLine:
        """Create a new rental return line."""
        pass
    
    @abstractmethod
    async def create_batch(self, lines: List[RentalReturnLine]) -> List[RentalReturnLine]:
        """Create multiple rental return lines."""
        pass
    
    @abstractmethod
    async def get_by_id(self, line_id: UUID) -> Optional[RentalReturnLine]:
        """Get rental return line by ID."""
        pass
    
    @abstractmethod
    async def get_by_return_id(self, return_id: UUID) -> List[RentalReturnLine]:
        """Get all lines for a rental return."""
        pass
    
    @abstractmethod
    async def get_by_inventory_unit_id(self, unit_id: UUID) -> List[RentalReturnLine]:
        """Get all return lines for an inventory unit."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        return_id: Optional[UUID] = None,
        inventory_unit_id: Optional[UUID] = None,
        damage_level: Optional[DamageLevel] = None,
        condition_grade: Optional[ConditionGrade] = None,
        is_processed: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[RentalReturnLine], int]:
        """List rental return lines with filters and pagination."""
        pass
    
    @abstractmethod
    async def update(self, line: RentalReturnLine) -> RentalReturnLine:
        """Update an existing rental return line."""
        pass
    
    @abstractmethod
    async def delete(self, line_id: UUID) -> bool:
        """Soft delete a rental return line."""
        pass
    
    @abstractmethod
    async def get_lines_with_damage(
        self,
        return_id: Optional[UUID] = None,
        damage_level: Optional[DamageLevel] = None
    ) -> List[RentalReturnLine]:
        """Get lines with damage."""
        pass
    
    @abstractmethod
    async def get_unprocessed_lines(
        self,
        return_id: Optional[UUID] = None
    ) -> List[RentalReturnLine]:
        """Get unprocessed return lines."""
        pass
    
    @abstractmethod
    async def get_lines_by_condition(
        self,
        condition_grade: ConditionGrade,
        return_id: Optional[UUID] = None
    ) -> List[RentalReturnLine]:
        """Get lines by condition grade."""
        pass
    
    @abstractmethod
    async def calculate_total_fees_by_return(
        self,
        return_id: UUID
    ) -> dict:
        """Calculate total fees for all lines in a return."""
        pass
    
    @abstractmethod
    async def get_partial_returns(
        self,
        inventory_unit_id: Optional[UUID] = None
    ) -> List[RentalReturnLine]:
        """Get lines representing partial returns."""
        pass