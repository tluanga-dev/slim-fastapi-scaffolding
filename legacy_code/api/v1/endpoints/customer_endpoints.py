from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.customer import (
    CreateCustomerUseCase,
    GetCustomerUseCase,
    UpdateCustomerUseCase
)
from ....infrastructure.repositories.customer_repository import SQLAlchemyCustomerRepository
from ....domain.value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus
from ..schemas.customer_schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerBlacklistRequest,
    CustomerCreditLimitUpdate,
    CustomerTierUpdate
)
from ..dependencies.database import get_db

router = APIRouter(tags=["customers"])


async def get_customer_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyCustomerRepository:
    """Get customer repository instance."""
    return SQLAlchemyCustomerRepository(db)


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Create a new customer."""
    use_case = CreateCustomerUseCase(repository)
    
    try:
        # Validate business customer has business name
        if customer_data.customer_type == CustomerType.BUSINESS and not customer_data.business_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business name is required for business customers"
            )
        
        # Validate individual customer has first and last name
        if customer_data.customer_type == CustomerType.INDIVIDUAL:
            if not customer_data.first_name or not customer_data.last_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="First name and last name are required for individual customers"
                )
        
        customer = await use_case.execute(
            customer_code=customer_data.customer_code,
            customer_type=CustomerType(customer_data.customer_type),
            business_name=customer_data.business_name,
            first_name=customer_data.first_name,
            last_name=customer_data.last_name,
            tax_id=customer_data.tax_id,
            customer_tier=CustomerTier(customer_data.customer_tier),
            credit_limit=customer_data.credit_limit,
            created_by=current_user_id
        )
        return CustomerResponse.from_entity(customer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
):
    """Get a customer by ID."""
    use_case = GetCustomerUseCase(repository)
    customer = await use_case.execute(customer_id)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    return CustomerResponse.from_entity(customer)


@router.get("/code/{customer_code}", response_model=CustomerResponse)
async def get_customer_by_code(
    customer_code: str,
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
):
    """Get a customer by code."""
    use_case = GetCustomerUseCase(repository)
    customer = await use_case.get_by_code(customer_code)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with code '{customer_code}' not found"
        )
    
    return CustomerResponse.from_entity(customer)


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    customer_type: Optional[CustomerType] = Query(None, description="Filter by customer type"),
    customer_tier: Optional[CustomerTier] = Query(None, description="Filter by customer tier"),
    blacklist_status: Optional[BlacklistStatus] = Query(None, description="Filter by blacklist status"),
    search: Optional[str] = Query(None, description="Search in code, names, or tax ID"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
):
    """List customers with pagination and filters."""
    customers, total_count = await repository.list(
        skip=skip,
        limit=limit,
        customer_type=customer_type,
        customer_tier=customer_tier,
        blacklist_status=blacklist_status,
        search=search,
        is_active=is_active
    )
    
    return CustomerListResponse(
        items=[CustomerResponse.from_entity(customer) for customer in customers],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update customer information."""
    use_case = UpdateCustomerUseCase(repository)
    
    try:
        # Get existing customer
        get_use_case = GetCustomerUseCase(repository)
        customer = await get_use_case.execute(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found"
            )
        
        # Update based on customer type
        if customer.customer_type == CustomerType.INDIVIDUAL:
            if customer_data.first_name is not None or customer_data.last_name is not None:
                customer = await use_case.update_personal_info(
                    customer_id=customer_id,
                    first_name=customer_data.first_name,
                    last_name=customer_data.last_name,
                    updated_by=current_user_id
                )
        
        if customer_data.business_name is not None or customer_data.tax_id is not None:
            customer = await use_case.update_business_info(
                customer_id=customer_id,
                business_name=customer_data.business_name,
                tax_id=customer_data.tax_id,
                updated_by=current_user_id
            )
        
        if customer_data.credit_limit is not None:
            customer = await use_case.update_credit_limit(
                customer_id=customer_id,
                credit_limit=customer_data.credit_limit,
                updated_by=current_user_id
            )
        
        if customer_data.customer_tier is not None:
            customer = await use_case.update_tier(
                customer_id=customer_id,
                tier=CustomerTier(customer_data.customer_tier),
                updated_by=current_user_id
            )
        
        return CustomerResponse.from_entity(customer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{customer_id}/blacklist", response_model=CustomerResponse)
async def manage_blacklist(
    customer_id: UUID,
    request: CustomerBlacklistRequest,
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Blacklist or unblacklist a customer."""
    try:
        # Get customer
        customer = await repository.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found"
            )
        
        # Perform action
        if request.action == "blacklist":
            customer.blacklist(updated_by=current_user_id)
        else:  # unblacklist
            customer.remove_from_blacklist(updated_by=current_user_id)
        
        # Save changes
        updated_customer = await repository.update(customer)
        
        return CustomerResponse.from_entity(updated_customer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{customer_id}/credit-limit", response_model=CustomerResponse)
async def update_credit_limit(
    customer_id: UUID,
    request: CustomerCreditLimitUpdate,
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update customer credit limit."""
    use_case = UpdateCustomerUseCase(repository)
    
    try:
        customer = await use_case.update_credit_limit(
            customer_id=customer_id,
            credit_limit=request.credit_limit,
            updated_by=current_user_id
        )
        return CustomerResponse.from_entity(customer)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{customer_id}/tier", response_model=CustomerResponse)
async def update_customer_tier(
    customer_id: UUID,
    request: CustomerTierUpdate,
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update customer tier."""
    use_case = UpdateCustomerUseCase(repository)
    
    try:
        customer = await use_case.update_tier(
            customer_id=customer_id,
            tier=request.customer_tier,
            updated_by=current_user_id
        )
        return CustomerResponse.from_entity(customer)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Soft delete a customer."""
    # Check if customer has transactions
    if await repository.has_transactions(customer_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete customer with existing transactions"
        )
    
    success = await repository.delete(customer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )


@router.get("/search/name", response_model=List[CustomerResponse])
async def search_customers_by_name(
    name: str = Query(..., min_length=2, description="Name to search for"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
):
    """Search customers by name (business name or individual name)."""
    customers = await repository.search_by_name(name, limit)
    return [CustomerResponse.from_entity(customer) for customer in customers]


@router.get("/blacklisted/", response_model=CustomerListResponse)
async def get_blacklisted_customers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
):
    """Get all blacklisted customers."""
    customers, total_count = await repository.get_blacklisted_customers(skip, limit)
    
    return CustomerListResponse(
        items=[CustomerResponse.from_entity(customer) for customer in customers],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/tier/{tier}", response_model=CustomerListResponse)
async def get_customers_by_tier(
    tier: CustomerTier,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
):
    """Get customers by tier."""
    customers, total_count = await repository.get_by_tier(tier, skip, limit)
    
    return CustomerListResponse(
        items=[CustomerResponse.from_entity(customer) for customer in customers],
        total=total_count,
        skip=skip,
        limit=limit
    )