from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from ...domain.entities.inspection_report import InspectionReport
from ...domain.value_objects.rental_return_type import InspectionStatus, DamageLevel
from ...domain.value_objects.item_type import ConditionGrade


class InspectionReportModel(BaseModel):
    """SQLAlchemy model for inspection reports."""
    
    __tablename__ = "inspection_reports"
    
    # Core fields
    return_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("rental_returns.id"),
        nullable=False,
        index=True
    )
    inventory_unit_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("inventory_units.id"),
        nullable=False,
        index=True
    )
    inspector_id = Column(String(255), nullable=False, index=True)
    inspection_date = Column(DateTime, nullable=False)
    
    # Condition assessment
    pre_condition_grade = Column(String(1), nullable=False)
    post_condition_grade = Column(String(1), nullable=False)
    damage_level = Column(String(20), nullable=False, default=DamageLevel.NONE.value)
    inspection_status = Column(String(20), nullable=False, default=InspectionStatus.PENDING.value)
    
    # Damage documentation
    damage_description = Column(Text, nullable=True)
    repair_estimate = Column(Float, nullable=True)
    photo_urls = Column(JSON, nullable=True)  # Store as JSON array
    inspection_notes = Column(Text, nullable=True)
    
    # Processing tracking
    completed_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    # rental_return = relationship(
    #     "RentalReturnModel",
    #     back_populates="inspection_reports", 
    #     foreign_keys=[return_id]
    # )
    inventory_unit = relationship(
        "InventoryUnitModel",
        foreign_keys=[inventory_unit_id]
    )
    
    @classmethod
    def from_entity(cls, entity: InspectionReport) -> "InspectionReportModel":
        """Create model from domain entity."""
        return cls(
            id=entity.id,
            return_id=entity.return_id,
            inventory_unit_id=entity.inventory_unit_id,
            inspector_id=entity.inspector_id,
            inspection_date=entity.inspection_date,
            pre_condition_grade=entity.pre_condition_grade.value,
            post_condition_grade=entity.post_condition_grade.value,
            damage_level=entity.damage_level.value,
            inspection_status=entity.inspection_status.value,
            damage_description=entity.damage_description,
            repair_estimate=entity.repair_estimate,
            photo_urls=entity.photo_urls,
            inspection_notes=entity.inspection_notes,
            completed_at=entity.completed_at,
            approved_by=entity.approved_by,
            approved_at=entity.approved_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            is_active=entity.is_active
        )
    
    def to_entity(self) -> InspectionReport:
        """Convert model to domain entity."""
        entity = InspectionReport(
            id=self.id,
            return_id=self.return_id,
            inventory_unit_id=self.inventory_unit_id,
            inspector_id=self.inspector_id,
            inspection_date=self.inspection_date,
            pre_condition_grade=ConditionGrade(self.pre_condition_grade),
            post_condition_grade=ConditionGrade(self.post_condition_grade),
            damage_level=DamageLevel(self.damage_level),
            inspection_status=InspectionStatus(self.inspection_status),
            damage_description=self.damage_description,
            repair_estimate=self.repair_estimate,
            photo_urls=self.photo_urls or [],
            inspection_notes=self.inspection_notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
        
        # Set processing fields
        entity._completed_at = self.completed_at
        entity._approved_by = self.approved_by
        entity._approved_at = self.approved_at
        
        return entity
    
    def update_from_entity(self, entity: InspectionReport) -> None:
        """Update model from domain entity."""
        self.return_id = entity.return_id
        self.inventory_unit_id = entity.inventory_unit_id
        self.inspector_id = entity.inspector_id
        self.inspection_date = entity.inspection_date
        self.pre_condition_grade = entity.pre_condition_grade.value
        self.post_condition_grade = entity.post_condition_grade.value
        self.damage_level = entity.damage_level.value
        self.inspection_status = entity.inspection_status.value
        self.damage_description = entity.damage_description
        self.repair_estimate = entity.repair_estimate
        self.photo_urls = entity.photo_urls
        self.inspection_notes = entity.inspection_notes
        self.completed_at = entity.completed_at
        self.approved_by = entity.approved_by
        self.approved_at = entity.approved_at
        self.updated_at = entity.updated_at
        self.updated_by = entity.updated_by
        self.is_active = entity.is_active