from typing import Optional, List, Tuple
from uuid import UUID
from decimal import Decimal

from ...domain.entities.supplier import Supplier
from ...domain.repositories.supplier_repository import SupplierRepository
from ...domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms


class CreateSupplierUseCase:
    """Use case for creating a new supplier."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(
        self,
        supplier_code: str,
        company_name: str,
        supplier_type: SupplierType,
        contact_person: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[PaymentTerms] = None,
        credit_limit: Optional[Decimal] = None,
        supplier_tier: Optional[SupplierTier] = None,
        created_by: Optional[str] = None
    ) -> Supplier:
        """Create a new supplier."""
        
        # Check if supplier code already exists
        if await self.supplier_repository.supplier_code_exists(supplier_code):
            raise ValueError(f"A supplier with code '{supplier_code}' already exists. Please use a different supplier code.")
        
        # Check if company name already exists
        if await self.supplier_repository.company_name_exists(company_name):
            raise ValueError(f"A supplier with company name '{company_name}' already exists. Please use a different company name.")
        
        # Create supplier entity
        supplier = Supplier(
            supplier_code=supplier_code,
            company_name=company_name,
            supplier_type=supplier_type,
            contact_person=contact_person,
            email=email,
            phone=phone,
            address=address,
            tax_id=tax_id,
            payment_terms=payment_terms,
            credit_limit=credit_limit,
            supplier_tier=supplier_tier,
            created_by=created_by
        )
        
        # Validate supplier
        errors = supplier.validate()
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        # Save supplier
        return await self.supplier_repository.create(supplier)


class GetSupplierUseCase:
    """Use case for retrieving suppliers."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(self, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID."""
        return await self.supplier_repository.get_by_id(supplier_id)
    
    async def get_by_code(self, supplier_code: str) -> Optional[Supplier]:
        """Get supplier by code."""
        return await self.supplier_repository.get_by_code(supplier_code)


class UpdateSupplierUseCase:
    """Use case for updating supplier information."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(
        self,
        supplier_id: UUID,
        company_name: Optional[str] = None,
        supplier_type: Optional[SupplierType] = None,
        contact_person: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[PaymentTerms] = None,
        credit_limit: Optional[Decimal] = None,
        supplier_tier: Optional[SupplierTier] = None,
        updated_by: Optional[str] = None
    ) -> Supplier:
        """Update supplier information."""
        
        # Get existing supplier
        supplier = await self.supplier_repository.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")
        
        # Update business info if provided
        if company_name is not None or supplier_type is not None or tax_id is not None:
            supplier.update_business_info(
                company_name=company_name,
                supplier_type=supplier_type,
                tax_id=tax_id,
                updated_by=updated_by
            )
        
        # Update contact info if provided
        if any(field is not None for field in [contact_person, email, phone, address]):
            supplier.update_contact_info(
                contact_person=contact_person,
                email=email,
                phone=phone,
                address=address,
                updated_by=updated_by
            )
        
        # Update payment terms if provided
        if payment_terms is not None or credit_limit is not None:
            supplier.update_payment_terms(
                payment_terms=payment_terms or supplier.payment_terms,
                credit_limit=credit_limit,
                updated_by=updated_by
            )
        
        # Update tier if provided
        if supplier_tier is not None:
            supplier.update_tier(supplier_tier, updated_by=updated_by)
        
        # Validate supplier
        errors = supplier.validate()
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        # Save updated supplier
        return await self.supplier_repository.update(supplier)


class ListSuppliersUseCase:
    """Use case for listing suppliers with filters."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_type: Optional[SupplierType] = None,
        supplier_tier: Optional[SupplierTier] = None,
        payment_terms: Optional[PaymentTerms] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Supplier], int]:
        """List suppliers with pagination and filters."""
        return await self.supplier_repository.list(
            skip=skip,
            limit=limit,
            supplier_type=supplier_type,
            supplier_tier=supplier_tier,
            payment_terms=payment_terms,
            search=search,
            is_active=is_active
        )


class DeactivateSupplierUseCase:
    """Use case for deactivating a supplier."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(self, supplier_id: UUID, updated_by: Optional[str] = None) -> bool:
        """Deactivate a supplier."""
        supplier = await self.supplier_repository.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")
        
        supplier.deactivate(updated_by=updated_by)
        await self.supplier_repository.update(supplier)
        return True


class ActivateSupplierUseCase:
    """Use case for activating a supplier."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(self, supplier_id: UUID, updated_by: Optional[str] = None) -> bool:
        """Activate a supplier."""
        supplier = await self.supplier_repository.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")
        
        supplier.activate(updated_by=updated_by)
        await self.supplier_repository.update(supplier)
        return True


class UpdateSupplierPerformanceUseCase:
    """Use case for updating supplier performance metrics."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(
        self,
        supplier_id: UUID,
        total_orders: Optional[int] = None,
        total_spend: Optional[Decimal] = None,
        average_delivery_days: Optional[int] = None,
        quality_rating: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ) -> Supplier:
        """Update supplier performance metrics."""
        supplier = await self.supplier_repository.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")
        
        supplier.update_performance_metrics(
            total_orders=total_orders,
            total_spend=total_spend,
            average_delivery_days=average_delivery_days,
            quality_rating=quality_rating
        )
        
        if updated_by:
            supplier.update_timestamp(updated_by)
        
        return await self.supplier_repository.update(supplier)


class SearchSuppliersUseCase:
    """Use case for searching suppliers."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(self, query: str, limit: int = 10) -> List[Supplier]:
        """Search suppliers by name."""
        if not query or len(query.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters long")
        
        return await self.supplier_repository.search_by_name(query.strip(), limit)


class GetSupplierAnalyticsUseCase:
    """Use case for getting supplier analytics."""
    
    def __init__(self, supplier_repository: SupplierRepository):
        self.supplier_repository = supplier_repository
    
    async def execute(self) -> dict:
        """Get supplier analytics data."""
        return await self.supplier_repository.get_supplier_analytics()