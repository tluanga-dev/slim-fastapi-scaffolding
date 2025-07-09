from enum import Enum


class SupplierType(Enum):
    """Supplier business type enumeration."""
    MANUFACTURER = "MANUFACTURER"
    DISTRIBUTOR = "DISTRIBUTOR"
    WHOLESALER = "WHOLESALER"
    RETAILER = "RETAILER"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"


class SupplierTier(Enum):
    """Supplier tier classification enumeration."""
    PREFERRED = "PREFERRED"
    STANDARD = "STANDARD"
    RESTRICTED = "RESTRICTED"


class PaymentTerms(Enum):
    """Payment terms enumeration."""
    NET15 = "NET15"
    NET30 = "NET30"
    NET45 = "NET45"
    NET60 = "NET60"
    NET90 = "NET90"
    COD = "COD"  # Cash on Delivery
    PREPAID = "PREPAID"


class SupplierStatus(Enum):
    """Supplier status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    BLACKLISTED = "BLACKLISTED"


class ContactType(Enum):
    """Supplier contact type enumeration."""
    PRIMARY = "PRIMARY"
    BILLING = "BILLING"
    TECHNICAL = "TECHNICAL"
    SALES = "SALES"
    EMERGENCY = "EMERGENCY"