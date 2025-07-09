from typing import Optional
from uuid import UUID
from decimal import Decimal

from ....domain.entities.customer import Customer
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.value_objects.customer_type import CustomerTier


class UpdateCustomerUseCase:
    """Use case for updating an existing customer."""
    
    def __init__(self, customer_repository: CustomerRepository):
        """Initialize use case with repository."""
        self.customer_repository = customer_repository
    
    async def update_personal_info(
        self,
        customer_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> Customer:
        """Update personal information for individual customers.
        
        Args:
            customer_id: UUID of the customer to update
            first_name: New first name (optional)
            last_name: New last name (optional)
            updated_by: ID of user updating the customer
            
        Returns:
            Updated customer entity
            
        Raises:
            ValueError: If customer not found or not individual type
        """
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")
        
        customer.update_personal_info(first_name, last_name, updated_by)
        
        return await self.customer_repository.update(customer)
    
    async def update_business_info(
        self,
        customer_id: UUID,
        business_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> Customer:
        """Update business information.
        
        Args:
            customer_id: UUID of the customer to update
            business_name: New business name (optional)
            tax_id: New tax ID (optional)
            updated_by: ID of user updating the customer
            
        Returns:
            Updated customer entity
            
        Raises:
            ValueError: If customer not found or tax ID already exists
        """
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")
        
        # Check if new tax ID already exists
        if tax_id and tax_id != customer.tax_id:
            if await self.customer_repository.exists_by_tax_id(tax_id, exclude_id=customer_id):
                raise ValueError(f"Customer with tax ID '{tax_id}' already exists")
        
        customer.update_business_info(business_name, tax_id, updated_by)
        
        return await self.customer_repository.update(customer)
    
    async def update_credit_limit(
        self,
        customer_id: UUID,
        credit_limit: Decimal,
        updated_by: Optional[str] = None
    ) -> Customer:
        """Update customer credit limit.
        
        Args:
            customer_id: UUID of the customer to update
            credit_limit: New credit limit
            updated_by: ID of user updating the customer
            
        Returns:
            Updated customer entity
            
        Raises:
            ValueError: If customer not found or credit limit invalid
        """
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")
        
        customer.update_credit_limit(credit_limit, updated_by)
        
        return await self.customer_repository.update(customer)
    
    async def update_tier(
        self,
        customer_id: UUID,
        tier: CustomerTier,
        updated_by: Optional[str] = None
    ) -> Customer:
        """Update customer tier.
        
        Args:
            customer_id: UUID of the customer to update
            tier: New customer tier
            updated_by: ID of user updating the customer
            
        Returns:
            Updated customer entity
            
        Raises:
            ValueError: If customer not found
        """
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")
        
        customer.update_tier(tier, updated_by)
        
        return await self.customer_repository.update(customer)