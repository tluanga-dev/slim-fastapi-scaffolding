from enum import Enum


class RentalStatus(str, Enum):
    """Rental transaction status enumeration."""
    RESERVED = "reserved"
    CHECKED_OUT = "checked_out"
    OVERDUE = "overdue"
    RETURNED = "returned"
    PARTIALLY_RETURNED = "partially_returned"
    CANCELLED = "cancelled"


class ReturnCondition(str, Enum):
    """Return condition enumeration."""
    GOOD = "good"
    DAMAGED = "damaged"
    MISSING_PARTS = "missing_parts"
    NOT_RETURNED = "not_returned"
    LOST = "lost"
    STOLEN = "stolen"


class LateFeeType(str, Enum):
    """Late fee type enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    FLAT = "flat"
    PERCENTAGE = "percentage"
    TIERED = "tiered"


class RentalExtensionStatus(str, Enum):
    """Rental extension status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"