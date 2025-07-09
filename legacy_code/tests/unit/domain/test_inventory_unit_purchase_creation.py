"""Unit tests for InventoryUnit entity creation during purchases."""

import pytest
from uuid import uuid4
from datetime import datetime, date
from decimal import Decimal

from src.domain.entities.inventory_unit import InventoryUnit
from src.domain.value_objects.item_type import InventoryStatus, ConditionGrade


class TestInventoryUnitPurchaseCreation:
    """Test InventoryUnit entity creation and behavior during purchase operations."""

    @pytest.fixture
    def item_id(self):
        """Sample item ID."""
        return uuid4()

    @pytest.fixture
    def location_id(self):
        """Sample location ID."""
        return uuid4()

    @pytest.fixture
    def purchase_date(self):
        """Sample purchase date."""
        return date(2024, 1, 15)

    @pytest.fixture
    def purchase_cost(self):
        """Sample purchase cost."""
        return Decimal("299.99")

    def test_create_inventory_unit_for_purchase(self, item_id, location_id, purchase_date, purchase_cost):
        """Test creating a new inventory unit from a purchase."""
        # When
        inventory_unit = InventoryUnit(
            inventory_code="INV-ABC12345",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN123456789",
            current_status=InventoryStatus.AVAILABLE_SALE,
            condition_grade=ConditionGrade.A,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            created_by="purchase_user"
        )

        # Then
        assert inventory_unit.inventory_code == "INV-ABC12345"
        assert inventory_unit.item_id == item_id
        assert inventory_unit.location_id == location_id
        assert inventory_unit.serial_number == "SN123456789"
        assert inventory_unit.current_status == InventoryStatus.AVAILABLE_SALE
        assert inventory_unit.condition_grade == ConditionGrade.A
        assert inventory_unit.purchase_date == purchase_date
        assert inventory_unit.purchase_cost == purchase_cost
        assert inventory_unit.current_value == purchase_cost  # Should default to purchase cost
        assert inventory_unit.total_rental_days == 0
        assert inventory_unit.rental_count == 0
        assert inventory_unit.is_active is True

    def test_create_inventory_unit_for_rental_item(self, item_id, location_id, purchase_date, purchase_cost):
        """Test creating inventory unit for rental-only item."""
        # When
        inventory_unit = InventoryUnit(
            inventory_code="INV-RENT001",
            item_id=item_id,
            location_id=location_id,
            serial_number="RENT123",
            current_status=InventoryStatus.AVAILABLE_RENT,
            condition_grade=ConditionGrade.A,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            created_by="purchase_user"
        )

        # Then
        assert inventory_unit.current_status == InventoryStatus.AVAILABLE_RENT
        assert inventory_unit.is_rentable is True
        assert inventory_unit.is_saleable is False

    def test_create_inventory_unit_without_serial_number(self, item_id, location_id, purchase_date, purchase_cost):
        """Test creating inventory unit for non-serialized item."""
        # When
        inventory_unit = InventoryUnit(
            inventory_code="INV-BULK001",
            item_id=item_id,
            location_id=location_id,
            serial_number=None,  # Non-serialized
            current_status=InventoryStatus.AVAILABLE_SALE,
            condition_grade=ConditionGrade.A,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            created_by="purchase_user"
        )

        # Then
        assert inventory_unit.serial_number is None
        assert inventory_unit.is_available is True

    def test_create_inventory_unit_with_custom_current_value(self, item_id, location_id, purchase_date, purchase_cost):
        """Test creating inventory unit with custom current value different from purchase cost."""
        # Given
        current_value = Decimal("350.00")

        # When
        inventory_unit = InventoryUnit(
            inventory_code="INV-CUSTOM01",
            item_id=item_id,
            location_id=location_id,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            current_value=current_value,
            created_by="purchase_user"
        )

        # Then
        assert inventory_unit.purchase_cost == purchase_cost
        assert inventory_unit.current_value == current_value

    def test_inventory_unit_defaults_to_grade_a_for_new_purchase(self, item_id, location_id, purchase_date, purchase_cost):
        """Test that new purchases default to condition grade A."""
        # When
        inventory_unit = InventoryUnit(
            inventory_code="INV-NEW001",
            item_id=item_id,
            location_id=location_id,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            # Not specifying condition_grade, should default to A
            created_by="purchase_user"
        )

        # Then
        assert inventory_unit.condition_grade == ConditionGrade.A

    def test_inventory_unit_validates_required_fields(self, item_id, location_id):
        """Test that required fields are validated."""
        # Test missing inventory_code
        with pytest.raises(ValueError) as exc_info:
            InventoryUnit(
                inventory_code="",  # Empty code
                item_id=item_id,
                location_id=location_id,
            )
        assert "Inventory code is required" in str(exc_info.value)

        # Test missing item_id
        with pytest.raises(ValueError) as exc_info:
            InventoryUnit(
                inventory_code="INV-TEST",
                item_id=None,  # Missing item_id
                location_id=location_id,
            )
        assert "Item ID is required" in str(exc_info.value)

        # Test missing location_id
        with pytest.raises(ValueError) as exc_info:
            InventoryUnit(
                inventory_code="INV-TEST",
                item_id=item_id,
                location_id=None,  # Missing location_id
            )
        assert "Location ID is required" in str(exc_info.value)

    def test_inventory_unit_validates_costs(self, item_id, location_id):
        """Test that cost validations work correctly."""
        # Test negative purchase cost
        with pytest.raises(ValueError) as exc_info:
            InventoryUnit(
                inventory_code="INV-TEST",
                item_id=item_id,
                location_id=location_id,
                purchase_cost=Decimal("-10.00"),  # Negative cost
            )
        assert "Purchase cost cannot be negative" in str(exc_info.value)

        # Test negative current value
        with pytest.raises(ValueError) as exc_info:
            InventoryUnit(
                inventory_code="INV-TEST",
                item_id=item_id,
                location_id=location_id,
                current_value=Decimal("-5.00"),  # Negative value
            )
        assert "Current value cannot be negative" in str(exc_info.value)

    def test_inventory_unit_validates_rental_stats(self, item_id, location_id):
        """Test that rental statistics validations work correctly."""
        # Test negative rental days
        with pytest.raises(ValueError) as exc_info:
            InventoryUnit(
                inventory_code="INV-TEST",
                item_id=item_id,
                location_id=location_id,
                total_rental_days=-1,  # Negative days
            )
        assert "Total rental days cannot be negative" in str(exc_info.value)

        # Test negative rental count
        with pytest.raises(ValueError) as exc_info:
            InventoryUnit(
                inventory_code="INV-TEST",
                item_id=item_id,
                location_id=location_id,
                rental_count=-1,  # Negative count
            )
        assert "Rental count cannot be negative" in str(exc_info.value)

    def test_inventory_unit_status_transitions_from_purchase(self, item_id, location_id, purchase_date, purchase_cost):
        """Test valid status transitions after purchase."""
        # Given - newly purchased item
        inventory_unit = InventoryUnit(
            inventory_code="INV-TRANS01",
            item_id=item_id,
            location_id=location_id,
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )

        # Test valid transitions from AVAILABLE_SALE
        assert inventory_unit.can_transition_to(InventoryStatus.RESERVED_SALE) is True
        assert inventory_unit.can_transition_to(InventoryStatus.AVAILABLE_RENT) is True
        assert inventory_unit.can_transition_to(InventoryStatus.INSPECTION_PENDING) is True
        assert inventory_unit.can_transition_to(InventoryStatus.DAMAGED) is True

        # Test invalid transitions
        assert inventory_unit.can_transition_to(InventoryStatus.SOLD) is False
        assert inventory_unit.can_transition_to(InventoryStatus.RENTED) is False

    def test_inventory_unit_update_status_after_purchase(self, item_id, location_id, purchase_date, purchase_cost):
        """Test updating status after purchase."""
        # Given
        inventory_unit = InventoryUnit(
            inventory_code="INV-UPDATE01",
            item_id=item_id,
            location_id=location_id,
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )

        # When - transitioning to reserved for sale
        inventory_unit.update_status(InventoryStatus.RESERVED_SALE, "sales_user")

        # Then
        assert inventory_unit.current_status == InventoryStatus.RESERVED_SALE
        assert inventory_unit.updated_by == "sales_user"

    def test_inventory_unit_cannot_transition_to_invalid_status(self, item_id, location_id, purchase_date, purchase_cost):
        """Test that invalid status transitions are rejected."""
        # Given
        inventory_unit = InventoryUnit(
            inventory_code="INV-INVALID01",
            item_id=item_id,
            location_id=location_id,
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )

        # When/Then - trying invalid transition
        with pytest.raises(ValueError) as exc_info:
            inventory_unit.update_status(InventoryStatus.SOLD, "invalid_user")

        assert "Cannot transition from AVAILABLE_SALE to SOLD" in str(exc_info.value)

    def test_inventory_unit_properties_after_purchase(self, item_id, location_id, purchase_date, purchase_cost):
        """Test inventory unit properties after purchase."""
        # Given - sale item
        sale_unit = InventoryUnit(
            inventory_code="INV-SALE01",
            item_id=item_id,
            location_id=location_id,
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )

        # Then
        assert sale_unit.is_available is True
        assert sale_unit.is_saleable is True
        assert sale_unit.is_rentable is False
        assert sale_unit.requires_inspection is False
        assert sale_unit.is_in_service is False

        # Given - rental item
        rental_unit = InventoryUnit(
            inventory_code="INV-RENT01",
            item_id=item_id,
            location_id=location_id,
            current_status=InventoryStatus.AVAILABLE_RENT,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )

        # Then
        assert rental_unit.is_available is True
        assert rental_unit.is_saleable is False
        assert rental_unit.is_rentable is True

    def test_inventory_unit_string_representations(self, item_id, location_id, purchase_date, purchase_cost):
        """Test string representations of inventory unit."""
        # Given
        inventory_unit = InventoryUnit(
            inventory_code="INV-STR01",
            item_id=item_id,
            location_id=location_id,
            current_status=InventoryStatus.AVAILABLE_SALE,
            condition_grade=ConditionGrade.A,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )

        # Then
        str_repr = str(inventory_unit)
        assert "INV-STR01" in str_repr
        assert "AVAILABLE_SALE" in str_repr

        dev_repr = repr(inventory_unit)
        assert "INV-STR01" in dev_repr
        assert "AVAILABLE_SALE" in dev_repr
        assert "condition=A" in dev_repr

    def test_inventory_unit_with_purchase_notes(self, item_id, location_id, purchase_date, purchase_cost):
        """Test inventory unit with purchase notes."""
        # Given
        purchase_notes = "Excellent condition, original packaging"

        # When
        inventory_unit = InventoryUnit(
            inventory_code="INV-NOTES01",
            item_id=item_id,
            location_id=location_id,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            notes=purchase_notes,
        )

        # Then
        assert inventory_unit.notes == purchase_notes