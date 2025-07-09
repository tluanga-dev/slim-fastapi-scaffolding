from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.rental_return_line import RentalReturnLine
from ...domain.repositories.rental_return_line_repository import RentalReturnLineRepository
from ..models.rental_return_line_model import RentalReturnLineModel


class SQLAlchemyRentalReturnLineRepository(RentalReturnLineRepository):
    """SQLAlchemy implementation of RentalReturnLineRepository."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db
    
    async def create(self, return_line: RentalReturnLine) -> RentalReturnLine:
        """Create a new rental return line."""
        db_line = RentalReturnLineModel.from_entity(return_line)
        self.db.add(db_line)
        await self.db.commit()
        await self.db.refresh(db_line)
        return db_line.to_entity()
    
    async def create_batch(self, return_lines: List[RentalReturnLine]) -> List[RentalReturnLine]:
        """Create multiple rental return lines."""
        db_lines = [RentalReturnLineModel.from_entity(line) for line in return_lines]
        self.db.add_all(db_lines)
        await self.db.commit()
        
        # Refresh all lines
        for db_line in db_lines:
            await self.db.refresh(db_line)
        
        return [db_line.to_entity() for db_line in db_lines]
    
    async def get_by_id(self, line_id: UUID) -> Optional[RentalReturnLine]:
        """Get rental return line by ID."""
        query = select(RentalReturnLineModel).where(
            and_(
                RentalReturnLineModel.id == line_id,
                RentalReturnLineModel.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        db_line = result.scalar_one_or_none()
        
        return db_line.to_entity() if db_line else None
    
    async def get_by_return_id(self, return_id: UUID) -> List[RentalReturnLine]:
        """Get all return lines for a return."""
        query = select(RentalReturnLineModel).where(
            and_(
                RentalReturnLineModel.return_id == return_id,
                RentalReturnLineModel.is_active == True
            )
        ).order_by(RentalReturnLineModel.created_at.asc())
        
        result = await self.db.execute(query)
        db_lines = result.scalars().all()
        
        return [db_line.to_entity() for db_line in db_lines]
    
    async def update(self, return_line: RentalReturnLine) -> RentalReturnLine:
        """Update an existing rental return line."""
        query = select(RentalReturnLineModel).where(RentalReturnLineModel.id == return_line.id)
        result = await self.db.execute(query)
        db_line = result.scalar_one_or_none()
        
        if not db_line:
            raise ValueError(f"Rental return line with ID {return_line.id} not found")
        
        db_line.update_from_entity(return_line)
        await self.db.commit()
        await self.db.refresh(db_line)
        return db_line.to_entity()
    
    async def delete(self, line_id: UUID) -> bool:
        """Soft delete a rental return line."""
        query = select(RentalReturnLineModel).where(RentalReturnLineModel.id == line_id)
        result = await self.db.execute(query)
        db_line = result.scalar_one_or_none()
        
        if not db_line:
            return False
        
        db_line.is_active = False
        await self.db.commit()
        return True
    
    async def get_by_inventory_unit(self, inventory_unit_id: UUID) -> List[RentalReturnLine]:
        """Get all return lines for a specific inventory unit."""
        query = select(RentalReturnLineModel).where(
            and_(
                RentalReturnLineModel.inventory_unit_id == inventory_unit_id,
                RentalReturnLineModel.is_active == True
            )
        ).order_by(RentalReturnLineModel.created_at.desc())
        
        result = await self.db.execute(query)
        db_lines = result.scalars().all()
        
        return [db_line.to_entity() for db_line in db_lines]
    
    async def get_unprocessed_lines(self, return_id: Optional[UUID] = None) -> List[RentalReturnLine]:
        """Get unprocessed return lines."""
        filters = [
            RentalReturnLineModel.is_processed == False,
            RentalReturnLineModel.returned_quantity > 0,
            RentalReturnLineModel.is_active == True
        ]
        
        if return_id:
            filters.append(RentalReturnLineModel.return_id == return_id)
        
        query = select(RentalReturnLineModel).where(
            and_(*filters)
        ).order_by(RentalReturnLineModel.created_at.asc())
        
        result = await self.db.execute(query)
        db_lines = result.scalars().all()
        
        return [db_line.to_entity() for db_line in db_lines]