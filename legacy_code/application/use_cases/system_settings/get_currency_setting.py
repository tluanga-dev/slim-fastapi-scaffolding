from typing import Optional

from ....domain.entities.system_setting import SystemSetting
from ....domain.repositories.system_setting_repository import SystemSettingRepositoryInterface


class GetCurrencySettingUseCase:
    """
    Use case for retrieving the current currency setting.
    
    Returns the configured currency or creates a default INR setting if none exists.
    """
    
    def __init__(self, system_setting_repository: SystemSettingRepositoryInterface):
        self._repository = system_setting_repository
    
    async def execute(self) -> SystemSetting:
        """
        Get the current currency setting.
        
        Returns:
            The currency SystemSetting entity
            
        If no currency setting exists, creates a default INR setting.
        """
        # Try to get existing currency setting
        currency_setting = await self._repository.get_by_key('default_currency')
        
        if currency_setting:
            return currency_setting
        
        # Create default INR currency setting if none exists
        default_setting = SystemSetting.create_currency_setting(
            currency_code='INR',
            description='Default system currency (Indian Rupee)',
            created_by='system'
        )
        
        return await self._repository.create(default_setting)