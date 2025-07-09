from typing import Optional

from ....domain.entities.system_setting import SystemSetting
from ....domain.repositories.system_setting_repository import SystemSettingRepositoryInterface


class UpdateCurrencySettingUseCase:
    """
    Use case for updating the system currency setting.
    """
    
    def __init__(self, system_setting_repository: SystemSettingRepositoryInterface):
        self._repository = system_setting_repository
    
    async def execute(
        self, 
        currency_code: str, 
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> SystemSetting:
        """
        Update the system currency setting.
        
        Args:
            currency_code: ISO 4217 currency code (e.g., 'INR', 'USD')
            description: Optional description for the currency setting
            updated_by: Who is making this update
            
        Returns:
            The updated currency SystemSetting entity
        """
        # Validate currency code
        if not currency_code or len(currency_code) != 3:
            raise ValueError("Currency code must be a 3-letter ISO 4217 code")
        
        currency_code = currency_code.upper()
        
        # Try to get existing currency setting
        existing_setting = await self._repository.get_by_key('default_currency')
        
        if existing_setting:
            # Update existing setting
            existing_setting.update_value(currency_code, updated_by)
            if description:
                existing_setting.update_description(description, updated_by)
            return await self._repository.update(existing_setting)
        else:
            # Create new currency setting
            new_setting = SystemSetting.create_currency_setting(
                currency_code=currency_code,
                description=description or f"Default currency code ({currency_code})",
                created_by=updated_by or 'system'
            )
            return await self._repository.create(new_setting)