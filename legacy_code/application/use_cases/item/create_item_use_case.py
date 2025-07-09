from typing import Optional, Dict
from uuid import UUID, uuid4
from decimal import Decimal

from ....domain.entities.item import Item
from ....domain.repositories.item_repository import ItemRepository


class CreateItemUseCase:
    """Use case for creating a new item."""
    
    def __init__(self, item_repository: ItemRepository):
        """Initialize use case with repository."""
        self.item_repository = item_repository
    
    async def execute(
        self,
        sku: str,
        item_name: str,
        category_id: UUID,
        brand_id: Optional[UUID] = None,
        description: Optional[str] = None,
        is_serialized: bool = False,
        barcode: Optional[str] = None,
        model_number: Optional[str] = None,
        weight: Optional[Decimal] = None,
        dimensions: Optional[Dict[str, Decimal]] = None,
        is_rentable: bool = False,
        is_saleable: bool = True,
        min_rental_days: int = 1,
        rental_period: Optional[int] = 1,
        max_rental_days: Optional[int] = None,
        rental_base_price: Optional[Decimal] = None,
        sale_base_price: Optional[Decimal] = None,
        created_by: Optional[str] = None
    ) -> Item:
        """Execute item creation.
        
        Args:
            sku: Unique SKU for the item
            item_name: Name of the item
            category_id: ID of the category
            brand_id: Optional ID of the brand
            description: Optional description
            is_serialized: Whether item requires serial number tracking
            barcode: Optional barcode
            model_number: Optional model number
            weight: Optional weight
            dimensions: Optional dimensions dict
            is_rentable: Whether item can be rented
            is_saleable: Whether item can be sold
            min_rental_days: Minimum rental period
            rental_period: Default rental period
            max_rental_days: Maximum rental period
            rental_base_price: Base rental price
            sale_base_price: Base sale price
            created_by: ID of user creating the item
            
        Returns:
            Created item entity
            
        Raises:
            ValueError: If SKU already exists or barcode is not unique
        """
        # Check if SKU already exists
        if await self.item_repository.get_by_sku(sku):
            raise ValueError(f"Item with SKU '{sku}' already exists")
        
        # Check if barcode already exists
        if barcode and await self.item_repository.get_by_barcode(barcode):
            raise ValueError(f"Item with barcode '{barcode}' already exists")
        
        # Create item entity
        item = Item(
            item_id=uuid4(),
            sku=sku,
            item_name=item_name,
            category_id=category_id,
            brand_id=brand_id,
            description=description,
            is_serialized=is_serialized,
            barcode=barcode,
            model_number=model_number,
            weight=weight,
            dimensions=dimensions,
            is_rentable=is_rentable,
            is_saleable=is_saleable,
            min_rental_days=min_rental_days,
            rental_period=rental_period,
            max_rental_days=max_rental_days,
            rental_base_price=rental_base_price,
            sale_base_price=sale_base_price,
            created_by=created_by,
            updated_by=created_by
        )
        
        # Save to repository
        return await self.item_repository.create(item)