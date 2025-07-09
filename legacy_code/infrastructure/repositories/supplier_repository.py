from typing import List, Optional, Tuple
from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, desc
from sqlalchemy.orm import selectinload

from ...domain.entities.supplier import Supplier
from ...domain.repositories.supplier_repository import SupplierRepository as ISupplierRepository
from ...domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms
from ..models.supplier_model import SupplierModel


class SQLAlchemySupplierRepository(ISupplierRepository):
    """SQLAlchemy implementation of supplier repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, supplier: Supplier) -> Supplier:
        """Create a new supplier."""
        model = SupplierModel.from_entity(supplier)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def get_by_id(self, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID with real-time purchase transaction metrics."""
        from ..models.transaction_header_model import TransactionHeaderModel
        from ...domain.value_objects.transaction_type import TransactionType
        
        stmt = select(SupplierModel).where(
            and_(SupplierModel.id == supplier_id, SupplierModel.is_active == True)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
            
        # Get real purchase transaction metrics for this supplier
        # Note: In current architecture, suppliers are stored as customer_id in PURCHASE transactions
        purchase_metrics = await self.session.execute(
            select(
                func.count(TransactionHeaderModel.id).label('total_orders'),
                func.coalesce(func.sum(TransactionHeaderModel.total_amount), 0).label('total_spend'),
                func.max(TransactionHeaderModel.transaction_date).label('last_order_date')
            )
            .where(
                and_(
                    TransactionHeaderModel.customer_id == supplier_id,
                    TransactionHeaderModel.transaction_type == TransactionType.PURCHASE,
                    TransactionHeaderModel.is_active == True
                )
            )
        )
        
        metrics = purchase_metrics.fetchone()
        total_orders = int(metrics.total_orders or 0)
        total_spend = float(metrics.total_spend or 0)
        last_order_date = metrics.last_order_date
        
        # Create entity with updated metrics
        supplier = model.to_entity()
        
        # Update the supplier with real transaction data
        supplier._total_orders = total_orders
        supplier._total_spend = total_spend
        supplier._last_order_date = last_order_date
        
        return supplier

    async def get_by_code(self, supplier_code: str) -> Optional[Supplier]:
        """Get supplier by supplier code."""
        stmt = select(SupplierModel).where(
            and_(SupplierModel.supplier_code == supplier_code, SupplierModel.is_active == True)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def update(self, supplier: Supplier) -> Supplier:
        """Update an existing supplier."""
        stmt = select(SupplierModel).where(SupplierModel.id == supplier.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Supplier with id {supplier.id} not found")
        
        model.update_from_entity(supplier)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def delete(self, supplier_id: UUID) -> bool:
        """Soft delete a supplier."""
        stmt = select(SupplierModel).where(SupplierModel.id == supplier_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.is_active = False
        await self.session.flush()
        return True

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_type: Optional[SupplierType] = None,
        supplier_tier: Optional[SupplierTier] = None,
        payment_terms: Optional[PaymentTerms] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Supplier], int]:
        """List suppliers with pagination and filters."""
        # Build base query
        conditions = []
        
        if is_active is not None:
            conditions.append(SupplierModel.is_active == is_active)
        else:
            conditions.append(SupplierModel.is_active == True)
            
        if supplier_type:
            conditions.append(SupplierModel.supplier_type == supplier_type.value)
            
        if supplier_tier:
            conditions.append(SupplierModel.supplier_tier == supplier_tier.value)
            
        if payment_terms:
            conditions.append(SupplierModel.payment_terms == payment_terms.value)
            
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    SupplierModel.company_name.ilike(search_pattern),
                    SupplierModel.supplier_code.ilike(search_pattern),
                    SupplierModel.contact_person.ilike(search_pattern),
                    SupplierModel.email.ilike(search_pattern)
                )
            )

        # Count query
        count_stmt = select(func.count(SupplierModel.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Data query
        stmt = (
            select(SupplierModel)
            .where(and_(*conditions))
            .order_by(SupplierModel.company_name)
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        suppliers = [model.to_entity() for model in models]
        
        return suppliers, total

    async def search_by_name(self, name: str, limit: int = 10) -> List[Supplier]:
        """Search suppliers by company name."""
        search_pattern = f"%{name}%"
        stmt = (
            select(SupplierModel)
            .where(
                and_(
                    SupplierModel.is_active == True,
                    SupplierModel.company_name.ilike(search_pattern)
                )
            )
            .order_by(SupplierModel.company_name)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [model.to_entity() for model in models]

    async def get_by_tier(
        self, 
        tier: SupplierTier, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Supplier], int]:
        """Get suppliers by tier."""
        return await self.list(
            skip=skip,
            limit=limit,
            supplier_tier=tier,
            is_active=True
        )

    async def get_active_suppliers(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Supplier], int]:
        """Get all active suppliers."""
        return await self.list(skip=skip, limit=limit, is_active=True)

    async def get_top_suppliers_by_spend(self, limit: int = 10) -> List[Supplier]:
        """Get top suppliers by total spend."""
        stmt = (
            select(SupplierModel)
            .where(SupplierModel.is_active == True)
            .order_by(desc(SupplierModel.total_spend))
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [model.to_entity() for model in models]

    async def supplier_code_exists(self, supplier_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if supplier code already exists."""
        conditions = [SupplierModel.supplier_code == supplier_code]
        
        if exclude_id:
            conditions.append(SupplierModel.id != exclude_id)
            
        stmt = select(func.count(SupplierModel.id)).where(and_(*conditions))
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def company_name_exists(self, company_name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if company name already exists."""
        conditions = [
            SupplierModel.company_name == company_name,
            SupplierModel.is_active == True
        ]
        
        if exclude_id:
            conditions.append(SupplierModel.id != exclude_id)
            
        stmt = select(func.count(SupplierModel.id)).where(and_(*conditions))
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0

    async def get_supplier_analytics(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> dict:
        """Get supplier analytics data."""
        from ..models.transaction_header_model import TransactionHeaderModel
        from ...domain.value_objects.transaction_type import TransactionType
        
        # Total suppliers
        total_result = await self.session.execute(
            select(func.count(SupplierModel.id)).where(SupplierModel.is_active == True)
        )
        total_suppliers = total_result.scalar() or 0

        # Active suppliers - those who appear as customer_id in PURCHASE transactions
        # (Note: In current architecture, purchase transactions use customer_id to store supplier_id)
        purchase_conditions = [
            TransactionHeaderModel.transaction_type == TransactionType.PURCHASE,
            TransactionHeaderModel.is_active == True
        ]
        
        if start_date and end_date:
            from datetime import datetime
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            purchase_conditions.extend([
                TransactionHeaderModel.transaction_date >= start_dt,
                TransactionHeaderModel.transaction_date <= end_dt
            ])
        else:
            # Default: last 6 months
            purchase_conditions.append(
                TransactionHeaderModel.transaction_date >= text("date('now', '-6 months')")
            )
        
        active_suppliers_with_purchases = await self.session.execute(
            select(func.count(func.distinct(TransactionHeaderModel.customer_id)))
            .where(and_(*purchase_conditions))
        )
        active_suppliers = active_suppliers_with_purchases.scalar() or 0

        # Supplier type distribution
        type_result = await self.session.execute(
            select(SupplierModel.supplier_type, func.count(SupplierModel.id))
            .where(SupplierModel.is_active == True)
            .group_by(SupplierModel.supplier_type)
        )
        
        type_distribution = {}
        for supplier_type, count in type_result.fetchall():
            type_distribution[supplier_type.lower()] = count

        # Supplier tier distribution
        tier_result = await self.session.execute(
            select(SupplierModel.supplier_tier, func.count(SupplierModel.id))
            .where(SupplierModel.is_active == True)
            .group_by(SupplierModel.supplier_tier)
        )
        
        tier_distribution = {}
        for tier, count in tier_result.fetchall():
            tier_distribution[tier.lower()] = count

        # Payment terms distribution
        terms_result = await self.session.execute(
            select(SupplierModel.payment_terms, func.count(SupplierModel.id))
            .where(SupplierModel.is_active == True)
            .group_by(SupplierModel.payment_terms)
        )
        
        payment_terms_distribution = {}
        for terms, count in terms_result.fetchall():
            payment_terms_distribution[terms.lower()] = count

        # Top suppliers by actual purchase transaction spend
        # Join suppliers with their purchase transactions to get real spending data
        purchase_spend_query = await self.session.execute(
            select(
                SupplierModel,
                func.coalesce(func.sum(TransactionHeaderModel.total_amount), 0).label('actual_spend'),
                func.count(TransactionHeaderModel.id).label('total_orders')
            )
            .outerjoin(
                TransactionHeaderModel,
                and_(
                    SupplierModel.id == TransactionHeaderModel.customer_id,
                    TransactionHeaderModel.transaction_type == TransactionType.PURCHASE,
                    TransactionHeaderModel.is_active == True
                )
            )
            .where(SupplierModel.is_active == True)
            .group_by(SupplierModel.id)
            .order_by(desc('actual_spend'))
            .limit(10)
        )
        
        top_suppliers = []
        for model, actual_spend, total_orders in purchase_spend_query.fetchall():
            supplier = model.to_entity()
            top_suppliers.append({
                "supplier": {
                    "id": str(supplier.id),
                    "supplier_code": supplier.supplier_code,
                    "company_name": supplier.company_name,
                    "supplier_type": supplier.supplier_type.value,
                    "supplier_tier": supplier.supplier_tier.value,
                    "total_spend": float(actual_spend or 0),
                    "total_orders": int(total_orders or 0),
                    "quality_rating": float(supplier.quality_rating)
                },
                "total_spend": float(actual_spend or 0)
            })

        # Monthly new suppliers - filter by date range if provided
        monthly_new = []
        
        # Determine date range for monthly data
        if start_date and end_date:
            # Custom date range - group by month within the range
            from datetime import datetime
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            # For custom ranges, we'll still show monthly breakdown
            month_result = await self.session.execute(
                select(
                    func.strftime('%Y-%m', SupplierModel.created_at).label('month'),
                    func.count(SupplierModel.id).label('count')
                )
                .where(
                    and_(
                        SupplierModel.created_at >= start_dt,
                        SupplierModel.created_at <= end_dt
                    )
                )
                .group_by(func.strftime('%Y-%m', SupplierModel.created_at))
                .order_by(func.strftime('%Y-%m', SupplierModel.created_at))
            )
            
            for month_str, count in month_result.fetchall():
                monthly_new.append({
                    "month": month_str,
                    "count": count
                })
        else:
            # Default: last 12 months - SQLite compatible
            for i in range(12):
                # SQLite: Get first day of month i months ago
                month_start = text(f"date('now', '-{i} months', 'start of month')")
                month_end = text(f"date('now', '-{i} months', 'start of month', '+1 month')")
                
                month_result = await self.session.execute(
                    select(func.count(SupplierModel.id))
                    .where(
                        and_(
                            SupplierModel.created_at >= month_start,
                            SupplierModel.created_at < month_end
                        )
                    )
                )
                count = month_result.scalar() or 0
                
                # Get month string
                month_str_result = await self.session.execute(
                    select(func.strftime('%Y-%m', month_start))
                )
                month_str = month_str_result.scalar()
                
                monthly_new.append({
                    "month": month_str,
                    "count": count
                })

            monthly_new.reverse()  # Show oldest first

        # Calculate total spend from all purchase transactions
        total_spend_result = await self.session.execute(
            select(func.coalesce(func.sum(TransactionHeaderModel.total_amount), 0))
            .where(
                and_(
                    TransactionHeaderModel.transaction_type == TransactionType.PURCHASE,
                    TransactionHeaderModel.is_active == True
                )
            )
        )
        total_spend = float(total_spend_result.scalar() or 0)
        
        # Calculate average quality rating from suppliers with purchase transactions
        avg_quality_result = await self.session.execute(
            select(func.avg(SupplierModel.quality_rating))
            .join(
                TransactionHeaderModel,
                and_(
                    SupplierModel.id == TransactionHeaderModel.customer_id,
                    TransactionHeaderModel.transaction_type == TransactionType.PURCHASE,
                    TransactionHeaderModel.is_active == True
                )
            )
            .where(SupplierModel.is_active == True)
        )
        average_quality_rating = float(avg_quality_result.scalar() or 0)

        return {
            "total_suppliers": total_suppliers,
            "active_suppliers": active_suppliers,
            "supplier_type_distribution": type_distribution,
            "supplier_tier_distribution": tier_distribution,
            "payment_terms_distribution": payment_terms_distribution,
            "monthly_new_suppliers": monthly_new,
            "top_suppliers_by_spend": top_suppliers,
            "total_spend": total_spend,
            "average_quality_rating": average_quality_rating
        }