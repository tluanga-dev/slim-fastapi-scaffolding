from enum import Enum


class CustomerType(str, Enum):
    """Customer type enumeration."""
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    INTERNAL = "internal"


class CustomerStatus(str, Enum):
    """Customer status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"
    VIP = "vip"


class CustomerTier(str, Enum):
    """Customer tier enumeration."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class BlacklistStatus(str, Enum):
    """Customer blacklist status enumeration."""
    CLEAR = "clear"
    BLACKLISTED = "blacklisted"
    PENDING_REVIEW = "pending_review"


class ContactMethodType(str, Enum):
    """Contact method type enumeration."""
    PHONE = "phone"
    MOBILE = "mobile"
    EMAIL = "email"
    SMS = "sms"
    FAX = "fax"
    MAIL = "mail"
    WHATSAPP = "whatsapp"
    OTHER = "other"


class ContactMethodPurpose(str, Enum):
    """Contact method purpose enumeration."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BILLING = "billing"
    SHIPPING = "shipping"
    EMERGENCY = "emergency"
    MARKETING = "marketing"