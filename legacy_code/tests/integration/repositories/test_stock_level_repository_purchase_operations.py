"""Integration tests for StockLevel repository purchase operations."""

import pytest
from uuid import uuid4
from decimal import Decimal

from src.domain.entities.stock_level import StockLevel
from src.infrastructure.repositories.stock_level_repository import StockLevelRepository


@pytest.mark.integration
class TestStockLevelRepositoryPurchaseOperations:
    """Test StockLevel repository operations related to purchases."""

    @pytest.fixture
    def stock_repository(self, db_session):
        """Create stock level repository instance."""
        return StockLevelRepository(db_session)

    @pytest.fixture
    def item_id(self):
        """Sample item ID."""
        return uuid4()

    @pytest.fixture
    def location_id(self):
        """Sample location ID."""
        return uuid4()

    @pytest.fixture
    def another_location_id(self):
        """Another location ID for multi-location tests."""
        return uuid4()

    @pytest.mark.asyncio
    async def test_create_new_stock_level_from_purchase(self, stock_repository, item_id, location_id):
        """Test creating a new stock level from a purchase."""
        # Given
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=25,
            quantity_available=25,
            quantity_reserved=0,
            reorder_point=5,
            reorder_quantity=50,
            maximum_stock=100,
            created_by="purchase_user"
        )

        # When
        created_stock = await stock_repository.create(stock_level)

        # Then
        assert created_stock.id is not None
        assert created_stock.item_id == item_id
        assert created_stock.location_id == location_id
        assert created_stock.quantity_on_hand == 25
        assert created_stock.quantity_available == 25
        assert created_stock.quantity_reserved == 0
        assert created_stock.created_by == "purchase_user"

    @pytest.mark.asyncio
    async def test_get_by_item_location_after_purchase(self, stock_repository, item_id, location_id):
        """Test retrieving stock level by item and location after purchase."""
        # Given - create stock level
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=15,
            quantity_available=15,
            created_by="purchase_user"
        )
        await stock_repository.create(stock_level)

        # When
        retrieved_stock = await stock_repository.get_by_item_location(item_id, location_id)

        # Then
        assert retrieved_stock is not None
        assert retrieved_stock.item_id == item_id
        assert retrieved_stock.location_id == location_id
        assert retrieved_stock.quantity_on_hand == 15
        assert retrieved_stock.quantity_available == 15

    @pytest.mark.asyncio
    async def test_get_by_item_location_returns_none_when_not_exists(self, stock_repository, item_id, location_id):
        """Test that get_by_item_location returns None when stock doesn't exist."""
        # When
        retrieved_stock = await stock_repository.get_by_item_location(item_id, location_id)

        # Then
        assert retrieved_stock is None

    @pytest.mark.asyncio
    async def test_update_existing_stock_from_purchase(self, stock_repository, item_id, location_id):
        """Test updating existing stock level from a purchase."""
        # Given - create initial stock
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=10,
            quantity_available=8,
            quantity_reserved=2,
            created_by="initial_user"
        )
        created_stock = await stock_repository.create(stock_level)

        # When - simulate purchase receipt (increase stock)
        created_stock.receive_stock(15, "purchase_user")
        updated_stock = await stock_repository.update(created_stock)

        # Then
        assert updated_stock.quantity_on_hand == 25  # 10 + 15
        assert updated_stock.quantity_available == 23  # 8 + 15
        assert updated_stock.quantity_reserved == 2  # Unchanged
        assert updated_stock.updated_by == "purchase_user"

    @pytest.mark.asyncio
    async def test_get_or_create_creates_when_not_exists(self, stock_repository, item_id, location_id):
        """Test get_or_create creates new stock level when none exists."""
        # When
        stock_level = await stock_repository.get_or_create(item_id, location_id)

        # Then
        assert stock_level is not None
        assert stock_level.item_id == item_id
        assert stock_level.location_id == location_id
        assert stock_level.quantity_on_hand == 0
        assert stock_level.quantity_available == 0

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing_when_exists(self, stock_repository, item_id, location_id):
        """Test get_or_create returns existing stock level when one exists."""
        # Given - create stock level
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=20,
            quantity_available=18,
            quantity_reserved=2,
        )
        created_stock = await stock_repository.create(stock_level)

        # When
        retrieved_stock = await stock_repository.get_or_create(item_id, location_id)

        # Then
        assert retrieved_stock.id == created_stock.id
        assert retrieved_stock.quantity_on_hand == 20
        assert retrieved_stock.quantity_available == 18

    @pytest.mark.asyncio
    async def test_get_total_stock_by_item_across_locations(
        self, stock_repository, item_id, location_id, another_location_id
    ):
        """Test getting total stock across multiple locations for an item."""
        # Given - stock at two locations
        stock1 = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=25,
            quantity_available=20,
            quantity_reserved=5,
        )
        stock2 = StockLevel(
            item_id=item_id,
            location_id=another_location_id,
            quantity_on_hand=15,
            quantity_available=12,
            quantity_reserved=3,
        )
        await stock_repository.create(stock1)
        await stock_repository.create(stock2)

        # When
        total_stock = await stock_repository.get_total_stock_by_item(item_id)

        # Then
        assert total_stock["total_on_hand"] == 40  # 25 + 15
        assert total_stock["total_available"] == 32  # 20 + 12
        assert total_stock["total_reserved"] == 8  # 5 + 3

    @pytest.mark.asyncio
    async def test_check_availability_after_purchase(self, stock_repository, item_id, location_id):
        """Test checking availability after purchase."""
        # Given - create stock from purchase
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=30,
            quantity_available=30,
        )
        await stock_repository.create(stock_level)

        # When - check if 25 units available
        is_available, total_available = await stock_repository.check_availability(
            item_id, 25, location_id
        )

        # Then
        assert is_available is True
        assert total_available == 30

        # When - check if 35 units available (more than stock)
        is_available, total_available = await stock_repository.check_availability(
            item_id, 35, location_id
        )

        # Then
        assert is_available is False
        assert total_available == 30

    @pytest.mark.asyncio
    async def test_check_availability_across_all_locations(
        self, stock_repository, item_id, location_id, another_location_id
    ):
        """Test checking availability across all locations when location not specified."""
        # Given - stock at multiple locations
        stock1 = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=15,
            quantity_available=15,
        )
        stock2 = StockLevel(
            item_id=item_id,
            location_id=another_location_id,
            quantity_on_hand=20,
            quantity_available=20,
        )
        await stock_repository.create(stock1)
        await stock_repository.create(stock2)

        # When - check availability without specifying location
        is_available, total_available = await stock_repository.check_availability(
            item_id, 30  # No location specified
        )

        # Then
        assert is_available is True
        assert total_available == 35  # 15 + 20

    @pytest.mark.asyncio
    async def test_list_stock_levels_by_location(self, stock_repository, item_id, location_id):
        """Test listing stock levels filtered by location."""
        # Given - stock levels at specific location
        stock1 = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=25,
            quantity_available=25,
        )
        another_item_id = uuid4()
        stock2 = StockLevel(
            item_id=another_item_id,
            location_id=location_id,
            quantity_on_hand=10,
            quantity_available=10,
        )
        await stock_repository.create(stock1)
        await stock_repository.create(stock2)

        # When
        stock_levels, total_count = await stock_repository.list(location_id=location_id)

        # Then
        assert total_count == 2
        assert len(stock_levels) == 2
        location_ids = [stock.location_id for stock in stock_levels]
        assert all(loc_id == location_id for loc_id in location_ids)

    @pytest.mark.asyncio
    async def test_list_stock_levels_by_item(self, stock_repository, item_id, location_id, another_location_id):
        """Test listing stock levels filtered by item."""
        # Given - same item at multiple locations
        stock1 = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=15,
            quantity_available=15,
        )
        stock2 = StockLevel(
            item_id=item_id,
            location_id=another_location_id,
            quantity_on_hand=20,
            quantity_available=20,
        )
        await stock_repository.create(stock1)
        await stock_repository.create(stock2)

        # When
        stock_levels, total_count = await stock_repository.list(item_id=item_id)

        # Then
        assert total_count == 2
        assert len(stock_levels) == 2
        item_ids = [stock.item_id for stock in stock_levels]
        assert all(it_id == item_id for it_id in item_ids)

    @pytest.mark.asyncio
    async def test_repository_respects_database_constraints(self, stock_repository, item_id, location_id):
        """Test that repository respects database constraints."""
        # Given - create stock level
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=10,
            quantity_available=10,
        )
        await stock_repository.create(stock_level)

        # When/Then - trying to create duplicate should fail (unique constraint on item_id + location_id)
        duplicate_stock = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=5,
            quantity_available=5,
        )
        
        with pytest.raises(Exception):  # Database constraint violation
            await stock_repository.create(duplicate_stock)

    @pytest.mark.asyncio
    async def test_stock_level_persistence_across_operations(self, stock_repository, item_id, location_id):
        """Test that stock level changes persist correctly across multiple operations."""
        # Given - create initial stock
        stock_level = StockLevel(
            item_id=item_id,
            location_id=location_id,
            quantity_on_hand=0,
            quantity_available=0,
            created_by="initial_user"
        )
        created_stock = await stock_repository.create(stock_level)

        # When - simulate multiple purchases
        # Purchase 1: 10 units
        created_stock.receive_stock(10, "purchase_1")
        await stock_repository.update(created_stock)

        # Purchase 2: 15 units
        created_stock.receive_stock(15, "purchase_2")
        await stock_repository.update(created_stock)

        # Then - retrieve and verify final state
        final_stock = await stock_repository.get_by_item_location(item_id, location_id)
        assert final_stock.quantity_on_hand == 25  # 0 + 10 + 15
        assert final_stock.quantity_available == 25
        assert final_stock.updated_by == "purchase_2"