from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import date, datetime
from uuid import UUID

from ..entities.transaction_header import TransactionHeader
from ..value_objects.transaction_type import TransactionType, TransactionStatus, PaymentStatus


class TransactionHeaderRepository(ABC):
    """Abstract repository interface for TransactionHeader entity."""
    
    @abstractmethod
    async def create(self, transaction: TransactionHeader) -> TransactionHeader:
        """Create a new transaction."""
        pass
    
    @abstractmethod
    async def get_by_id(self, transaction_id: UUID) -> Optional[TransactionHeader]:
        """Get transaction by ID."""
        pass
    
    @abstractmethod
    async def get_by_number(self, transaction_number: str) -> Optional[TransactionHeader]:
        """Get transaction by transaction number."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[TransactionHeader], int]:
        """List transactions with filters and pagination."""
        pass
    
    @abstractmethod
    async def update(self, transaction_id: UUID, transaction: TransactionHeader) -> TransactionHeader:
        """Update existing transaction."""
        pass
    
    @abstractmethod
    async def delete(self, transaction_id: UUID) -> bool:
        """Soft delete transaction by setting is_active to False."""
        pass
    
    @abstractmethod
    async def get_customer_transactions(
        self,
        customer_id: UUID,
        transaction_type: Optional[TransactionType] = None,
        include_cancelled: bool = False
    ) -> List[TransactionHeader]:
        """Get all transactions for a customer."""
        pass
    
    @abstractmethod
    async def get_active_rentals(
        self,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        as_of_date: Optional[date] = None
    ) -> List[TransactionHeader]:
        """Get active rental transactions."""
        pass
    
    @abstractmethod
    async def get_overdue_rentals(
        self,
        location_id: Optional[UUID] = None,
        include_returned: bool = False,
        as_of_date: Optional[date] = None
    ) -> List[TransactionHeader]:
        """Get overdue rental transactions."""
        pass
    
    @abstractmethod
    async def get_pending_payments(
        self,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None
    ) -> List[TransactionHeader]:
        """Get transactions with pending payments."""
        pass
    
    @abstractmethod
    async def get_daily_summary(
        self,
        summary_date: date,
        location_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None
    ) -> dict:
        """Get daily transaction summary."""
        pass
    
    @abstractmethod
    async def get_revenue_by_period(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
        group_by: str = "day"  # day, week, month
    ) -> List[dict]:
        """Get revenue grouped by time period."""
        pass
    
    @abstractmethod
    async def generate_transaction_number(
        self,
        transaction_type: TransactionType,
        location_id: UUID
    ) -> str:
        """Generate unique transaction number."""
        pass
    
    @abstractmethod
    async def exists_by_number(self, transaction_number: str) -> bool:
        """Check if transaction with given number exists."""
        pass
    
    @abstractmethod
    async def get_customer_summary(self, customer_id: UUID) -> dict:
        """Get customer transaction summary."""
        pass
    
    @abstractmethod
    async def get_daily_summary(self, start_date: date, end_date: date, location_id: Optional[UUID] = None) -> List[dict]:
        """Get daily transaction summaries."""
        pass
    
    @abstractmethod
    async def get_by_date(self, transaction_date: date, location_id: Optional[UUID] = None) -> List[TransactionHeader]:
        """Get transactions by date."""
        pass
    
    @abstractmethod
    async def get_revenue_report(self, start_date: date, end_date: date, group_by: str, location_id: Optional[UUID] = None) -> List[dict]:
        """Get revenue report."""
        pass
    
    @abstractmethod
    async def count_by_date(self, transaction_date: date) -> int:
        """Count transactions by date."""
        pass
    
    @abstractmethod
    async def get_active_rentals_by_unit(self, unit_id: UUID) -> List[TransactionHeader]:
        """Get active rental transactions for a specific inventory unit."""
        pass
    
