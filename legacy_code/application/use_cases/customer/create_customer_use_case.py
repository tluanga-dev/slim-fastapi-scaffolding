from typing import Optional
from decimal import Decimal

from ....domain.entities.customer import Customer
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus


class CreateCustomerUseCase:
    """Use case for creating a new customer."""
    
    def __init__(self, customer_repository: CustomerRepository):
        """Initialize use case with repository."""
        self.customer_repository = customer_repository
    
    async def execute(
        self,
        customer_code: str,
        customer_type: CustomerType,
        business_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        customer_tier: CustomerTier = CustomerTier.BRONZE,
        credit_limit: Decimal = Decimal("0.00"),
        created_by: Optional[str] = None
    ) -> Customer:
        """Execute customer creation.
        
        Args:
            customer_code: Unique customer code
            customer_type: Type of customer (INDIVIDUAL or BUSINESS)
            business_name: Company name (required for business customers)
            first_name: First name (required for individual customers)
            last_name: Last name (required for individual customers)
            tax_id: GST/Tax identification number
            customer_tier: Customer tier level
            credit_limit: Credit limit amount
            created_by: ID of user creating the customer
            
        Returns:
            Created customer entity
            
        Raises:
            ValueError: If customer code already exists or validation fails
        """
        # Check if customer code already exists
        if await self.customer_repository.exists_by_code(customer_code):
            raise ValueError(f"Customer with code '{customer_code}' already exists")
        
        # Check if tax ID already exists (if provided)
        if tax_id and await self.customer_repository.exists_by_tax_id(tax_id):
            raise ValueError(f"Customer with tax ID '{tax_id}' already exists")
        
        # Create customer entity
        customer = Customer(
            customer_code=customer_code,
            customer_type=customer_type,
            business_name=business_name,
            first_name=first_name,
            last_name=last_name,
            tax_id=tax_id,
            customer_tier=customer_tier,
            credit_limit=credit_limit,
            blacklist_status=BlacklistStatus.CLEAR,
            lifetime_value=Decimal("0.00"),
            created_by=created_by,
            updated_by=created_by
        )
        
        # Save to repository
        return await self.customer_repository.create(customer)