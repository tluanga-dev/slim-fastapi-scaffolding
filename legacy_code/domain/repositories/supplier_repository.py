from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities.supplier import Supplier
from ..value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms


class SupplierRepository(ABC):
    """Abstract repository interface for supplier operations."""

    @abstractmethod
    async def create(self, supplier: Supplier) -> Supplier:
        """Create a new supplier."""
        pass

    @abstractmethod
    async def get_by_id(self, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID."""
        pass

    @abstractmethod
    async def get_by_code(self, supplier_code: str) -> Optional[Supplier]:
        """Get supplier by supplier code."""
        pass

    @abstractmethod
    async def update(self, supplier: Supplier) -> Supplier:
        """Update an existing supplier."""
        pass

    @abstractmethod
    async def delete(self, supplier_id: UUID) -> bool:
        """Soft delete a supplier."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_type: Optional[SupplierType] = None,
        supplier_tier: Optional[SupplierTier] = None,
        payment_terms: Optional[PaymentTerms] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Supplier], int]:
        """List suppliers with pagination and filters."""
        pass

    @abstractmethod
    async def search_by_name(self, name: str, limit: int = 10) -> List[Supplier]:
        """Search suppliers by company name."""
        pass

    @abstractmethod
    async def get_by_tier(
        self, 
        tier: SupplierTier, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Supplier], int]:
        """Get suppliers by tier."""
        pass

    @abstractmethod
    async def get_active_suppliers(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Supplier], int]:
        """Get all active suppliers."""
        pass

    @abstractmethod
    async def get_top_suppliers_by_spend(
        self, 
        limit: int = 10
    ) -> List[Supplier]:
        """Get top suppliers by total spend."""
        pass

    @abstractmethod
    async def supplier_code_exists(self, supplier_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if supplier code already exists."""
        pass
    
    @abstractmethod
    async def company_name_exists(self, company_name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if company name already exists."""
        pass

    @abstractmethod
    async def get_supplier_analytics(self) -> dict:
        """Get supplier analytics data."""
        pass