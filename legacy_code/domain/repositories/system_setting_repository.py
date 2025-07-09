from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.system_setting import SystemSetting


class SystemSettingRepositoryInterface(ABC):
    """
    Abstract repository interface for system settings.
    
    Provides the contract for persisting and retrieving system configuration settings.
    """
    
    @abstractmethod
    async def create(self, setting: SystemSetting) -> SystemSetting:
        """
        Create a new system setting.
        
        Args:
            setting: The SystemSetting entity to create
            
        Returns:
            The created SystemSetting with populated ID and timestamps
            
        Raises:
            ValueError: If a setting with the same key already exists
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, setting_id: UUID) -> Optional[SystemSetting]:
        """
        Retrieve a system setting by its ID.
        
        Args:
            setting_id: The unique identifier of the setting
            
        Returns:
            The SystemSetting if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_key(self, key: str) -> Optional[SystemSetting]:
        """
        Retrieve a system setting by its key.
        
        Args:
            key: The unique key of the setting (e.g., 'default_currency')
            
        Returns:
            The SystemSetting if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_category(self, category: str, active_only: bool = True) -> List[SystemSetting]:
        """
        Retrieve all system settings in a specific category.
        
        Args:
            category: The category to filter by (e.g., 'currency', 'localization')
            active_only: Whether to include only active settings
            
        Returns:
            List of SystemSetting entities in the category
        """
        pass
    
    @abstractmethod
    async def get_user_configurable(self, active_only: bool = True) -> List[SystemSetting]:
        """
        Retrieve all user-configurable system settings.
        
        Args:
            active_only: Whether to include only active settings
            
        Returns:
            List of user-configurable SystemSetting entities
        """
        pass
    
    @abstractmethod
    async def list_all(self, active_only: bool = True) -> List[SystemSetting]:
        """
        Retrieve all system settings.
        
        Args:
            active_only: Whether to include only active settings
            
        Returns:
            List of all SystemSetting entities
        """
        pass
    
    @abstractmethod
    async def update(self, setting: SystemSetting) -> SystemSetting:
        """
        Update an existing system setting.
        
        Args:
            setting: The SystemSetting entity with updated values
            
        Returns:
            The updated SystemSetting
            
        Raises:
            ValueError: If the setting doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete(self, setting_id: UUID) -> bool:
        """
        Soft delete a system setting (set is_active to False).
        
        Args:
            setting_id: The unique identifier of the setting to delete
            
        Returns:
            True if the setting was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def upsert_by_key(self, setting: SystemSetting) -> SystemSetting:
        """
        Create or update a setting by its key.
        
        If a setting with the same key exists, update it.
        Otherwise, create a new setting.
        
        Args:
            setting: The SystemSetting entity to create or update
            
        Returns:
            The created or updated SystemSetting
        """
        pass