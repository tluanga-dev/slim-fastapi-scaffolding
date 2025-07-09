"""Unit tests for RecordCompletedPurchaseUseCase inventory and stock effects."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date
from decimal import Decimal

from src.application.use_cases.transaction.record_completed_purchase_use_case import (
    RecordCompletedPurchaseUseCase,
)
from src.domain.entities.customer import Customer
from src.domain.entities.item import Item
from src.domain.entities.stock_level import StockLevel
from src.domain.entities.inventory_unit import InventoryUnit
from src.domain.value_objects.customer_type import CustomerType
from src.domain.value_objects.item_type import InventoryStatus, ConditionGrade


class TestRecordCompletedPurchaseUseCase:
    """Test RecordCompletedPurchaseUseCase for inventory and stock management effects."""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            "transaction_repository": AsyncMock(),
            "line_repository": AsyncMock(),
            "item_repository": AsyncMock(),
            "customer_repository": AsyncMock(),
            "inventory_repository": AsyncMock(),
            "stock_repository": AsyncMock(),
        }

    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mock repositories."""
        return RecordCompletedPurchaseUseCase(
            transaction_repository=mock_repositories["transaction_repository"],
            line_repository=mock_repositories["line_repository"],
            item_repository=mock_repositories["item_repository"],
            customer_repository=mock_repositories["customer_repository"],
            inventory_repository=mock_repositories["inventory_repository"],
            stock_repository=mock_repositories["stock_repository"],
        )

    @pytest.fixture
    def supplier_id(self):
        """Sample supplier ID."""
        return uuid4()

    @pytest.fixture
    def location_id(self):
        """Sample location ID."""
        return uuid4()

    @pytest.fixture
    def item_id(self):
        """Sample item ID."""
        return uuid4()

    @pytest.fixture
    def mock_supplier(self, supplier_id):
        """Create mock supplier (business customer)."""
        supplier = MagicMock(spec=Customer)
        supplier.id = supplier_id
        supplier.customer_type = CustomerType.BUSINESS
        supplier.is_active = True
        return supplier

    @pytest.fixture
    def mock_serialized_item(self, item_id):
        """Create mock serialized item."""
        item = MagicMock(spec=Item)
        item.id = item_id
        item.item_id = "ITEM001"
        item.item_name = "Test Serialized Item"
        item.is_active = True
        item.is_serialized = True
        item.is_saleable = True
        return item

    @pytest.fixture
    def mock_non_serialized_item(self, item_id):
        """Create mock non-serialized item."""
        item = MagicMock(spec=Item)
        item.id = item_id
        item.item_id = "ITEM002"
        item.item_name = "Test Non-Serialized Item"
        item.is_active = True
        item.is_serialized = False
        item.is_saleable = True
        return item

    @pytest.fixture
    def purchase_items_serialized(self, item_id):
        """Sample purchase items with serialized items."""
        return [
            {
                "item_id": item_id,
                "quantity": 2,
                "unit_cost": "150.00",
                "serial_numbers": ["SN001", "SN002"],
                "condition_notes": "Excellent condition",
                "notes": "New stock arrival",
            }
        ]

    @pytest.fixture
    def purchase_items_non_serialized(self, item_id):
        """Sample purchase items with non-serialized items."""
        return [
            {
                "item_id": item_id,
                "quantity": 10,
                "unit_cost": "25.50",
                "notes": "Bulk purchase",
            }
        ]

    @pytest.mark.asyncio
    async def test_create_inventory_units_for_serialized_items(
        self, use_case, mock_repositories, mock_supplier, mock_serialized_item,
        supplier_id, location_id, purchase_items_serialized
    ):
        """Test that inventory units are created for serialized items."""
        # Given
        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = mock_serialized_item
        mock_repositories["inventory_repository"].get_by_serial_number.return_value = None
        mock_repositories["stock_repository"].get_by_item_location.return_value = None
        mock_repositories["transaction_repository"].generate_transaction_number.return_value = "PUR-001"

        # When
        await use_case.execute(
            supplier_id=supplier_id,
            location_id=location_id,
            items=purchase_items_serialized,
            purchase_date=date(2024, 1, 15),
            created_by="test_user",
        )

        # Then - verify inventory units were created
        assert mock_repositories["inventory_repository"].create.call_count == 2  # Two serial numbers
        
        # Verify serial number uniqueness checks
        assert mock_repositories["inventory_repository"].get_by_serial_number.call_count == 2
        mock_repositories["inventory_repository"].get_by_serial_number.assert_any_call("SN001")
        mock_repositories["inventory_repository"].get_by_serial_number.assert_any_call("SN002")

    @pytest.mark.asyncio
    async def test_reject_duplicate_serial_numbers(
        self, use_case, mock_repositories, mock_supplier, mock_serialized_item,
        supplier_id, location_id, purchase_items_serialized
    ):
        """Test that duplicate serial numbers are rejected."""
        # Given
        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = mock_serialized_item
        # Simulate existing serial number
        existing_unit = MagicMock(spec=InventoryUnit)
        mock_repositories["inventory_repository"].get_by_serial_number.return_value = existing_unit

        # When/Then
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(
                supplier_id=supplier_id,
                location_id=location_id,
                items=purchase_items_serialized,
                purchase_date=date(2024, 1, 15),
                created_by="test_user",
            )

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_serial_number_count_matches_quantity(
        self, use_case, mock_repositories, mock_supplier, mock_serialized_item,
        supplier_id, location_id, item_id
    ):
        """Test that serial number count must match quantity for serialized items."""
        # Given
        items = [
            {
                "item_id": item_id,
                "quantity": 3,  # Quantity is 3
                "unit_cost": "150.00",
                "serial_numbers": ["SN001", "SN002"],  # But only 2 serial numbers
            }
        ]
        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = mock_serialized_item

        # When/Then
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(
                supplier_id=supplier_id,
                location_id=location_id,
                items=items,
                purchase_date=date(2024, 1, 15),
                created_by="test_user",
            )

        assert "must match quantity" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_require_serial_numbers_for_serialized_items(
        self, use_case, mock_repositories, mock_supplier, mock_serialized_item,
        supplier_id, location_id, item_id
    ):
        """Test that serial numbers are required for serialized items."""
        # Given
        items = [
            {
                "item_id": item_id,
                "quantity": 2,
                "unit_cost": "150.00",
                # Missing serial_numbers
            }
        ]
        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = mock_serialized_item

        # When/Then
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(
                supplier_id=supplier_id,
                location_id=location_id,
                items=items,
                purchase_date=date(2024, 1, 15),
                created_by="test_user",
            )

        assert "Serial numbers required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_inventory_units_for_non_serialized_items(
        self, use_case, mock_repositories, mock_supplier, mock_non_serialized_item,
        supplier_id, location_id, purchase_items_non_serialized
    ):
        """Test that no inventory units are created for non-serialized items."""
        # Given
        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = mock_non_serialized_item
        mock_repositories["stock_repository"].get_by_item_location.return_value = None
        mock_repositories["transaction_repository"].generate_transaction_number.return_value = "PUR-002"

        # When
        await use_case.execute(
            supplier_id=supplier_id,
            location_id=location_id,
            items=purchase_items_non_serialized,
            purchase_date=date(2024, 1, 15),
            created_by="test_user",
        )

        # Then - verify no inventory units were created
        mock_repositories["inventory_repository"].create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_new_stock_level(
        self, use_case, mock_repositories, mock_supplier, mock_non_serialized_item,
        supplier_id, location_id, purchase_items_non_serialized, item_id
    ):
        """Test creating new stock level when none exists."""
        # Given
        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = mock_non_serialized_item
        mock_repositories["stock_repository"].get_by_item_location.return_value = None  # No existing stock
        mock_repositories["transaction_repository"].generate_transaction_number.return_value = "PUR-003"

        # When
        await use_case.execute(
            supplier_id=supplier_id,
            location_id=location_id,
            items=purchase_items_non_serialized,
            purchase_date=date(2024, 1, 15),
            created_by="test_user",
        )

        # Then - verify new stock level was created
        mock_repositories["stock_repository"].create.assert_called_once()
        created_stock = mock_repositories["stock_repository"].create.call_args[0][0]
        assert created_stock.item_id == item_id
        assert created_stock.location_id == location_id
        assert created_stock.quantity_on_hand == 10
        assert created_stock.quantity_available == 10
        assert created_stock.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_update_existing_stock_level(
        self, use_case, mock_repositories, mock_supplier, mock_non_serialized_item,
        supplier_id, location_id, purchase_items_non_serialized, item_id
    ):
        """Test updating existing stock level when one exists."""
        # Given
        existing_stock = MagicMock(spec=StockLevel)
        existing_stock.item_id = item_id
        existing_stock.location_id = location_id
        existing_stock.quantity_on_hand = 5
        existing_stock.quantity_available = 3
        existing_stock.quantity_reserved = 2

        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = mock_non_serialized_item
        mock_repositories["stock_repository"].get_by_item_location.return_value = existing_stock
        mock_repositories["transaction_repository"].generate_transaction_number.return_value = "PUR-004"

        # When
        await use_case.execute(
            supplier_id=supplier_id,
            location_id=location_id,
            items=purchase_items_non_serialized,
            purchase_date=date(2024, 1, 15),
            created_by="test_user",
        )

        # Then - verify existing stock was updated
        mock_repositories["stock_repository"].update.assert_called_once_with(existing_stock)
        assert existing_stock.quantity_on_hand == 15  # 5 + 10
        assert existing_stock.quantity_available == 13  # 3 + 10
        assert existing_stock.quantity_reserved == 2  # Unchanged
        assert existing_stock.updated_by == "test_user"

    @pytest.mark.asyncio
    async def test_stock_levels_updated_for_serialized_items_too(
        self, use_case, mock_repositories, mock_supplier, mock_serialized_item,
        supplier_id, location_id, purchase_items_serialized, item_id
    ):
        """Test that stock levels are updated even for serialized items."""
        # Given
        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = mock_serialized_item
        mock_repositories["inventory_repository"].get_by_serial_number.return_value = None
        mock_repositories["stock_repository"].get_by_item_location.return_value = None
        mock_repositories["transaction_repository"].generate_transaction_number.return_value = "PUR-005"

        # When
        await use_case.execute(
            supplier_id=supplier_id,
            location_id=location_id,
            items=purchase_items_serialized,
            purchase_date=date(2024, 1, 15),
            created_by="test_user",
        )

        # Then - verify stock level was created for serialized items too
        mock_repositories["stock_repository"].create.assert_called_once()
        created_stock = mock_repositories["stock_repository"].create.call_args[0][0]
        assert created_stock.quantity_on_hand == 2  # Quantity from purchase
        assert created_stock.quantity_available == 2

    @pytest.mark.asyncio
    async def test_reject_inactive_supplier(
        self, use_case, mock_repositories, supplier_id, location_id, purchase_items_non_serialized
    ):
        """Test that inactive suppliers are rejected."""
        # Given
        inactive_supplier = MagicMock(spec=Customer)
        inactive_supplier.customer_type = CustomerType.BUSINESS
        inactive_supplier.is_active = False  # Inactive
        mock_repositories["customer_repository"].get_by_id.return_value = inactive_supplier

        # When/Then
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(
                supplier_id=supplier_id,
                location_id=location_id,
                items=purchase_items_non_serialized,
                purchase_date=date(2024, 1, 15),
                created_by="test_user",
            )

        assert "inactive supplier" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reject_non_business_supplier(
        self, use_case, mock_repositories, supplier_id, location_id, purchase_items_non_serialized
    ):
        """Test that non-business customers are rejected as suppliers."""
        # Given
        individual_customer = MagicMock(spec=Customer)
        individual_customer.customer_type = CustomerType.INDIVIDUAL  # Not business
        individual_customer.is_active = True
        mock_repositories["customer_repository"].get_by_id.return_value = individual_customer

        # When/Then
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(
                supplier_id=supplier_id,
                location_id=location_id,
                items=purchase_items_non_serialized,
                purchase_date=date(2024, 1, 15),
                created_by="test_user",
            )

        assert "must be a business customer" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reject_inactive_item(
        self, use_case, mock_repositories, mock_supplier, supplier_id, location_id, item_id
    ):
        """Test that inactive items are rejected."""
        # Given
        inactive_item = MagicMock(spec=Item)
        inactive_item.id = item_id
        inactive_item.item_id = "INACTIVE001"
        inactive_item.is_active = False  # Inactive
        mock_repositories["customer_repository"].get_by_id.return_value = mock_supplier
        mock_repositories["item_repository"].get_by_id.return_value = inactive_item

        items = [{"item_id": item_id, "quantity": 1, "unit_cost": "100.00"}]

        # When/Then
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(
                supplier_id=supplier_id,
                location_id=location_id,
                items=items,
                purchase_date=date(2024, 1, 15),
                created_by="test_user",
            )

        assert "is not active" in str(exc_info.value)