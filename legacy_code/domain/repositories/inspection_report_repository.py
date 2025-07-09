from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities.inspection_report import InspectionReport
from ..value_objects.inspection_type import InspectionStatus, DamageSeverity
from ..value_objects.item_type import ConditionGrade


class InspectionReportRepository(ABC):
    """Abstract repository for inspection reports."""
    
    @abstractmethod
    async def create(self, report: InspectionReport) -> InspectionReport:
        """Create a new inspection report."""
        pass
    
    @abstractmethod
    async def get_by_id(self, report_id: UUID) -> Optional[InspectionReport]:
        """Get inspection report by ID."""
        pass
    
    @abstractmethod
    async def get_by_return_id(self, return_id: UUID) -> List[InspectionReport]:
        """Get all inspection reports for a return."""
        pass
    
    @abstractmethod
    async def get_by_inventory_unit_id(self, unit_id: UUID) -> List[InspectionReport]:
        """Get all inspection reports for an inventory unit."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        return_id: Optional[UUID] = None,
        inventory_unit_id: Optional[UUID] = None,
        inspector_id: Optional[str] = None,
        inspection_status: Optional[InspectionStatus] = None,
        damage_severity: Optional[DamageSeverity] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[InspectionReport], int]:
        """List inspection reports with filters and pagination."""
        pass
    
    @abstractmethod
    async def update(self, report: InspectionReport) -> InspectionReport:
        """Update an existing inspection report."""
        pass
    
    @abstractmethod
    async def delete(self, report_id: UUID) -> bool:
        """Soft delete an inspection report."""
        pass
    
    @abstractmethod
    async def get_pending_inspections(
        self,
        inspector_id: Optional[str] = None,
        location_id: Optional[UUID] = None
    ) -> List[InspectionReport]:
        """Get pending inspection reports."""
        pass
    
    @abstractmethod
    async def get_reports_with_damage(
        self,
        damage_severity: Optional[DamageSeverity] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[InspectionReport]:
        """Get inspection reports with damage."""
        pass
    
    @abstractmethod
    async def get_reports_by_inspector(
        self,
        inspector_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[InspectionReport]:
        """Get inspection reports by inspector."""
        pass
    
    @abstractmethod
    async def get_unapproved_reports(
        self,
        location_id: Optional[UUID] = None
    ) -> List[InspectionReport]:
        """Get unapproved inspection reports."""
        pass
    
    @abstractmethod
    async def count_reports_by_status(
        self,
        inspector_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """Count inspection reports by status."""
        pass
    
    @abstractmethod
    async def get_damage_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        location_id: Optional[UUID] = None
    ) -> dict:
        """Get damage statistics from inspection reports."""
        pass