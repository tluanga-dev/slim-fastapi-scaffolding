from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import date
from uuid import UUID
from decimal import Decimal

from ..entities.transaction_line import TransactionLine
from ..value_objects.transaction_type import LineItemType


class TransactionLineRepository(ABC):
    """Abstract repository interface for TransactionLine entity."""
    
    @abstractmethod
    async def create(self, transaction_line: TransactionLine) -> TransactionLine:
        """Create a new transaction line."""
        pass
    
    @abstractmethod
    async def create_batch(self, transaction_lines: List[TransactionLine]) -> List[TransactionLine]:
        """Create multiple transaction lines in batch."""
        pass
    
    @abstractmethod
    async def get_by_id(self, line_id: UUID) -> Optional[TransactionLine]:
        """Get transaction line by ID."""
        pass
    
    @abstractmethod
    async def get_by_transaction(
        self,
        transaction_id: UUID,
        line_type: Optional[LineItemType] = None,
        include_inactive: bool = False
    ) -> List[TransactionLine]:
        """Get all lines for a transaction."""
        pass
    
    @abstractmethod
    async def get_by_sku(
        self,
        sku_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TransactionLine]:
        """Get all transaction lines for a SKU."""
        pass
    
    @abstractmethod
    async def get_by_inventory_unit(
        self,
        inventory_unit_id: UUID,
        include_returned: bool = True
    ) -> List[TransactionLine]:
        """Get all transaction lines for an inventory unit."""
        pass
    
    @abstractmethod
    async def update(self, transaction_line: TransactionLine) -> TransactionLine:
        """Update existing transaction line."""
        pass
    
    @abstractmethod
    async def update_batch(self, transaction_lines: List[TransactionLine]) -> List[TransactionLine]:
        """Update multiple transaction lines in batch."""
        pass
    
    @abstractmethod
    async def delete(self, line_id: UUID) -> bool:
        """Soft delete transaction line."""
        pass
    
    @abstractmethod
    async def delete_by_transaction(self, transaction_id: UUID) -> int:
        """Delete all lines for a transaction. Returns count of deleted lines."""
        pass
    
    @abstractmethod
    async def get_unreturned_rentals(
        self,
        customer_id: Optional[UUID] = None,
        sku_id: Optional[UUID] = None,
        overdue_only: bool = False,
        as_of_date: Optional[date] = None
    ) -> List[TransactionLine]:
        """Get rental lines that haven't been fully returned."""
        pass
    
    @abstractmethod
    async def get_rental_history(
        self,
        inventory_unit_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TransactionLine]:
        """Get rental history for an inventory unit."""
        pass
    
    @abstractmethod
    async def calculate_line_totals(self, transaction_id: UUID) -> dict:
        """Calculate totals for all lines in a transaction."""
        pass
    
    @abstractmethod
    async def get_sales_by_sku(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[dict]:
        """Get sales summary by SKU for a period."""
        pass
    
    @abstractmethod
    async def get_rental_utilization(
        self,
        sku_id: UUID,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get rental utilization statistics for a SKU."""
        pass
    
    @abstractmethod
    async def get_next_line_number(self, transaction_id: UUID) -> int:
        """Get next available line number for a transaction."""
        pass