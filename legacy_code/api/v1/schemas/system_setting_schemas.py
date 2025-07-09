from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator


class SystemSettingBase(BaseModel):
    """Base schema for system settings."""
    key: str = Field(..., min_length=1, max_length=100, description="Unique setting key")
    value: str = Field(..., description="Setting value as string")
    description: Optional[str] = Field(None, description="Human-readable description")
    value_type: str = Field(default='string', description="Data type of the value")
    is_user_configurable: bool = Field(default=True, description="Whether users can modify this setting")
    category: str = Field(default='general', description="Setting category for grouping")
    
    @validator('value_type')
    def validate_value_type(cls, v):
        valid_types = {'string', 'integer', 'boolean', 'json', 'float'}
        if v not in valid_types:
            raise ValueError(f"Value type must be one of: {valid_types}")
        return v
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = {'general', 'localization', 'features', 'display', 'currency'}
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        return v


class SystemSettingCreate(SystemSettingBase):
    """Schema for creating a system setting."""
    pass


class SystemSettingUpdate(BaseModel):
    """Schema for updating a system setting."""
    value: Optional[str] = Field(None, description="New setting value")
    description: Optional[str] = Field(None, description="New description")


class SystemSettingResponse(SystemSettingBase):
    """Schema for system setting response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    typed_value: Any = Field(..., description="Value converted to its proper type")
    
    class Config:
        from_attributes = True


class CurrencySettingCreate(BaseModel):
    """Schema for creating/updating currency setting specifically."""
    currency_code: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    description: Optional[str] = Field(None, description="Optional description")
    
    @validator('currency_code')
    def validate_currency_code(cls, v):
        if len(v) != 3:
            raise ValueError("Currency code must be exactly 3 characters")
        return v.upper()


class CurrencySettingResponse(BaseModel):
    """Schema for currency setting response."""
    currency_code: str
    symbol: str
    description: str
    is_default: bool = True
    
    class Config:
        from_attributes = True


class SystemSettingsListResponse(BaseModel):
    """Schema for listing system settings."""
    settings: list[SystemSettingResponse]
    total_count: int
    
    class Config:
        from_attributes = True