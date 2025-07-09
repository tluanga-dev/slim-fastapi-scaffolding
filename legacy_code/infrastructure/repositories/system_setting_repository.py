from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update
from sqlalchemy.exc import IntegrityError

from ...domain.entities.system_setting import SystemSetting
from ...domain.repositories.system_setting_repository import SystemSettingRepositoryInterface
from ..models.system_setting_model import SystemSettingModel


class SystemSettingRepository(SystemSettingRepositoryInterface):
    """
    SQLAlchemy implementation of the SystemSettingRepositoryInterface.
    
    Handles persistence and retrieval of system configuration settings.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, setting: SystemSetting) -> SystemSetting:
        """Create a new system setting."""
        model = self._entity_to_model(setting)
        
        try:
            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)
            return self._model_to_entity(model)
        except IntegrityError:
            await self._session.rollback()
            raise ValueError(f"A setting with key '{setting.key}' already exists")
    
    async def get_by_id(self, setting_id: UUID) -> Optional[SystemSetting]:
        """Retrieve a system setting by its ID."""
        stmt = select(SystemSettingModel).where(
            SystemSettingModel.id == setting_id,
            SystemSettingModel.is_active == True
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._model_to_entity(model) if model else None
    
    async def get_by_key(self, key: str) -> Optional[SystemSetting]:
        """Retrieve a system setting by its key."""
        stmt = select(SystemSettingModel).where(
            SystemSettingModel.key == key,
            SystemSettingModel.is_active == True
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._model_to_entity(model) if model else None
    
    async def get_by_category(self, category: str, active_only: bool = True) -> List[SystemSetting]:
        """Retrieve all system settings in a specific category."""
        stmt = select(SystemSettingModel).where(SystemSettingModel.category == category)
        
        if active_only:
            stmt = stmt.where(SystemSettingModel.is_active == True)
        
        stmt = stmt.order_by(SystemSettingModel.key)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def get_user_configurable(self, active_only: bool = True) -> List[SystemSetting]:
        """Retrieve all user-configurable system settings."""
        stmt = select(SystemSettingModel).where(SystemSettingModel.is_user_configurable == True)
        
        if active_only:
            stmt = stmt.where(SystemSettingModel.is_active == True)
        
        stmt = stmt.order_by(SystemSettingModel.category, SystemSettingModel.key)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def list_all(self, active_only: bool = True) -> List[SystemSetting]:
        """Retrieve all system settings."""
        stmt = select(SystemSettingModel)
        
        if active_only:
            stmt = stmt.where(SystemSettingModel.is_active == True)
        
        stmt = stmt.order_by(SystemSettingModel.category, SystemSettingModel.key)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def update(self, setting: SystemSetting) -> SystemSetting:
        """Update an existing system setting."""
        stmt = sql_update(SystemSettingModel).where(
            SystemSettingModel.id == setting.id
        ).values(
            value=setting.value,
            description=setting.description,
            updated_at=setting.updated_at,
            updated_by=setting.updated_by
        )
        
        result = await self._session.execute(stmt)
        
        if result.rowcount == 0:
            raise ValueError(f"System setting with ID {setting.id} not found")
        
        await self._session.commit()
        
        # Fetch and return the updated entity
        updated_model = await self._session.get(SystemSettingModel, setting.id)
        return self._model_to_entity(updated_model)
    
    async def delete(self, setting_id: UUID) -> bool:
        """Soft delete a system setting."""
        stmt = sql_update(SystemSettingModel).where(
            SystemSettingModel.id == setting_id
        ).values(is_active=False)
        
        result = await self._session.execute(stmt)
        
        if result.rowcount > 0:
            await self._session.commit()
            return True
        
        return False
    
    async def upsert_by_key(self, setting: SystemSetting) -> SystemSetting:
        """Create or update a setting by its key."""
        existing = await self.get_by_key(setting.key)
        
        if existing:
            # Update existing setting
            existing.update_value(setting.value, setting.updated_by)
            if setting.description:
                existing.update_description(setting.description, setting.updated_by)
            return await self.update(existing)
        else:
            # Create new setting
            return await self.create(setting)
    
    def _entity_to_model(self, entity: SystemSetting) -> SystemSettingModel:
        """Convert a SystemSetting entity to a SystemSettingModel."""
        return SystemSettingModel(
            id=entity.id,
            key=entity.key,
            value=entity.value,
            description=entity.description,
            value_type=entity.value_type,
            is_user_configurable=entity.is_user_configurable,
            category=entity.category,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_active=entity.is_active,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )
    
    def _model_to_entity(self, model: SystemSettingModel) -> SystemSetting:
        """Convert a SystemSettingModel to a SystemSetting entity."""
        return SystemSetting(
            id=model.id,
            key=model.key,
            value=model.value,
            description=model.description,
            value_type=model.value_type,
            is_user_configurable=model.is_user_configurable,
            category=model.category,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active,
            created_by=model.created_by,
            updated_by=model.updated_by
        )