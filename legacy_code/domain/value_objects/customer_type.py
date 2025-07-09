from enum import Enum


class CustomerType(Enum):
    """Customer type enumeration."""
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"


class CustomerTier(Enum):
    """Customer tier enumeration."""
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class BlacklistStatus(Enum):
    """Customer blacklist status enumeration."""
    CLEAR = "CLEAR"
    BLACKLISTED = "BLACKLISTED"


class ContactType(Enum):
    """Contact method type enumeration."""
    MOBILE = "MOBILE"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    FAX = "FAX"


class AddressType(Enum):
    """Address type enumeration."""
    BILLING = "BILLING"
    SHIPPING = "SHIPPING"
    BOTH = "BOTH"