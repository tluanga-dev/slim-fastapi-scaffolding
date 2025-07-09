from typing import Optional
from uuid import UUID

from ....domain.entities.brand import Brand
from ....domain.repositories.brand_repository import BrandRepository


class CreateBrandUseCase:
    """Use case for creating a new brand."""
    
    def __init__(self, brand_repository: BrandRepository):
        """Initialize use case with repository."""
        self.brand_repository = brand_repository
    
    async def execute(
        self,
        brand_name: str,
        brand_code: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Brand:
        """Execute brand creation.
        
        Args:
            brand_name: Name of the brand
            brand_code: Optional unique code for the brand
            description: Optional brand description
            created_by: ID of user creating the brand
            
        Returns:
            Created brand entity
            
        Raises:
            ValueError: If brand name already exists or code is not unique
        """
        # Check if brand name already exists
        if await self.brand_repository.exists_by_name(brand_name):
            raise ValueError(f"Brand with name '{brand_name}' already exists")
        
        # Check if brand code already exists
        if brand_code and await self.brand_repository.exists_by_code(brand_code):
            raise ValueError(f"Brand with code '{brand_code}' already exists")
        
        # Create brand entity
        brand = Brand(
            brand_name=brand_name,
            brand_code=brand_code,
            description=description,
            created_by=created_by,
            updated_by=created_by
        )
        
        # Save to repository
        return await self.brand_repository.create(brand)