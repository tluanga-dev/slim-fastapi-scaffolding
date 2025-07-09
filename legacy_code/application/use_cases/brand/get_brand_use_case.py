from typing import Optional
from uuid import UUID

from ....domain.entities.brand import Brand
from ....domain.repositories.brand_repository import BrandRepository


class GetBrandUseCase:
    """Use case for retrieving a brand."""
    
    def __init__(self, brand_repository: BrandRepository):
        """Initialize use case with repository."""
        self.brand_repository = brand_repository
    
    async def execute(self, brand_id: UUID) -> Optional[Brand]:
        """Get brand by ID.
        
        Args:
            brand_id: UUID of the brand
            
        Returns:
            Brand entity if found, None otherwise
        """
        return await self.brand_repository.get_by_id(brand_id)
    
    async def get_by_name(self, brand_name: str) -> Optional[Brand]:
        """Get brand by name.
        
        Args:
            brand_name: Name of the brand
            
        Returns:
            Brand entity if found, None otherwise
        """
        return await self.brand_repository.get_by_name(brand_name)
    
    async def get_by_code(self, brand_code: str) -> Optional[Brand]:
        """Get brand by code.
        
        Args:
            brand_code: Code of the brand
            
        Returns:
            Brand entity if found, None otherwise
        """
        return await self.brand_repository.get_by_code(brand_code)