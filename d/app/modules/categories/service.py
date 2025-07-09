from typing import List, Optional
from uuid import UUID

from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate, CategoryPath
from app.modules.categories.models import Category
from app.core.domain.base import BaseEntity


class CategoryService:
    """Business logic for category management."""
    
    def __init__(self, category_repo: CategoryRepository):
        self.repo = category_repo
    
    async def create_category(
        self, 
        category_data: CategoryCreate, 
        created_by: Optional[str] = None
    ) -> Category:
        """Create a new category."""
        # Check if category with same name exists under same parent
        exists = await self.repo.exists_by_name_and_parent(
            category_data.category_name,
            category_data.parent_category_id
        )
        if exists:
            raise ValueError(f"Category '{category_data.category_name}' already exists under this parent")
        
        # Prepare category data
        data = category_data.model_dump()
        data['created_by'] = created_by
        data['updated_by'] = created_by
        
        # Handle root category
        if category_data.parent_category_id is None:
            data['category_level'] = 1
            data['category_path'] = category_data.category_name
            data['is_leaf'] = True
        else:
            # Get parent category
            parent = await self.repo.get_category(category_data.parent_category_id)
            if not parent:
                raise ValueError("Parent category not found")
            
            # Set level and path based on parent
            data['category_level'] = parent.category_level + 1
            data['category_path'] = f"{parent.category_path}/{category_data.category_name}"
            data['is_leaf'] = True
            
            # Update parent to mark as non-leaf if it was a leaf
            if parent.is_leaf:
                await self.repo.update_category(
                    parent.id,
                    {'is_leaf': False, 'updated_by': created_by}
                )
        
        # Create the category
        return await self.repo.create_category(data)
    
    async def get_category(self, category_id: UUID) -> Optional[Category]:
        """Get a category by ID."""
        return await self.repo.get_category(category_id)
    
    async def get_category_tree(self, category_id: Optional[UUID] = None) -> List[Category]:
        """Get category tree starting from a specific category or root."""
        if category_id:
            # Get specific category with children
            category = await self.repo.get_category_with_children(category_id)
            return [category] if category else []
        else:
            # Get all root categories
            return await self.repo.get_root_categories()
    
    async def get_categories_by_parent(self, parent_id: Optional[UUID]) -> List[Category]:
        """Get all categories for a given parent."""
        return await self.repo.get_categories_by_parent(parent_id)
    
    async def get_leaf_categories(self) -> List[Category]:
        """Get all leaf categories (categories that can have products)."""
        return await self.repo.get_leaf_categories()
    
    async def update_category(
        self, 
        category_id: UUID, 
        update_data: CategoryUpdate,
        updated_by: Optional[str] = None
    ) -> Optional[Category]:
        """Update a category."""
        # Get existing category
        category = await self.repo.get_category(category_id)
        if not category:
            return None
        
        # Prepare update data
        data = update_data.model_dump(exclude_unset=True)
        if not data:
            return category  # Nothing to update
        
        data['updated_by'] = updated_by
        
        # If name is being changed, update path and all descendants
        if 'category_name' in data and data['category_name'] != category.category_name:
            old_name = category.category_name
            new_name = data['category_name']
            
            # Check if new name already exists under same parent
            exists = await self.repo.exists_by_name_and_parent(
                new_name,
                category.parent_category_id
            )
            if exists:
                raise ValueError(f"Category '{new_name}' already exists under this parent")
            
            # Update the category path
            if category.parent_category_id is None:
                # Root category
                data['category_path'] = new_name
                old_path_prefix = old_name
                new_path_prefix = new_name
            else:
                # Non-root category
                parent_path = "/".join(category.category_path.split("/")[:-1])
                data['category_path'] = f"{parent_path}/{new_name}"
                old_path_prefix = category.category_path
                new_path_prefix = data['category_path']
            
            # Update all descendant paths
            await self.repo.update_category_paths(
                f"{old_path_prefix}/",
                f"{new_path_prefix}/"
            )
        
        # Update the category
        return await self.repo.update_category(category_id, data)
    
    async def delete_category(
        self, 
        category_id: UUID,
        deleted_by: Optional[str] = None
    ) -> bool:
        """Soft delete a category and all its descendants."""
        # Check if category exists
        category = await self.repo.get_category(category_id)
        if not category:
            return False
        
        # Check if category has children
        children_count = await self.repo.count_children(category_id)
        if children_count > 0:
            # Get all descendants and delete them first
            descendants = await self.repo.get_all_descendants(category_id)
            for desc in descendants:
                await self.repo.soft_delete_category(desc.id, deleted_by)
        
        # Delete the category itself
        success = await self.repo.soft_delete_category(category_id, deleted_by)
        
        # If this was the last child of its parent, mark parent as leaf
        if success and category.parent_category_id:
            remaining_children = await self.repo.count_children(category.parent_category_id)
            if remaining_children == 0:
                await self.repo.update_category(
                    category.parent_category_id,
                    {'is_leaf': True, 'updated_by': deleted_by}
                )
        
        return success
    
    async def move_category(
        self,
        category_id: UUID,
        new_parent_id: Optional[UUID],
        updated_by: Optional[str] = None
    ) -> Optional[Category]:
        """Move a category to a new parent."""
        # Get the category to move
        category = await self.repo.get_category(category_id)
        if not category:
            return None
        
        # Can't move to the same parent
        if category.parent_category_id == new_parent_id:
            return category
        
        # Validate new parent if provided
        new_parent = None
        if new_parent_id:
            new_parent = await self.repo.get_category(new_parent_id)
            if not new_parent:
                raise ValueError("New parent category not found")
            
            # Check for circular reference
            if await self._would_create_circular_reference(category_id, new_parent_id):
                raise ValueError("Cannot move category to its own descendant")
        
        # Check if name exists under new parent
        exists = await self.repo.exists_by_name_and_parent(
            category.category_name,
            new_parent_id
        )
        if exists:
            raise ValueError(f"Category '{category.category_name}' already exists under the new parent")
        
        # Prepare update data
        old_path = category.category_path
        if new_parent_id is None:
            # Moving to root
            new_level = 1
            new_path = category.category_name
        else:
            # Moving under another category
            new_level = new_parent.category_level + 1
            new_path = f"{new_parent.category_path}/{category.category_name}"
        
        # Update the category
        update_data = {
            'parent_category_id': new_parent_id,
            'category_level': new_level,
            'category_path': new_path,
            'updated_by': updated_by
        }
        
        # Update all descendant paths and levels
        level_diff = new_level - category.category_level
        await self._update_descendants_after_move(
            old_path,
            new_path,
            level_diff,
            updated_by
        )
        
        # Update old parent if it has no more children
        if category.parent_category_id:
            old_parent_children = await self.repo.count_children(category.parent_category_id)
            if old_parent_children == 0:
                await self.repo.update_category(
                    category.parent_category_id,
                    {'is_leaf': True, 'updated_by': updated_by}
                )
        
        # Update new parent to mark as non-leaf
        if new_parent_id:
            if new_parent.is_leaf:
                await self.repo.update_category(
                    new_parent_id,
                    {'is_leaf': False, 'updated_by': updated_by}
                )
        
        # Update and return the moved category
        return await self.repo.update_category(category_id, update_data)
    
    async def _would_create_circular_reference(
        self,
        category_id: UUID,
        potential_parent_id: UUID
    ) -> bool:
        """Check if moving a category would create a circular reference."""
        # Get all descendants of the category being moved
        descendants = await self.repo.get_all_descendants(category_id)
        descendant_ids = {desc.id for desc in descendants}
        
        # Check if the potential parent is among the descendants
        return potential_parent_id in descendant_ids
    
    async def _update_descendants_after_move(
        self,
        old_path_prefix: str,
        new_path_prefix: str,
        level_diff: int,
        updated_by: Optional[str]
    ):
        """Update all descendants after a category move."""
        # Update paths for all descendants
        await self.repo.update_category_paths(
            f"{old_path_prefix}/",
            f"{new_path_prefix}/"
        )
        
        # If level changed, we need to update levels too
        if level_diff != 0:
            # Get all descendants and update their levels
            descendants = await self.repo.get_all_descendants_by_path_prefix(f"{new_path_prefix}/")
            for desc in descendants:
                await self.repo.update_category(
                    desc.id,
                    {
                        'category_level': desc.category_level + level_diff,
                        'updated_by': updated_by
                    }
                )