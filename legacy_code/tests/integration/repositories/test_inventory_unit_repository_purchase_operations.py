"""Integration tests for InventoryUnit repository purchase operations."""

import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from src.domain.entities.inventory_unit import InventoryUnit
from src.domain.value_objects.item_type import InventoryStatus, ConditionGrade
from src.infrastructure.repositories.inventory_unit_repository import InventoryUnitRepository


@pytest.mark.integration
class TestInventoryUnitRepositoryPurchaseOperations:
    """Test InventoryUnit repository operations related to purchases."""

    @pytest.fixture
    def inventory_repository(self, db_session):
        """Create inventory unit repository instance."""
        return InventoryUnitRepository(db_session)

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

    @pytest.mark.asyncio
    async def test_create_inventory_unit_from_purchase(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test creating inventory unit from purchase."""
        # Given
        inventory_unit = InventoryUnit(
            inventory_code="INV-PURCH001",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN12345678",
            current_status=InventoryStatus.AVAILABLE_SALE,
            condition_grade=ConditionGrade.A,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            created_by="purchase_user"
        )

        # When
        created_unit = await inventory_repository.create(inventory_unit)

        # Then
        assert created_unit.id is not None
        assert created_unit.inventory_code == "INV-PURCH001"
        assert created_unit.item_id == item_id
        assert created_unit.location_id == location_id
        assert created_unit.serial_number == "SN12345678"
        assert created_unit.current_status == InventoryStatus.AVAILABLE_SALE
        assert created_unit.condition_grade == ConditionGrade.A
        assert created_unit.purchase_date == purchase_date
        assert created_unit.purchase_cost == purchase_cost
        assert created_unit.current_value == purchase_cost
        assert created_unit.created_by == "purchase_user"

    @pytest.mark.asyncio
    async def test_get_by_serial_number_after_purchase(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test retrieving inventory unit by serial number after purchase."""
        # Given - create inventory unit
        inventory_unit = InventoryUnit(
            inventory_code="INV-SERIAL01",
            item_id=item_id,
            location_id=location_id,
            serial_number="UNIQUE-SN-001",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        await inventory_repository.create(inventory_unit)

        # When
        retrieved_unit = await inventory_repository.get_by_serial_number("UNIQUE-SN-001")

        # Then
        assert retrieved_unit is not None
        assert retrieved_unit.serial_number == "UNIQUE-SN-001"
        assert retrieved_unit.item_id == item_id
        assert retrieved_unit.current_status == InventoryStatus.AVAILABLE_SALE

    @pytest.mark.asyncio
    async def test_get_by_inventory_code_after_purchase(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test retrieving inventory unit by inventory code after purchase."""
        # Given - create inventory unit
        inventory_unit = InventoryUnit(
            inventory_code="INV-CODE-001",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-CODE-001",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        await inventory_repository.create(inventory_unit)

        # When
        retrieved_unit = await inventory_repository.get_by_code("INV-CODE-001")

        # Then
        assert retrieved_unit is not None
        assert retrieved_unit.inventory_code == "INV-CODE-001"
        assert retrieved_unit.item_id == item_id

    @pytest.mark.asyncio
    async def test_serial_number_uniqueness_constraint(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test that serial numbers must be unique across all inventory units."""
        # Given - create first inventory unit
        inventory_unit1 = InventoryUnit(
            inventory_code="INV-UNIQUE01",
            item_id=item_id,
            location_id=location_id,
            serial_number="DUPLICATE-SN",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        await inventory_repository.create(inventory_unit1)

        # When/Then - trying to create another unit with same serial number should fail
        inventory_unit2 = InventoryUnit(
            inventory_code="INV-UNIQUE02",
            item_id=uuid4(),  # Different item
            location_id=location_id,
            serial_number="DUPLICATE-SN",  # Same serial number
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        
        with pytest.raises(Exception):  # Database constraint violation
            await inventory_repository.create(inventory_unit2)

    @pytest.mark.asyncio
    async def test_inventory_code_uniqueness_constraint(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test that inventory codes must be unique."""
        # Given - create first inventory unit
        inventory_unit1 = InventoryUnit(
            inventory_code="INV-DUPLICATE",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-001",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        await inventory_repository.create(inventory_unit1)

        # When/Then - trying to create another unit with same inventory code should fail
        inventory_unit2 = InventoryUnit(
            inventory_code="INV-DUPLICATE",  # Same inventory code
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-002",  # Different serial
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        
        with pytest.raises(Exception):  # Database constraint violation
            await inventory_repository.create(inventory_unit2)

    @pytest.mark.asyncio
    async def test_exists_by_serial_number(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test checking existence by serial number."""
        # Given - create inventory unit
        inventory_unit = InventoryUnit(
            inventory_code="INV-EXISTS01",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-EXISTS-001",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        created_unit = await inventory_repository.create(inventory_unit)

        # When/Then - check existence
        assert await inventory_repository.exists_by_serial("SN-EXISTS-001") is True
        assert await inventory_repository.exists_by_serial("NON-EXISTENT") is False

        # When/Then - check existence excluding current unit
        assert await inventory_repository.exists_by_serial(
            "SN-EXISTS-001", exclude_id=created_unit.id
        ) is False

    @pytest.mark.asyncio
    async def test_exists_by_inventory_code(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test checking existence by inventory code."""
        # Given - create inventory unit
        inventory_unit = InventoryUnit(
            inventory_code="INV-EXISTS02",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-002",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        created_unit = await inventory_repository.create(inventory_unit)

        # When/Then - check existence
        assert await inventory_repository.exists_by_code("INV-EXISTS02") is True
        assert await inventory_repository.exists_by_code("INV-NONEXISTENT") is False

        # When/Then - check existence excluding current unit
        assert await inventory_repository.exists_by_code(
            "INV-EXISTS02", exclude_id=created_unit.id
        ) is False

    @pytest.mark.asyncio
    async def test_get_available_units_after_purchase(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test getting available units after purchase."""
        # Given - create multiple inventory units
        for i in range(3):
            inventory_unit = InventoryUnit(
                inventory_code=f"INV-AVAIL{i:03d}",
                item_id=item_id,
                location_id=location_id,
                serial_number=f"SN-AVAIL-{i:03d}",
                current_status=InventoryStatus.AVAILABLE_SALE,
                purchase_date=purchase_date,
                purchase_cost=purchase_cost,
            )
            await inventory_repository.create(inventory_unit)

        # Create one sold unit (not available)
        sold_unit = InventoryUnit(
            inventory_code="INV-SOLD001",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-SOLD-001",
            current_status=InventoryStatus.SOLD,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        await inventory_repository.create(sold_unit)

        # When
        available_units = await inventory_repository.get_available_units(item_id, location_id)

        # Then - only available units should be returned
        assert len(available_units) == 3
        for unit in available_units:
            assert unit.current_status == InventoryStatus.AVAILABLE_SALE
            assert unit.item_id == item_id

    @pytest.mark.asyncio
    async def test_list_inventory_units_by_location(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test listing inventory units filtered by location."""
        # Given - create units at specific location
        for i in range(2):
            inventory_unit = InventoryUnit(
                inventory_code=f"INV-LOC{i:03d}",
                item_id=item_id,
                location_id=location_id,
                serial_number=f"SN-LOC-{i:03d}",
                current_status=InventoryStatus.AVAILABLE_SALE,
                purchase_date=purchase_date,
                purchase_cost=purchase_cost,
            )
            await inventory_repository.create(inventory_unit)

        # Create unit at different location
        other_location_id = uuid4()
        other_unit = InventoryUnit(
            inventory_code="INV-OTHER001",
            item_id=item_id,
            location_id=other_location_id,
            serial_number="SN-OTHER-001",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        await inventory_repository.create(other_unit)

        # When
        units, total_count = await inventory_repository.list(location_id=location_id)

        # Then
        assert total_count == 2
        assert len(units) == 2
        for unit in units:
            assert unit.location_id == location_id

    @pytest.mark.asyncio
    async def test_get_units_by_status(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test getting units by status."""
        # Given - create units with different statuses
        available_unit = InventoryUnit(
            inventory_code="INV-AVAIL001",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-AVAIL-001",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        reserved_unit = InventoryUnit(
            inventory_code="INV-RESERV001",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-RESERV-001",
            current_status=InventoryStatus.RESERVED_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        await inventory_repository.create(available_unit)
        await inventory_repository.create(reserved_unit)

        # When
        available_units, count = await inventory_repository.get_units_by_status(
            InventoryStatus.AVAILABLE_SALE, location_id
        )

        # Then
        assert count == 1
        assert len(available_units) == 1
        assert available_units[0].current_status == InventoryStatus.AVAILABLE_SALE

    @pytest.mark.asyncio
    async def test_count_by_status_after_purchases(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test counting inventory units by status after purchases."""
        # Given - create units with different statuses
        statuses = [
            InventoryStatus.AVAILABLE_SALE,
            InventoryStatus.AVAILABLE_SALE,
            InventoryStatus.RESERVED_SALE,
            InventoryStatus.SOLD,
        ]
        
        for i, status in enumerate(statuses):
            inventory_unit = InventoryUnit(
                inventory_code=f"INV-COUNT{i:03d}",
                item_id=item_id,
                location_id=location_id,
                serial_number=f"SN-COUNT-{i:03d}",
                current_status=status,
                purchase_date=purchase_date,
                purchase_cost=purchase_cost,
            )
            await inventory_repository.create(inventory_unit)

        # When
        status_counts = await inventory_repository.count_by_status(location_id)

        # Then
        assert status_counts.get(InventoryStatus.AVAILABLE_SALE.value, 0) == 2
        assert status_counts.get(InventoryStatus.RESERVED_SALE.value, 0) == 1
        assert status_counts.get(InventoryStatus.SOLD.value, 0) == 1

    @pytest.mark.asyncio
    async def test_count_by_condition_after_purchases(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test counting inventory units by condition grade after purchases."""
        # Given - create units with different conditions
        conditions = [ConditionGrade.A, ConditionGrade.A, ConditionGrade.B, ConditionGrade.C]
        
        for i, condition in enumerate(conditions):
            inventory_unit = InventoryUnit(
                inventory_code=f"INV-COND{i:03d}",
                item_id=item_id,
                location_id=location_id,
                serial_number=f"SN-COND-{i:03d}",
                current_status=InventoryStatus.AVAILABLE_SALE,
                condition_grade=condition,
                purchase_date=purchase_date,
                purchase_cost=purchase_cost,
            )
            await inventory_repository.create(inventory_unit)

        # When
        condition_counts = await inventory_repository.count_by_condition(location_id)

        # Then
        assert condition_counts.get(ConditionGrade.A.value, 0) == 2
        assert condition_counts.get(ConditionGrade.B.value, 0) == 1
        assert condition_counts.get(ConditionGrade.C.value, 0) == 1

    @pytest.mark.asyncio
    async def test_update_inventory_unit_status_after_purchase(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test updating inventory unit status after purchase."""
        # Given - create inventory unit
        inventory_unit = InventoryUnit(
            inventory_code="INV-UPDATE001",
            item_id=item_id,
            location_id=location_id,
            serial_number="SN-UPDATE-001",
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )
        created_unit = await inventory_repository.create(inventory_unit)

        # When - update status to reserved
        created_unit.update_status(InventoryStatus.RESERVED_SALE, "sales_user")
        updated_unit = await inventory_repository.update(created_unit)

        # Then
        assert updated_unit.current_status == InventoryStatus.RESERVED_SALE
        assert updated_unit.updated_by == "sales_user"

        # Verify by retrieving again
        retrieved_unit = await inventory_repository.get_by_id(created_unit.id)
        assert retrieved_unit.current_status == InventoryStatus.RESERVED_SALE

    @pytest.mark.asyncio
    async def test_inventory_unit_without_serial_number(
        self, inventory_repository, item_id, location_id, purchase_date, purchase_cost
    ):
        """Test creating inventory unit without serial number (non-serialized item)."""
        # Given
        inventory_unit = InventoryUnit(
            inventory_code="INV-NONSERIALIZED",
            item_id=item_id,
            location_id=location_id,
            serial_number=None,  # No serial number
            current_status=InventoryStatus.AVAILABLE_SALE,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
        )

        # When
        created_unit = await inventory_repository.create(inventory_unit)

        # Then
        assert created_unit.serial_number is None
        assert created_unit.inventory_code == "INV-NONSERIALIZED"

        # Should be retrievable by code
        retrieved_unit = await inventory_repository.get_by_code("INV-NONSERIALIZED")
        assert retrieved_unit is not None
        assert retrieved_unit.serial_number is None