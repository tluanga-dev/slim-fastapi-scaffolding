from enum import Enum


class ReturnStatus(str, Enum):
    """Return status enumeration."""
    PENDING = "PENDING"
    INITIATED = "INITIATED"
    IN_INSPECTION = "IN_INSPECTION"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DamageLevel(str, Enum):
    """Damage level enumeration for returned items."""
    NONE = "NONE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    TOTAL_LOSS = "TOTAL_LOSS"


class ReturnType(str, Enum):
    """Return type enumeration."""
    FULL = "FULL"
    PARTIAL = "PARTIAL"


class InspectionStatus(str, Enum):
    """Inspection status enumeration."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FeeType(str, Enum):
    """Fee type enumeration for return-related charges."""
    LATE_FEE = "LATE_FEE"
    DAMAGE_FEE = "DAMAGE_FEE"
    CLEANING_FEE = "CLEANING_FEE"
    REPLACEMENT_FEE = "REPLACEMENT_FEE"
    RESTOCKING_FEE = "RESTOCKING_FEE"


class ReturnLineStatus(str, Enum):
    """Return line status enumeration."""
    PENDING = "PENDING"
    INSPECTED = "INSPECTED"
    PROCESSED = "PROCESSED"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"