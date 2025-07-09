"""User type value object for user hierarchy."""

from enum import Enum


class UserType(str, Enum):
    """User type hierarchy."""
    
    SUPERADMIN = "SUPERADMIN"  # Full system access, can manage everything
    ADMIN = "ADMIN"            # Can manage users, roles, and system settings
    USER = "USER"              # Regular internal user (staff, manager)
    CUSTOMER = "CUSTOMER"      # External customer with limited access
    
    @classmethod
    def get_hierarchy_level(cls, user_type: 'UserType') -> int:
        """Get the hierarchy level for a user type (lower number = higher authority)."""
        hierarchy = {
            cls.SUPERADMIN: 1,
            cls.ADMIN: 2,
            cls.USER: 3,
            cls.CUSTOMER: 4,
        }
        return hierarchy.get(user_type, 999)
    
    def is_higher_than(self, other: 'UserType') -> bool:
        """Check if this user type has higher authority than another."""
        return self.get_hierarchy_level(self) < self.get_hierarchy_level(other)
    
    def is_higher_or_equal(self, other: 'UserType') -> bool:
        """Check if this user type has higher or equal authority than another."""
        return self.get_hierarchy_level(self) <= self.get_hierarchy_level(other)
    
    def can_manage(self, other: 'UserType') -> bool:
        """Check if this user type can manage another user type."""
        # SUPERADMIN can manage everyone
        if self == UserType.SUPERADMIN:
            return True
        
        # ADMIN can manage USER and CUSTOMER
        if self == UserType.ADMIN and other in [UserType.USER, UserType.CUSTOMER]:
            return True
        
        # USER cannot manage anyone
        # CUSTOMER cannot manage anyone
        return False
    
    def get_display_name(self) -> str:
        """Get a user-friendly display name."""
        display_names = {
            UserType.SUPERADMIN: "Super Administrator",
            UserType.ADMIN: "Administrator",
            UserType.USER: "User",
            UserType.CUSTOMER: "Customer",
        }
        return display_names.get(self, self.value)
    
    def get_description(self) -> str:
        """Get a description of the user type."""
        descriptions = {
            UserType.SUPERADMIN: "Full system access with ability to manage all aspects of the system",
            UserType.ADMIN: "Administrative access with ability to manage users, roles, and settings",
            UserType.USER: "Regular user with role-based permissions",
            UserType.CUSTOMER: "External customer with limited portal access",
        }
        return descriptions.get(self, "")