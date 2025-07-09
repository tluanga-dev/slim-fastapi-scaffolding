from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.customer_address import CustomerAddress
from ..value_objects.customer_type import AddressType


class CustomerAddressRepository(ABC):
    """Abstract repository interface for CustomerAddress entity."""
    
    @abstractmethod
    async def create(self, address: CustomerAddress) -> CustomerAddress:
        """Create a new address."""
        pass
    
    @abstractmethod
    async def get_by_id(self, address_id: UUID) -> Optional[CustomerAddress]:
        """Get address by ID."""
        pass
    
    @abstractmethod
    async def get_by_customer(
        self,
        customer_id: UUID,
        address_type: Optional[AddressType] = None,
        is_default: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> List[CustomerAddress]:
        """Get all addresses for a customer."""
        pass
    
    @abstractmethod
    async def get_default_by_type(
        self,
        customer_id: UUID,
        address_type: AddressType
    ) -> Optional[CustomerAddress]:
        """Get default address by type for a customer."""
        pass
    
    @abstractmethod
    async def update(self, address: CustomerAddress) -> CustomerAddress:
        """Update existing address."""
        pass
    
    @abstractmethod
    async def delete(self, address_id: UUID) -> bool:
        """Soft delete address."""
        pass
    
    @abstractmethod
    async def set_default(
        self,
        address_id: UUID,
        customer_id: UUID,
        address_type: AddressType
    ) -> bool:
        """Set an address as default (unsets others of same type)."""
        pass
    
    @abstractmethod
    async def get_billing_addresses(self, customer_id: UUID) -> List[CustomerAddress]:
        """Get all billing addresses for a customer."""
        pass
    
    @abstractmethod
    async def get_shipping_addresses(self, customer_id: UUID) -> List[CustomerAddress]:
        """Get all shipping addresses for a customer."""
        pass
    
    @abstractmethod
    async def count_by_customer(self, customer_id: UUID) -> int:
        """Count total addresses for a customer."""
        pass