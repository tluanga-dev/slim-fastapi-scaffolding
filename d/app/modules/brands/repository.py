from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.modules.brands.models import BrandModel


class BrandRepository:
    """Repository for brand data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_brand(self, brand_data: dict) -> BrandModel:
        """Create a new brand."""
        brand = BrandModel(**brand_data)
        self.session.add(brand)
        await self.session.commit()
        await self.session.refresh(brand)
        return brand
    
    async def get_brand_by_id(self, brand_id: UUID) -> Optional[BrandModel]:
        """Get brand by ID."""
        result = await self.session.execute(
            select(BrandModel).filter(BrandModel.id == brand_id)
        )
        return result.scalars().first()
    
    async def get_brand_by_name(self, brand_name: str) -> Optional[BrandModel]:
        """Get brand by name (case-insensitive)."""
        result = await self.session.execute(
            select(BrandModel).filter(BrandModel.brand_name.ilike(brand_name))
        )
        return result.scalars().first()
    
    async def get_brand_by_code(self, brand_code: str) -> Optional[BrandModel]:
        """Get brand by brand code (case-insensitive)."""
        result = await self.session.execute(
            select(BrandModel).filter(BrandModel.brand_code.ilike(brand_code))
        )
        return result.scalars().first()
    
    async def get_brands(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "brand_name",
        sort_order: str = "asc"
    ) -> List[BrandModel]:
        """Get brands with optional filtering and sorting."""
        query = select(BrandModel)
        
        # Apply filters
        conditions = []
        
        if is_active is not None:
            conditions.append(BrandModel.is_active == is_active)
        
        if search:
            search_conditions = [
                BrandModel.brand_name.ilike(f"%{search}%"),
                BrandModel.brand_code.ilike(f"%{search}%"),
                BrandModel.description.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Apply sorting
        if hasattr(BrandModel, sort_by):
            sort_column = getattr(BrandModel, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(BrandModel.brand_name.asc())
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_brands(
        self,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """Count brands with optional filtering."""
        query = select(func.count(BrandModel.id))
        
        # Apply same filters as get_brands
        conditions = []
        
        if is_active is not None:
            conditions.append(BrandModel.is_active == is_active)
        
        if search:
            search_conditions = [
                BrandModel.brand_name.ilike(f"%{search}%"),
                BrandModel.brand_code.ilike(f"%{search}%"),
                BrandModel.description.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def update_brand(self, brand_id: UUID, update_data: dict) -> Optional[BrandModel]:
        """Update brand by ID."""
        brand = await self.get_brand_by_id(brand_id)
        if not brand:
            return None
        
        for key, value in update_data.items():
            if hasattr(brand, key):
                setattr(brand, key, value)
        
        await self.session.commit()
        await self.session.refresh(brand)
        return brand
    
    async def delete_brand(self, brand_id: UUID) -> bool:
        """Delete brand by ID (hard delete)."""
        brand = await self.get_brand_by_id(brand_id)
        if not brand:
            return False
        
        await self.session.delete(brand)
        await self.session.commit()
        return True
    
    async def soft_delete_brand(self, brand_id: UUID, deleted_by: Optional[str] = None) -> Optional[BrandModel]:
        """Soft delete brand by ID."""
        update_data = {
            'is_active': False,
            'updated_by': deleted_by
        }
        return await self.update_brand(brand_id, update_data)
    
    async def get_active_brands(self) -> List[BrandModel]:
        """Get all active brands ordered by name."""
        result = await self.session.execute(
            select(BrandModel).filter(
                BrandModel.is_active == True
            ).order_by(BrandModel.brand_name.asc())
        )
        return result.scalars().all()
    
    async def brand_name_exists(self, brand_name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if brand name already exists (case-insensitive)."""
        query = select(BrandModel).filter(BrandModel.brand_name.ilike(brand_name))
        
        if exclude_id:
            query = query.filter(BrandModel.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None
    
    async def brand_code_exists(self, brand_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if brand code already exists (case-insensitive)."""
        if not brand_code:
            return False
            
        query = select(BrandModel).filter(BrandModel.brand_code.ilike(brand_code))
        
        if exclude_id:
            query = query.filter(BrandModel.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalars().first() is not None
    
    async def search_brands(self, search_term: str, limit: int = 20) -> List[BrandModel]:
        """Search brands by name or code."""
        search_conditions = [
            BrandModel.brand_name.ilike(f"%{search_term}%"),
            BrandModel.brand_code.ilike(f"%{search_term}%")
        ]
        
        result = await self.session.execute(
            select(BrandModel).filter(
                and_(
                    BrandModel.is_active == True,
                    or_(*search_conditions)
                )
            ).order_by(BrandModel.brand_name.asc()).limit(limit)
        )
        return result.scalars().all()
    
    async def get_brands_by_prefix(self, prefix: str, limit: int = 10) -> List[BrandModel]:
        """Get brands that start with the given prefix."""
        result = await self.session.execute(
            select(BrandModel).filter(
                and_(
                    BrandModel.is_active == True,
                    or_(
                        BrandModel.brand_name.ilike(f"{prefix}%"),
                        BrandModel.brand_code.ilike(f"{prefix}%")
                    )
                )
            ).order_by(BrandModel.brand_name.asc()).limit(limit)
        )
        return result.scalars().all()