from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....infrastructure.database import get_session
from ....infrastructure.repositories.system_setting_repository import SystemSettingRepository
from ....application.use_cases.system_settings.get_currency_setting import GetCurrencySettingUseCase
from ....application.use_cases.system_settings.update_currency_setting import UpdateCurrencySettingUseCase
from ....application.use_cases.system_settings.list_settings import ListSettingsUseCase
from ..schemas.system_setting_schemas import (
    SystemSettingResponse,
    SystemSettingsListResponse,
    CurrencySettingCreate,
    CurrencySettingResponse
)


router = APIRouter(prefix="/system-settings", tags=["System Settings"])


def get_currency_symbol(currency_code: str) -> str:
    """Get currency symbol for common currencies."""
    symbols = {
        'INR': '₹',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'CAD': 'C$',
        'AUD': 'A$',
        'CNY': '¥',
        'CHF': 'CHF',
        'SGD': 'S$'
    }
    return symbols.get(currency_code.upper(), currency_code)


async def get_system_setting_repository(
    session: AsyncSession = Depends(get_session)
) -> SystemSettingRepository:
    """Dependency for system setting repository."""
    return SystemSettingRepository(session)


@router.get("/", response_model=SystemSettingsListResponse)
async def list_system_settings(
    category: Optional[str] = Query(None, description="Filter by category"),
    user_configurable_only: bool = Query(False, description="Only return user-configurable settings"),
    active_only: bool = Query(True, description="Only return active settings"),
    repository: SystemSettingRepository = Depends(get_system_setting_repository)
):
    """
    List system settings with optional filters.
    """
    try:
        use_case = ListSettingsUseCase(repository)
        settings = await use_case.execute(category, user_configurable_only, active_only)
        
        setting_responses = []
        for setting in settings:
            setting_responses.append(SystemSettingResponse(
                id=setting.id,
                key=setting.key,
                value=setting.value,
                description=setting.description,
                value_type=setting.value_type,
                is_user_configurable=setting.is_user_configurable,
                category=setting.category,
                created_at=setting.created_at,
                updated_at=setting.updated_at,
                is_active=setting.is_active,
                created_by=setting.created_by,
                updated_by=setting.updated_by,
                typed_value=setting.get_typed_value()
            ))
        
        return SystemSettingsListResponse(
            settings=setting_responses,
            total_count=len(setting_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list settings: {str(e)}")


@router.get("/currency", response_model=CurrencySettingResponse)
async def get_currency_setting(
    repository: SystemSettingRepository = Depends(get_system_setting_repository)
):
    """
    Get the current system currency setting.
    """
    try:
        use_case = GetCurrencySettingUseCase(repository)
        setting = await use_case.execute()
        
        currency_code = setting.get_typed_value()
        
        return CurrencySettingResponse(
            currency_code=currency_code,
            symbol=get_currency_symbol(currency_code),
            description=setting.description or f"Default currency ({currency_code})",
            is_default=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get currency setting: {str(e)}")


@router.put("/currency", response_model=CurrencySettingResponse)
async def update_currency_setting(
    currency_data: CurrencySettingCreate,
    repository: SystemSettingRepository = Depends(get_system_setting_repository)
):
    """
    Update the system currency setting.
    """
    try:
        use_case = UpdateCurrencySettingUseCase(repository)
        setting = await use_case.execute(
            currency_code=currency_data.currency_code,
            description=currency_data.description,
            updated_by='api_user'  # TODO: Get from authentication context
        )
        
        currency_code = setting.get_typed_value()
        
        return CurrencySettingResponse(
            currency_code=currency_code,
            symbol=get_currency_symbol(currency_code),
            description=setting.description or f"Default currency ({currency_code})",
            is_default=True
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update currency setting: {str(e)}")


@router.get("/currency/supported", response_model=List[dict])
async def get_supported_currencies():
    """
    Get list of supported currencies with their symbols.
    """
    currencies = [
        {"code": "INR", "name": "Indian Rupee", "symbol": "₹"},
        {"code": "USD", "name": "US Dollar", "symbol": "$"},
        {"code": "EUR", "name": "Euro", "symbol": "€"},
        {"code": "GBP", "name": "British Pound", "symbol": "£"},
        {"code": "JPY", "name": "Japanese Yen", "symbol": "¥"},
        {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$"},
        {"code": "AUD", "name": "Australian Dollar", "symbol": "A$"},
        {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥"},
        {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF"},
        {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$"}
    ]
    return currencies