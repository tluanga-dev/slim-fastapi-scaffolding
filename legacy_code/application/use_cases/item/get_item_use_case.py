from typing import Optional
from uuid import UUID

from ....domain.entities.item import Item
from ....domain.repositories.item_repository import ItemRepository


class GetItemUseCase:
    """Use case for getting an item."""
    
    def __init__(self, item_repository: ItemRepository):
        """Initialize use case with repository."""
        self.item_repository = item_repository
    
    async def execute(self, item_id: UUID) -> Optional[Item]:
        """Execute item retrieval.
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            Item entity or None if not found
        """
        return await self.item_repository.get_by_item_id(item_id)