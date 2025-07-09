from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from .models import TransactionHeaderModel, TransactionLineModel
from .enums import TransactionType, TransactionStatus, PaymentStatus, LineItemType
from .schemas import TransactionHeaderCreate, TransactionHeaderUpdate, TransactionLineCreate, TransactionLineUpdate


class TransactionHeaderRepository:
    """Repository for TransactionHeader operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, transaction_data: TransactionHeaderCreate) -> TransactionHeaderModel:
        """Create a new transaction header."""
        transaction = TransactionHeaderModel(**transaction_data.model_dump())
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
    
    async def get_by_id(self, transaction_id: UUID) -> Optional[TransactionHeaderModel]:
        """Get transaction header by ID."""
        stmt = select(TransactionHeaderModel).where(
            and_(
                TransactionHeaderModel.id == transaction_id,
                TransactionHeaderModel.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_transaction_number(self, transaction_number: str) -> Optional[TransactionHeaderModel]:
        """Get transaction header by transaction number."""
        stmt = select(TransactionHeaderModel).where(
            and_(
                TransactionHeaderModel.transaction_number == transaction_number,
                TransactionHeaderModel.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_with_details(self, transaction_id: UUID) -> Optional[TransactionHeaderModel]:
        """Get transaction header with all related details."""
        stmt = select(TransactionHeaderModel).options(
            selectinload(TransactionHeaderModel.lines),
            selectinload(TransactionHeaderModel.customer),
            selectinload(TransactionHeaderModel.location),
            selectinload(TransactionHeaderModel.sales_person),
            selectinload(TransactionHeaderModel.reference_transaction)
        ).where(
            and_(
                TransactionHeaderModel.id == transaction_id,
                TransactionHeaderModel.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TransactionHeaderModel]:
        """Get all transaction headers with optional filtering."""
        stmt = select(TransactionHeaderModel).where(TransactionHeaderModel.is_active == True)
        
        # Apply filters
        if transaction_type:
            stmt = stmt.where(TransactionHeaderModel.transaction_type == transaction_type)
        
        if status:
            stmt = stmt.where(TransactionHeaderModel.status == status)
        
        if payment_status:
            stmt = stmt.where(TransactionHeaderModel.payment_status == payment_status)
        
        if customer_id:
            stmt = stmt.where(TransactionHeaderModel.customer_id == customer_id)
        
        if location_id:
            stmt = stmt.where(TransactionHeaderModel.location_id == location_id)
        
        if start_date:
            stmt = stmt.where(TransactionHeaderModel.transaction_date >= start_date)
        
        if end_date:
            stmt = stmt.where(TransactionHeaderModel.transaction_date <= end_date)
        
        # Add ordering and pagination
        stmt = stmt.order_by(TransactionHeaderModel.transaction_date.desc())
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def count_all(
        self,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count all transaction headers with optional filtering."""
        stmt = select(func.count(TransactionHeaderModel.id)).where(
            TransactionHeaderModel.is_active == True
        )
        
        # Apply same filters as get_all
        if transaction_type:
            stmt = stmt.where(TransactionHeaderModel.transaction_type == transaction_type)
        
        if status:
            stmt = stmt.where(TransactionHeaderModel.status == status)
        
        if payment_status:
            stmt = stmt.where(TransactionHeaderModel.payment_status == payment_status)
        
        if customer_id:
            stmt = stmt.where(TransactionHeaderModel.customer_id == customer_id)
        
        if location_id:
            stmt = stmt.where(TransactionHeaderModel.location_id == location_id)
        
        if start_date:
            stmt = stmt.where(TransactionHeaderModel.transaction_date >= start_date)
        
        if end_date:
            stmt = stmt.where(TransactionHeaderModel.transaction_date <= end_date)
        
        result = await self.session.execute(stmt)
        return result.scalar()
    
    async def update(
        self, 
        transaction_id: UUID, 
        transaction_data: TransactionHeaderUpdate
    ) -> Optional[TransactionHeaderModel]:
        """Update a transaction header."""
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return None
        
        update_data = transaction_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)
        
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
    
    async def delete(self, transaction_id: UUID) -> bool:
        """Soft delete a transaction header."""
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return False
        
        transaction.is_active = False
        await self.session.commit()
        return True
    
    async def get_by_customer(
        self, 
        customer_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionHeaderModel]:
        """Get all transactions for a specific customer."""
        stmt = select(TransactionHeaderModel).where(
            and_(
                TransactionHeaderModel.customer_id == customer_id,
                TransactionHeaderModel.is_active == True
            )
        ).order_by(TransactionHeaderModel.transaction_date.desc())
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_pending_payments(self) -> List[TransactionHeaderModel]:
        """Get all transactions with pending or partial payments."""
        stmt = select(TransactionHeaderModel).where(
            and_(
                TransactionHeaderModel.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.PARTIAL]),
                TransactionHeaderModel.is_active == True
            )
        ).order_by(TransactionHeaderModel.transaction_date.asc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_reference_transaction(
        self, 
        reference_transaction_id: UUID
    ) -> List[TransactionHeaderModel]:
        """Get all transactions that reference another transaction."""
        stmt = select(TransactionHeaderModel).where(
            and_(
                TransactionHeaderModel.reference_transaction_id == reference_transaction_id,
                TransactionHeaderModel.is_active == True
            )
        ).order_by(TransactionHeaderModel.transaction_date.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()


class TransactionLineRepository:
    """Repository for TransactionLine operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, line_data: TransactionLineCreate) -> TransactionLineModel:
        """Create a new transaction line."""
        line = TransactionLineModel(**line_data.model_dump())
        self.session.add(line)
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def get_by_id(self, line_id: UUID) -> Optional[TransactionLineModel]:
        """Get transaction line by ID."""
        stmt = select(TransactionLineModel).where(
            and_(
                TransactionLineModel.id == line_id,
                TransactionLineModel.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_transaction_id(
        self, 
        transaction_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionLineModel]:
        """Get all lines for a specific transaction."""
        stmt = select(TransactionLineModel).where(
            and_(
                TransactionLineModel.transaction_id == transaction_id,
                TransactionLineModel.is_active == True
            )
        ).order_by(TransactionLineModel.line_number.asc())
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_with_details(self, line_id: UUID) -> Optional[TransactionLineModel]:
        """Get transaction line with all related details."""
        stmt = select(TransactionLineModel).options(
            selectinload(TransactionLineModel.item),
            selectinload(TransactionLineModel.inventory_unit),
            selectinload(TransactionLineModel.transaction)
        ).where(
            and_(
                TransactionLineModel.id == line_id,
                TransactionLineModel.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_id: Optional[UUID] = None,
        line_type: Optional[LineItemType] = None,
        item_id: Optional[UUID] = None,
        inventory_unit_id: Optional[UUID] = None
    ) -> List[TransactionLineModel]:
        """Get all transaction lines with optional filtering."""
        stmt = select(TransactionLineModel).where(TransactionLineModel.is_active == True)
        
        # Apply filters
        if transaction_id:
            stmt = stmt.where(TransactionLineModel.transaction_id == transaction_id)
        
        if line_type:
            stmt = stmt.where(TransactionLineModel.line_type == line_type)
        
        if item_id:
            stmt = stmt.where(TransactionLineModel.item_id == item_id)
        
        if inventory_unit_id:
            stmt = stmt.where(TransactionLineModel.inventory_unit_id == inventory_unit_id)
        
        # Add ordering and pagination
        stmt = stmt.order_by(
            TransactionLineModel.transaction_id.asc(),
            TransactionLineModel.line_number.asc()
        )
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def count_all(
        self,
        transaction_id: Optional[UUID] = None,
        line_type: Optional[LineItemType] = None,
        item_id: Optional[UUID] = None,
        inventory_unit_id: Optional[UUID] = None
    ) -> int:
        """Count all transaction lines with optional filtering."""
        stmt = select(func.count(TransactionLineModel.id)).where(
            TransactionLineModel.is_active == True
        )
        
        # Apply same filters as get_all
        if transaction_id:
            stmt = stmt.where(TransactionLineModel.transaction_id == transaction_id)
        
        if line_type:
            stmt = stmt.where(TransactionLineModel.line_type == line_type)
        
        if item_id:
            stmt = stmt.where(TransactionLineModel.item_id == item_id)
        
        if inventory_unit_id:
            stmt = stmt.where(TransactionLineModel.inventory_unit_id == inventory_unit_id)
        
        result = await self.session.execute(stmt)
        return result.scalar()
    
    async def update(
        self, 
        line_id: UUID, 
        line_data: TransactionLineUpdate
    ) -> Optional[TransactionLineModel]:
        """Update a transaction line."""
        line = await self.get_by_id(line_id)
        if not line:
            return None
        
        update_data = line_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(line, field, value)
        
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def delete(self, line_id: UUID) -> bool:
        """Soft delete a transaction line."""
        line = await self.get_by_id(line_id)
        if not line:
            return False
        
        line.is_active = False
        await self.session.commit()
        return True
    
    async def get_next_line_number(self, transaction_id: UUID) -> int:
        """Get the next line number for a transaction."""
        stmt = select(func.max(TransactionLineModel.line_number)).where(
            and_(
                TransactionLineModel.transaction_id == transaction_id,
                TransactionLineModel.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        max_line_number = result.scalar()
        
        return (max_line_number or 0) + 1
    
    async def get_rental_lines_due(self, due_date: datetime) -> List[TransactionLineModel]:
        """Get all rental lines that are due by a specific date."""
        stmt = select(TransactionLineModel).where(
            and_(
                TransactionLineModel.line_type == LineItemType.RENTAL,
                TransactionLineModel.rental_end_date <= due_date.date(),
                TransactionLineModel.returned_quantity < TransactionLineModel.quantity,
                TransactionLineModel.is_active == True
            )
        ).order_by(TransactionLineModel.rental_end_date.asc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_item_id(
        self, 
        item_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionLineModel]:
        """Get all transaction lines for a specific item."""
        stmt = select(TransactionLineModel).where(
            and_(
                TransactionLineModel.item_id == item_id,
                TransactionLineModel.is_active == True
            )
        ).order_by(TransactionLineModel.created_at.desc())
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_inventory_unit_id(
        self, 
        inventory_unit_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TransactionLineModel]:
        """Get all transaction lines for a specific inventory unit."""
        stmt = select(TransactionLineModel).where(
            and_(
                TransactionLineModel.inventory_unit_id == inventory_unit_id,
                TransactionLineModel.is_active == True
            )
        ).order_by(TransactionLineModel.created_at.desc())
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()