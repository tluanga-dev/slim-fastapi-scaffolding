from typing import List, Optional, Tuple

from ....domain.entities.brand import Brand
from ....domain.repositories.brand_repository import BrandRepository


class ListBrandsUseCase:
    """Use case for listing brands with pagination and search."""
    
    def __init__(self, brand_repository: BrandRepository):
        """Initialize use case with repository."""
        self.brand_repository = brand_repository
    
    async def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[Brand], int]:
        """Execute brand listing with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Optional search term for name, code, or description
            is_active: Filter by active status (None for all)
            
        Returns:
            Tuple of (list of brands, total count)
        """
        # Get brands
        brands = await self.brand_repository.list(
            skip=skip,
            limit=limit,
            search=search,
            is_active=is_active
        )
        
        # Get total count
        total_count = await self.brand_repository.count(
            search=search,
            is_active=is_active
        )
        
        return brands, total_count