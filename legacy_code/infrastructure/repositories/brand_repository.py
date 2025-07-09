from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.brand import Brand
from ...domain.repositories.brand_repository import BrandRepository
from ..models.brand_model import BrandModel


class SQLAlchemyBrandRepository(BrandRepository):
    """SQLAlchemy implementation of BrandRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, brand: Brand) -> Brand:
        """Create a new brand."""
        db_brand = BrandModel.from_entity(brand)
        self.session.add(db_brand)
        await self.session.commit()
        await self.session.refresh(db_brand)
        return db_brand.to_entity()
    
    async def get_by_id(self, brand_id: UUID) -> Optional[Brand]:
        """Get brand by ID."""
        query = select(BrandModel).where(BrandModel.id == brand_id)
        result = await self.session.execute(query)
        db_brand = result.scalar_one_or_none()
        
        if db_brand:
            return db_brand.to_entity()
        return None
    
    async def get_by_name(self, brand_name: str) -> Optional[Brand]:
        """Get brand by name."""
        query = select(BrandModel).where(BrandModel.brand_name == brand_name)
        result = await self.session.execute(query)
        db_brand = result.scalar_one_or_none()
        
        if db_brand:
            return db_brand.to_entity()
        return None
    
    async def get_by_code(self, brand_code: str) -> Optional[Brand]:
        """Get brand by code."""
        query = select(BrandModel).where(BrandModel.brand_code == brand_code)
        result = await self.session.execute(query)
        db_brand = result.scalar_one_or_none()
        
        if db_brand:
            return db_brand.to_entity()
        return None
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[Brand]:
        """List brands with optional search and filters."""
        query = select(BrandModel)
        
        # Apply active filter
        if is_active is not None:
            query = query.where(BrandModel.is_active == is_active)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    BrandModel.brand_name.ilike(search_term),
                    BrandModel.brand_code.ilike(search_term),
                    BrandModel.description.ilike(search_term)
                )
            )
        
        # Apply ordering, pagination
        query = query.order_by(BrandModel.brand_name).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        brands = result.scalars().all()
        
        return [brand.to_entity() for brand in brands]
    
    async def update(self, brand: Brand) -> Brand:
        """Update existing brand."""
        query = select(BrandModel).where(BrandModel.id == brand.id)
        result = await self.session.execute(query)
        db_brand = result.scalar_one_or_none()
        
        if not db_brand:
            raise ValueError(f"Brand with id {brand.id} not found")
        
        # Update fields
        db_brand.brand_name = brand.brand_name
        db_brand.brand_code = brand.brand_code
        db_brand.description = brand.description
        db_brand.updated_at = brand.updated_at
        db_brand.updated_by = brand.updated_by
        db_brand.is_active = brand.is_active
        
        await self.session.commit()
        await self.session.refresh(db_brand)
        
        return db_brand.to_entity()
    
    async def delete(self, brand_id: UUID) -> bool:
        """Soft delete brand by setting is_active to False."""
        query = select(BrandModel).where(BrandModel.id == brand_id)
        result = await self.session.execute(query)
        db_brand = result.scalar_one_or_none()
        
        if not db_brand:
            return False
        
        db_brand.is_active = False
        await self.session.commit()
        
        return True
    
    async def count(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> int:
        """Count brands matching filters."""
        query = select(func.count()).select_from(BrandModel)
        
        # Apply active filter
        if is_active is not None:
            query = query.where(BrandModel.is_active == is_active)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    BrandModel.brand_name.ilike(search_term),
                    BrandModel.brand_code.ilike(search_term),
                    BrandModel.description.ilike(search_term)
                )
            )
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def exists_by_name(self, brand_name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a brand with the given name exists."""
        query = select(func.count()).select_from(BrandModel).where(
            BrandModel.brand_name == brand_name
        )
        
        if exclude_id:
            query = query.where(BrandModel.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_code(self, brand_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a brand with the given code exists."""
        query = select(func.count()).select_from(BrandModel).where(
            BrandModel.brand_code == brand_code
        )
        
        if exclude_id:
            query = query.where(BrandModel.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def has_products(self, brand_id: UUID) -> bool:
        """Check if a brand has any products assigned to it."""
        # This will be implemented when Product entity is created
        # For now, return False
        return False