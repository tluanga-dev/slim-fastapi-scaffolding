from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities.rental_return import RentalReturn
from ..value_objects.rental_return_type import ReturnStatus, ReturnType


class RentalReturnRepository(ABC):
    """Abstract repository for rental returns."""
    
    @abstractmethod
    async def create(self, rental_return: RentalReturn) -> RentalReturn:
        """Create a new rental return."""
        pass
    
    @abstractmethod
    async def get_by_id(self, return_id: UUID) -> Optional[RentalReturn]:
        """Get rental return by ID."""
        pass
    
    @abstractmethod
    async def get_by_transaction_id(self, transaction_id: UUID) -> List[RentalReturn]:
        """Get all returns for a rental transaction."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_id: Optional[UUID] = None,
        return_status: Optional[ReturnStatus] = None,
        return_type: Optional[ReturnType] = None,
        location_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[RentalReturn], int]:
        """List rental returns with filters and pagination."""
        pass
    
    @abstractmethod
    async def update(self, rental_return: RentalReturn) -> RentalReturn:
        """Update an existing rental return."""
        pass
    
    @abstractmethod
    async def delete(self, return_id: UUID) -> bool:
        """Soft delete a rental return."""
        pass
    
    @abstractmethod
    async def get_outstanding_returns(
        self,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        days_overdue: Optional[int] = None
    ) -> List[RentalReturn]:
        """Get outstanding returns (not completed)."""
        pass
    
    @abstractmethod
    async def get_returns_by_customer(
        self,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[RentalReturn], int]:
        """Get all returns for a specific customer."""
        pass
    
    @abstractmethod
    async def get_late_returns(
        self,
        as_of_date: Optional[date] = None,
        location_id: Optional[UUID] = None
    ) -> List[RentalReturn]:
        """Get returns that are past due."""
        pass
    
    @abstractmethod
    async def get_returns_needing_inspection(
        self,
        location_id: Optional[UUID] = None
    ) -> List[RentalReturn]:
        """Get returns that need inspection."""
        pass
    
    @abstractmethod
    async def count_returns_by_status(
        self,
        location_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """Count returns by status."""
        pass
    
    @abstractmethod
    async def calculate_total_fees(
        self,
        return_id: UUID
    ) -> dict:
        """Calculate total fees for a return."""
        pass