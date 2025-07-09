from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.inspection_report import InspectionReport
from ...domain.repositories.inspection_report_repository import InspectionReportRepository
from ...domain.value_objects.inspection_type import InspectionStatus
from ..models.inspection_report_model import InspectionReportModel


class SQLAlchemyInspectionReportRepository(InspectionReportRepository):
    """SQLAlchemy implementation of InspectionReportRepository."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db
    
    async def create(self, inspection_report: InspectionReport) -> InspectionReport:
        """Create a new inspection report."""
        db_report = InspectionReportModel.from_entity(inspection_report)
        self.db.add(db_report)
        await self.db.commit()
        await self.db.refresh(db_report)
        return db_report.to_entity()
    
    async def get_by_id(self, report_id: UUID) -> Optional[InspectionReport]:
        """Get inspection report by ID."""
        query = select(InspectionReportModel).where(
            and_(
                InspectionReportModel.id == report_id,
                InspectionReportModel.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        db_report = result.scalar_one_or_none()
        
        return db_report.to_entity() if db_report else None
    
    async def get_by_return_id(self, return_id: UUID) -> List[InspectionReport]:
        """Get all inspection reports for a return."""
        query = select(InspectionReportModel).where(
            and_(
                InspectionReportModel.return_id == return_id,
                InspectionReportModel.is_active == True
            )
        ).order_by(InspectionReportModel.inspection_date.desc())
        
        result = await self.db.execute(query)
        db_reports = result.scalars().all()
        
        return [db_report.to_entity() for db_report in db_reports]
    
    async def update(self, inspection_report: InspectionReport) -> InspectionReport:
        """Update an existing inspection report."""
        query = select(InspectionReportModel).where(InspectionReportModel.id == inspection_report.id)
        result = await self.db.execute(query)
        db_report = result.scalar_one_or_none()
        
        if not db_report:
            raise ValueError(f"Inspection report with ID {inspection_report.id} not found")
        
        db_report.update_from_entity(inspection_report)
        await self.db.commit()
        await self.db.refresh(db_report)
        return db_report.to_entity()
    
    async def delete(self, report_id: UUID) -> bool:
        """Soft delete an inspection report."""
        query = select(InspectionReportModel).where(InspectionReportModel.id == report_id)
        result = await self.db.execute(query)
        db_report = result.scalar_one_or_none()
        
        if not db_report:
            return False
        
        db_report.is_active = False
        await self.db.commit()
        return True
    
    async def get_by_inspector(
        self,
        inspector_id: str,
        status: Optional[InspectionStatus] = None
    ) -> List[InspectionReport]:
        """Get inspection reports by inspector."""
        filters = [
            InspectionReportModel.inspector_id == inspector_id,
            InspectionReportModel.is_active == True
        ]
        
        if status:
            filters.append(InspectionReportModel.inspection_status == status.value)
        
        query = select(InspectionReportModel).where(
            and_(*filters)
        ).order_by(InspectionReportModel.inspection_date.desc())
        
        result = await self.db.execute(query)
        db_reports = result.scalars().all()
        
        return [db_report.to_entity() for db_report in db_reports]
    
    async def get_pending_approvals(self) -> List[InspectionReport]:
        """Get inspection reports pending approval."""
        query = select(InspectionReportModel).where(
            and_(
                InspectionReportModel.inspection_status == InspectionStatus.COMPLETED.value,
                InspectionReportModel.is_approved == False,
                InspectionReportModel.is_active == True
            )
        ).order_by(InspectionReportModel.inspection_date.asc())
        
        result = await self.db.execute(query)
        db_reports = result.scalars().all()
        
        return [db_report.to_entity() for db_report in db_reports]