from enum import Enum


class ItemType(str, Enum):
    """Item type enumeration."""
    RENTAL = "RENTAL"
    SALE = "SALE"
    SERVICE = "SERVICE"
    CONSUMABLE = "CONSUMABLE"


class InventoryStatus(str, Enum):
    """Inventory status enumeration."""
    AVAILABLE_RENTAL = "AVAILABLE_RENTAL"
    AVAILABLE_SALE = "AVAILABLE_SALE"
    RENTED = "RENTED"
    SOLD = "SOLD"
    MAINTENANCE = "MAINTENANCE"
    DAMAGED = "DAMAGED"
    LOST = "LOST"
    RETIRED = "RETIRED"
    
    def is_available(self) -> bool:
        """Check if the item is available for rental or sale."""
        return self in [self.AVAILABLE_RENTAL, self.AVAILABLE_SALE]
    
    def is_unavailable(self) -> bool:
        """Check if the item is unavailable."""
        return not self.is_available()
    
    def can_be_rented(self) -> bool:
        """Check if the item can be rented."""
        return self == self.AVAILABLE_RENTAL
    
    def can_be_sold(self) -> bool:
        """Check if the item can be sold."""
        return self == self.AVAILABLE_SALE


class ConditionGrade(str, Enum):
    """Condition grade enumeration."""
    A = "A"  # Excellent - Like new
    B = "B"  # Good - Minor wear
    C = "C"  # Fair - Moderate wear
    D = "D"  # Poor - Significant wear
    F = "F"  # Fail - Not usable
    
    def get_description(self) -> str:
        """Get human-readable description of condition grade."""
        descriptions = {
            self.A: "Excellent - Like new condition",
            self.B: "Good - Minor wear, fully functional",
            self.C: "Fair - Moderate wear, functional",
            self.D: "Poor - Significant wear, may need repair",
            self.F: "Fail - Not usable, requires major repair or replacement"
        }
        return descriptions.get(self, "Unknown condition")
    
    def is_rentable(self) -> bool:
        """Check if the condition allows the item to be rented."""
        return self in [self.A, self.B, self.C]
    
    def is_sellable(self) -> bool:
        """Check if the condition allows the item to be sold."""
        return self in [self.A, self.B, self.C, self.D]
    
    def requires_maintenance(self) -> bool:
        """Check if the condition requires maintenance."""
        return self in [self.D, self.F]