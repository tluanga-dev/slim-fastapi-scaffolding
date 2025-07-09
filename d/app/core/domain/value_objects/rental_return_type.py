from enum import Enum


class ReturnStatus(str, Enum):
    """Return status enumeration."""
    PENDING = "PENDING"
    INITIATED = "INITIATED"
    IN_INSPECTION = "IN_INSPECTION"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    
    def is_active(self) -> bool:
        """Check if the return is in an active state."""
        return self in [self.PENDING, self.INITIATED, self.IN_INSPECTION, self.PARTIALLY_COMPLETED]
    
    def is_completed(self) -> bool:
        """Check if the return is completed."""
        return self == self.COMPLETED
    
    def is_cancelled(self) -> bool:
        """Check if the return is cancelled."""
        return self == self.CANCELLED
    
    def can_be_modified(self) -> bool:
        """Check if the return can still be modified."""
        return self in [self.PENDING, self.INITIATED]
    
    def can_process_inspection(self) -> bool:
        """Check if inspection can be processed."""
        return self in [self.INITIATED, self.IN_INSPECTION, self.PARTIALLY_COMPLETED]


class DamageLevel(str, Enum):
    """Damage level enumeration for returned items."""
    NONE = "NONE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    TOTAL_LOSS = "TOTAL_LOSS"
    
    def get_severity_score(self) -> int:
        """Get numeric severity score for damage level."""
        severity_mapping = {
            self.NONE: 0,
            self.MINOR: 1,
            self.MODERATE: 2,
            self.MAJOR: 3,
            self.TOTAL_LOSS: 4
        }
        return severity_mapping.get(self, 0)
    
    def requires_repair(self) -> bool:
        """Check if damage level requires repair."""
        return self in [self.MINOR, self.MODERATE, self.MAJOR]
    
    def requires_replacement(self) -> bool:
        """Check if damage level requires replacement."""
        return self == self.TOTAL_LOSS
    
    def affects_rentability(self) -> bool:
        """Check if damage affects the item's rentability."""
        return self in [self.MODERATE, self.MAJOR, self.TOTAL_LOSS]
    
    def get_description(self) -> str:
        """Get human-readable description of damage level."""
        descriptions = {
            self.NONE: "No damage - Item in perfect condition",
            self.MINOR: "Minor damage - Small scratches or cosmetic issues",
            self.MODERATE: "Moderate damage - Functional but with visible wear",
            self.MAJOR: "Major damage - Significant damage affecting functionality",
            self.TOTAL_LOSS: "Total loss - Item beyond repair or missing"
        }
        return descriptions.get(self, "Unknown damage level")


class ReturnType(str, Enum):
    """Return type enumeration."""
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    
    def is_full_return(self) -> bool:
        """Check if this is a full return."""
        return self == self.FULL
    
    def is_partial_return(self) -> bool:
        """Check if this is a partial return."""
        return self == self.PARTIAL


class InspectionStatus(str, Enum):
    """Inspection status enumeration."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
    def is_active(self) -> bool:
        """Check if inspection is in active state."""
        return self in [self.PENDING, self.IN_PROGRESS]
    
    def is_completed(self) -> bool:
        """Check if inspection is completed."""
        return self == self.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if inspection failed."""
        return self == self.FAILED
    
    def can_be_restarted(self) -> bool:
        """Check if inspection can be restarted."""
        return self in [self.PENDING, self.FAILED]


class FeeType(str, Enum):
    """Fee type enumeration for return-related charges."""
    LATE_FEE = "LATE_FEE"
    DAMAGE_FEE = "DAMAGE_FEE"
    CLEANING_FEE = "CLEANING_FEE"
    REPLACEMENT_FEE = "REPLACEMENT_FEE"
    RESTOCKING_FEE = "RESTOCKING_FEE"
    
    def get_description(self) -> str:
        """Get human-readable description of fee type."""
        descriptions = {
            self.LATE_FEE: "Late return fee",
            self.DAMAGE_FEE: "Damage repair fee",
            self.CLEANING_FEE: "Professional cleaning fee",
            self.REPLACEMENT_FEE: "Item replacement fee",
            self.RESTOCKING_FEE: "Restocking fee"
        }
        return descriptions.get(self, "Unknown fee type")
    
    def is_damage_related(self) -> bool:
        """Check if fee is related to damage."""
        return self in [self.DAMAGE_FEE, self.CLEANING_FEE, self.REPLACEMENT_FEE]
    
    def is_time_related(self) -> bool:
        """Check if fee is related to timing."""
        return self == self.LATE_FEE


class ReturnLineStatus(str, Enum):
    """Return line status enumeration."""
    PENDING = "PENDING"
    INSPECTED = "INSPECTED"
    PROCESSED = "PROCESSED"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"
    
    def is_final(self) -> bool:
        """Check if status is final."""
        return self in [self.PROCESSED, self.RESOLVED]
    
    def requires_attention(self) -> bool:
        """Check if status requires attention."""
        return self in [self.PENDING, self.DISPUTED]
    
    def is_disputed(self) -> bool:
        """Check if line is disputed."""
        return self == self.DISPUTED
    
    def can_be_modified(self) -> bool:
        """Check if line can still be modified."""
        return self in [self.PENDING, self.INSPECTED, self.DISPUTED]