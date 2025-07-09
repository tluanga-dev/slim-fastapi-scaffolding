from typing import Optional
from uuid import UUID

from ....domain.entities.brand import Brand
from ....domain.repositories.brand_repository import BrandRepository


class UpdateBrandUseCase:
    """Use case for updating an existing brand."""
    
    def __init__(self, brand_repository: BrandRepository):
        """Initialize use case with repository."""
        self.brand_repository = brand_repository
    
    async def execute(
        self,
        brand_id: UUID,
        brand_name: Optional[str] = None,
        brand_code: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> Brand:
        """Execute brand update.
        
        Args:
            brand_id: UUID of the brand to update
            brand_name: New brand name (optional)
            brand_code: New brand code (optional)
            description: New description (optional)
            updated_by: ID of user updating the brand
            
        Returns:
            Updated brand entity
            
        Raises:
            ValueError: If brand not found or name/code already exists
        """
        # Get existing brand
        brand = await self.brand_repository.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with id {brand_id} not found")
        
        # Update name if provided
        if brand_name and brand_name != brand.brand_name:
            # Check if new name already exists
            if await self.brand_repository.exists_by_name(brand_name, exclude_id=brand_id):
                raise ValueError(f"Brand with name '{brand_name}' already exists")
            brand.update_name(brand_name, updated_by)
        
        # Update code if provided
        if brand_code is not None and brand_code != brand.brand_code:
            # Check if new code already exists
            if brand_code and await self.brand_repository.exists_by_code(brand_code, exclude_id=brand_id):
                raise ValueError(f"Brand with code '{brand_code}' already exists")
            brand.update_code(brand_code, updated_by)
        
        # Update description if provided
        if description is not None and description != brand.description:
            brand.update_description(description, updated_by)
        
        # Save changes
        return await self.brand_repository.update(brand)