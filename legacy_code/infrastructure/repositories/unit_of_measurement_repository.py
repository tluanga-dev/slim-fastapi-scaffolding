from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.unit_of_measurement import UnitOfMeasurement
from src.domain.repositories.unit_of_measurement_repository import UnitOfMeasurementRepository
from src.infrastructure.models.unit_of_measurement_model import UnitOfMeasurementModel
from .base import SQLAlchemyRepository


class UnitOfMeasurementRepositoryImpl(SQLAlchemyRepository[UnitOfMeasurement, UnitOfMeasurementModel], UnitOfMeasurementRepository):
    """Implementation of UnitOfMeasurementRepository using SQLAlchemy."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UnitOfMeasurementModel, UnitOfMeasurement)
    
    def _to_entity(self, model: UnitOfMeasurementModel) -> UnitOfMeasurement:
        """Convert SQLAlchemy model to domain entity."""
        return UnitOfMeasurement(
            unit_id=model.unit_id,
            name=model.name,
            abbreviation=model.abbreviation,
            description=model.description,
            is_active=model.is_active,
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
    
    def _to_model(self, entity: UnitOfMeasurement) -> UnitOfMeasurementModel:
        """Convert domain entity to SQLAlchemy model."""
        return UnitOfMeasurementModel(
            id=entity.id,
            unit_id=entity.unit_id,
            name=entity.name,
            abbreviation=entity.abbreviation,
            description=entity.description,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )
    
    async def get_by_unit_id(self, unit_id: UUID) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by unit_id."""
        query = select(self.model).filter(self.model.unit_id == unit_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_name(self, name: str) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by name."""
        query = select(self.model).filter(
            func.lower(self.model.name) == func.lower(name),
            self.model.is_active == True
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_abbreviation(self, abbreviation: str) -> Optional[UnitOfMeasurement]:
        """Get unit of measurement by abbreviation."""
        query = select(self.model).filter(
            func.lower(self.model.abbreviation) == func.lower(abbreviation),
            self.model.is_active == True
        )
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def search_by_name(self, name_pattern: str, skip: int = 0, limit: int = 100) -> List[UnitOfMeasurement]:
        """Search units of measurement by name pattern."""
        query = select(self.model).filter(
            func.lower(self.model.name).contains(func.lower(name_pattern)),
            self.model.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]