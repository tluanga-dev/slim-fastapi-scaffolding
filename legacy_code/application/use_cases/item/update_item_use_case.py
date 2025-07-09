from typing import Optional, Dict
from uuid import UUID
from decimal import Decimal

from ....domain.entities.item import Item
from ....domain.repositories.item_repository import ItemRepository


class UpdateItemUseCase:
    """Use case for updating an item."""
    
    def __init__(self, item_repository: ItemRepository):
        """Initialize use case with repository."""
        self.item_repository = item_repository
    
    async def execute(
        self,
        item_id: UUID,
        item_name: Optional[str] = None,
        description: Optional[str] = None,
        barcode: Optional[str] = None,
        model_number: Optional[str] = None,
        weight: Optional[Decimal] = None,
        dimensions: Optional[Dict[str, Decimal]] = None,
        updated_by: Optional[str] = None
    ) -> Item:
        """Execute item basic info update.
        
        Args:
            item_id: ID of the item to update
            item_name: Optional new name
            description: Optional new description
            barcode: Optional new barcode
            model_number: Optional new model number
            weight: Optional new weight
            dimensions: Optional new dimensions
            updated_by: ID of user updating the item
            
        Returns:
            Updated item entity
            
        Raises:
            ValueError: If item not found or barcode conflicts
        """
        # Get existing item
        item = await self.item_repository.get_by_item_id(item_id)
        if not item:
            raise ValueError(f"Item with ID '{item_id}' not found")
        
        # Check if new barcode already exists (exclude current item)
        if barcode and barcode != item.barcode:
            existing_item = await self.item_repository.get_by_barcode(barcode)
            if existing_item and existing_item.item_id != item_id:
                raise ValueError(f"Item with barcode '{barcode}' already exists")
        
        # Update item basic info
        item.update_basic_info(
            item_name=item_name,
            description=description,
            barcode=barcode,
            model_number=model_number,
            weight=weight,
            dimensions=dimensions,
            updated_by=updated_by
        )
        
        # Save to repository
        return await self.item_repository.update(item)
    
    async def execute_pricing(
        self,
        item_id: UUID,
        rental_base_price: Optional[Decimal] = None,
        sale_base_price: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ) -> Item:
        """Execute item pricing update.
        
        Args:
            item_id: ID of the item to update
            rental_base_price: Optional new rental base price
            sale_base_price: Optional new sale base price
            updated_by: ID of user updating the item
            
        Returns:
            Updated item entity
            
        Raises:
            ValueError: If item not found
        """
        # Get existing item
        item = await self.item_repository.get_by_item_id(item_id)
        if not item:
            raise ValueError(f"Item with ID '{item_id}' not found")
        
        # Update item pricing
        item.update_pricing(
            rental_base_price=rental_base_price,
            sale_base_price=sale_base_price,
            updated_by=updated_by
        )
        
        # Save to repository
        return await self.item_repository.update(item)
    
    async def execute_rental_settings(
        self,
        item_id: UUID,
        is_rentable: Optional[bool] = None,
        min_rental_days: Optional[int] = None,
        rental_period: Optional[int] = None,
        max_rental_days: Optional[int] = None,
        updated_by: Optional[str] = None
    ) -> Item:
        """Execute item rental settings update.
        
        Args:
            item_id: ID of the item to update
            is_rentable: Optional new rentable status
            min_rental_days: Optional new minimum rental days
            rental_period: Optional new rental period
            max_rental_days: Optional new maximum rental days
            updated_by: ID of user updating the item
            
        Returns:
            Updated item entity
            
        Raises:
            ValueError: If item not found
        """
        # Get existing item
        item = await self.item_repository.get_by_item_id(item_id)
        if not item:
            raise ValueError(f"Item with ID '{item_id}' not found")
        
        # Update item rental settings
        item.update_rental_settings(
            is_rentable=is_rentable,
            min_rental_days=min_rental_days,
            rental_period=rental_period,
            max_rental_days=max_rental_days,
            updated_by=updated_by
        )
        
        # Save to repository
        return await self.item_repository.update(item)
    
    async def execute_sale_settings(
        self,
        item_id: UUID,
        is_saleable: Optional[bool] = None,
        updated_by: Optional[str] = None
    ) -> Item:
        """Execute item sale settings update.
        
        Args:
            item_id: ID of the item to update
            is_saleable: Optional new saleable status
            updated_by: ID of user updating the item
            
        Returns:
            Updated item entity
            
        Raises:
            ValueError: If item not found
        """
        # Get existing item
        item = await self.item_repository.get_by_item_id(item_id)
        if not item:
            raise ValueError(f"Item with ID '{item_id}' not found")
        
        # Update item sale settings
        item.update_sale_settings(
            is_saleable=is_saleable,
            updated_by=updated_by
        )
        
        # Save to repository
        return await self.item_repository.update(item)