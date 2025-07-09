from typing import Any, Dict, Optional
import json
from datetime import datetime
from uuid import UUID

from .base import BaseEntity


class SystemSetting(BaseEntity):
    """
    Domain entity representing a system configuration setting.
    
    Handles validation and type conversion for system-wide configuration values.
    Supports multiple data types with automatic serialization/deserialization.
    """
    
    VALID_VALUE_TYPES = {'string', 'integer', 'boolean', 'json', 'float'}
    VALID_CATEGORIES = {'general', 'localization', 'features', 'display', 'currency'}
    
    def __init__(
        self,
        key: str,
        value: str,
        description: Optional[str] = None,
        value_type: str = 'string',
        is_user_configurable: bool = True,
        category: str = 'general',
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """
        Initialize a SystemSetting entity.
        
        Args:
            key: Unique identifier for the setting (e.g., 'default_currency')
            value: The setting value as a string (will be parsed based on value_type)
            description: Human-readable description of the setting
            value_type: The expected data type ('string', 'integer', 'boolean', 'json', 'float')
            is_user_configurable: Whether users can modify this setting
            category: Category for grouping settings ('general', 'localization', etc.)
        """
        super().__init__(id, created_at, updated_at, is_active, created_by, updated_by)
        
        if not key or not isinstance(key, str):
            raise ValueError("Setting key must be a non-empty string")
        
        if value_type not in self.VALID_VALUE_TYPES:
            raise ValueError(f"Value type must be one of: {self.VALID_VALUE_TYPES}")
            
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {self.VALID_CATEGORIES}")
        
        # Validate the value can be parsed according to its type
        self._validate_value_type(value, value_type)
        
        self._key = key
        self._value = value
        self._description = description
        self._value_type = value_type
        self._is_user_configurable = is_user_configurable
        self._category = category
    
    @property
    def key(self) -> str:
        return self._key
    
    @property
    def value(self) -> str:
        return self._value
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def value_type(self) -> str:
        return self._value_type
    
    @property
    def is_user_configurable(self) -> bool:
        return self._is_user_configurable
    
    @property
    def category(self) -> str:
        return self._category
    
    def get_typed_value(self) -> Any:
        """
        Get the setting value converted to its proper type.
        
        Returns:
            The value converted to the type specified by value_type
        """
        return self._parse_value(self._value, self._value_type)
    
    def update_value(self, new_value: str, updated_by: Optional[str] = None) -> None:
        """
        Update the setting value with validation.
        
        Args:
            new_value: The new value as a string
            updated_by: Who is making this update
        """
        self._validate_value_type(new_value, self._value_type)
        self._value = new_value
        self._updated_by = updated_by
        self._updated_at = datetime.utcnow()
    
    def update_description(self, description: Optional[str], updated_by: Optional[str] = None) -> None:
        """Update the setting description."""
        self._description = description
        self._updated_by = updated_by
        self._updated_at = datetime.utcnow()
    
    @staticmethod
    def _validate_value_type(value: str, value_type: str) -> None:
        """Validate that a value can be parsed as the specified type."""
        try:
            SystemSetting._parse_value(value, value_type)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise ValueError(f"Value '{value}' cannot be parsed as {value_type}: {e}")
    
    @staticmethod
    def _parse_value(value: str, value_type: str) -> Any:
        """Parse a string value according to its type."""
        if value_type == 'string':
            return value
        elif value_type == 'integer':
            return int(value)
        elif value_type == 'float':
            return float(value)
        elif value_type == 'boolean':
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
            else:
                raise ValueError(f"Cannot parse '{value}' as boolean")
        elif value_type == 'json':
            return json.loads(value)
        else:
            raise ValueError(f"Unknown value type: {value_type}")
    
    @classmethod
    def create_currency_setting(
        cls,
        currency_code: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> 'SystemSetting':
        """
        Factory method to create a currency setting.
        
        Args:
            currency_code: ISO 4217 currency code (e.g., 'INR', 'USD')
            description: Optional description
            created_by: Who is creating this setting
        """
        if not currency_code or len(currency_code) != 3:
            raise ValueError("Currency code must be a 3-letter ISO 4217 code")
        
        return cls(
            key='default_currency',
            value=currency_code.upper(),
            description=description or f"Default currency code ({currency_code.upper()})",
            value_type='string',
            is_user_configurable=True,
            category='currency',
            created_by=created_by
        )
    
    def __str__(self) -> str:
        return f"SystemSetting(key='{self.key}', value='{self.value}', type='{self.value_type}')"
    
    def __repr__(self) -> str:
        return (f"SystemSetting(key='{self.key}', value='{self.value}', "
                f"type='{self.value_type}', category='{self.category}')")