from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from ....domain.entities.rental_return import RentalReturn
from ....domain.entities.rental_return_line import RentalReturnLine
from ....domain.entities.inspection_report import InspectionReport
from ....domain.repositories.rental_return_repository import RentalReturnRepository
from ....domain.repositories.rental_return_line_repository import RentalReturnLineRepository
from ....domain.repositories.inspection_report_repository import InspectionReportRepository
from ....domain.value_objects.rental_return_type import ReturnStatus
from ....domain.value_objects.inspection_type import InspectionStatus, DamageSeverity
from ....domain.value_objects.item_type import ConditionGrade


class AssessDamageUseCase:
    """Use case for assessing damage during rental returns."""
    
    def __init__(
        self,
        return_repository: RentalReturnRepository,
        line_repository: RentalReturnLineRepository,
        inspection_repository: InspectionReportRepository
    ):
        """Initialize use case with repositories."""
        self.return_repository = return_repository
        self.line_repository = line_repository
        self.inspection_repository = inspection_repository
    
    async def execute(
        self,
        return_id: UUID,
        inspector_id: str,
        line_assessments: List[Dict],  # [{"line_id": UUID, "condition_grade": str, "damage_description": str, "damage_photos": List[str], "estimated_repair_cost": Decimal}]
        general_notes: Optional[str] = None,
        inspection_date: Optional[datetime] = None
    ) -> InspectionReport:
        """Execute the assess damage use case."""
        
        # 1. Get the rental return
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise ValueError(f"Rental return {return_id} not found")
        
        # 2. Validate return status allows inspection
        if rental_return.return_status not in [ReturnStatus.INITIATED, ReturnStatus.IN_INSPECTION]:
            raise ValueError(f"Cannot inspect return in status {rental_return.return_status}")
        
        # 3. Get return lines
        return_lines = await self.line_repository.get_by_return_id(return_id)
        line_map = {line.id: line for line in return_lines}
        
        # 4. Validate all line assessments
        if not line_assessments:
            raise ValueError("At least one line assessment is required")
        
        for assessment in line_assessments:
            line_id = assessment.get("line_id")
            if not line_id or line_id not in line_map:
                raise ValueError(f"Invalid line_id: {line_id}")
            
            condition_grade = assessment.get("condition_grade")
            if condition_grade:
                try:
                    ConditionGrade(condition_grade)
                except ValueError:
                    raise ValueError(f"Invalid condition grade: {condition_grade}")
        
        # 5. Create inspection report
        inspection_report = InspectionReport(
            return_id=return_id,
            inspector_id=inspector_id,
            inspection_date=inspection_date or datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS,
            general_notes=general_notes
        )
        
        # 6. Process each line assessment
        total_damage_cost = Decimal("0.00")
        has_damage = False
        
        for assessment in line_assessments:
            line_id = assessment["line_id"]
            line = line_map[line_id]
            
            condition_grade = assessment.get("condition_grade")
            damage_description = assessment.get("damage_description", "")
            damage_photos = assessment.get("damage_photos", [])
            estimated_repair_cost = assessment.get("estimated_repair_cost", Decimal("0.00"))
            cleaning_required = assessment.get("cleaning_required", False)
            replacement_required = assessment.get("replacement_required", False)
            
            # Update line condition
            if condition_grade:
                try:
                    grade = ConditionGrade(condition_grade)
                    line.update_condition(grade, damage_description, inspector_id)
                    
                    # Determine if there's damage
                    if grade in [ConditionGrade.C, ConditionGrade.D]:
                        has_damage = True
                except ValueError:
                    continue  # Skip invalid grades
            
            # Set damage fees based on assessment
            if estimated_repair_cost > 0:
                line.set_damage_fee(estimated_repair_cost, inspector_id)
                total_damage_cost += estimated_repair_cost
                has_damage = True
            
            # Set cleaning fee if required
            if cleaning_required:
                cleaning_fee = assessment.get("cleaning_fee", Decimal("25.00"))  # Default cleaning fee
                line.set_cleaning_fee(cleaning_fee, inspector_id)
                total_damage_cost += cleaning_fee
            
            # Set replacement fee if required
            if replacement_required:
                replacement_fee = assessment.get("replacement_fee", Decimal("0.00"))
                if replacement_fee > 0:
                    line.set_replacement_fee(replacement_fee, inspector_id)
                    total_damage_cost += replacement_fee
                    has_damage = True
            
            # Update line with assessment
            await self.line_repository.update(line)
            
            # Add damage details to inspection report
            if damage_description or damage_photos or estimated_repair_cost > 0:
                severity = DamageSeverity.MINOR
                if estimated_repair_cost > 100:
                    severity = DamageSeverity.MAJOR
                elif estimated_repair_cost > 50:
                    severity = DamageSeverity.MODERATE
                
                inspection_report.add_damage_finding(
                    item_description=f"Line {line_id}",
                    damage_description=damage_description,
                    severity=severity,
                    estimated_cost=estimated_repair_cost,
                    photos=damage_photos
                )
        
        # 7. Finalize inspection report
        if has_damage:
            inspection_report.mark_damage_found(total_damage_cost)
        else:
            inspection_report.mark_no_damage_found()
        
        # 8. Create inspection report
        created_report = await self.inspection_repository.create(inspection_report)
        
        # 9. Update return status to in inspection if not already
        if rental_return.return_status == ReturnStatus.INITIATED:
            rental_return.update_status(ReturnStatus.IN_INSPECTION, inspector_id)
            await self.return_repository.update(rental_return)
        
        return created_report
    
    async def complete_inspection(
        self,
        inspection_report_id: UUID,
        approved: bool,
        approver_id: str,
        approval_notes: Optional[str] = None
    ) -> InspectionReport:
        """Complete an inspection with approval/rejection."""
        
        # 1. Get inspection report
        inspection_report = await self.inspection_repository.get_by_id(inspection_report_id)
        if not inspection_report:
            raise ValueError(f"Inspection report {inspection_report_id} not found")
        
        # 2. Validate can be completed
        if inspection_report.inspection_status != InspectionStatus.IN_PROGRESS:
            raise ValueError("Inspection is not in progress")
        
        # 3. Complete inspection
        if approved:
            inspection_report.approve_inspection(approver_id, approval_notes)
        else:
            inspection_report.reject_inspection(approver_id, approval_notes or "Inspection rejected")
        
        # 4. Update inspection report
        updated_report = await self.inspection_repository.update(inspection_report)
        
        # 5. If approved, we can proceed to finalize the return
        # This would typically trigger the FinalizeReturnUseCase
        
        return updated_report
    
    async def get_inspection_summary(self, return_id: UUID) -> Dict:
        """Get inspection summary for a return."""
        
        # 1. Get inspection reports for return
        reports = await self.inspection_repository.get_by_return_id(return_id)
        
        if not reports:
            return {
                "return_id": str(return_id),
                "has_inspections": False,
                "total_reports": 0
            }
        
        # 2. Calculate summary statistics
        total_damage_cost = Decimal("0.00")
        damage_findings = 0
        completed_inspections = 0
        approved_inspections = 0
        
        for report in reports:
            if report.inspection_status == InspectionStatus.COMPLETED:
                completed_inspections += 1
                if report.is_approved:
                    approved_inspections += 1
            
            if report.damage_found:
                total_damage_cost += report.total_damage_cost
                damage_findings += len(report.damage_findings)
        
        # 3. Get return lines for context
        return_lines = await self.line_repository.get_by_return_id(return_id)
        total_fees = sum(
            (line.damage_fee or 0) + (line.cleaning_fee or 0) + (line.replacement_fee or 0)
            for line in return_lines
        )
        
        return {
            "return_id": str(return_id),
            "has_inspections": True,
            "total_reports": len(reports),
            "completed_inspections": completed_inspections,
            "approved_inspections": approved_inspections,
            "damage_findings": damage_findings,
            "total_damage_cost": float(total_damage_cost),
            "total_assessed_fees": float(total_fees),
            "inspection_complete": completed_inspections > 0 and approved_inspections > 0
        }