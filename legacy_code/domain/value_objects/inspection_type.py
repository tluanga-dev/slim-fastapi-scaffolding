from enum import Enum


class InspectionStatus(str, Enum):
    """Inspection status enumeration."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class DamageSeverity(str, Enum):
    """Damage severity enumeration."""
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class InspectionType(str, Enum):
    """Inspection type enumeration."""
    PRE_RENTAL = "PRE_RENTAL"
    POST_RENTAL = "POST_RENTAL"
    MAINTENANCE = "MAINTENANCE"
    QUALITY_CHECK = "QUALITY_CHECK"


class InspectionResult(str, Enum):
    """Inspection result enumeration."""
    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL = "CONDITIONAL"
    PENDING = "PENDING"


# Alias for backward compatibility
DamageLevel = DamageSeverity