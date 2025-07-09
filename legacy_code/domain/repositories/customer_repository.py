from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal

from ..entities.customer import Customer
from ..value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus


class CustomerRepository(ABC):
    """Abstract repository interface for Customer entity."""
    
    @abstractmethod
    async def create(self, customer: Customer) -> Customer:
        """Create a new customer."""
        pass
    
    @abstractmethod
    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID."""
        pass
    
    @abstractmethod
    async def get_by_code(self, customer_code: str) -> Optional[Customer]:
        """Get customer by customer code."""
        pass
    
    @abstractmethod
    async def get_by_tax_id(self, tax_id: str) -> Optional[Customer]:
        """Get customer by tax ID."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        customer_type: Optional[CustomerType] = None,
        customer_tier: Optional[CustomerTier] = None,
        blacklist_status: Optional[BlacklistStatus] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[Customer], int]:
        """List customers with filters and pagination.
        
        Returns:
            Tuple of (customers list, total count)
        """
        pass
    
    @abstractmethod
    async def update(self, customer: Customer) -> Customer:
        """Update existing customer."""
        pass
    
    @abstractmethod
    async def delete(self, customer_id: UUID) -> bool:
        """Soft delete customer by setting is_active to False."""
        pass
    
    @abstractmethod
    async def exists_by_code(self, customer_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a customer with the given code exists."""
        pass
    
    @abstractmethod
    async def exists_by_tax_id(self, tax_id: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a customer with the given tax ID exists."""
        pass
    
    @abstractmethod
    async def get_total_credit_used(self, customer_id: UUID) -> Decimal:
        """Get total credit currently used by customer."""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str, limit: int = 10) -> List[Customer]:
        """Search customers by name (business name or first/last name)."""
        pass
    
    @abstractmethod
    async def get_blacklisted_customers(self, skip: int = 0, limit: int = 100) -> Tuple[List[Customer], int]:
        """Get all blacklisted customers."""
        pass
    
    @abstractmethod
    async def get_by_tier(self, tier: CustomerTier, skip: int = 0, limit: int = 100) -> Tuple[List[Customer], int]:
        """Get customers by tier."""
        pass
    
    @abstractmethod
    async def count_by_type(self) -> dict:
        """Get count of customers by type."""
        pass
    
    @abstractmethod
    async def has_transactions(self, customer_id: UUID) -> bool:
        """Check if customer has any transactions."""
        pass