from typing import Optional
from uuid import UUID

from ....domain.repositories.brand_repository import BrandRepository


class DeleteBrandUseCase:
    """Use case for deleting (deactivating) a brand."""
    
    def __init__(self, brand_repository: BrandRepository):
        """Initialize use case with repository."""
        self.brand_repository = brand_repository
    
    async def execute(self, brand_id: UUID, deleted_by: Optional[str] = None) -> bool:
        """Execute brand deletion (soft delete).
        
        Args:
            brand_id: UUID of the brand to delete
            deleted_by: ID of user deleting the brand
            
        Returns:
            True if deleted successfully, False if brand not found
            
        Raises:
            ValueError: If brand has products assigned
        """
        # Check if brand exists
        brand = await self.brand_repository.get_by_id(brand_id)
        if not brand:
            return False
        
        # Check if brand has products
        if await self.brand_repository.has_products(brand_id):
            raise ValueError("Cannot delete brand with assigned products")
        
        # Soft delete
        brand.deactivate(deleted_by)
        await self.brand_repository.update(brand)
        
        return True