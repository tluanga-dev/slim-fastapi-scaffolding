from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.modules.suppliers.models import Supplier
from app.core.domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms


class SupplierRepository:
    """Repository for supplier data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_supplier(self, supplier_data: dict) -> Supplier:
        """Create a new supplier."""
        supplier = Supplier(**supplier_data)
        self.session.add(supplier)
        await self.session.commit()
        await self.session.refresh(supplier)
        return supplier
    
    async def get_supplier_by_id(self, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID."""
        result = await self.session.execute(
            select(Supplier).filter(Supplier.id == supplier_id)
        )
        return result.scalars().first()
    
    async def get_supplier_by_code(self, supplier_code: str) -> Optional[Supplier]:
        """Get supplier by supplier code."""
        result = await self.session.execute(
            select(Supplier).filter(Supplier.supplier_code == supplier_code)
        )
        return result.scalars().first()
    
    async def get_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_type: Optional[SupplierType] = None,
        supplier_tier: Optional[SupplierTier] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Supplier]:
        """Get suppliers with optional filtering."""
        query = select(Supplier)
        
        # Apply filters
        conditions = []
        
        if supplier_type:
            conditions.append(Supplier.supplier_type == supplier_type)
        
        if supplier_tier:
            conditions.append(Supplier.supplier_tier == supplier_tier)
        
        if is_active is not None:
            conditions.append(Supplier.is_active == is_active)
        
        if search:
            search_conditions = [
                Supplier.company_name.ilike(f"%{search}%"),
                Supplier.supplier_code.ilike(f"%{search}%"),
                Supplier.contact_person.ilike(f"%{search}%"),
                Supplier.email.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        query = query.order_by(Supplier.company_name).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_suppliers(
        self,
        supplier_type: Optional[SupplierType] = None,
        supplier_tier: Optional[SupplierTier] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """Count suppliers with optional filtering."""
        query = select(func.count(Supplier.id))
        
        # Apply same filters as get_suppliers
        conditions = []
        
        if supplier_type:
            conditions.append(Supplier.supplier_type == supplier_type)
        
        if supplier_tier:
            conditions.append(Supplier.supplier_tier == supplier_tier)
        
        if is_active is not None:
            conditions.append(Supplier.is_active == is_active)
        
        if search:
            search_conditions = [
                Supplier.company_name.ilike(f"%{search}%"),
                Supplier.supplier_code.ilike(f"%{search}%"),
                Supplier.contact_person.ilike(f"%{search}%"),
                Supplier.email.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def update_supplier(self, supplier_id: UUID, update_data: dict) -> Optional[Supplier]:
        """Update supplier by ID."""
        supplier = await self.get_supplier_by_id(supplier_id)
        if not supplier:
            return None
        
        for key, value in update_data.items():
            if hasattr(supplier, key):
                setattr(supplier, key, value)
        
        await self.session.commit()
        await self.session.refresh(supplier)
        return supplier
    
    async def delete_supplier(self, supplier_id: UUID) -> bool:
        """Delete supplier by ID (hard delete)."""
        supplier = await self.get_supplier_by_id(supplier_id)
        if not supplier:
            return False
        
        await self.session.delete(supplier)
        await self.session.commit()
        return True
    
    async def get_suppliers_by_type(self, supplier_type: SupplierType) -> List[Supplier]:
        """Get all suppliers of a specific type."""
        result = await self.session.execute(
            select(Supplier).filter(
                and_(
                    Supplier.supplier_type == supplier_type,
                    Supplier.is_active == True
                )
            ).order_by(Supplier.company_name)
        )
        return result.scalars().all()
    
    async def get_suppliers_by_tier(self, supplier_tier: SupplierTier) -> List[Supplier]:
        """Get all suppliers of a specific tier."""
        result = await self.session.execute(
            select(Supplier).filter(
                and_(
                    Supplier.supplier_tier == supplier_tier,
                    Supplier.is_active == True
                )
            ).order_by(Supplier.company_name)
        )
        return result.scalars().all()
    
    async def get_suppliers_by_payment_terms(self, payment_terms: PaymentTerms) -> List[Supplier]:
        """Get all suppliers with specific payment terms."""
        result = await self.session.execute(
            select(Supplier).filter(
                and_(
                    Supplier.payment_terms == payment_terms,
                    Supplier.is_active == True
                )
            ).order_by(Supplier.company_name)
        )
        return result.scalars().all()
    
    async def get_top_suppliers_by_spend(self, limit: int = 10) -> List[Supplier]:
        """Get top suppliers by total spend."""
        result = await self.session.execute(
            select(Supplier).filter(
                Supplier.is_active == True
            ).order_by(Supplier.total_spend.desc()).limit(limit)
        )
        return result.scalars().all()
    
    async def get_suppliers_with_credit_limit_above(self, amount: Decimal) -> List[Supplier]:
        """Get suppliers with credit limit above specified amount."""
        result = await self.session.execute(
            select(Supplier).filter(
                and_(
                    Supplier.credit_limit >= amount,
                    Supplier.is_active == True
                )
            ).order_by(Supplier.credit_limit.desc())
        )
        return result.scalars().all()
    
    async def get_suppliers_by_quality_rating(self, min_rating: Decimal) -> List[Supplier]:
        """Get suppliers with quality rating above minimum threshold."""
        result = await self.session.execute(
            select(Supplier).filter(
                and_(
                    Supplier.quality_rating >= min_rating,
                    Supplier.is_active == True
                )
            ).order_by(Supplier.quality_rating.desc())
        )
        return result.scalars().all()
    
    async def supplier_code_exists(self, supplier_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if supplier code already exists."""
        query = select(Supplier).filter(Supplier.supplier_code == supplier_code)
        
        if exclude_id:
            query = query.filter(Supplier.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None
    
    async def get_supplier_performance_metrics(self) -> List[dict]:
        """Get performance metrics for all active suppliers."""
        result = await self.session.execute(
            select(
                Supplier.id,
                Supplier.supplier_code,
                Supplier.company_name,
                Supplier.total_orders,
                Supplier.total_spend,
                Supplier.average_delivery_days,
                Supplier.quality_rating,
                Supplier.last_order_date,
                Supplier.supplier_tier
            ).filter(Supplier.is_active == True)
            .order_by(Supplier.total_spend.desc())
        )
        
        return [
            {
                'supplier_id': row.id,
                'supplier_code': row.supplier_code,
                'company_name': row.company_name,
                'total_orders': row.total_orders,
                'total_spend': row.total_spend,
                'average_delivery_days': row.average_delivery_days,
                'quality_rating': row.quality_rating,
                'last_order_date': row.last_order_date,
                'supplier_tier': row.supplier_tier
            }
            for row in result
        ]