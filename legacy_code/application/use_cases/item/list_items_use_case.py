from typing import List
from uuid import UUID

from ....domain.entities.item import Item
from ....domain.repositories.item_repository import ItemRepository


class ListItemsUseCase:
    """Use case for listing items."""
    
    def __init__(self, item_repository: ItemRepository):
        """Initialize use case with repository."""
        self.item_repository = item_repository
    
    async def execute(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """Execute items listing.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active item entities
        """
        return await self.item_repository.get_active(skip=skip, limit=limit)
    
    async def execute_by_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[Item]:
        """Execute items listing by category.
        
        Args:
            category_id: ID of the category
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active item entities in the category
        """
        return await self.item_repository.get_by_category_id(category_id, skip=skip, limit=limit)
    
    async def execute_by_brand(self, brand_id: UUID, skip: int = 0, limit: int = 100) -> List[Item]:
        """Execute items listing by brand.
        
        Args:
            brand_id: ID of the brand
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active item entities from the brand
        """
        return await self.item_repository.get_by_brand_id(brand_id, skip=skip, limit=limit)
    
    async def execute_rentable(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """Execute rentable items listing.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of rentable item entities
        """
        return await self.item_repository.get_rentable_items(skip=skip, limit=limit)
    
    async def execute_saleable(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """Execute saleable items listing.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of saleable item entities
        """
        return await self.item_repository.get_saleable_items(skip=skip, limit=limit)