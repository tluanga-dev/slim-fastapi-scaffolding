from typing import List, Optional
from uuid import UUID
from app.modules.brands.repository import BrandRepository
from app.modules.brands.schemas import (
    BrandCreate, BrandUpdate, BrandStatusUpdate, 
    BrandResponse, BrandListResponse, BrandSearchResponse
)
from app.core.domain.entities.brand import Brand as BrandEntity
from app.core.errors import NotFoundError, ValidationError
from app.modules.brands.models import BrandModel


class BrandService:
    """Service layer for brand business logic."""
    
    def __init__(self, repository: BrandRepository):
        self.repository = repository
    
    def _model_to_entity(self, model: BrandModel) -> BrandEntity:
        """Convert SQLAlchemy model to domain entity."""
        return BrandEntity(
            id=model.id,
            brand_name=model.brand_name,
            brand_code=model.brand_code,
            description=model.description,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
    
    def _entity_to_dict(self, entity: BrandEntity) -> dict:
        """Convert domain entity to dictionary for database operations."""
        return {
            'id': entity.id,
            'brand_name': entity.brand_name,
            'brand_code': entity.brand_code,
            'description': entity.description,
            'is_active': entity.is_active,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'created_by': entity.created_by,
            'updated_by': entity.updated_by
        }
    
    async def create_brand(self, brand_data: BrandCreate) -> BrandResponse:
        """Create a new brand."""
        # Check if brand name already exists
        existing_name = await self.repository.brand_name_exists(brand_data.brand_name)
        if existing_name:
            raise ValidationError(f"Brand name '{brand_data.brand_name}' already exists")
        
        # Check if brand code already exists (if provided)
        if brand_data.brand_code:
            existing_code = await self.repository.brand_code_exists(brand_data.brand_code)
            if existing_code:
                raise ValidationError(f"Brand code '{brand_data.brand_code}' already exists")
        
        # Create domain entity to validate business rules
        try:
            entity = BrandEntity(
                brand_name=brand_data.brand_name,
                brand_code=brand_data.brand_code,
                description=brand_data.description,
                created_by=brand_data.created_by
            )
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Convert to dict for database creation
        create_data = self._entity_to_dict(entity)
        
        # Create in database
        brand_model = await self.repository.create_brand(create_data)
        
        return BrandResponse.model_validate(brand_model)
    
    async def get_brand_by_id(self, brand_id: UUID) -> BrandResponse:
        """Get brand by ID."""
        brand = await self.repository.get_brand_by_id(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with ID {brand_id} not found")
        
        return BrandResponse.model_validate(brand)
    
    async def get_brand_by_name(self, brand_name: str) -> BrandResponse:
        """Get brand by name."""
        brand = await self.repository.get_brand_by_name(brand_name)
        if not brand:
            raise NotFoundError(f"Brand with name '{brand_name}' not found")
        
        return BrandResponse.model_validate(brand)
    
    async def get_brand_by_code(self, brand_code: str) -> BrandResponse:
        """Get brand by code."""
        brand = await self.repository.get_brand_by_code(brand_code)
        if not brand:
            raise NotFoundError(f"Brand with code '{brand_code}' not found")
        
        return BrandResponse.model_validate(brand)
    
    async def get_brands(
        self,
        page: int = 1,
        page_size: int = 50,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "brand_name",
        sort_order: str = "asc"
    ) -> BrandListResponse:
        """Get brands with filtering, pagination, and sorting."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        if page_size > 100:
            page_size = 100
        
        # Validate sort_by field
        valid_sort_fields = ["brand_name", "brand_code", "created_at", "updated_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "brand_name"
        
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "asc"
        
        skip = (page - 1) * page_size
        
        # Get brands and total count
        brands = await self.repository.get_brands(
            skip=skip,
            limit=page_size,
            is_active=is_active,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total = await self.repository.count_brands(
            is_active=is_active,
            search=search
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return BrandListResponse(
            brands=[BrandResponse.model_validate(brand) for brand in brands],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_brand(self, brand_id: UUID, update_data: BrandUpdate) -> BrandResponse:
        """Update brand information."""
        brand = await self.repository.get_brand_by_id(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with ID {brand_id} not found")
        
        # Convert to domain entity for validation
        entity = self._model_to_entity(brand)
        
        # Check for duplicate name (if being updated)
        if update_data.brand_name is not None and update_data.brand_name != brand.brand_name:
            existing_name = await self.repository.brand_name_exists(update_data.brand_name, exclude_id=brand_id)
            if existing_name:
                raise ValidationError(f"Brand name '{update_data.brand_name}' already exists")
        
        # Check for duplicate code (if being updated)
        if update_data.brand_code is not None and update_data.brand_code != brand.brand_code:
            existing_code = await self.repository.brand_code_exists(update_data.brand_code, exclude_id=brand_id)
            if existing_code:
                raise ValidationError(f"Brand code '{update_data.brand_code}' already exists")
        
        # Update entity using domain methods
        try:
            if update_data.brand_name is not None:
                entity.update_name(update_data.brand_name, update_data.updated_by)
            
            if update_data.brand_code is not None:
                entity.update_code(update_data.brand_code, update_data.updated_by)
            
            if update_data.description is not None:
                entity.update_description(update_data.description, update_data.updated_by)
            
            # Update timestamp even if only updated_by changes
            if update_data.updated_by and not any([
                update_data.brand_name, 
                update_data.brand_code, 
                update_data.description
            ]):
                entity.update_timestamp(update_data.updated_by)
                
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Prepare update data for database
        update_dict = {}
        if update_data.brand_name is not None:
            update_dict['brand_name'] = entity.brand_name
        if update_data.brand_code is not None:
            update_dict['brand_code'] = entity.brand_code
        if update_data.description is not None:
            update_dict['description'] = entity.description
        
        update_dict['updated_at'] = entity.updated_at
        if update_data.updated_by:
            update_dict['updated_by'] = entity.updated_by
        
        # Update in database
        updated_brand = await self.repository.update_brand(brand_id, update_dict)
        
        return BrandResponse.model_validate(updated_brand)
    
    async def update_brand_status(self, brand_id: UUID, status_data: BrandStatusUpdate) -> BrandResponse:
        """Update brand active status."""
        brand = await self.repository.get_brand_by_id(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with ID {brand_id} not found")
        
        update_dict = {
            'is_active': status_data.is_active,
            'updated_by': status_data.updated_by
        }
        
        updated_brand = await self.repository.update_brand(brand_id, update_dict)
        
        return BrandResponse.model_validate(updated_brand)
    
    async def delete_brand(self, brand_id: UUID, deleted_by: Optional[str] = None) -> bool:
        """Soft delete brand."""
        brand = await self.repository.get_brand_by_id(brand_id)
        if not brand:
            raise NotFoundError(f"Brand with ID {brand_id} not found")
        
        # Perform soft delete
        deleted_brand = await self.repository.soft_delete_brand(brand_id, deleted_by)
        return deleted_brand is not None
    
    async def get_active_brands(self) -> List[BrandResponse]:
        """Get all active brands."""
        brands = await self.repository.get_active_brands()
        return [BrandResponse.model_validate(brand) for brand in brands]
    
    async def search_brands(self, search_term: str, limit: int = 20) -> List[BrandSearchResponse]:
        """Search brands by name or code."""
        if not search_term or not search_term.strip():
            return []
        
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
        
        brands = await self.repository.search_brands(search_term.strip(), limit)
        return [BrandSearchResponse.model_validate(brand) for brand in brands]
    
    async def get_brands_by_prefix(self, prefix: str, limit: int = 10) -> List[BrandSearchResponse]:
        """Get brands that start with the given prefix."""
        if not prefix or not prefix.strip():
            return []
        
        if limit < 1:
            limit = 10
        if limit > 50:
            limit = 50
        
        brands = await self.repository.get_brands_by_prefix(prefix.strip(), limit)
        return [BrandSearchResponse.model_validate(brand) for brand in brands]
    
    async def check_brand_name_availability(self, brand_name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if brand name is available."""
        if not brand_name or not brand_name.strip():
            return False
        
        exists = await self.repository.brand_name_exists(brand_name.strip(), exclude_id)
        return not exists
    
    async def check_brand_code_availability(self, brand_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if brand code is available."""
        if not brand_code or not brand_code.strip():
            return True  # Empty codes are allowed
        
        exists = await self.repository.brand_code_exists(brand_code.strip(), exclude_id)
        return not exists