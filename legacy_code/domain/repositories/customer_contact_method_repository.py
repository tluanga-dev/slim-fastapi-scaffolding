from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.customer_contact_method import CustomerContactMethod
from ..value_objects.customer_type import ContactType


class CustomerContactMethodRepository(ABC):
    """Abstract repository interface for CustomerContactMethod entity."""
    
    @abstractmethod
    async def create(self, contact_method: CustomerContactMethod) -> CustomerContactMethod:
        """Create a new contact method."""
        pass
    
    @abstractmethod
    async def get_by_id(self, contact_method_id: UUID) -> Optional[CustomerContactMethod]:
        """Get contact method by ID."""
        pass
    
    @abstractmethod
    async def get_by_customer(
        self,
        customer_id: UUID,
        contact_type: Optional[ContactType] = None,
        is_primary: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> List[CustomerContactMethod]:
        """Get all contact methods for a customer."""
        pass
    
    @abstractmethod
    async def get_primary_by_type(
        self,
        customer_id: UUID,
        contact_type: ContactType
    ) -> Optional[CustomerContactMethod]:
        """Get primary contact method by type for a customer."""
        pass
    
    @abstractmethod
    async def update(self, contact_method: CustomerContactMethod) -> CustomerContactMethod:
        """Update existing contact method."""
        pass
    
    @abstractmethod
    async def delete(self, contact_method_id: UUID) -> bool:
        """Soft delete contact method."""
        pass
    
    @abstractmethod
    async def exists(
        self,
        customer_id: UUID,
        contact_type: ContactType,
        contact_value: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if a contact method already exists for customer."""
        pass
    
    @abstractmethod
    async def set_primary(
        self,
        contact_method_id: UUID,
        customer_id: UUID,
        contact_type: ContactType
    ) -> bool:
        """Set a contact method as primary (unsets others of same type)."""
        pass
    
    @abstractmethod
    async def verify(self, contact_method_id: UUID) -> bool:
        """Mark contact method as verified."""
        pass
    
    @abstractmethod
    async def get_verified_emails(self, customer_id: UUID) -> List[CustomerContactMethod]:
        """Get all verified email addresses for a customer."""
        pass
    
    @abstractmethod
    async def get_marketing_contacts(self, customer_id: UUID) -> List[CustomerContactMethod]:
        """Get all contacts that opted in for marketing."""
        pass