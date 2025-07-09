from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.item import Item
from src.domain.repositories.item_repository import ItemRepository
from src.infrastructure.models.item_model import ItemModel
from src.infrastructure.models.category_model import CategoryModel
from src.infrastructure.models.brand_model import BrandModel
from .base import SQLAlchemyRepository


class ItemRepositoryImpl(SQLAlchemyRepository[Item, ItemModel], ItemRepository):
    """Implementation of ItemRepository using SQLAlchemy."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ItemModel, Item)
    
    def _to_entity(self, model: ItemModel) -> Item:
        """Convert SQLAlchemy model to domain entity."""
        return Item(
            item_id=model.item_id,
            sku=model.sku,
            item_name=model.item_name,
            category_id=model.category_id,
            brand_id=model.brand_id,
            description=model.description,
            is_serialized=model.is_serialized,
            barcode=model.barcode,
            model_number=model.model_number,
            weight=model.weight,
            dimensions=model.dimensions,
            is_rentable=model.is_rentable,
            is_saleable=model.is_saleable,
            min_rental_days=model.min_rental_days,
            rental_period=model.rental_period,
            max_rental_days=model.max_rental_days,
            rental_base_price=model.rental_base_price,
            sale_base_price=model.sale_base_price,
            is_active=model.is_active,
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
    
    def _to_model(self, entity: Item) -> ItemModel:
        """Convert domain entity to SQLAlchemy model."""
        # Convert dimensions with Decimal values to float for JSON serialization
        dimensions = None
        if entity.dimensions:
            dimensions = {k: float(v) if isinstance(v, Decimal) else v 
                         for k, v in entity.dimensions.items()}
        
        return ItemModel(
            id=entity.id,
            item_id=entity.item_id,
            sku=entity.sku,
            item_name=entity.item_name,
            category_id=entity.category_id,
            brand_id=entity.brand_id,
            description=entity.description,
            is_serialized=entity.is_serialized,
            barcode=entity.barcode,
            model_number=entity.model_number,
            weight=entity.weight,
            dimensions=dimensions,
            is_rentable=entity.is_rentable,
            is_saleable=entity.is_saleable,
            min_rental_days=entity.min_rental_days,
            rental_period=entity.rental_period,
            max_rental_days=entity.max_rental_days,
            rental_base_price=entity.rental_base_price,
            sale_base_price=entity.sale_base_price,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )
    
    async def get_by_item_id(self, item_id: UUID) -> Optional[Item]:
        """Get item by item_id."""
        query = select(self.model).filter(self.model.item_id == item_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_sku(self, sku: str) -> Optional[Item]:
        """Get item by SKU."""
        query = select(self.model).filter(
            func.lower(self.model.sku) == func.lower(sku),
            self.model.is_active == True
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_barcode(self, barcode: str) -> Optional[Item]:
        """Get item by barcode."""
        query = select(self.model).filter(
            self.model.barcode == barcode,
            self.model.is_active == True
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_category_id(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items by category."""
        query = select(self.model).filter(
            self.model.category_id == category_id,
            self.model.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_by_brand_id(self, brand_id: UUID, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items by brand."""
        query = select(self.model).filter(
            self.model.brand_id == brand_id,
            self.model.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_rentable_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items that can be rented."""
        query = select(self.model).filter(
            self.model.is_rentable == True,
            self.model.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_saleable_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get items that can be sold."""
        query = select(self.model).filter(
            self.model.is_saleable == True,
            self.model.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def search_by_name(self, name_pattern: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """Search items by name pattern."""
        query = select(self.model).filter(
            func.lower(self.model.item_name).contains(func.lower(name_pattern)),
            self.model.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def search_by_sku(self, sku_pattern: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """Search items by SKU pattern."""
        query = select(self.model).filter(
            func.lower(self.model.sku).contains(func.lower(sku_pattern)),
            self.model.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_all_with_relations(self, skip: int = 0, limit: int = 100, 
                                     category_id: Optional[UUID] = None,
                                     brand_id: Optional[UUID] = None,
                                     is_rentable: Optional[bool] = None,
                                     is_saleable: Optional[bool] = None) -> List[ItemModel]:
        """Get all active items with category and brand relationships loaded."""
        query = select(self.model).options(
            selectinload(self.model.category),
            selectinload(self.model.brand)
        ).filter(
            self.model.is_active == True
        )
        
        # Apply filters
        if category_id:
            query = query.filter(self.model.category_id == category_id)
        if brand_id:
            query = query.filter(self.model.brand_id == brand_id)
        if is_rentable is not None:
            query = query.filter(self.model.is_rentable == is_rentable)
        if is_saleable is not None:
            query = query.filter(self.model.is_saleable == is_saleable)
            
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rentable_items_with_search(
        self, 
        search: Optional[str] = None, 
        category_id: Optional[UUID] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Item]:
        """Get rentable items with optional search and category filter."""
        query = select(self.model).filter(
            self.model.is_rentable == True,
            self.model.is_active == True
        )
        
        # Apply search filter if provided
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(self.model.item_name).like(search_pattern),
                    func.lower(self.model.sku).like(search_pattern)
                )
            )
        
        # Apply category filter if provided
        if category_id:
            query = query.filter(self.model.category_id == category_id)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def count_rentable_items(
        self, 
        search: Optional[str] = None, 
        category_id: Optional[UUID] = None
    ) -> int:
        """Count rentable items with optional search and category filter."""
        query = select(func.count(self.model.id)).filter(
            self.model.is_rentable == True,
            self.model.is_active == True
        )
        
        # Apply search filter if provided
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(self.model.item_name).like(search_pattern),
                    func.lower(self.model.sku).like(search_pattern)
                )
            )
        
        # Apply category filter if provided
        if category_id:
            query = query.filter(self.model.category_id == category_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0