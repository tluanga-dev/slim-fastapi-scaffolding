from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.customer import Customer
from ...domain.repositories.customer_repository import CustomerRepository
from ...domain.value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus
from ..models.customer_model import CustomerModel


class SQLAlchemyCustomerRepository(CustomerRepository):
    """SQLAlchemy implementation of CustomerRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, customer: Customer) -> Customer:
        """Create a new customer."""
        db_customer = CustomerModel.from_entity(customer)
        self.session.add(db_customer)
        await self.session.commit()
        await self.session.refresh(db_customer)
        return db_customer.to_entity()
    
    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID."""
        query = select(CustomerModel).where(CustomerModel.id == customer_id)
        result = await self.session.execute(query)
        db_customer = result.scalar_one_or_none()
        
        if db_customer:
            return db_customer.to_entity()
        return None
    
    async def get_by_code(self, customer_code: str) -> Optional[Customer]:
        """Get customer by customer code."""
        query = select(CustomerModel).where(CustomerModel.customer_code == customer_code)
        result = await self.session.execute(query)
        db_customer = result.scalar_one_or_none()
        
        if db_customer:
            return db_customer.to_entity()
        return None
    
    async def get_by_tax_id(self, tax_id: str) -> Optional[Customer]:
        """Get customer by tax ID."""
        query = select(CustomerModel).where(CustomerModel.tax_id == tax_id)
        result = await self.session.execute(query)
        db_customer = result.scalar_one_or_none()
        
        if db_customer:
            return db_customer.to_entity()
        return None
    
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
        """List customers with filters and pagination."""
        # Base query
        query = select(CustomerModel)
        count_query = select(func.count()).select_from(CustomerModel)
        
        # Apply filters
        filters = []
        
        if is_active is not None:
            filters.append(CustomerModel.is_active == is_active)
        
        if customer_type:
            filters.append(CustomerModel.customer_type == customer_type)
        
        if customer_tier:
            filters.append(CustomerModel.customer_tier == customer_tier)
        
        if blacklist_status:
            filters.append(CustomerModel.blacklist_status == blacklist_status)
        
        if search:
            search_term = f"%{search}%"
            search_filter = or_(
                CustomerModel.customer_code.ilike(search_term),
                CustomerModel.business_name.ilike(search_term),
                CustomerModel.first_name.ilike(search_term),
                CustomerModel.last_name.ilike(search_term),
                CustomerModel.tax_id.ilike(search_term)
            )
            filters.append(search_filter)
        
        # Apply all filters
        if filters:
            where_clause = and_(*filters)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(CustomerModel.customer_code).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        customers = result.scalars().all()
        
        return [customer.to_entity() for customer in customers], total_count
    
    async def update(self, customer: Customer) -> Customer:
        """Update existing customer."""
        query = select(CustomerModel).where(CustomerModel.id == customer.id)
        result = await self.session.execute(query)
        db_customer = result.scalar_one_or_none()
        
        if not db_customer:
            raise ValueError(f"Customer with id {customer.id} not found")
        
        # Update fields
        db_customer.customer_code = customer.customer_code
        db_customer.customer_type = customer.customer_type
        db_customer.business_name = customer.business_name
        db_customer.first_name = customer.first_name
        db_customer.last_name = customer.last_name
        db_customer.tax_id = customer.tax_id
        db_customer.customer_tier = customer.customer_tier
        db_customer.credit_limit = customer.credit_limit
        db_customer.blacklist_status = customer.blacklist_status
        db_customer.lifetime_value = customer.lifetime_value
        db_customer.last_transaction_date = customer.last_transaction_date
        db_customer.updated_at = customer.updated_at
        db_customer.updated_by = customer.updated_by
        db_customer.is_active = customer.is_active
        
        await self.session.commit()
        await self.session.refresh(db_customer)
        
        return db_customer.to_entity()
    
    async def delete(self, customer_id: UUID) -> bool:
        """Soft delete customer by setting is_active to False."""
        query = select(CustomerModel).where(CustomerModel.id == customer_id)
        result = await self.session.execute(query)
        db_customer = result.scalar_one_or_none()
        
        if not db_customer:
            return False
        
        db_customer.is_active = False
        await self.session.commit()
        
        return True
    
    async def exists_by_code(self, customer_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a customer with the given code exists."""
        query = select(func.count()).select_from(CustomerModel).where(
            CustomerModel.customer_code == customer_code
        )
        
        if exclude_id:
            query = query.where(CustomerModel.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_tax_id(self, tax_id: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a customer with the given tax ID exists."""
        query = select(func.count()).select_from(CustomerModel).where(
            CustomerModel.tax_id == tax_id
        )
        
        if exclude_id:
            query = query.where(CustomerModel.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def get_total_credit_used(self, customer_id: UUID) -> Decimal:
        """Get total credit currently used by customer."""
        # This would typically join with transaction tables
        # For now, return 0 as transactions are not implemented yet
        return Decimal("0.00")
    
    async def search_by_name(self, name: str, limit: int = 10) -> List[Customer]:
        """Search customers by name (business name or first/last name)."""
        search_term = f"%{name}%"
        
        query = select(CustomerModel).where(
            or_(
                CustomerModel.business_name.ilike(search_term),
                CustomerModel.first_name.ilike(search_term),
                CustomerModel.last_name.ilike(search_term),
                (CustomerModel.first_name + ' ' + CustomerModel.last_name).ilike(search_term)
            )
        ).where(
            CustomerModel.is_active == True
        ).order_by(
            CustomerModel.business_name,
            CustomerModel.last_name,
            CustomerModel.first_name
        ).limit(limit)
        
        result = await self.session.execute(query)
        customers = result.scalars().all()
        
        return [customer.to_entity() for customer in customers]
    
    async def get_blacklisted_customers(self, skip: int = 0, limit: int = 100) -> Tuple[List[Customer], int]:
        """Get all blacklisted customers."""
        # Base query
        query = select(CustomerModel).where(
            CustomerModel.blacklist_status == BlacklistStatus.BLACKLISTED
        )
        
        # Count query
        count_query = select(func.count()).select_from(CustomerModel).where(
            CustomerModel.blacklist_status == BlacklistStatus.BLACKLISTED
        )
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(CustomerModel.updated_at.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        customers = result.scalars().all()
        
        return [customer.to_entity() for customer in customers], total_count
    
    async def get_by_tier(self, tier: CustomerTier, skip: int = 0, limit: int = 100) -> Tuple[List[Customer], int]:
        """Get customers by tier."""
        # Base query
        query = select(CustomerModel).where(
            and_(
                CustomerModel.customer_tier == tier,
                CustomerModel.is_active == True
            )
        )
        
        # Count query
        count_query = select(func.count()).select_from(CustomerModel).where(
            and_(
                CustomerModel.customer_tier == tier,
                CustomerModel.is_active == True
            )
        )
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(CustomerModel.lifetime_value.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        customers = result.scalars().all()
        
        return [customer.to_entity() for customer in customers], total_count
    
    async def count_by_type(self) -> dict:
        """Get count of customers by type."""
        query = select(
            CustomerModel.customer_type,
            func.count(CustomerModel.id)
        ).where(
            CustomerModel.is_active == True
        ).group_by(
            CustomerModel.customer_type
        )
        
        result = await self.session.execute(query)
        counts = result.all()
        
        return {
            customer_type.value: count
            for customer_type, count in counts
        }
    
    async def has_transactions(self, customer_id: UUID) -> bool:
        """Check if customer has any transactions."""
        # This would check transaction tables when implemented
        # For now, return False
        return False