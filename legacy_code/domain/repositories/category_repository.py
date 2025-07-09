from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.category import Category


class CategoryRepository(ABC):
    """Abstract repository interface for Category entity."""
    
    @abstractmethod
    async def create(self, category: Category) -> Category:
        """Create a new category."""
        pass
    
    @abstractmethod
    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Get category by ID."""
        pass
    
    @abstractmethod
    async def get_by_name_and_parent(
        self, 
        category_name: str, 
        parent_category_id: Optional[UUID]
    ) -> Optional[Category]:
        """Get category by name and parent (for uniqueness check)."""
        pass
    
    @abstractmethod
    async def get_children(self, parent_category_id: UUID) -> List[Category]:
        """Get all direct children of a category."""
        pass
    
    @abstractmethod
    async def get_descendants(self, category_id: UUID) -> List[Category]:
        """Get all descendants (children, grandchildren, etc.) of a category."""
        pass
    
    @abstractmethod
    async def get_ancestors(self, category_id: UUID) -> List[Category]:
        """Get all ancestors (parent, grandparent, etc.) of a category."""
        pass
    
    @abstractmethod
    async def get_root_categories(self) -> List[Category]:
        """Get all root categories (categories with no parent)."""
        pass
    
    @abstractmethod
    async def get_leaf_categories(self) -> List[Category]:
        """Get all leaf categories (categories with no children)."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[UUID] = None,
        is_leaf: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> List[Category]:
        """List categories with optional filters."""
        pass
    
    @abstractmethod
    async def update(self, category: Category) -> Category:
        """Update existing category."""
        pass
    
    @abstractmethod
    async def update_paths_for_descendants(
        self, 
        category_id: UUID, 
        old_path: str, 
        new_path: str
    ) -> int:
        """Update paths for all descendants when a category is renamed.
        Returns the number of categories updated."""
        pass
    
    @abstractmethod
    async def delete(self, category_id: UUID) -> bool:
        """Soft delete category by setting is_active to False."""
        pass
    
    @abstractmethod
    async def count(
        self,
        parent_id: Optional[UUID] = None,
        is_leaf: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> int:
        """Count categories matching filters."""
        pass
    
    @abstractmethod
    async def has_children(self, category_id: UUID) -> bool:
        """Check if a category has any children."""
        pass
    
    @abstractmethod
    async def has_products(self, category_id: UUID) -> bool:
        """Check if a category has any products assigned to it."""
        pass
    
    @abstractmethod
    async def get_max_level(self) -> int:
        """Get the maximum category level in the hierarchy."""
        pass
    
    @abstractmethod
    async def get_by_path(self, category_path: str) -> Optional[Category]:
        """Get category by its full path."""
        pass