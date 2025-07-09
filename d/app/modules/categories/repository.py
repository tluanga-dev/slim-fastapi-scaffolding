from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.modules.categories.models import Category


class CategoryRepository:
    """Repository for category data access."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_category(self, category_data: dict) -> Category:
        """Create a new category."""
        # Set timestamps if not provided
        if 'created_at' not in category_data:
            category_data['created_at'] = datetime.utcnow()
        if 'updated_at' not in category_data:
            category_data['updated_at'] = datetime.utcnow()
            
        category = Category(**category_data)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def get_category(self, category_id: UUID) -> Optional[Category]:
        """Get a category by ID."""
        result = await self.session.execute(
            select(Category).filter(
                and_(Category.id == category_id, Category.is_active == True)
            )
        )
        return result.scalars().first()
    
    async def get_category_with_children(self, category_id: UUID) -> Optional[Category]:
        """Get a category with its children."""
        result = await self.session.execute(
            select(Category)
            .options(selectinload(Category.children))
            .filter(
                and_(Category.id == category_id, Category.is_active == True)
            )
        )
        return result.scalars().first()
    
    async def get_categories_by_parent(self, parent_id: Optional[UUID]) -> List[Category]:
        """Get all categories for a given parent."""
        query = select(Category).filter(Category.is_active == True)
        
        if parent_id is None:
            query = query.filter(Category.parent_category_id.is_(None))
        else:
            query = query.filter(Category.parent_category_id == parent_id)
            
        query = query.order_by(Category.display_order, Category.category_name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_root_categories(self) -> List[Category]:
        """Get all root categories."""
        return await self.get_categories_by_parent(None)
    
    async def get_category_by_path(self, path: str) -> Optional[Category]:
        """Get a category by its path."""
        result = await self.session.execute(
            select(Category).filter(
                and_(Category.category_path == path, Category.is_active == True)
            )
        )
        return result.scalars().first()
    
    async def get_categories_by_level(self, level: int) -> List[Category]:
        """Get all categories at a specific level."""
        result = await self.session.execute(
            select(Category).filter(
                and_(Category.category_level == level, Category.is_active == True)
            ).order_by(Category.display_order, Category.category_name)
        )
        return list(result.scalars().all())
    
    async def get_leaf_categories(self) -> List[Category]:
        """Get all leaf categories."""
        result = await self.session.execute(
            select(Category).filter(
                and_(Category.is_leaf == True, Category.is_active == True)
            ).order_by(Category.category_path)
        )
        return list(result.scalars().all())
    
    async def update_category(self, category_id: UUID, update_data: dict) -> Optional[Category]:
        """Update a category."""
        # Always update the timestamp
        update_data['updated_at'] = datetime.utcnow()
        
        result = await self.session.execute(
            update(Category)
            .where(and_(Category.id == category_id, Category.is_active == True))
            .values(**update_data)
            .returning(Category)
        )
        await self.session.commit()
        
        # Fetch the updated category
        return await self.get_category(category_id)
    
    async def update_category_paths(self, old_path_prefix: str, new_path_prefix: str) -> int:
        """Update all category paths that start with the old prefix."""
        # This is used when a parent category is renamed
        result = await self.session.execute(
            update(Category)
            .where(
                and_(
                    Category.category_path.startswith(old_path_prefix),
                    Category.is_active == True
                )
            )
            .values(
                category_path=func.replace(Category.category_path, old_path_prefix, new_path_prefix),
                updated_at=datetime.utcnow()
            )
        )
        await self.session.commit()
        return result.rowcount
    
    async def soft_delete_category(self, category_id: UUID, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a category."""
        update_data = {
            'is_active': False,
            'updated_at': datetime.utcnow()
        }
        if deleted_by:
            update_data['updated_by'] = deleted_by
            
        result = await self.session.execute(
            update(Category)
            .where(Category.id == category_id)
            .values(**update_data)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def count_children(self, category_id: UUID) -> int:
        """Count the number of active children for a category."""
        result = await self.session.execute(
            select(func.count(Category.id)).filter(
                and_(
                    Category.parent_category_id == category_id,
                    Category.is_active == True
                )
            )
        )
        return result.scalar() or 0
    
    async def exists_by_name_and_parent(self, name: str, parent_id: Optional[UUID]) -> bool:
        """Check if a category with the same name exists under the same parent."""
        query = select(Category).filter(
            and_(
                Category.category_name == name,
                Category.is_active == True
            )
        )
        
        if parent_id is None:
            query = query.filter(Category.parent_category_id.is_(None))
        else:
            query = query.filter(Category.parent_category_id == parent_id)
            
        result = await self.session.execute(query.limit(1))
        return result.scalars().first() is not None
    
    async def get_all_descendants(self, category_id: UUID) -> List[Category]:
        """Get all descendants of a category (children, grandchildren, etc.)."""
        # Get the parent category first
        parent = await self.get_category(category_id)
        if not parent:
            return []
        
        # Get all categories whose path starts with the parent's path
        result = await self.session.execute(
            select(Category).filter(
                and_(
                    Category.category_path.startswith(f"{parent.category_path}/"),
                    Category.is_active == True
                )
            ).order_by(Category.category_level, Category.display_order)
        )
        return list(result.scalars().all())
    
    async def get_all_descendants_by_path_prefix(self, path_prefix: str) -> List[Category]:
        """Get all categories whose path starts with the given prefix."""
        result = await self.session.execute(
            select(Category).filter(
                and_(
                    Category.category_path.startswith(path_prefix),
                    Category.is_active == True
                )
            ).order_by(Category.category_level, Category.display_order)
        )
        return list(result.scalars().all())