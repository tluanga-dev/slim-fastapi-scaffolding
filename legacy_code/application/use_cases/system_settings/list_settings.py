from typing import List, Optional

from ....domain.entities.system_setting import SystemSetting
from ....domain.repositories.system_setting_repository import SystemSettingRepositoryInterface


class ListSettingsUseCase:
    """
    Use case for listing system settings with various filters.
    """
    
    def __init__(self, system_setting_repository: SystemSettingRepositoryInterface):
        self._repository = system_setting_repository
    
    async def execute(
        self, 
        category: Optional[str] = None,
        user_configurable_only: bool = False,
        active_only: bool = True
    ) -> List[SystemSetting]:
        """
        List system settings with optional filters.
        
        Args:
            category: Filter by category (e.g., 'currency', 'localization')
            user_configurable_only: Only return user-configurable settings
            active_only: Only return active settings
            
        Returns:
            List of SystemSetting entities matching the criteria
        """
        if category:
            return await self._repository.get_by_category(category, active_only)
        elif user_configurable_only:
            return await self._repository.get_user_configurable(active_only)
        else:
            return await self._repository.list_all(active_only)