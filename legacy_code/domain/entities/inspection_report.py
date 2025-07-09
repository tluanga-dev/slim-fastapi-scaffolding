from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID, uuid4

from .base import BaseEntity
from ..value_objects.rental_return_type import InspectionStatus, DamageLevel
from ..value_objects.item_type import ConditionGrade


class InspectionReport(BaseEntity):
    """Inspection report entity for documenting item condition during returns."""
    
    def __init__(
        self,
        return_id: UUID,
        inventory_unit_id: UUID,
        inspector_id: str,
        inspection_date: datetime,
        pre_condition_grade: ConditionGrade,
        post_condition_grade: ConditionGrade,
        damage_level: DamageLevel = DamageLevel.NONE,
        inspection_status: InspectionStatus = InspectionStatus.PENDING,
        damage_description: Optional[str] = None,
        repair_estimate: Optional[float] = None,
        photo_urls: Optional[List[str]] = None,
        inspection_notes: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
        is_active: bool = True
    ):
        """Initialize an inspection report."""
        super().__init__(id, created_at, updated_at, created_by, updated_by, is_active)
        
        self._return_id = return_id
        self._inventory_unit_id = inventory_unit_id
        self._inspector_id = inspector_id
        self._inspection_date = inspection_date
        self._pre_condition_grade = pre_condition_grade
        self._post_condition_grade = post_condition_grade
        self._damage_level = damage_level
        self._inspection_status = inspection_status
        self._damage_description = damage_description
        self._repair_estimate = repair_estimate
        self._photo_urls = photo_urls or []
        self._inspection_notes = inspection_notes
        
        # Additional tracking
        self._completed_at: Optional[datetime] = None
        self._approved_by: Optional[str] = None
        self._approved_at: Optional[datetime] = None
        
        # Validate business rules
        self._validate()
    
    def _validate(self):
        """Validate business rules."""
        if not self._return_id:
            raise ValueError("Return ID is required")
        
        if not self._inventory_unit_id:
            raise ValueError("Inventory unit ID is required")
        
        if not self._inspector_id:
            raise ValueError("Inspector ID is required")
        
        if not self._inspection_date:
            raise ValueError("Inspection date is required")
        
        if self._repair_estimate is not None and self._repair_estimate < 0:
            raise ValueError("Repair estimate cannot be negative")
        
        # If there's damage, there should be a description
        if self._damage_level != DamageLevel.NONE and not self._damage_description:
            raise ValueError("Damage description is required when damage level is not NONE")
    
    @property
    def return_id(self) -> UUID:
        return self._return_id
    
    @property
    def inventory_unit_id(self) -> UUID:
        return self._inventory_unit_id
    
    @property
    def inspector_id(self) -> str:
        return self._inspector_id
    
    @property
    def inspection_date(self) -> datetime:
        return self._inspection_date
    
    @property
    def pre_condition_grade(self) -> ConditionGrade:
        return self._pre_condition_grade
    
    @property
    def post_condition_grade(self) -> ConditionGrade:
        return self._post_condition_grade
    
    @property
    def damage_level(self) -> DamageLevel:
        return self._damage_level
    
    @property
    def inspection_status(self) -> InspectionStatus:
        return self._inspection_status
    
    @property
    def damage_description(self) -> Optional[str]:
        return self._damage_description
    
    @property
    def repair_estimate(self) -> Optional[float]:
        return self._repair_estimate
    
    @property
    def photo_urls(self) -> List[str]:
        return self._photo_urls.copy()
    
    @property
    def inspection_notes(self) -> Optional[str]:
        return self._inspection_notes
    
    @property
    def completed_at(self) -> Optional[datetime]:
        return self._completed_at
    
    @property
    def approved_by(self) -> Optional[str]:
        return self._approved_by
    
    @property
    def approved_at(self) -> Optional[datetime]:
        return self._approved_at
    
    def has_damage(self) -> bool:
        """Check if the inspection found damage."""
        return self._damage_level != DamageLevel.NONE
    
    def has_deteriorated(self) -> bool:
        """Check if condition has deteriorated since rental."""
        # Compare condition grades (A=1, B=2, C=3, D=4)
        grade_values = {"A": 1, "B": 2, "C": 3, "D": 4}
        pre_value = grade_values.get(self._pre_condition_grade.value, 1)
        post_value = grade_values.get(self._post_condition_grade.value, 1)
        return post_value > pre_value
    
    def is_completed(self) -> bool:
        """Check if the inspection is completed."""
        return self._inspection_status == InspectionStatus.COMPLETED
    
    def is_approved(self) -> bool:
        """Check if the inspection is approved."""
        return self._approved_by is not None and self._approved_at is not None
    
    def start_inspection(self, updated_by: Optional[str] = None) -> None:
        """Start the inspection process."""
        if self._inspection_status != InspectionStatus.PENDING:
            raise ValueError("Inspection is not in pending status")
        
        self._inspection_status = InspectionStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def update_condition_assessment(
        self,
        post_condition_grade: ConditionGrade,
        damage_level: DamageLevel,
        damage_description: Optional[str] = None,
        repair_estimate: Optional[float] = None,
        updated_by: Optional[str] = None
    ) -> None:
        """Update the condition assessment."""
        if self._inspection_status not in [InspectionStatus.PENDING, InspectionStatus.IN_PROGRESS]:
            raise ValueError("Cannot update completed or failed inspection")
        
        self._post_condition_grade = post_condition_grade
        self._damage_level = damage_level
        self._damage_description = damage_description
        self._repair_estimate = repair_estimate
        
        # Validate damage description requirement
        if damage_level != DamageLevel.NONE and not damage_description:
            raise ValueError("Damage description is required when damage level is not NONE")
        
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def add_photo(self, photo_url: str, updated_by: Optional[str] = None) -> None:
        """Add a photo to the inspection report."""
        if not photo_url:
            raise ValueError("Photo URL is required")
        
        if photo_url not in self._photo_urls:
            self._photo_urls.append(photo_url)
            self.updated_at = datetime.utcnow()
            self.updated_by = updated_by
    
    def remove_photo(self, photo_url: str, updated_by: Optional[str] = None) -> bool:
        """Remove a photo from the inspection report."""
        if photo_url in self._photo_urls:
            self._photo_urls.remove(photo_url)
            self.updated_at = datetime.utcnow()
            self.updated_by = updated_by
            return True
        return False
    
    def add_note(self, note: str, updated_by: Optional[str] = None) -> None:
        """Add a note to the inspection."""
        if not note:
            raise ValueError("Note cannot be empty")
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        new_note = f"[{timestamp}] {note}"
        
        if self._inspection_notes:
            self._inspection_notes += f"\n{new_note}"
        else:
            self._inspection_notes = new_note
        
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def complete_inspection(self, updated_by: Optional[str] = None) -> None:
        """Complete the inspection."""
        if self._inspection_status != InspectionStatus.IN_PROGRESS:
            raise ValueError("Inspection must be in progress to complete")
        
        # Validate required fields for completion
        if not self._post_condition_grade:
            raise ValueError("Post-condition grade is required to complete inspection")
        
        if self._damage_level != DamageLevel.NONE and not self._damage_description:
            raise ValueError("Damage description is required when damage is present")
        
        self._inspection_status = InspectionStatus.COMPLETED
        self._completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def fail_inspection(self, reason: str, updated_by: Optional[str] = None) -> None:
        """Mark the inspection as failed."""
        if not reason:
            raise ValueError("Failure reason is required")
        
        self._inspection_status = InspectionStatus.FAILED
        self.add_note(f"Inspection failed: {reason}", updated_by)
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def approve_inspection(self, approved_by: str) -> None:
        """Approve the completed inspection."""
        if not self.is_completed():
            raise ValueError("Inspection must be completed before approval")
        
        if not approved_by:
            raise ValueError("Approver ID is required")
        
        self._approved_by = approved_by
        self._approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.updated_by = approved_by
    
    def calculate_damage_severity_score(self) -> int:
        """Calculate a damage severity score (0-10 scale)."""
        # Base score from damage level
        damage_scores = {
            DamageLevel.NONE: 0,
            DamageLevel.MINOR: 2,
            DamageLevel.MODERATE: 5,
            DamageLevel.MAJOR: 8,
            DamageLevel.TOTAL_LOSS: 10
        }
        
        base_score = damage_scores.get(self._damage_level, 0)
        
        # Adjust based on condition deterioration
        if self.has_deteriorated():
            base_score += 1
        
        # Adjust based on repair estimate if available
        if self._repair_estimate:
            if self._repair_estimate > 1000:
                base_score += 2
            elif self._repair_estimate > 500:
                base_score += 1
        
        return min(base_score, 10)  # Cap at 10
    
    def get_inspection_summary(self) -> Dict:
        """Get a summary of the inspection report."""
        return {
            "inspection_id": str(self.id),
            "return_id": str(self._return_id),
            "inventory_unit_id": str(self._inventory_unit_id),
            "inspector_id": self._inspector_id,
            "inspection_date": self._inspection_date.isoformat(),
            "inspection_status": self._inspection_status.value,
            "pre_condition_grade": self._pre_condition_grade.value,
            "post_condition_grade": self._post_condition_grade.value,
            "damage_level": self._damage_level.value,
            "has_damage": self.has_damage(),
            "has_deteriorated": self.has_deteriorated(),
            "damage_severity_score": self.calculate_damage_severity_score(),
            "repair_estimate": self._repair_estimate,
            "photo_count": len(self._photo_urls),
            "is_completed": self.is_completed(),
            "is_approved": self.is_approved(),
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "approved_by": self._approved_by,
            "approved_at": self._approved_at.isoformat() if self._approved_at else None
        }