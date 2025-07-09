from typing import Optional
from uuid import UUID

from ....domain.entities.customer import Customer
from ....domain.repositories.customer_repository import CustomerRepository


class GetCustomerUseCase:
    """Use case for retrieving a customer."""
    
    def __init__(self, customer_repository: CustomerRepository):
        """Initialize use case with repository."""
        self.customer_repository = customer_repository
    
    async def execute(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID.
        
        Args:
            customer_id: UUID of the customer
            
        Returns:
            Customer entity if found, None otherwise
        """
        return await self.customer_repository.get_by_id(customer_id)
    
    async def get_by_code(self, customer_code: str) -> Optional[Customer]:
        """Get customer by code.
        
        Args:
            customer_code: Customer code
            
        Returns:
            Customer entity if found, None otherwise
        """
        return await self.customer_repository.get_by_code(customer_code)
    
    async def get_by_tax_id(self, tax_id: str) -> Optional[Customer]:
        """Get customer by tax ID.
        
        Args:
            tax_id: Tax identification number
            
        Returns:
            Customer entity if found, None otherwise
        """
        return await self.customer_repository.get_by_tax_id(tax_id)