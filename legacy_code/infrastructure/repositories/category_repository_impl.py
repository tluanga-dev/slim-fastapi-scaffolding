from typing import List, Optional
from uuid import UUID
from sqlalchemy import and_, or_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.category import Category
from ...domain.repositories.category_repository import CategoryRepository
from ..models.category_model import CategoryModel


class SQLAlchemyCategoryRepository(CategoryRepository):
    """SQLAlchemy implementation of CategoryRepository."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db
    
    async def create(self, category: Category) -> Category:
        """Create a new category."""
        db_category = CategoryModel.from_entity(category)
        self.db.add(db_category)
        await self.db.commit()
        await self.db.refresh(db_category)
        return db_category.to_entity()
    
    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Get category by ID."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.id == category_id,
                CategoryModel.is_active == True
            )
        )
        result = await self.db.execute(query)
        db_category = result.scalar_one_or_none()
        return db_category.to_entity() if db_category else None
    
    async def get_by_name_and_parent(
        self, 
        category_name: str, 
        parent_category_id: Optional[UUID]
    ) -> Optional[Category]:
        """Get category by name and parent."""
        filters = [
            CategoryModel.category_name == category_name,
            CategoryModel.is_active == True
        ]
        
        if parent_category_id is None:
            filters.append(CategoryModel.parent_category_id.is_(None))
        else:
            filters.append(CategoryModel.parent_category_id == parent_category_id)
        
        query = select(CategoryModel).where(and_(*filters))
        result = await self.db.execute(query)
        db_category = result.scalar_one_or_none()
        
        return db_category.to_entity() if db_category else None
    
    async def get_children(self, parent_category_id: UUID) -> List[Category]:
        """Get all direct children of a category."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.parent_category_id == parent_category_id,
                CategoryModel.is_active == True
            )
        ).order_by(CategoryModel.display_order, CategoryModel.category_name)
        result = await self.db.execute(query)
        db_categories = result.scalars().all()
        
        return [db_category.to_entity() for db_category in db_categories]
    
    async def get_descendants(self, category_id: UUID) -> List[Category]:
        """Get all descendants of a category using path matching."""
        # First get the category to find its path
        query = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self.db.execute(query)
        parent = result.scalar_one_or_none()
        
        if not parent:
            return []
        
        # Find all categories whose path starts with parent's path
        query = select(CategoryModel).where(
            and_(
                CategoryModel.category_path.like(f"{parent.category_path}/%"),
                CategoryModel.is_active == True
            )
        ).order_by(CategoryModel.category_level, CategoryModel.display_order)
        result = await self.db.execute(query)
        db_categories = result.scalars().all()
        
        return [db_category.to_entity() for db_category in db_categories]
    
    async def get_ancestors(self, category_id: UUID) -> List[Category]:
        """Get all ancestors of a category."""
        # Get the category
        query = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        
        if not category or not category.parent_category_id:
            return []
        
        ancestors = []
        current_id = category.parent_category_id
        
        # Walk up the tree
        while current_id:
            query = select(CategoryModel).where(
                and_(
                    CategoryModel.id == current_id,
                    CategoryModel.is_active == True
                )
            )
            result = await self.db.execute(query)
            parent = result.scalar_one_or_none()
            
            if parent:
                ancestors.append(parent.to_entity())
                current_id = parent.parent_category_id
            else:
                break
        
        # Return in order from root to immediate parent
        return list(reversed(ancestors))
    
    async def get_root_categories(self) -> List[Category]:
        """Get all root categories."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.parent_category_id.is_(None),
                CategoryModel.is_active == True
            )
        ).order_by(CategoryModel.display_order, CategoryModel.category_name)
        result = await self.db.execute(query)
        db_categories = result.scalars().all()
        
        return [db_category.to_entity() for db_category in db_categories]
    
    async def get_leaf_categories(self) -> List[Category]:
        """Get all leaf categories."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.is_leaf == True,
                CategoryModel.is_active == True
            )
        ).order_by(CategoryModel.category_path)
        result = await self.db.execute(query)
        db_categories = result.scalars().all()
        
        return [db_category.to_entity() for db_category in db_categories]
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[UUID] = None,
        is_leaf: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> List[Category]:
        """List categories with optional filters."""
        query = select(CategoryModel)
        
        filters = []
        if is_active is not None:
            filters.append(CategoryModel.is_active == is_active)
        if parent_id is not None:
            filters.append(CategoryModel.parent_category_id == parent_id)
        if is_leaf is not None:
            filters.append(CategoryModel.is_leaf == is_leaf)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(
            CategoryModel.category_level,
            CategoryModel.display_order,
            CategoryModel.category_name
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        db_categories = result.scalars().all()
        
        return [db_category.to_entity() for db_category in db_categories]
    
    async def update(self, category: Category) -> Category:
        """Update existing category."""
        query = select(CategoryModel).where(CategoryModel.id == category.id)
        result = await self.db.execute(query)
        db_category = result.scalar_one_or_none()
        
        if not db_category:
            raise ValueError(f"Category with ID {category.id} not found")
        
        # Update all fields
        db_category.category_name = category.category_name
        db_category.parent_category_id = category.parent_category_id
        db_category.category_path = category.category_path
        db_category.category_level = category.category_level
        db_category.display_order = category.display_order
        db_category.is_leaf = category.is_leaf
        db_category.updated_at = category.updated_at
        db_category.updated_by = category.updated_by
        db_category.is_active = category.is_active
        
        await self.db.commit()
        await self.db.refresh(db_category)
        return db_category.to_entity()
    
    async def update_paths_for_descendants(
        self, 
        category_id: UUID, 
        old_path: str, 
        new_path: str
    ) -> int:
        """Update paths for all descendants when a category is renamed."""
        # Find all descendants
        query = select(CategoryModel).where(
            and_(
                CategoryModel.category_path.like(f"{old_path}/%"),
                CategoryModel.is_active == True
            )
        )
        result = await self.db.execute(query)
        descendants = result.scalars().all()
        
        count = 0
        for descendant in descendants:
            # Replace the old path prefix with new path
            descendant.category_path = descendant.category_path.replace(old_path, new_path, 1)
            count += 1
        
        if count > 0:
            await self.db.commit()
        
        return count
    
    async def delete(self, category_id: UUID) -> bool:
        """Soft delete category."""
        query = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self.db.execute(query)
        db_category = result.scalar_one_or_none()
        
        if not db_category:
            return False
        
        db_category.is_active = False
        await self.db.commit()
        return True
    
    async def count(
        self,
        parent_id: Optional[UUID] = None,
        is_leaf: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> int:
        """Count categories matching filters."""
        query = select(func.count()).select_from(CategoryModel)
        
        filters = []
        if is_active is not None:
            filters.append(CategoryModel.is_active == is_active)
        if parent_id is not None:
            filters.append(CategoryModel.parent_category_id == parent_id)
        if is_leaf is not None:
            filters.append(CategoryModel.is_leaf == is_leaf)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def has_children(self, category_id: UUID) -> bool:
        """Check if a category has any children."""
        query = select(func.count()).select_from(CategoryModel).where(
            and_(
                CategoryModel.parent_category_id == category_id,
                CategoryModel.is_active == True
            )
        )
        result = await self.db.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def has_products(self, category_id: UUID) -> bool:
        """Check if a category has any products assigned."""
        # This will be implemented when we have the Product model
        # For now, return False
        return False
    
    async def get_max_level(self) -> int:
        """Get the maximum category level in the hierarchy."""
        query = select(func.max(CategoryModel.category_level))
        result = await self.db.execute(query)
        max_level = result.scalar_one_or_none()
        return max_level or 0
    
    async def get_by_path(self, category_path: str) -> Optional[Category]:
        """Get category by its full path."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.category_path == category_path,
                CategoryModel.is_active == True
            )
        )
        result = await self.db.execute(query)
        db_category = result.scalar_one_or_none()
        
        return db_category.to_entity() if db_category else None