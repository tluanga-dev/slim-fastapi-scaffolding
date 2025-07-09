"""Unit tests for StockLevel entity purchase effects."""

import pytest
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from src.domain.entities.stock_level import StockLevel


class TestStockLevelPurchaseEffects:
    """Test StockLevel entity behavior during purchase operations."""

    @pytest.fixture
    def item_id(self):
        """Sample item ID."""
        return uuid4()

    @pytest.fixture
    def location_id(self):
        """Sample location ID."""
        return uuid4()

    @pytest.fixture
    def base_stock_level(self, item_id, location_id):
        """Create a base stock level for testing."""
        return StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=10,
            quantity_available=8,
            quantity_reserved=2,
            quantity_in_transit=0,
            quantity_damaged=0,
            reorder_point=5,
            reorder_quantity=20,
            maximum_stock=100,
        )

    def test_receive_stock_increases_quantities(self, base_stock_level):
        """Test that receiving stock increases both on_hand and available quantities."""
        # Given
        initial_on_hand = base_stock_level.quantity_on_hand
        initial_available = base_stock_level.quantity_available
        purchase_quantity = 15

        # When
        base_stock_level.receive_stock(purchase_quantity, "test_user")

        # Then
        assert base_stock_level.quantity_on_hand == initial_on_hand + purchase_quantity
        assert base_stock_level.quantity_available == initial_available + purchase_quantity
        assert base_stock_level.quantity_reserved == 2  # Unchanged
        assert base_stock_level.quantity_damaged == 0   # Unchanged

    def test_receive_stock_validates_quantity_relationships(self, base_stock_level):
        """Test that quantity relationships remain valid after receiving stock."""
        # When
        base_stock_level.receive_stock(25, "test_user")

        # Then - verify business rule: on_hand = available + reserved + damaged
        total_accounted = (
            base_stock_level.quantity_available +
            base_stock_level.quantity_reserved +
            base_stock_level.quantity_damaged
        )
        assert base_stock_level.quantity_on_hand == total_accounted

    def test_receive_stock_updates_timestamp(self, base_stock_level):
        """Test that receiving stock updates the timestamp."""
        # Given
        original_updated_at = base_stock_level.updated_at

        # When
        base_stock_level.receive_stock(10, "test_user")

        # Then
        assert base_stock_level.updated_at > original_updated_at
        assert base_stock_level.updated_by == "test_user"

    def test_receive_stock_respects_maximum_stock_constraint(self, base_stock_level):
        """Test that receiving stock respects maximum stock constraints."""
        # Given - base has 10 on hand, max is 100
        # When trying to exceed maximum
        with pytest.raises(ValueError) as exc_info:
            base_stock_level.receive_stock(91, "test_user")  # Would make 101 total

        # Then
        assert "exceed maximum stock" in str(exc_info.value)

    def test_receive_stock_allows_up_to_maximum(self, base_stock_level):
        """Test that receiving stock up to maximum is allowed."""
        # Given - base has 10 on hand, max is 100
        # When receiving exactly up to maximum
        base_stock_level.receive_stock(90, "test_user")  # Makes exactly 100

        # Then
        assert base_stock_level.quantity_on_hand == 100
        assert base_stock_level.quantity_available == 98  # 8 + 90

    def test_receive_stock_with_no_maximum_constraint(self, item_id, location_id):
        """Test receiving stock when no maximum constraint is set."""
        # Given
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=50,
            quantity_available=50,
            maximum_stock=None,  # No constraint
        )

        # When
        stock_level.receive_stock(1000, "test_user")

        # Then
        assert stock_level.quantity_on_hand == 1050
        assert stock_level.quantity_available == 1050

    def test_receive_stock_rejects_zero_quantity(self, base_stock_level):
        """Test that zero quantity is rejected."""
        with pytest.raises(ValueError) as exc_info:
            base_stock_level.receive_stock(0, "test_user")

        assert "must be positive" in str(exc_info.value)

    def test_receive_stock_rejects_negative_quantity(self, base_stock_level):
        """Test that negative quantity is rejected."""
        with pytest.raises(ValueError) as exc_info:
            base_stock_level.receive_stock(-5, "test_user")

        assert "must be positive" in str(exc_info.value)

    def test_multiple_purchases_accumulate_correctly(self, base_stock_level):
        """Test that multiple purchase receipts accumulate correctly."""
        # Given
        initial_on_hand = base_stock_level.quantity_on_hand
        initial_available = base_stock_level.quantity_available

        # When - multiple purchases
        base_stock_level.receive_stock(5, "user1")
        base_stock_level.receive_stock(10, "user2")
        base_stock_level.receive_stock(3, "user3")

        # Then
        expected_on_hand = initial_on_hand + 5 + 10 + 3
        expected_available = initial_available + 5 + 10 + 3
        
        assert base_stock_level.quantity_on_hand == expected_on_hand
        assert base_stock_level.quantity_available == expected_available

    def test_reverse_purchase_reduces_stock(self, base_stock_level):
        """Test that reversing a purchase reduces stock correctly."""
        # Given
        initial_on_hand = base_stock_level.quantity_on_hand
        initial_available = base_stock_level.quantity_available

        # When
        base_stock_level.reverse_purchase(3, "test_user")

        # Then
        assert base_stock_level.quantity_on_hand == initial_on_hand - 3
        assert base_stock_level.quantity_available == initial_available - 3

    def test_reverse_purchase_validates_available_quantity(self, base_stock_level):
        """Test that reverse purchase validates available quantity."""
        # Given - only 8 available (10 on hand - 2 reserved)
        # When trying to reverse more than available
        with pytest.raises(ValueError) as exc_info:
            base_stock_level.reverse_purchase(9, "test_user")

        # Then
        assert "Only 8 available" in str(exc_info.value)

    def test_reverse_purchase_validates_on_hand_quantity(self, base_stock_level):
        """Test that reverse purchase validates on hand quantity."""
        # Given - trying to reverse more than total on hand
        # When
        with pytest.raises(ValueError) as exc_info:
            base_stock_level.reverse_purchase(11, "test_user")

        # Then
        assert "Only 10 on hand" in str(exc_info.value)

    def test_create_new_stock_level_from_purchase(self, item_id, location_id):
        """Test creating a new stock level from a purchase (zero starting inventory)."""
        # When - creating new stock level from purchase
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=25,
            quantity_available=25,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0,
        )

        # Then
        assert stock_level.quantity_on_hand == 25
        assert stock_level.quantity_available == 25
        assert stock_level.quantity_reserved == 0

    def test_purchase_with_in_transit_stock(self, item_id, location_id):
        """Test purchase when there's stock in transit (should not affect purchase receipt)."""
        # Given
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=10,
            quantity_available=10,
            quantity_in_transit=5,  # Some stock coming
            maximum_stock=30,
        )

        # When - receiving purchase
        stock_level.receive_stock(10, "test_user")

        # Then - in_transit is not affected by purchase receipt
        assert stock_level.quantity_on_hand == 20
        assert stock_level.quantity_available == 20
        assert stock_level.quantity_in_transit == 5  # Unchanged

    def test_purchase_respects_maximum_including_in_transit(self, item_id, location_id):
        """Test that maximum stock validation includes in_transit quantity."""
        # Given
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=20,
            quantity_available=20,
            quantity_in_transit=10,  # 10 more coming
            maximum_stock=35,        # Total capacity 35
        )

        # When - trying to receive more than max allows (20 on hand + 10 in transit + 6 new = 36)
        with pytest.raises(ValueError) as exc_info:
            stock_level.receive_stock(6, "test_user")

        # Then
        assert "exceeds maximum" in str(exc_info.value)
        assert "36" in str(exc_info.value)
        assert "35" in str(exc_info.value)