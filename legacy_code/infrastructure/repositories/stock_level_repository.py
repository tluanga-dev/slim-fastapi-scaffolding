from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.stock_level import StockLevel
from ...domain.repositories.stock_level_repository import StockLevelRepository
from ..models.stock_level_model import StockLevelModel


class SQLAlchemyStockLevelRepository(StockLevelRepository):
    """SQLAlchemy implementation of StockLevelRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, stock_level: StockLevel) -> StockLevel:
        """Create a new stock level record."""
        db_stock = StockLevelModel.from_entity(stock_level)
        self.session.add(db_stock)
        await self.session.flush()  # Flush to get the ID, but don't commit
        await self.session.refresh(db_stock)
        return db_stock.to_entity()
    
    async def get_by_id(self, stock_level_id: UUID) -> Optional[StockLevel]:
        """Get stock level by ID."""
        query = select(StockLevelModel).where(StockLevelModel.id == stock_level_id)
        result = await self.session.execute(query)
        db_stock = result.scalar_one_or_none()
        
        if db_stock:
            return db_stock.to_entity()
        return None
    
    async def get_by_item_location(self, item_id: UUID, location_id: UUID) -> Optional[StockLevel]:
        """Get stock level for a specific Item at a location."""
        query = select(StockLevelModel).where(
            and_(
                StockLevelModel.item_id == item_id,
                StockLevelModel.location_id == location_id,
                StockLevelModel.is_active == True
            )
        )
        result = await self.session.execute(query)
        db_stock = result.scalar_one_or_none()
        
        if db_stock:
            return db_stock.to_entity()
        return None
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        location_id: Optional[UUID] = None,
        item_id: Optional[UUID] = None,
        low_stock_only: bool = False,
        is_active: Optional[bool] = True
    ) -> Tuple[List[StockLevel], int]:
        """List stock levels with filters and pagination."""
        # Base query
        query = select(StockLevelModel)
        count_query = select(func.count()).select_from(StockLevelModel)
        
        # Apply filters
        filters = []
        
        if is_active is not None:
            filters.append(StockLevelModel.is_active == is_active)
        
        if location_id:
            filters.append(StockLevelModel.location_id == location_id)
        
        if item_id:
            filters.append(StockLevelModel.item_id == item_id)
        
        if low_stock_only:
            filters.append(StockLevelModel.quantity_available <= StockLevelModel.reorder_point)
        
        # Apply all filters
        if filters:
            where_clause = and_(*filters)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(
            StockLevelModel.quantity_available.asc() if low_stock_only else StockLevelModel.id
        ).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        stock_levels = result.scalars().all()
        
        return [stock.to_entity() for stock in stock_levels], total_count
    
    async def update(self, stock_level: StockLevel) -> StockLevel:
        """Update existing stock level."""
        query = select(StockLevelModel).where(StockLevelModel.id == stock_level.id)
        result = await self.session.execute(query)
        db_stock = result.scalar_one_or_none()
        
        if not db_stock:
            raise ValueError(f"Stock level with id {stock_level.id} not found")
        
        # Update fields
        db_stock.item_id = stock_level.item_id
        db_stock.location_id = stock_level.location_id
        db_stock.quantity_on_hand = stock_level.quantity_on_hand
        db_stock.quantity_available = stock_level.quantity_available
        db_stock.quantity_reserved = stock_level.quantity_reserved
        db_stock.quantity_in_transit = stock_level.quantity_in_transit
        db_stock.quantity_damaged = stock_level.quantity_damaged
        db_stock.reorder_point = stock_level.reorder_point
        db_stock.reorder_quantity = stock_level.reorder_quantity
        db_stock.maximum_stock = stock_level.maximum_stock
        db_stock.updated_at = stock_level.updated_at
        db_stock.updated_by = stock_level.updated_by
        db_stock.is_active = stock_level.is_active
        
        await self.session.flush()  # Flush to persist changes, but don't commit
        await self.session.refresh(db_stock)
        
        return db_stock.to_entity()
    
    async def delete(self, stock_level_id: UUID) -> bool:
        """Soft delete stock level by setting is_active to False."""
        query = select(StockLevelModel).where(StockLevelModel.id == stock_level_id)
        result = await self.session.execute(query)
        db_stock = result.scalar_one_or_none()
        
        if not db_stock:
            return False
        
        db_stock.is_active = False
        await self.session.flush()  # Flush to persist changes, but don't commit
        
        return True
    
    async def get_or_create(self, item_id: UUID, location_id: UUID) -> StockLevel:
        """Get existing stock level or create new one."""
        existing = await self.get_by_item_location(item_id, location_id)
        if existing:
            return existing
        
        # Create new stock level
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=0,
            quantity_available=0,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0,
            reorder_point=0,
            reorder_quantity=1
        )
        
        return await self.create(stock_level)
    
    async def get_total_stock_by_item(self, item_id: UUID) -> dict:
        """Get total stock quantities across all locations for an Item."""
        query = select(
            func.sum(StockLevelModel.quantity_on_hand).label('total_on_hand'),
            func.sum(StockLevelModel.quantity_available).label('total_available'),
            func.sum(StockLevelModel.quantity_reserved).label('total_reserved'),
            func.sum(StockLevelModel.quantity_in_transit).label('total_in_transit'),
            func.sum(StockLevelModel.quantity_damaged).label('total_damaged')
        ).where(
            and_(
                StockLevelModel.item_id == item_id,
                StockLevelModel.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        row = result.one()
        
        return {
            'total_on_hand': row.total_on_hand or 0,
            'total_available': row.total_available or 0,
            'total_reserved': row.total_reserved or 0,
            'total_in_transit': row.total_in_transit or 0,
            'total_damaged': row.total_damaged or 0
        }
    
    async def get_stock_by_location(self, location_id: UUID) -> List[StockLevel]:
        """Get all stock levels for a location."""
        query = select(StockLevelModel).where(
            and_(
                StockLevelModel.location_id == location_id,
                StockLevelModel.is_active == True
            )
        ).order_by(StockLevelModel.quantity_available.asc())
        
        result = await self.session.execute(query)
        stock_levels = result.scalars().all()
        
        return [stock.to_entity() for stock in stock_levels]
    
    async def get_low_stock_items(
        self,
        location_id: Optional[UUID] = None,
        include_zero: bool = True
    ) -> List[StockLevel]:
        """Get items that are at or below reorder point."""
        query = select(StockLevelModel).where(
            and_(
                StockLevelModel.is_active == True,
                StockLevelModel.quantity_available <= StockLevelModel.reorder_point
            )
        )
        
        if location_id:
            query = query.where(StockLevelModel.location_id == location_id)
        
        if not include_zero:
            query = query.where(StockLevelModel.quantity_available > 0)
        
        # Order by urgency (lowest available first)
        query = query.order_by(StockLevelModel.quantity_available.asc())
        
        result = await self.session.execute(query)
        stock_levels = result.scalars().all()
        
        return [stock.to_entity() for stock in stock_levels]
    
    async def get_overstock_items(self, location_id: Optional[UUID] = None) -> List[StockLevel]:
        """Get items that exceed maximum stock level."""
        query = select(StockLevelModel).where(
            and_(
                StockLevelModel.is_active == True,
                StockLevelModel.maximum_stock != None,
                StockLevelModel.quantity_on_hand > StockLevelModel.maximum_stock
            )
        )
        
        if location_id:
            query = query.where(StockLevelModel.location_id == location_id)
        
        # Order by overage amount descending
        query = query.order_by(
            (StockLevelModel.quantity_on_hand - StockLevelModel.maximum_stock).desc()
        )
        
        result = await self.session.execute(query)
        stock_levels = result.scalars().all()
        
        return [stock.to_entity() for stock in stock_levels]
    
    async def check_availability(
        self,
        item_id: UUID,
        quantity: int,
        location_id: Optional[UUID] = None
    ) -> Tuple[bool, int]:
        """Check if quantity is available. Returns (is_available, total_available)."""
        if location_id:
            # Check specific location
            stock = await self.get_by_item_location(item_id, location_id)
            if stock:
                available = stock.quantity_available
                return available >= quantity, available
            return False, 0
        else:
            # Check across all locations
            totals = await self.get_total_stock_by_item(item_id)
            available = totals['total_available']
            return available >= quantity, available
    
    async def get_stock_valuation(self, location_id: Optional[UUID] = None) -> dict:
        """Get stock valuation summary."""
        # This would typically join with SKU/Item tables for pricing
        # For now, return basic quantities
        query = select(
            func.count(StockLevelModel.id).label('total_skus'),
            func.sum(StockLevelModel.quantity_on_hand).label('total_units'),
            func.sum(StockLevelModel.quantity_available).label('total_available'),
            func.sum(StockLevelModel.quantity_damaged).label('total_damaged')
        ).where(
            StockLevelModel.is_active == True
        )
        
        if location_id:
            query = query.where(StockLevelModel.location_id == location_id)
        
        result = await self.session.execute(query)
        row = result.one()
        
        return {
            'total_items': row.total_skus or 0,
            'total_units': row.total_units or 0,
            'total_available': row.total_available or 0,
            'total_damaged': row.total_damaged or 0
        }
    
    async def transfer_stock(
        self,
        item_id: UUID,
        from_location_id: UUID,
        to_location_id: UUID,
        quantity: int,
        updated_by: Optional[str] = None
    ) -> Tuple[StockLevel, StockLevel]:
        """Transfer stock between locations. Returns (from_stock, to_stock)."""
        # Get source stock level
        from_stock = await self.get_by_item_location(item_id, from_location_id)
        if not from_stock:
            raise ValueError(f"No stock found for Item {item_id} at location {from_location_id}")
        
        # Check availability
        if from_stock.quantity_available < quantity:
            raise ValueError(
                f"Insufficient stock. Available: {from_stock.quantity_available}, "
                f"Requested: {quantity}"
            )
        
        # Get or create destination stock level
        to_stock = await self.get_or_create(item_id, to_location_id)
        
        # Perform transfer
        from_stock.quantity_available -= quantity
        from_stock.quantity_on_hand -= quantity
        from_stock.update_timestamp(updated_by)
        
        to_stock.quantity_available += quantity
        to_stock.quantity_on_hand += quantity
        to_stock.update_timestamp(updated_by)
        
        # Save changes
        from_stock = await self.update(from_stock)
        to_stock = await self.update(to_stock)
        
        return from_stock, to_stock