"""Comprehensive API integration tests for complete purchase workflow."""

import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4

from src.domain.value_objects.customer_type import CustomerType
from src.domain.value_objects.item_type import InventoryStatus, ConditionGrade


@pytest.mark.integration
class TestCompletePurchaseWorkflow:
    """Test complete purchase workflow from API to database with inventory and stock effects."""

    @pytest.fixture
    async def test_supplier(self, async_client, test_data):
        """Create a test supplier (business customer)."""
        supplier_data = {
            "customer_id": "SUP001",
            "customer_name": "Test Supplier Corp",
            "customer_type": "BUSINESS",
            "phone": "555-1234",
            "email": "supplier@test.com",
            "is_active": True,
        }
        
        response = await async_client.post("/api/v1/customers/", json=supplier_data)
        assert response.status_code == 201
        return response.json()

    @pytest.fixture
    async def test_item_serialized(self, async_client, test_data):
        """Create a test serialized item."""
        item_data = {
            "item_id": "ITEM-SER-001",
            "item_name": "Test Serialized Item",
            "description": "A test item that requires serial numbers",
            "category_id": test_data["category"]["id"],
            "brand_id": test_data["brand"]["id"],
            "is_serialized": True,
            "is_saleable": True,
            "is_rentable": False,
            "is_active": True,
        }
        
        response = await async_client.post("/api/v1/items/", json=item_data)
        assert response.status_code == 201
        return response.json()

    @pytest.fixture
    async def test_item_non_serialized(self, async_client, test_data):
        """Create a test non-serialized item."""
        item_data = {
            "item_id": "ITEM-BULK-001",
            "item_name": "Test Bulk Item",
            "description": "A bulk item without serial numbers",
            "category_id": test_data["category"]["id"],
            "brand_id": test_data["brand"]["id"],
            "is_serialized": False,
            "is_saleable": True,
            "is_rentable": True,
            "is_active": True,
        }
        
        response = await async_client.post("/api/v1/items/", json=item_data)
        assert response.status_code == 201
        return response.json()

    @pytest.mark.asyncio
    async def test_complete_purchase_workflow_serialized_items(
        self, async_client, test_supplier, test_item_serialized, test_data
    ):
        """Test complete purchase workflow with serialized items affecting inventory and stock."""
        # Given - purchase data with serialized items
        purchase_data = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-15",
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-01-15",
            "notes": "Test purchase for integration testing",
            "tax_rate": 8.5,
            "discount_amount": 50.00,
            "items": [
                {
                    "item_id": test_item_serialized["id"],
                    "quantity": 2,
                    "unit_cost": 299.99,
                    "serial_numbers": ["SN-TEST-001", "SN-TEST-002"],
                    "condition_notes": "Excellent condition - factory sealed",
                    "notes": "First batch of serialized items",
                }
            ]
        }

        # When - create purchase
        response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )

        # Then - verify purchase creation
        assert response.status_code == 201
        purchase_response = response.json()
        
        assert purchase_response["transaction_type"] == "PURCHASE"
        assert purchase_response["status"] == "COMPLETED"
        assert purchase_response["payment_status"] == "PAID"
        assert purchase_response["customer_id"] == test_supplier["id"]
        assert purchase_response["location_id"] == test_data["location"]["id"]
        
        # Verify totals
        assert Decimal(str(purchase_response["subtotal"])) == Decimal("599.98")  # 2 * 299.99
        assert Decimal(str(purchase_response["discount_amount"])) == Decimal("50.00")
        
        purchase_id = purchase_response["id"]

        # Verify inventory units were created
        inventory_response = await async_client.get(f"/api/v1/inventory/units?item_id={test_item_serialized['id']}")
        assert inventory_response.status_code == 200
        inventory_data = inventory_response.json()
        
        assert inventory_data["total"] == 2  # Two units created
        units = inventory_data["items"]
        
        # Verify both serial numbers are present
        serial_numbers = [unit["serial_number"] for unit in units]
        assert "SN-TEST-001" in serial_numbers
        assert "SN-TEST-002" in serial_numbers
        
        # Verify inventory unit properties
        for unit in units:
            assert unit["item_id"] == test_item_serialized["id"]
            assert unit["location_id"] == test_data["location"]["id"]
            assert unit["current_status"] == InventoryStatus.AVAILABLE_SALE.value
            assert unit["condition_grade"] == ConditionGrade.A.value
            assert Decimal(str(unit["purchase_cost"])) == Decimal("299.99")
            assert unit["purchase_date"] == "2024-01-15"

        # Verify stock levels were updated
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_item_serialized['id']}&location_id={test_data['location']['id']}"
        )
        assert stock_response.status_code == 200
        stock_data = stock_response.json()
        
        assert stock_data["total"] == 1  # One stock level record
        stock_level = stock_data["items"][0]
        
        assert stock_level["item_id"] == test_item_serialized["id"]
        assert stock_level["location_id"] == test_data["location"]["id"]
        assert stock_level["quantity_on_hand"] == 2
        assert stock_level["quantity_available"] == 2
        assert stock_level["quantity_reserved"] == 0

    @pytest.mark.asyncio
    async def test_complete_purchase_workflow_non_serialized_items(
        self, async_client, test_supplier, test_item_non_serialized, test_data
    ):
        """Test complete purchase workflow with non-serialized items affecting stock only."""
        # Given - purchase data with non-serialized items
        purchase_data = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-16",
            "notes": "Bulk purchase test",
            "items": [
                {
                    "item_id": test_item_non_serialized["id"],
                    "quantity": 50,
                    "unit_cost": 12.50,
                    "notes": "Bulk non-serialized items",
                }
            ]
        }

        # When - create purchase
        response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )

        # Then - verify purchase creation
        assert response.status_code == 201
        purchase_response = response.json()
        
        assert purchase_response["transaction_type"] == "PURCHASE"
        assert purchase_response["status"] == "COMPLETED"
        assert Decimal(str(purchase_response["subtotal"])) == Decimal("625.00")  # 50 * 12.50

        # Verify NO inventory units were created for non-serialized items
        inventory_response = await async_client.get(f"/api/v1/inventory/units?item_id={test_item_non_serialized['id']}")
        assert inventory_response.status_code == 200
        inventory_data = inventory_response.json()
        assert inventory_data["total"] == 0  # No individual units for non-serialized

        # Verify stock levels were updated
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_item_non_serialized['id']}&location_id={test_data['location']['id']}"
        )
        assert stock_response.status_code == 200
        stock_data = stock_response.json()
        
        assert stock_data["total"] == 1
        stock_level = stock_data["items"][0]
        
        assert stock_level["quantity_on_hand"] == 50
        assert stock_level["quantity_available"] == 50
        assert stock_level["quantity_reserved"] == 0

    @pytest.mark.asyncio
    async def test_multiple_purchases_accumulate_stock_correctly(
        self, async_client, test_supplier, test_item_non_serialized, test_data
    ):
        """Test that multiple purchases to same item/location accumulate stock correctly."""
        # Given - first purchase
        purchase_data_1 = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-17",
            "items": [
                {
                    "item_id": test_item_non_serialized["id"],
                    "quantity": 20,
                    "unit_cost": 10.00,
                }
            ]
        }

        # When - create first purchase
        response1 = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data_1
        )
        assert response1.status_code == 201

        # Verify initial stock
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_item_non_serialized['id']}&location_id={test_data['location']['id']}"
        )
        assert stock_response.status_code == 200
        stock_data = stock_response.json()
        initial_stock = stock_data["items"][0]
        assert initial_stock["quantity_on_hand"] == 20

        # Given - second purchase
        purchase_data_2 = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-18",
            "items": [
                {
                    "item_id": test_item_non_serialized["id"],
                    "quantity": 30,
                    "unit_cost": 11.00,
                }
            ]
        }

        # When - create second purchase
        response2 = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data_2
        )
        assert response2.status_code == 201

        # Then - verify accumulated stock
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_item_non_serialized['id']}&location_id={test_data['location']['id']}"
        )
        assert stock_response.status_code == 200
        stock_data = stock_response.json()
        
        final_stock = stock_data["items"][0]
        assert final_stock["quantity_on_hand"] == 50  # 20 + 30
        assert final_stock["quantity_available"] == 50

    @pytest.mark.asyncio
    async def test_purchase_validation_errors(
        self, async_client, test_supplier, test_data
    ):
        """Test that purchase validation errors are properly handled."""
        # Test invalid supplier
        invalid_supplier_data = {
            "supplier_id": str(uuid4()),  # Non-existent supplier
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(uuid4()),
                    "quantity": 1,
                    "unit_cost": 100.00,
                }
            ]
        }

        response = await async_client.post(
            "/api/v1/transactions/purchases", json=invalid_supplier_data
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

        # Test invalid item
        invalid_item_data = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-15",
            "items": [
                {
                    "item_id": str(uuid4()),  # Non-existent item
                    "quantity": 1,
                    "unit_cost": 100.00,
                }
            ]
        }

        response = await async_client.post(
            "/api/v1/transactions/purchases", json=invalid_item_data
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_duplicate_serial_number_rejection(
        self, async_client, test_supplier, test_item_serialized, test_data
    ):
        """Test that duplicate serial numbers are rejected."""
        # Given - first purchase with serial numbers
        purchase_data_1 = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-19",
            "items": [
                {
                    "item_id": test_item_serialized["id"],
                    "quantity": 1,
                    "unit_cost": 299.99,
                    "serial_numbers": ["DUPLICATE-SN-001"],
                }
            ]
        }

        # When - create first purchase
        response1 = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data_1
        )
        assert response1.status_code == 201

        # Given - second purchase with same serial number
        purchase_data_2 = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-20",
            "items": [
                {
                    "item_id": test_item_serialized["id"],
                    "quantity": 1,
                    "unit_cost": 299.99,
                    "serial_numbers": ["DUPLICATE-SN-001"],  # Same serial number
                }
            ]
        }

        # When/Then - second purchase should fail
        response2 = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data_2
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_purchase_with_mixed_item_types(
        self, async_client, test_supplier, test_item_serialized, test_item_non_serialized, test_data
    ):
        """Test purchase with both serialized and non-serialized items."""
        # Given - mixed purchase data
        purchase_data = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-21",
            "items": [
                {
                    "item_id": test_item_serialized["id"],
                    "quantity": 1,
                    "unit_cost": 299.99,
                    "serial_numbers": ["MIXED-SN-001"],
                },
                {
                    "item_id": test_item_non_serialized["id"],
                    "quantity": 25,
                    "unit_cost": 15.00,
                }
            ]
        }

        # When - create purchase
        response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )

        # Then - verify successful creation
        assert response.status_code == 201
        purchase_response = response.json()
        
        # Should have 2 product lines
        product_lines = [line for line in purchase_response["lines"] if line["line_type"] == "PRODUCT"]
        assert len(product_lines) == 2

        # Verify inventory unit was created for serialized item only
        inventory_response = await async_client.get(
            f"/api/v1/inventory/units?item_id={test_item_serialized['id']}"
        )
        assert inventory_response.status_code == 200
        serialized_inventory = inventory_response.json()
        assert serialized_inventory["total"] >= 1  # At least one from this test

        # Verify no inventory units for non-serialized item
        inventory_response = await async_client.get(
            f"/api/v1/inventory/units?item_id={test_item_non_serialized['id']}"
        )
        assert inventory_response.status_code == 200
        bulk_inventory = inventory_response.json()
        assert bulk_inventory["total"] == 0

        # Verify stock levels updated for both items
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?location_id={test_data['location']['id']}"
        )
        assert stock_response.status_code == 200
        stock_data = stock_response.json()
        
        # Should have stock records for both items
        item_ids = [stock["item_id"] for stock in stock_data["items"]]
        assert test_item_serialized["id"] in item_ids
        assert test_item_non_serialized["id"] in item_ids

    @pytest.mark.asyncio
    async def test_real_time_data_consistency(
        self, async_client, test_supplier, test_item_non_serialized, test_data
    ):
        """Test that data is immediately available after purchase (real-time consistency)."""
        # Given - purchase data
        purchase_data = {
            "supplier_id": test_supplier["id"],
            "location_id": test_data["location"]["id"],
            "purchase_date": "2024-01-22",
            "items": [
                {
                    "item_id": test_item_non_serialized["id"],
                    "quantity": 100,
                    "unit_cost": 5.00,
                }
            ]
        }

        # When - create purchase
        purchase_response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )
        assert purchase_response.status_code == 201
        purchase_id = purchase_response.json()["id"]

        # Then - data should be immediately available
        
        # 1. Transaction should be retrievable
        transaction_response = await async_client.get(f"/api/v1/transactions/{purchase_id}")
        assert transaction_response.status_code == 200
        
        # 2. Stock levels should be immediately updated
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_item_non_serialized['id']}&location_id={test_data['location']['id']}"
        )
        assert stock_response.status_code == 200
        stock_data = stock_response.json()
        assert len(stock_data["items"]) > 0
        stock_level = stock_data["items"][0]
        assert stock_level["quantity_on_hand"] >= 100  # At least 100 from this purchase

        # 3. Purchase should appear in transaction list
        transactions_response = await async_client.get(
            f"/api/v1/transactions/purchases/list?location_id={test_data['location']['id']}"
        )
        assert transactions_response.status_code == 200
        transactions_data = transactions_response.json()
        
        purchase_ids = [t["id"] for t in transactions_data["items"]]
        assert purchase_id in purchase_ids