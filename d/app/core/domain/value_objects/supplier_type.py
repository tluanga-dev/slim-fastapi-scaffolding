from enum import Enum


class SupplierType(str, Enum):
    """Supplier type enumeration."""
    MANUFACTURER = "MANUFACTURER"
    DISTRIBUTOR = "DISTRIBUTOR"
    RETAILER = "RETAILER"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    LOGISTICS = "LOGISTICS"
    TECHNOLOGY = "TECHNOLOGY"
    MATERIALS = "MATERIALS"
    EQUIPMENT = "EQUIPMENT"


class SupplierTier(str, Enum):
    """Supplier tier classification."""
    PREFERRED = "PREFERRED"
    STANDARD = "STANDARD"
    RESTRICTED = "RESTRICTED"


class PaymentTerms(str, Enum):
    """Payment terms enumeration."""
    COD = "COD"  # Cash on Delivery
    NET15 = "NET15"  # Net 15 days
    NET30 = "NET30"  # Net 30 days
    NET45 = "NET45"  # Net 45 days
    NET60 = "NET60"  # Net 60 days
    NET90 = "NET90"  # Net 90 days
    PREPAID = "PREPAID"  # Payment in advance
    
    def get_days(self) -> int:
        """Get the number of days for the payment term."""
        days_mapping = {
            PaymentTerms.COD: 0,
            PaymentTerms.NET15: 15,
            PaymentTerms.NET30: 30,
            PaymentTerms.NET45: 45,
            PaymentTerms.NET60: 60,
            PaymentTerms.NET90: 90,
            PaymentTerms.PREPAID: -1,  # Negative indicates prepayment
        }
        return days_mapping.get(self, 30)
    
    def get_description(self) -> str:
        """Get human-readable description of payment terms."""
        descriptions = {
            PaymentTerms.COD: "Cash on Delivery",
            PaymentTerms.NET15: "Payment due in 15 days",
            PaymentTerms.NET30: "Payment due in 30 days",
            PaymentTerms.NET45: "Payment due in 45 days",
            PaymentTerms.NET60: "Payment due in 60 days",
            PaymentTerms.NET90: "Payment due in 90 days",
            PaymentTerms.PREPAID: "Payment required in advance",
        }
        return descriptions.get(self, "Net 30 days")