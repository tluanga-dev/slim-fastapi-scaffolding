from typing import List, Dict, Optional, Tuple
from uuid import UUID

from ....domain.entities.item import Item
from ....domain.repositories.item_repository import ItemRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.location_repository import LocationRepository
from ....domain.repositories.category_repository import CategoryRepository
from ....domain.repositories.brand_repository import BrandRepository
from ....domain.value_objects.item_type import InventoryStatus


class GetRentableItemsWithAvailabilityUseCase:
    """Use case for getting rentable items with availability information."""
    
    def __init__(
        self,
        item_repository: ItemRepository,
        stock_repository: StockLevelRepository,
        location_repository: LocationRepository,
        category_repository: CategoryRepository,
        brand_repository: BrandRepository
    ):
        """Initialize use case with repositories."""
        self.item_repository = item_repository
        self.stock_repository = stock_repository
        self.location_repository = location_repository
        self.category_repository = category_repository
        self.brand_repository = brand_repository
    
    async def execute(
        self,
        search: Optional[str] = None,
        location_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        Execute rentable items with availability retrieval.
        
        Args:
            search: Search term for item name or SKU
            location_id: Optional location filter
            category_id: Optional category filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (items with availability info, total count)
        """
        # Get rentable items with basic filtering
        rentable_items = await self.item_repository.get_rentable_items_with_search(
            search=search,
            category_id=category_id,
            skip=skip,
            limit=limit
        )
        
        # Get total count for pagination
        total_count = await self.item_repository.count_rentable_items(
            search=search,
            category_id=category_id
        )
        
        if not rentable_items:
            return [], total_count
        
        # Build result with availability information
        results = []
        for item in rentable_items:
            item_data = await self._build_item_with_availability(item, location_id)
            # Only include items that have availability > 0
            if item_data['availability']['total_available'] > 0:
                results.append(item_data)
        
        return results, total_count
    
    async def _build_item_with_availability(
        self, 
        item: Item, 
        location_id: Optional[UUID] = None
    ) -> Dict:
        """Build item data with availability information."""
        
        # Get availability information
        availability = await self._get_item_availability(item.id, location_id)
        
        # Get category and brand information
        category = None
        brand = None
        
        if item.category_id:
            category = await self.category_repository.get_by_id(item.category_id)
        
        if item.brand_id:
            brand = await self.brand_repository.get_by_id(item.brand_id)
        
        return {
            'id': str(item.id),
            'sku': item.sku,
            'item_name': item.item_name,
            'category': {
                'id': str(category.id) if category else None,
                'name': category.category_name if category else None
            } if category else None,
            'brand': {
                'id': str(brand.id) if brand else None,
                'name': brand.brand_name if brand else None
            } if brand else None,
            'rental_pricing': {
                'base_price': float(item.rental_base_price) if item.rental_base_price else None,
                'min_rental_days': item.min_rental_days,
                'max_rental_days': item.max_rental_days,
                'rental_period': str(item.rental_period) if item.rental_period else None
            },
            'availability': availability,
            'item_details': {
                'model_number': item.model_number,
                'barcode': item.barcode,
                'weight': float(item.weight) if item.weight else None,
                'dimensions': str(item.dimensions) if item.dimensions else None,
                'is_serialized': item.is_serialized
            }
        }
    
    async def _get_item_availability(
        self, 
        item_id: UUID, 
        location_id: Optional[UUID] = None
    ) -> Dict:
        """Get availability information for an item."""
        
        if location_id:
            # Get availability for specific location
            stock_level = await self.stock_repository.get_by_item_location(item_id, location_id)
            
            if not stock_level:
                return {
                    'total_available': 0,
                    'locations': []
                }
            
            # Get location details
            location = await self.location_repository.get_by_id(location_id)
            
            # Count available units with AVAILABLE_RENT status
            available_quantity = await self._count_available_rental_units(
                item_id, location_id
            )
            
            return {
                'total_available': available_quantity,
                'locations': [{
                    'location_id': str(location_id),
                    'location_name': location.location_name if location else 'Unknown',
                    'available_quantity': available_quantity,
                    'total_stock': stock_level.quantity_on_hand
                }] if available_quantity > 0 else []
            }
        else:
            # Get availability across all locations
            stock_levels, _ = await self.stock_repository.list(item_id=item_id)
            
            total_available = 0
            locations_with_stock = []
            
            for stock_level in stock_levels:
                if stock_level.quantity_available > 0:
                    available_quantity = await self._count_available_rental_units(
                        item_id, stock_level.location_id
                    )
                    
                    if available_quantity > 0:
                        location = await self.location_repository.get_by_id(stock_level.location_id)
                        locations_with_stock.append({
                            'location_id': str(stock_level.location_id),
                            'location_name': location.location_name if location else 'Unknown',
                            'available_quantity': available_quantity,
                            'total_stock': stock_level.quantity_on_hand
                        })
                        total_available += available_quantity
            
            return {
                'total_available': total_available,
                'locations': locations_with_stock
            }
    
    async def _count_available_rental_units(
        self, 
        item_id: UUID, 
        location_id: UUID
    ) -> int:
        """Count units available for rental at a specific location."""
        # This would need to be implemented in the stock repository
        # For now, we'll use the stock level's quantity_available
        # In a real implementation, this would query inventory_units
        # with status = AVAILABLE_RENT
        
        stock_level = await self.stock_repository.get_by_item_location(item_id, location_id)
        if not stock_level:
            return 0
        
        # For now, assume available quantity represents rental availability
        # In a more sophisticated implementation, this would check actual
        # inventory units with AVAILABLE_RENT status
        return stock_level.quantity_available