from typing import Optional, List
from uuid import UUID

from .base import BaseEntity


class Category(BaseEntity):
    """Category domain entity with hierarchical support."""
    
    def __init__(
        self,
        category_name: str,
        parent_category_id: Optional[UUID] = None,
        category_path: Optional[str] = None,
        category_level: int = 1,
        display_order: int = 0,
        is_leaf: bool = True,
        **kwargs
    ):
        """Initialize a Category entity.
        
        Args:
            category_name: Name of the category
            parent_category_id: UUID of parent category (None for root categories)
            category_path: Full path like "Electronics/Computers/Laptops"
            category_level: Hierarchy level (1=root, 2=sub, etc.)
            display_order: Sort order within parent
            is_leaf: True if category has no children
        """
        super().__init__(**kwargs)
        self.category_name = category_name
        self.parent_category_id = parent_category_id
        self.category_path = category_path or category_name
        self.category_level = category_level
        self.display_order = display_order
        self.is_leaf = is_leaf
        self._validate()
    
    def _validate(self):
        """Validate category business rules."""
        if not self.category_name or not self.category_name.strip():
            raise ValueError("Category name cannot be empty")
        
        if len(self.category_name) > 100:
            raise ValueError("Category name cannot exceed 100 characters")
        
        if self.category_level < 1:
            raise ValueError("Category level must be at least 1")
        
        if self.display_order < 0:
            raise ValueError("Display order cannot be negative")
        
        # Root categories should not have parent
        if self.category_level == 1 and self.parent_category_id is not None:
            raise ValueError("Root categories cannot have a parent")
        
        # Non-root categories must have parent
        if self.category_level > 1 and self.parent_category_id is None:
            raise ValueError("Non-root categories must have a parent")
    
    def update_name(self, category_name: str, updated_by: Optional[str] = None):
        """Update category name."""
        if not category_name or not category_name.strip():
            raise ValueError("Category name cannot be empty")
        
        self.category_name = category_name
        # Path will need to be updated by the service/use case
        self.update_timestamp(updated_by)
    
    def update_display_order(self, display_order: int, updated_by: Optional[str] = None):
        """Update display order."""
        if display_order < 0:
            raise ValueError("Display order cannot be negative")
        
        self.display_order = display_order
        self.update_timestamp(updated_by)
    
    def mark_as_parent(self, updated_by: Optional[str] = None):
        """Mark category as parent (not leaf)."""
        self.is_leaf = False
        self.update_timestamp(updated_by)
    
    def mark_as_leaf(self, updated_by: Optional[str] = None):
        """Mark category as leaf (no children)."""
        self.is_leaf = True
        self.update_timestamp(updated_by)
    
    def update_path(self, new_path: str, updated_by: Optional[str] = None):
        """Update category path. Usually called when parent category is renamed."""
        if not new_path:
            raise ValueError("Category path cannot be empty")
        
        self.category_path = new_path
        self.update_timestamp(updated_by)
    
    def can_have_products(self) -> bool:
        """Check if this category can have products assigned."""
        return self.is_leaf
    
    def can_have_children(self) -> bool:
        """Check if this category can have child categories."""
        # In theory any category can have children, but business rules might limit depth
        return True
    
    def is_root(self) -> bool:
        """Check if this is a root category."""
        return self.category_level == 1 and self.parent_category_id is None
    
    def get_path_segments(self) -> List[str]:
        """Get category path as a list of segments."""
        if not self.category_path:
            return []
        return self.category_path.split("/")
    
    def get_depth(self) -> int:
        """Get the depth of this category in the hierarchy."""
        return self.category_level
    
    def __str__(self) -> str:
        """String representation of category."""
        return f"Category({self.category_path})"
    
    def __repr__(self) -> str:
        """Developer representation of category."""
        return f"Category(id={self.id}, name='{self.category_name}', path='{self.category_path}', level={self.category_level}, is_leaf={self.is_leaf})"


class CategoryPath:
    """Value object for managing category paths."""
    
    def __init__(self, path: str):
        """Initialize category path."""
        if not path:
            raise ValueError("Category path cannot be empty")
        self.path = path.strip("/")  # Remove leading/trailing slashes
    
    def append(self, segment: str) -> "CategoryPath":
        """Append a segment to the path."""
        if not segment:
            raise ValueError("Path segment cannot be empty")
        return CategoryPath(f"{self.path}/{segment}")
    
    def parent_path(self) -> Optional["CategoryPath"]:
        """Get the parent path, or None if this is root."""
        segments = self.path.split("/")
        if len(segments) <= 1:
            return None
        return CategoryPath("/".join(segments[:-1]))
    
    def replace_segment(self, old_segment: str, new_segment: str) -> "CategoryPath":
        """Replace a segment in the path."""
        segments = self.path.split("/")
        new_segments = [new_segment if seg == old_segment else seg for seg in segments]
        return CategoryPath("/".join(new_segments))
    
    def starts_with(self, prefix: str) -> bool:
        """Check if path starts with a prefix."""
        return self.path.startswith(prefix)
    
    def get_segments(self) -> List[str]:
        """Get path segments as a list."""
        return self.path.split("/")
    
    def get_level(self) -> int:
        """Get the level (depth) of this path."""
        return len(self.get_segments())
    
    def __str__(self) -> str:
        """String representation."""
        return self.path
    
    def __eq__(self, other) -> bool:
        """Check equality."""
        if not isinstance(other, CategoryPath):
            return False
        return self.path == other.path