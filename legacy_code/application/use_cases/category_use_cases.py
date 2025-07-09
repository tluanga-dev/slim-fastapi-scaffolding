from typing import List, Optional, Tuple
from uuid import UUID

from ...domain.entities.category import Category, CategoryPath
from ...domain.repositories.category_repository import CategoryRepository


class CategoryUseCases:
    """Category use cases for hierarchical category management."""
    
    def __init__(self, category_repository: CategoryRepository):
        """Initialize with category repository."""
        self.category_repository = category_repository
    
    async def create_category(
        self,
        category_name: str,
        parent_category_id: Optional[UUID] = None,
        display_order: int = 0,
        created_by: Optional[str] = None
    ) -> Category:
        """Create a new category."""
        # Check if category with same name exists under same parent
        existing = await self.category_repository.get_by_name_and_parent(
            category_name, parent_category_id
        )
        if existing:
            raise ValueError(
                f"Category '{category_name}' already exists under the same parent"
            )
        
        # Determine level and path
        if parent_category_id:
            # Get parent category
            parent = await self.category_repository.get_by_id(parent_category_id)
            if not parent:
                raise ValueError(f"Parent category with ID {parent_category_id} not found")
            
            # Build path and level from parent
            category_path = f"{parent.category_path}/{category_name}"
            category_level = parent.category_level + 1
            
            # Mark parent as non-leaf if it was a leaf
            if parent.is_leaf:
                parent.mark_as_parent(updated_by=created_by)
                await self.category_repository.update(parent)
        else:
            # Root category
            category_path = category_name
            category_level = 1
        
        # Create category
        category = Category(
            category_name=category_name,
            parent_category_id=parent_category_id,
            category_path=category_path,
            category_level=category_level,
            display_order=display_order,
            is_leaf=True,  # New categories are always leaves initially
            created_by=created_by
        )
        
        return await self.category_repository.create(category)
    
    async def get_category(self, category_id: UUID) -> Category:
        """Get category by ID."""
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")
        return category
    
    async def get_category_by_path(self, category_path: str) -> Category:
        """Get category by its full path."""
        category = await self.category_repository.get_by_path(category_path)
        if not category:
            raise ValueError(f"Category with path '{category_path}' not found")
        return category
    
    async def list_categories(
        self,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[UUID] = None,
        is_leaf: Optional[bool] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[Category], int]:
        """List categories with pagination and filters."""
        categories = await self.category_repository.list(
            skip=skip,
            limit=limit,
            parent_id=parent_id,
            is_leaf=is_leaf,
            is_active=is_active
        )
        total = await self.category_repository.count(
            parent_id=parent_id,
            is_leaf=is_leaf,
            is_active=is_active
        )
        return categories, total
    
    async def get_category_tree(self, root_id: Optional[UUID] = None) -> List[Category]:
        """Get category tree starting from root or specific category."""
        if root_id:
            # Get specific category and its descendants
            root = await self.get_category(root_id)
            descendants = await self.category_repository.get_descendants(root_id)
            return [root] + descendants
        else:
            # Get all root categories
            roots = await self.category_repository.get_root_categories()
            
            # For each root, get its descendants
            tree = []
            for root in roots:
                tree.append(root)
                descendants = await self.category_repository.get_descendants(root.id)
                tree.extend(descendants)
            
            return tree
    
    async def get_category_breadcrumb(self, category_id: UUID) -> List[Category]:
        """Get breadcrumb trail from root to category."""
        category = await self.get_category(category_id)
        ancestors = await self.category_repository.get_ancestors(category_id)
        return ancestors + [category]
    
    async def update_category(
        self,
        category_id: UUID,
        category_name: Optional[str] = None,
        display_order: Optional[int] = None,
        updated_by: Optional[str] = None
    ) -> Category:
        """Update category details."""
        category = await self.get_category(category_id)
        
        if category_name and category_name != category.category_name:
            # Check if new name conflicts with sibling
            existing = await self.category_repository.get_by_name_and_parent(
                category_name, category.parent_category_id
            )
            if existing and existing.id != category_id:
                raise ValueError(
                    f"Category '{category_name}' already exists under the same parent"
                )
            
            # Update name and path
            old_path = category.category_path
            category.update_name(category_name, updated_by)
            
            # Rebuild path
            if category.parent_category_id:
                parent = await self.category_repository.get_by_id(category.parent_category_id)
                category.update_path(f"{parent.category_path}/{category_name}", updated_by)
            else:
                category.update_path(category_name, updated_by)
            
            # Update paths for all descendants
            await self.category_repository.update_paths_for_descendants(
                category_id, old_path, category.category_path
            )
        
        if display_order is not None:
            category.update_display_order(display_order, updated_by)
        
        return await self.category_repository.update(category)
    
    async def move_category(
        self,
        category_id: UUID,
        new_parent_id: Optional[UUID],
        updated_by: Optional[str] = None
    ) -> Category:
        """Move category to a new parent."""
        category = await self.get_category(category_id)
        
        # Prevent moving to self or descendant
        if new_parent_id:
            if new_parent_id == category_id:
                raise ValueError("Cannot move category to itself")
            
            # Check if new parent is a descendant
            descendants = await self.category_repository.get_descendants(category_id)
            if any(d.id == new_parent_id for d in descendants):
                raise ValueError("Cannot move category to its own descendant")
            
            # Get new parent
            new_parent = await self.category_repository.get_by_id(new_parent_id)
            if not new_parent:
                raise ValueError(f"New parent category with ID {new_parent_id} not found")
            
            # Check for name conflict in new location
            existing = await self.category_repository.get_by_name_and_parent(
                category.category_name, new_parent_id
            )
            if existing:
                raise ValueError(
                    f"Category '{category.category_name}' already exists under the new parent"
                )
            
            # Update parent and rebuild paths
            old_path = category.category_path
            category.parent_category_id = new_parent_id
            category.category_level = new_parent.category_level + 1
            category.category_path = f"{new_parent.category_path}/{category.category_name}"
            
            # Mark new parent as non-leaf
            if new_parent.is_leaf:
                new_parent.mark_as_parent(updated_by)
                await self.category_repository.update(new_parent)
        else:
            # Moving to root
            if category.parent_category_id is None:
                raise ValueError("Category is already at root level")
            
            # Check for name conflict at root
            existing = await self.category_repository.get_by_name_and_parent(
                category.category_name, None
            )
            if existing:
                raise ValueError(
                    f"Category '{category.category_name}' already exists at root level"
                )
            
            old_path = category.category_path
            category.parent_category_id = None
            category.category_level = 1
            category.category_path = category.category_name
        
        # Update category
        category.update_timestamp(updated_by)
        updated_category = await self.category_repository.update(category)
        
        # Update all descendant paths
        await self._update_descendant_levels_and_paths(
            category_id, old_path, category.category_path, category.category_level
        )
        
        # Check if old parent should be marked as leaf
        if category.parent_category_id:
            old_parent_has_children = await self.category_repository.has_children(
                category.parent_category_id
            )
            if not old_parent_has_children:
                old_parent = await self.category_repository.get_by_id(
                    category.parent_category_id
                )
                old_parent.mark_as_leaf(updated_by)
                await self.category_repository.update(old_parent)
        
        return updated_category
    
    async def delete_category(self, category_id: UUID) -> bool:
        """Delete a category (soft delete)."""
        category = await self.get_category(category_id)
        
        # Check if category has children
        if await self.category_repository.has_children(category_id):
            raise ValueError("Cannot delete category with child categories")
        
        # Check if category has products
        if await self.category_repository.has_products(category_id):
            raise ValueError("Cannot delete category with assigned products")
        
        # Delete the category
        result = await self.category_repository.delete(category_id)
        
        # If deleted and had a parent, check if parent should be marked as leaf
        if result and category.parent_category_id:
            parent_has_children = await self.category_repository.has_children(
                category.parent_category_id
            )
            if not parent_has_children:
                parent = await self.category_repository.get_by_id(
                    category.parent_category_id
                )
                parent.mark_as_leaf()
                await self.category_repository.update(parent)
        
        return result
    
    async def get_leaf_categories(self) -> List[Category]:
        """Get all leaf categories (those that can have products)."""
        return await self.category_repository.get_leaf_categories()
    
    async def get_category_statistics(self) -> dict:
        """Get category hierarchy statistics."""
        total = await self.category_repository.count()
        roots = await self.category_repository.count(parent_id=None)
        leaves = await self.category_repository.count(is_leaf=True)
        max_level = await self.category_repository.get_max_level()
        
        return {
            "total_categories": total,
            "root_categories": roots,
            "leaf_categories": leaves,
            "max_depth": max_level,
            "branch_categories": total - leaves
        }
    
    async def _update_descendant_levels_and_paths(
        self,
        category_id: UUID,
        old_path: str,
        new_path: str,
        new_base_level: int
    ):
        """Update levels and paths for all descendants after a move."""
        descendants = await self.category_repository.get_descendants(category_id)
        
        for descendant in descendants:
            # Update path
            descendant.category_path = descendant.category_path.replace(old_path, new_path, 1)
            
            # Update level based on path depth
            path_segments = descendant.category_path.split("/")
            descendant.category_level = new_base_level + len(path_segments) - len(new_path.split("/"))
            
            await self.category_repository.update(descendant)