from typing import Optional
from datetime import datetime
from uuid import UUID

from ..entities.base import BaseEntity


class StockLevel(BaseEntity):
    """Stock Level entity for aggregate inventory tracking by Item and location."""

    def __init__(
        self,
        item_id: UUID,
        location_id: UUID,
        quantity_on_hand: int = 0,
        quantity_available: int = 0,
        quantity_reserved: int = 0,
        quantity_in_transit: int = 0,
        quantity_damaged: int = 0,
        reorder_point: int = 0,
        reorder_quantity: int = 0,
        maximum_stock: Optional[int] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ):
        """Initialize Stock Level entity."""
        super().__init__(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            is_active=is_active,
            created_by=created_by,
            updated_by=updated_by,
        )
        self.item_id = item_id
        self.location_id = location_id
        self.quantity_on_hand = quantity_on_hand
        self.quantity_available = quantity_available
        self.quantity_reserved = quantity_reserved
        self.quantity_in_transit = quantity_in_transit
        self.quantity_damaged = quantity_damaged
        self.reorder_point = reorder_point
        self.reorder_quantity = reorder_quantity
        self.maximum_stock = maximum_stock
        self._validate()

    def _validate(self):
        """Validate stock level business rules."""
        if not self.item_id:
            raise ValueError("Item ID is required")

        if not self.location_id:
            raise ValueError("Location ID is required")

        # Validate quantities are non-negative
        if self.quantity_on_hand < 0:
            raise ValueError("Quantity on hand cannot be negative")

        if self.quantity_available < 0:
            raise ValueError("Quantity available cannot be negative")

        if self.quantity_reserved < 0:
            raise ValueError("Quantity reserved cannot be negative")

        if self.quantity_in_transit < 0:
            raise ValueError("Quantity in transit cannot be negative")

        if self.quantity_damaged < 0:
            raise ValueError("Quantity damaged cannot be negative")

        if self.reorder_point < 0:
            raise ValueError("Reorder point cannot be negative")

        if self.reorder_quantity < 0:
            raise ValueError("Reorder quantity cannot be negative")

        if self.maximum_stock is not None and self.maximum_stock < 0:
            raise ValueError("Maximum stock cannot be negative")

        # Validate quantity relationships
        total_accounted = (
            self.quantity_available + self.quantity_reserved + self.quantity_damaged
        )

        if total_accounted != self.quantity_on_hand:
            raise ValueError(
                f"Quantity mismatch: on_hand ({self.quantity_on_hand}) != "
                f"available ({self.quantity_available}) + "
                f"reserved ({self.quantity_reserved}) + "
                f"damaged ({self.quantity_damaged})"
            )

        # Validate maximum stock
        if self.maximum_stock is not None:
            total_incoming = self.quantity_on_hand + self.quantity_in_transit
            if total_incoming > self.maximum_stock:
                raise ValueError(
                    f"Total stock ({total_incoming}) exceeds maximum ({self.maximum_stock})"
                )

    def reserve_stock(self, quantity: int, updated_by: Optional[str] = None):
        """Reserve stock for a transaction."""
        if quantity <= 0:
            raise ValueError("Reserve quantity must be positive")

        if quantity > self.quantity_available:
            raise ValueError(
                f"Cannot reserve {quantity} units. Only {self.quantity_available} available"
            )

        self.quantity_available -= quantity
        self.quantity_reserved += quantity
        self.update_timestamp(updated_by)
        self._validate()

    def release_reservation(self, quantity: int, updated_by: Optional[str] = None):
        """Release reserved stock back to available."""
        if quantity <= 0:
            raise ValueError("Release quantity must be positive")

        if quantity > self.quantity_reserved:
            raise ValueError(
                f"Cannot release {quantity} units. Only {self.quantity_reserved} reserved"
            )

        self.quantity_reserved -= quantity
        self.quantity_available += quantity
        self.update_timestamp(updated_by)
        self._validate()

    def confirm_sale(self, quantity: int, updated_by: Optional[str] = None):
        """Confirm sale from reserved stock."""
        if quantity <= 0:
            raise ValueError("Sale quantity must be positive")

        if quantity > self.quantity_reserved:
            raise ValueError(
                f"Cannot sell {quantity} units. Only {self.quantity_reserved} reserved"
            )

        self.quantity_reserved -= quantity
        self.quantity_on_hand -= quantity
        self.update_timestamp(updated_by)
        self._validate()
    
    def sell_direct(self, quantity: int, updated_by: Optional[str] = None):
        """Sell directly from available stock (for completed sales)."""
        if quantity <= 0:
            raise ValueError("Sale quantity must be positive")

        if quantity > self.quantity_available:
            raise ValueError(
                f"Cannot sell {quantity} units. Only {self.quantity_available} available"
            )

        self.quantity_available -= quantity
        self.quantity_on_hand -= quantity
        self.update_timestamp(updated_by)
        self._validate()

    def receive_stock(self, quantity: int, updated_by: Optional[str] = None):
        """Receive new stock."""
        if quantity <= 0:
            raise ValueError("Receive quantity must be positive")

        # Check maximum stock constraint
        if self.maximum_stock is not None:
            new_total = self.quantity_on_hand + quantity
            if new_total > self.maximum_stock:
                raise ValueError(
                    f"Receiving {quantity} units would exceed maximum stock "
                    f"({new_total} > {self.maximum_stock})"
                )

        self.quantity_on_hand += quantity
        self.quantity_available += quantity
        self.update_timestamp(updated_by)
        self._validate()

    def start_transit(self, quantity: int, updated_by: Optional[str] = None):
        """Mark stock as in transit."""
        if quantity <= 0:
            raise ValueError("Transit quantity must be positive")

        self.quantity_in_transit += quantity
        self.update_timestamp(updated_by)

    def complete_transit(self, quantity: int, updated_by: Optional[str] = None):
        """Complete transit and receive stock."""
        if quantity <= 0:
            raise ValueError("Transit quantity must be positive")

        if quantity > self.quantity_in_transit:
            raise ValueError(
                f"Cannot complete transit for {quantity} units. "
                f"Only {self.quantity_in_transit} in transit"
            )

        self.quantity_in_transit -= quantity
        self.receive_stock(quantity, updated_by)

    def mark_damaged(self, quantity: int, updated_by: Optional[str] = None):
        """Mark stock as damaged."""
        if quantity <= 0:
            raise ValueError("Damage quantity must be positive")

        if quantity > self.quantity_available:
            raise ValueError(
                f"Cannot mark {quantity} units as damaged. "
                f"Only {self.quantity_available} available"
            )

        self.quantity_available -= quantity
        self.quantity_damaged += quantity
        self.update_timestamp(updated_by)
        self._validate()

    def write_off_damaged(self, quantity: int, updated_by: Optional[str] = None):
        """Write off damaged stock."""
        if quantity <= 0:
            raise ValueError("Write-off quantity must be positive")

        if quantity > self.quantity_damaged:
            raise ValueError(
                f"Cannot write off {quantity} units. "
                f"Only {self.quantity_damaged} damaged"
            )

        self.quantity_damaged -= quantity
        self.quantity_on_hand -= quantity
        self.update_timestamp(updated_by)
        self._validate()

    def repair_damaged(self, quantity: int, updated_by: Optional[str] = None):
        """Return repaired stock to available."""
        if quantity <= 0:
            raise ValueError("Repair quantity must be positive")

        if quantity > self.quantity_damaged:
            raise ValueError(
                f"Cannot repair {quantity} units. "
                f"Only {self.quantity_damaged} damaged"
            )

        self.quantity_damaged -= quantity
        self.quantity_available += quantity
        self.update_timestamp(updated_by)
        self._validate()

    def adjust_stock(
        self, adjustment: int, reason: str, updated_by: Optional[str] = None
    ):
        """Manual stock adjustment."""
        if not reason or not reason.strip():
            raise ValueError("Adjustment reason is required")

        new_on_hand = self.quantity_on_hand + adjustment
        if new_on_hand < 0:
            raise ValueError("Adjustment would result in negative stock")

        new_available = self.quantity_available + adjustment
        if new_available < 0:
            # Adjustment affects reserved or damaged stock
            raise ValueError(
                "Adjustment would result in negative available stock. "
                "Check reserved and damaged quantities."
            )

        self.quantity_on_hand = new_on_hand
        self.quantity_available = new_available
        self.update_timestamp(updated_by)
        self._validate()

    def reverse_purchase(self, quantity: int, updated_by: Optional[str] = None):
        """Reverse a purchase by removing stock (returning items to supplier)."""
        if quantity <= 0:
            raise ValueError("Reverse purchase quantity must be positive")

        if quantity > self.quantity_on_hand:
            raise ValueError(
                f"Cannot reverse purchase of {quantity} units. "
                f"Only {self.quantity_on_hand} on hand"
            )

        if quantity > self.quantity_available:
            raise ValueError(
                f"Cannot reverse purchase of {quantity} units. "
                f"Only {self.quantity_available} available (some may be reserved)"
            )

        self.quantity_on_hand -= quantity
        self.quantity_available -= quantity
        self.update_timestamp(updated_by)
        self._validate()

    def reverse_sale(self, quantity: int, updated_by: Optional[str] = None):
        """Reverse a sale by adding stock back (customer returning items)."""
        if quantity <= 0:
            raise ValueError("Reverse sale quantity must be positive")

        # Check maximum stock constraint
        if self.maximum_stock is not None:
            new_total = self.quantity_on_hand + quantity
            if new_total > self.maximum_stock:
                raise ValueError(
                    f"Reversing sale of {quantity} units would exceed maximum stock "
                    f"({new_total} > {self.maximum_stock})"
                )

        self.quantity_on_hand += quantity
        self.quantity_available += quantity
        self.update_timestamp(updated_by)
        self._validate()

    def update_reorder_levels(
        self,
        reorder_point: int,
        reorder_quantity: int,
        maximum_stock: Optional[int] = None,
        updated_by: Optional[str] = None,
    ):
        """Update reorder levels."""
        if reorder_point < 0:
            raise ValueError("Reorder point cannot be negative")

        if reorder_quantity <= 0:
            raise ValueError("Reorder quantity must be positive")

        if maximum_stock is not None and maximum_stock < 0:
            raise ValueError("Maximum stock cannot be negative")

        if maximum_stock is not None and reorder_point >= maximum_stock:
            raise ValueError("Reorder point must be less than maximum stock")

        self.reorder_point = reorder_point
        self.reorder_quantity = reorder_quantity
        self.maximum_stock = maximum_stock
        self.update_timestamp(updated_by)

    def ship_stock(self, quantity: int, updated_by: Optional[str] = None):
        """Ship stock (reduce from available)."""
        if quantity <= 0:
            raise ValueError("Ship quantity must be positive")

        if quantity > self.quantity_available:
            raise ValueError(
                f"Cannot ship {quantity} units. Only {self.quantity_available} available"
            )

        self.quantity_available -= quantity
        self.quantity_on_hand -= quantity
        self.update_timestamp(updated_by)
        self._validate()

    def release_stock(self, quantity: int, updated_by: Optional[str] = None):
        """Release reserved stock back to available."""
        if quantity <= 0:
            raise ValueError("Release quantity must be positive")

        if quantity > self.quantity_reserved:
            raise ValueError(
                f"Cannot release {quantity} units. Only {self.quantity_reserved} reserved"
            )

        self.quantity_reserved -= quantity
        self.quantity_available += quantity
        self.update_timestamp(updated_by)
        self._validate()

    def unmark_damaged(self, quantity: int, updated_by: Optional[str] = None):
        """Repair damaged stock back to available."""
        if quantity <= 0:
            raise ValueError("Repair quantity must be positive")

        if quantity > self.quantity_damaged:
            raise ValueError(
                f"Cannot repair {quantity} units. Only {self.quantity_damaged} damaged"
            )

        self.quantity_damaged -= quantity
        self.quantity_available += quantity
        self.update_timestamp(updated_by)
        self._validate()

    @property
    def needs_reorder(self) -> bool:
        """Check if stock needs reordering."""
        return self.quantity_available <= self.reorder_point

    @property
    def suggested_order_quantity(self) -> int:
        """Calculate suggested order quantity."""
        if not self.needs_reorder:
            return 0

        if self.maximum_stock is not None:
            # Order up to maximum stock level
            current_total = self.quantity_on_hand + self.quantity_in_transit
            max_order = self.maximum_stock - current_total
            return min(self.reorder_quantity, max_order)

        return self.reorder_quantity

    @property
    def stock_utilization(self) -> float:
        """Calculate stock utilization percentage."""
        if self.maximum_stock is None or self.maximum_stock == 0:
            return 0.0

        return (self.quantity_on_hand / self.maximum_stock) * 100

    def __str__(self) -> str:
        """String representation of stock level."""
        return (
            f"StockLevel(Item={self.item_id}, Location={self.location_id}, "
            f"Available={self.quantity_available})"
        )

    def __repr__(self) -> str:
        """Developer representation of stock level."""
        return (
            f"StockLevel(id={self.id}, item_id={self.item_id}, "
            f"location_id={self.location_id}, on_hand={self.quantity_on_hand}, "
            f"available={self.quantity_available})"
        )
