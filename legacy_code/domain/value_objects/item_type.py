from enum import Enum


class ItemType(str, Enum):
    """Item type enumeration."""

    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    BUNDLE = "BUNDLE"


class InventoryStatus(str, Enum):
    """Inventory unit status enumeration."""

    AVAILABLE_SALE = "AVAILABLE_SALE"
    AVAILABLE_RENT = "AVAILABLE_RENT"
    RESERVED_SALE = "RESERVED_SALE"
    RESERVED_RENT = "RESERVED_RENT"
    RENTED = "RENTED"
    SOLD = "SOLD"
    IN_TRANSIT = "IN_TRANSIT"
    INSPECTION_PENDING = "INSPECTION_PENDING"
    CLEANING = "CLEANING"
    REPAIR = "REPAIR"
    DAMAGED = "DAMAGED"
    LOST = "LOST"
    RETURNED_TO_SUPPLIER = "RETURNED_TO_SUPPLIER"


class ConditionGrade(str, Enum):
    """Item condition grade enumeration."""

    A = "A"  # Excellent/Like New
    B = "B"  # Good
    C = "C"  # Fair
    D = "D"  # Poor
