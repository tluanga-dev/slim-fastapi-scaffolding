from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from app.modules.suppliers.repository import SupplierRepository
from app.modules.suppliers.schemas import (
    SupplierCreate, SupplierUpdate, SupplierContactUpdate,
    SupplierPaymentUpdate, SupplierTierUpdate, SupplierStatusUpdate,
    SupplierPerformanceUpdate, SupplierResponse, SupplierListResponse,
    SupplierPerformanceResponse
)
from app.core.domain.entities.supplier import Supplier as SupplierEntity
from app.core.domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms
from app.core.errors import NotFoundError, ValidationError
from app.modules.suppliers.models import Supplier as SupplierModel


class SupplierService:
    """Service layer for supplier business logic."""
    
    def __init__(self, repository: SupplierRepository):
        self.repository = repository
    
    def _model_to_entity(self, model: SupplierModel) -> SupplierEntity:
        """Convert SQLAlchemy model to domain entity."""
        return SupplierEntity(
            id=model.id,
            supplier_code=model.supplier_code,
            company_name=model.company_name,
            supplier_type=model.supplier_type,
            contact_person=model.contact_person,
            email=model.email,
            phone=model.phone,
            address=model.address,
            tax_id=model.tax_id,
            payment_terms=model.payment_terms,
            credit_limit=model.credit_limit,
            supplier_tier=model.supplier_tier,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
    
    def _entity_to_dict(self, entity: SupplierEntity) -> dict:
        """Convert domain entity to dictionary for database operations."""
        return {
            'id': entity.id,
            'supplier_code': entity.supplier_code,
            'company_name': entity.company_name,
            'supplier_type': entity.supplier_type,
            'contact_person': entity.contact_person,
            'email': entity.email,
            'phone': entity.phone,
            'address': entity.address,
            'tax_id': entity.tax_id,
            'payment_terms': entity.payment_terms,
            'credit_limit': entity.credit_limit,
            'supplier_tier': entity.supplier_tier,
            'total_orders': entity.total_orders,
            'total_spend': entity.total_spend,
            'average_delivery_days': entity.average_delivery_days,
            'quality_rating': entity.quality_rating,
            'last_order_date': entity.last_order_date,
            'is_active': entity.is_active,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'created_by': entity.created_by,
            'updated_by': entity.updated_by
        }
    
    async def create_supplier(self, supplier_data: SupplierCreate) -> SupplierResponse:
        """Create a new supplier."""
        # Check if supplier code already exists
        existing = await self.repository.get_supplier_by_code(supplier_data.supplier_code)
        if existing:
            raise ValidationError(f"Supplier code '{supplier_data.supplier_code}' already exists")
        
        # Create domain entity to validate business rules
        try:
            entity = SupplierEntity(
                supplier_code=supplier_data.supplier_code,
                company_name=supplier_data.company_name,
                supplier_type=supplier_data.supplier_type,
                contact_person=supplier_data.contact_person,
                email=supplier_data.email,
                phone=supplier_data.phone,
                address=supplier_data.address,
                tax_id=supplier_data.tax_id,
                payment_terms=supplier_data.payment_terms,
                credit_limit=supplier_data.credit_limit,
                supplier_tier=supplier_data.supplier_tier,
                created_by=supplier_data.created_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Convert to dict for database creation
        create_data = self._entity_to_dict(entity)
        
        # Create in database
        supplier_model = await self.repository.create_supplier(create_data)
        
        return SupplierResponse.model_validate(supplier_model)
    
    async def get_supplier_by_id(self, supplier_id: UUID) -> SupplierResponse:
        """Get supplier by ID."""
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        return SupplierResponse.model_validate(supplier)
    
    async def get_supplier_by_code(self, supplier_code: str) -> SupplierResponse:
        """Get supplier by supplier code."""
        supplier = await self.repository.get_supplier_by_code(supplier_code)
        if not supplier:
            raise NotFoundError(f"Supplier with code '{supplier_code}' not found")
        
        return SupplierResponse.model_validate(supplier)
    
    async def get_suppliers(
        self,
        page: int = 1,
        page_size: int = 50,
        supplier_type: Optional[SupplierType] = None,
        supplier_tier: Optional[SupplierTier] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> SupplierListResponse:
        """Get suppliers with filtering and pagination."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        if page_size > 100:
            page_size = 100
        
        skip = (page - 1) * page_size
        
        # Get suppliers and total count
        suppliers = await self.repository.get_suppliers(
            skip=skip,
            limit=page_size,
            supplier_type=supplier_type,
            supplier_tier=supplier_tier,
            is_active=is_active,
            search=search
        )
        
        total = await self.repository.count_suppliers(
            supplier_type=supplier_type,
            supplier_tier=supplier_tier,
            is_active=is_active,
            search=search
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return SupplierListResponse(
            suppliers=[SupplierResponse.model_validate(sup) for sup in suppliers],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_supplier(self, supplier_id: UUID, update_data: SupplierUpdate) -> SupplierResponse:
        """Update supplier business information."""
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        # Convert to domain entity for validation
        entity = self._model_to_entity(supplier)
        
        # Update entity using domain method
        try:
            entity.update_business_info(
                company_name=update_data.company_name,
                tax_id=update_data.tax_id,
                supplier_type=update_data.supplier_type,
                updated_by=update_data.updated_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Prepare update data for database
        update_dict = {}
        if update_data.company_name is not None:
            update_dict['company_name'] = entity.company_name
        if update_data.tax_id is not None:
            update_dict['tax_id'] = entity.tax_id
        if update_data.supplier_type is not None:
            update_dict['supplier_type'] = entity.supplier_type
        
        update_dict['updated_at'] = entity.updated_at
        if update_data.updated_by:
            update_dict['updated_by'] = update_data.updated_by
        
        # Update in database
        updated_supplier = await self.repository.update_supplier(supplier_id, update_dict)
        
        return SupplierResponse.model_validate(updated_supplier)
    
    async def update_contact_info(self, supplier_id: UUID, contact_data: SupplierContactUpdate) -> SupplierResponse:
        """Update supplier contact information."""
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        # Convert to domain entity for validation
        entity = self._model_to_entity(supplier)
        
        # Update entity using domain method
        try:
            entity.update_contact_info(
                contact_person=contact_data.contact_person,
                email=contact_data.email,
                phone=contact_data.phone,
                address=contact_data.address,
                updated_by=contact_data.updated_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Update in database
        update_dict = {
            'contact_person': entity.contact_person,
            'email': entity.email,
            'phone': entity.phone,
            'address': entity.address,
            'updated_at': entity.updated_at
        }
        if contact_data.updated_by:
            update_dict['updated_by'] = contact_data.updated_by
        
        updated_supplier = await self.repository.update_supplier(supplier_id, update_dict)
        
        return SupplierResponse.model_validate(updated_supplier)
    
    async def update_payment_terms(self, supplier_id: UUID, payment_data: SupplierPaymentUpdate) -> SupplierResponse:
        """Update supplier payment terms and credit limit."""
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        # Convert to domain entity for validation
        entity = self._model_to_entity(supplier)
        
        # Update entity using domain method
        try:
            entity.update_payment_terms(
                payment_terms=payment_data.payment_terms,
                credit_limit=payment_data.credit_limit,
                updated_by=payment_data.updated_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Update in database
        update_dict = {
            'payment_terms': entity.payment_terms,
            'credit_limit': entity.credit_limit,
            'updated_at': entity.updated_at
        }
        if payment_data.updated_by:
            update_dict['updated_by'] = payment_data.updated_by
        
        updated_supplier = await self.repository.update_supplier(supplier_id, update_dict)
        
        return SupplierResponse.model_validate(updated_supplier)
    
    async def update_tier(self, supplier_id: UUID, tier_data: SupplierTierUpdate) -> SupplierResponse:
        """Update supplier tier."""
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        # Convert to domain entity
        entity = self._model_to_entity(supplier)
        
        # Update entity using domain method
        entity.update_tier(tier_data.supplier_tier, tier_data.updated_by)
        
        # Update in database
        update_dict = {
            'supplier_tier': entity.supplier_tier,
            'updated_at': entity.updated_at
        }
        if tier_data.updated_by:
            update_dict['updated_by'] = tier_data.updated_by
        
        updated_supplier = await self.repository.update_supplier(supplier_id, update_dict)
        
        return SupplierResponse.model_validate(updated_supplier)
    
    async def update_status(self, supplier_id: UUID, status_data: SupplierStatusUpdate) -> SupplierResponse:
        """Update supplier status (activate/deactivate)."""
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        # Convert to domain entity
        entity = self._model_to_entity(supplier)
        
        # Update entity using domain method
        if status_data.is_active:
            entity.activate(status_data.updated_by)
        else:
            entity.deactivate(status_data.updated_by)
        
        # Update in database
        update_dict = {
            'is_active': entity.is_active,
            'updated_at': entity.updated_at
        }
        if status_data.updated_by:
            update_dict['updated_by'] = status_data.updated_by
        
        updated_supplier = await self.repository.update_supplier(supplier_id, update_dict)
        
        return SupplierResponse.model_validate(updated_supplier)
    
    async def update_performance_metrics(self, supplier_id: UUID, performance_data: SupplierPerformanceUpdate) -> SupplierResponse:
        """Update supplier performance metrics."""
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        # Convert to domain entity
        entity = self._model_to_entity(supplier)
        
        # Update entity using domain method
        try:
            entity.update_performance_metrics(
                total_orders=performance_data.total_orders,
                total_spend=performance_data.total_spend,
                average_delivery_days=performance_data.average_delivery_days,
                quality_rating=performance_data.quality_rating,
                last_order_date=performance_data.last_order_date
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Update in database
        update_dict = {
            'total_orders': entity.total_orders,
            'total_spend': entity.total_spend,
            'average_delivery_days': entity.average_delivery_days,
            'quality_rating': entity.quality_rating,
            'last_order_date': entity.last_order_date
        }
        
        updated_supplier = await self.repository.update_supplier(supplier_id, update_dict)
        
        return SupplierResponse.model_validate(updated_supplier)
    
    async def delete_supplier(self, supplier_id: UUID) -> bool:
        """Delete supplier."""
        supplier = await self.repository.get_supplier_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        return await self.repository.delete_supplier(supplier_id)
    
    async def get_suppliers_by_type(self, supplier_type: SupplierType) -> List[SupplierResponse]:
        """Get all suppliers of a specific type."""
        suppliers = await self.repository.get_suppliers_by_type(supplier_type)
        return [SupplierResponse.model_validate(sup) for sup in suppliers]
    
    async def get_suppliers_by_tier(self, supplier_tier: SupplierTier) -> List[SupplierResponse]:
        """Get all suppliers of a specific tier."""
        suppliers = await self.repository.get_suppliers_by_tier(supplier_tier)
        return [SupplierResponse.model_validate(sup) for sup in suppliers]
    
    async def get_top_suppliers_by_spend(self, limit: int = 10) -> List[SupplierResponse]:
        """Get top suppliers by total spend."""
        suppliers = await self.repository.get_top_suppliers_by_spend(limit)
        return [SupplierResponse.model_validate(sup) for sup in suppliers]
    
    async def get_supplier_performance_metrics(self) -> List[SupplierPerformanceResponse]:
        """Get performance metrics for all active suppliers."""
        metrics = await self.repository.get_supplier_performance_metrics()
        
        return [
            SupplierPerformanceResponse(
                supplier_id=metric['supplier_id'],
                supplier_code=metric['supplier_code'],
                company_name=metric['company_name'],
                total_orders=metric['total_orders'],
                total_spend=metric['total_spend'],
                average_delivery_days=metric['average_delivery_days'],
                quality_rating=metric['quality_rating'],
                last_order_date=metric['last_order_date'],
                supplier_tier=metric['supplier_tier'],
                performance_score=self._calculate_performance_score(metric)
            )
            for metric in metrics
        ]
    
    def _calculate_performance_score(self, metric: dict) -> Decimal:
        """Calculate performance score for a supplier metric."""
        if metric['total_orders'] == 0:
            return Decimal('0')
            
        # Weighted scoring: Quality (40%), Delivery (30%), Tier (30%)
        quality_score = (metric['quality_rating'] / 5) * 40
        
        # Delivery score (inverse of delivery days, capped at 30 days)
        delivery_score = max(0, (30 - min(metric['average_delivery_days'], 30)) / 30) * 30
        
        # Tier score
        tier_scores = {
            SupplierTier.PREFERRED: 30,
            SupplierTier.STANDARD: 20,
            SupplierTier.RESTRICTED: 10
        }
        tier_score = tier_scores.get(metric['supplier_tier'], 15)
        
        return quality_score + Decimal(str(delivery_score)) + Decimal(str(tier_score))