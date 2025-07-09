from typing import Optional, List, Dict
from uuid import UUID
from decimal import Decimal

from ....domain.entities.stock_level import StockLevel
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.item_repository import ItemRepository
from ....domain.repositories.location_repository import LocationRepository


class UpdateStockLevelsUseCase:
    """Use case for updating stock levels."""
    
    def __init__(
        self,
        stock_repository: StockLevelRepository,
        item_repository: ItemRepository,
        location_repository: LocationRepository
    ):
        """Initialize use case with repositories."""
        self.stock_repository = stock_repository
        self.item_repository = item_repository
        self.location_repository = location_repository
    
    async def execute(
        self,
        item_id: UUID,
        location_id: UUID,
        operation: str,
        quantity: int,
        reason: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> StockLevel:
        """Execute stock level update operation."""
        # Verify Item exists
        item = await self.item_repository.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found")
        
        # Verify location exists
        location = await self.location_repository.get_by_id(location_id)
        if not location:
            raise ValueError(f"Location with id {location_id} not found")
        
        # Get or create stock level
        stock_level = await self.stock_repository.get_or_create(item_id, location_id)
        
        # Perform operation
        if operation == "receive":
            stock_level.receive_stock(quantity, updated_by)
        elif operation == "reserve":
            stock_level.reserve_stock(quantity, updated_by)
        elif operation == "release":
            stock_level.release_stock(quantity, updated_by)
        elif operation == "ship":
            stock_level.ship_stock(quantity, updated_by)
        elif operation == "damage":
            stock_level.mark_damaged(quantity, updated_by)
        elif operation == "undamage":
            stock_level.unmark_damaged(quantity, updated_by)
        elif operation == "adjust":
            await self._adjust_stock(stock_level, quantity, reason, updated_by)
        else:
            raise ValueError(f"Invalid operation: {operation}")
        
        # Save updated stock level
        updated_stock = await self.stock_repository.update(stock_level)
        
        return updated_stock
    
    async def set_reorder_parameters(
        self,
        item_id: UUID,
        location_id: UUID,
        reorder_point: int,
        reorder_quantity: int,
        maximum_stock: Optional[int] = None,
        updated_by: Optional[str] = None
    ) -> StockLevel:
        """Set reorder parameters for a SKU at a location."""
        # Get or create stock level
        stock_level = await self.stock_repository.get_or_create(item_id, location_id)
        
        # Update reorder parameters
        stock_level.set_reorder_point(reorder_point, updated_by)
        stock_level.reorder_quantity = reorder_quantity
        
        if maximum_stock is not None:
            stock_level.maximum_stock = maximum_stock
        
        stock_level.update_timestamp(updated_by)
        
        # Save changes
        updated_stock = await self.stock_repository.update(stock_level)
        
        return updated_stock
    
    async def bulk_receive(
        self,
        items: List[Dict[str, any]],
        location_id: UUID,
        reference_number: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> List[StockLevel]:
        """Receive multiple items in bulk."""
        updated_stocks = []
        
        for item in items:
            item_id = item.get('item_id')
            quantity = item.get('quantity', 0)
            
            if quantity > 0:
                stock_level = await self.execute(
                    item_id=item_id,
                    location_id=location_id,
                    operation="receive",
                    quantity=quantity,
                    reason=f"Bulk receive - Ref: {reference_number}" if reference_number else "Bulk receive",
                    updated_by=updated_by
                )
                updated_stocks.append(stock_level)
        
        return updated_stocks
    
    async def reconcile_stock(
        self,
        item_id: UUID,
        location_id: UUID,
        physical_count: int,
        reason: str,
        updated_by: Optional[str] = None
    ) -> StockLevel:
        """Reconcile stock to match physical count."""
        # Get current stock level
        stock_level = await self.stock_repository.get_or_create(item_id, location_id)
        
        # Calculate adjustment needed
        current_on_hand = stock_level.quantity_on_hand
        adjustment = physical_count - current_on_hand
        
        if adjustment != 0:
            # Adjust stock to match physical count
            await self._adjust_stock(
                stock_level,
                adjustment,
                f"Stock reconciliation: {reason}",
                updated_by
            )
            
            # Save changes
            stock_level = await self.stock_repository.update(stock_level)
        
        return stock_level
    
    async def get_stock_valuation(
        self,
        location_id: Optional[UUID] = None
    ) -> Dict:
        """Get stock valuation summary."""
        valuation = await self.stock_repository.get_stock_valuation(location_id)
        
        # Get location details if specified
        if location_id:
            location = await self.location_repository.get_by_id(location_id)
            valuation['location_name'] = location.location_name if location else 'Unknown'
        
        return valuation
    
    async def get_overstock_report(
        self,
        location_id: Optional[UUID] = None
    ) -> List[Dict]:
        """Get report of overstocked items."""
        overstock_items = await self.stock_repository.get_overstock_items(location_id)
        
        report = []
        for stock_level in overstock_items:
            sku = await self.item_repository.get_by_id(stock_level.item_id)
            location = await self.location_repository.get_by_id(stock_level.location_id)
            
            overage = stock_level.quantity_on_hand - (stock_level.maximum_stock or 0)
            
            report.append({
                'item_id': str(stock_level.item_id),
                'sku_code': sku.sku_code if sku else 'Unknown',
                'sku_name': sku.sku_name if sku else 'Unknown',
                'location_id': str(stock_level.location_id),
                'location_name': location.location_name if location else 'Unknown',
                'quantity_on_hand': stock_level.quantity_on_hand,
                'maximum_stock': stock_level.maximum_stock,
                'overage': overage,
                'overage_percentage': round((overage / stock_level.maximum_stock) * 100, 2) if stock_level.maximum_stock else 0
            })
        
        return report
    
    async def _adjust_stock(
        self,
        stock_level: StockLevel,
        adjustment: int,
        reason: Optional[str],
        updated_by: Optional[str]
    ):
        """Perform stock adjustment."""
        if adjustment > 0:
            # Positive adjustment - add stock
            stock_level.quantity_on_hand += adjustment
            stock_level.quantity_available += adjustment
        else:
            # Negative adjustment - remove stock
            adjustment = abs(adjustment)
            if stock_level.quantity_available < adjustment:
                raise ValueError(
                    f"Cannot adjust stock. Available: {stock_level.quantity_available}, "
                    f"Adjustment: {adjustment}"
                )
            stock_level.quantity_on_hand -= adjustment
            stock_level.quantity_available -= adjustment
        
        stock_level.update_timestamp(updated_by)