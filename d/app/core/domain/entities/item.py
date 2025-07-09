from typing import Optional
from uuid import UUID

from .base import BaseEntity
from ..value_objects.item_type import ItemType


class Item(BaseEntity):
    """Item domain entity representing master item catalog."""
    
    def __init__(
        self,
        item_code: str,
        item_name: str,
        item_type: ItemType,
        brand_id: UUID,
        category_id: UUID,
        unit_of_measurement_id: UUID,
        description: Optional[str] = None,
        **kwargs
    ):
        """Initialize an Item entity."""
        super().__init__(**kwargs)
        self.item_code = item_code
        self.item_name = item_name
        self.item_type = item_type
        self.brand_id = brand_id
        self.category_id = category_id
        self.unit_of_measurement_id = unit_of_measurement_id
        self.description = description
        self._validate()
    
    def _validate(self):
        """Validate item business rules."""
        if not self.item_code or not self.item_code.strip():
            raise ValueError("Item code cannot be empty")
        
        if not self.item_name or not self.item_name.strip():
            raise ValueError("Item name cannot be empty")
        
        if not isinstance(self.item_type, ItemType):
            raise ValueError(f"Invalid item type: {self.item_type}")
        
        if not self.brand_id:
            raise ValueError("Brand ID cannot be empty")
        
        if not self.category_id:
            raise ValueError("Category ID cannot be empty")
        
        if not self.unit_of_measurement_id:
            raise ValueError("Unit of measurement ID cannot be empty")
    
    def update_details(
        self,
        item_name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update item details."""
        if item_name:
            self.item_name = item_name
        if description is not None:  # Allow clearing description
            self.description = description
        
        self._validate()
        self.update_timestamp(updated_by)
    
    def update_classification(
        self,
        item_type: Optional[ItemType] = None,
        brand_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        unit_of_measurement_id: Optional[UUID] = None,
        updated_by: Optional[str] = None
    ):
        """Update item classification."""
        if item_type:
            self.item_type = item_type
        if brand_id:
            self.brand_id = brand_id
        if category_id:
            self.category_id = category_id
        if unit_of_measurement_id:
            self.unit_of_measurement_id = unit_of_measurement_id
        
        self._validate()
        self.update_timestamp(updated_by)
    
    def is_rental_item(self) -> bool:
        """Check if this is a rental item."""
        return self.item_type == ItemType.RENTAL
    
    def is_sale_item(self) -> bool:
        """Check if this is a sale item."""
        return self.item_type == ItemType.SALE
    
    def is_service_item(self) -> bool:
        """Check if this is a service item."""
        return self.item_type == ItemType.SERVICE
    
    def is_consumable_item(self) -> bool:
        """Check if this is a consumable item."""
        return self.item_type == ItemType.CONSUMABLE