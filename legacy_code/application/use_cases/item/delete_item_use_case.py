from uuid import UUID

from ....domain.repositories.item_repository import ItemRepository


class DeleteItemUseCase:
    """Use case for deleting an item."""
    
    def __init__(self, item_repository: ItemRepository):
        """Initialize use case with repository."""
        self.item_repository = item_repository
    
    async def execute(self, item_id: UUID) -> bool:
        """Execute item deletion (soft delete).
        
        Args:
            item_id: ID of the item to delete
            
        Returns:
            True if item was deleted, False if not found
        """
        # Get existing item
        item = await self.item_repository.get_by_item_id(item_id)
        if not item:
            return False
        
        # Soft delete
        return await self.item_repository.delete(item.id)