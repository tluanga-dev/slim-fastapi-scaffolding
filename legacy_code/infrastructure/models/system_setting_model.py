from sqlalchemy import Column, String, Text, Boolean
from .base import BaseModel


class SystemSettingModel(BaseModel):
    """
    Database model for system-wide configuration settings.
    
    Stores key-value pairs for application configuration that can be
    modified at runtime without code changes.
    """
    __tablename__ = 'system_settings'
    
    # The setting key (e.g., 'currency', 'date_format', 'timezone')
    key = Column(String(100), unique=True, nullable=False, index=True)
    
    # The setting value (stored as string, parsed by application)
    value = Column(Text, nullable=False)
    
    # Human-readable description of what this setting controls
    description = Column(Text, nullable=True)
    
    # Data type for validation ('string', 'integer', 'boolean', 'json')
    value_type = Column(String(20), nullable=False, default='string')
    
    # Whether this setting is user-configurable or system-only
    is_user_configurable = Column(Boolean, default=True, nullable=False)
    
    # Category for grouping settings in UI ('general', 'localization', 'features')
    category = Column(String(50), nullable=False, default='general')
    
    def __repr__(self):
        return f"<SystemSetting(key='{self.key}', value='{self.value}', category='{self.category}')>"