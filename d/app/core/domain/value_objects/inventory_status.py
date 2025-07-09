from enum import Enum


class InventoryStatus(str, Enum):
    """Inventory unit status enumeration."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    RENTED = "rented"
    IN_TRANSIT = "in_transit"
    IN_MAINTENANCE = "in_maintenance"
    DAMAGED = "damaged"
    LOST = "lost"
    STOLEN = "stolen"
    DISPOSED = "disposed"
    RETURNED = "returned"


class ConditionGrade(str, Enum):
    """Inventory condition grade enumeration."""
    NEW = "new"
    LIKE_NEW = "like_new"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"
    FOR_PARTS = "for_parts"


class InspectionStatus(str, Enum):
    """Inspection status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DamageType(str, Enum):
    """Damage type enumeration."""
    SCRATCH = "scratch"
    DENT = "dent"
    CRACK = "crack"
    TEAR = "tear"
    STAIN = "stain"
    BURN = "burn"
    WATER_DAMAGE = "water_damage"
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    COSMETIC = "cosmetic"
    FUNCTIONAL = "functional"
    OTHER = "other"


class DamageSeverity(str, Enum):
    """Damage severity enumeration."""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    SEVERE = "severe"
    TOTAL_LOSS = "total_loss"