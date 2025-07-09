from typing import TypeVar, Generic, Optional, List, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeMeta

from src.domain.entities.base import BaseEntity
from src.domain.repositories.base import BaseRepository
from src.infrastructure.models.base import BaseModel

T = TypeVar("T", bound=BaseEntity)
M = TypeVar("M", bound=BaseModel)


class SQLAlchemyRepository(BaseRepository[T], Generic[T, M]):
    def __init__(self, session: AsyncSession, model: Type[M], entity_class: Type[T]):
        self.session = session
        self.model = model
        self.entity_class = entity_class

    def _to_entity(self, model: M) -> T:
        raise NotImplementedError("Subclasses must implement _to_entity method")

    def _to_model(self, entity: T) -> M:
        raise NotImplementedError("Subclasses must implement _to_model method")

    async def create(self, entity: T) -> T:
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, id: UUID) -> Optional[T]:
        result = await self.session.get(self.model, id)
        return self._to_entity(result) if result else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def update(self, entity: T) -> T:
        model = await self.session.get(self.model, entity.id)
        if not model:
            raise ValueError(f"Entity with id {entity.id} not found")
        
        updated_model = self._to_model(entity)
        for key, value in updated_model.__dict__.items():
            if not key.startswith("_"):
                setattr(model, key, value)
        
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: UUID) -> bool:
        model = await self.session.get(self.model, id)
        if not model:
            return False
        
        model.is_active = False
        await self.session.commit()
        return True

    async def get_active(self, skip: int = 0, limit: int = 100) -> List[T]:
        query = select(self.model).filter(
            self.model.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]