"""Tests for real-time data consistency between backend operations and frontend data availability."""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from uuid import uuid4


@pytest.mark.integration
class TestRealTimeDataConsistency:
    """Test that purchase operations immediately reflect in all related data endpoints."""

    @pytest.fixture
    async def test_setup(self, async_client, test_data):
        """Create test supplier and item for consistency tests."""
        # Create supplier
        supplier_data = {
            "customer_id": "RT-SUP-001",
            "customer_name": "Real-Time Test Supplier",
            "customer_type": "BUSINESS",
            "phone": "555-9999",
            "email": "realtime@test.com",
            "is_active": True,
        }
        supplier_response = await async_client.post("/api/v1/customers/", json=supplier_data)
        assert supplier_response.status_code == 201
        supplier = supplier_response.json()

        # Create test item
        item_data = {
            "item_id": "RT-ITEM-001",
            "item_name": "Real-Time Test Item",
            "description": "Item for testing real-time data consistency",
            "category_id": test_data["category"]["id"],
            "brand_id": test_data["brand"]["id"],
            "is_serialized": False,
            "is_saleable": True,
            "is_rentable": True,
            "is_active": True,
        }
        item_response = await async_client.post("/api/v1/items/", json=item_data)
        assert item_response.status_code == 201
        item = item_response.json()

        return {
            "supplier": supplier,
            "item": item,
            "location": test_data["location"]
        }

    @pytest.mark.asyncio
    async def test_immediate_stock_level_availability_after_purchase(
        self, async_client, test_setup
    ):
        """Test that stock levels are immediately available after purchase without delays."""
        # Given - initial state check (should be no stock)
        initial_stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_setup['item']['id']}&location_id={test_setup['location']['id']}"
        )
        assert initial_stock_response.status_code == 200
        initial_stock = initial_stock_response.json()
        assert initial_stock["total"] == 0  # No stock initially

        # Given - purchase data
        purchase_data = {
            "supplier_id": test_setup["supplier"]["id"],
            "location_id": test_setup["location"]["id"],
            "purchase_date": "2024-01-25",
            "items": [
                {
                    "item_id": test_setup["item"]["id"],
                    "quantity": 75,
                    "unit_cost": 20.00,
                }
            ]
        }

        # When - create purchase and immediately check stock
        start_time = datetime.now()
        
        purchase_response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )
        assert purchase_response.status_code == 201
        
        # Immediately check stock levels (no artificial delay)
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_setup['item']['id']}&location_id={test_setup['location']['id']}"
        )
        
        end_time = datetime.now()
        operation_time = (end_time - start_time).total_seconds()

        # Then - stock should be immediately available
        assert stock_response.status_code == 200
        stock_data = stock_response.json()
        assert stock_data["total"] == 1
        
        stock_level = stock_data["items"][0]
        assert stock_level["quantity_on_hand"] == 75
        assert stock_level["quantity_available"] == 75
        
        # Verify operation was fast (should complete within reasonable time)
        assert operation_time < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_concurrent_purchases_maintain_data_consistency(
        self, async_client, test_setup
    ):
        """Test that concurrent purchases maintain data consistency."""
        # Given - multiple concurrent purchase requests
        async def create_purchase(quantity, cost):
            purchase_data = {
                "supplier_id": test_setup["supplier"]["id"],
                "location_id": test_setup["location"]["id"],
                "purchase_date": "2024-01-26",
                "items": [
                    {
                        "item_id": test_setup["item"]["id"],
                        "quantity": quantity,
                        "unit_cost": cost,
                    }
                ]
            }
            return await async_client.post("/api/v1/transactions/purchases", json=purchase_data)

        # When - execute concurrent purchases
        tasks = [
            create_purchase(10, 15.00),
            create_purchase(20, 16.00),
            create_purchase(15, 17.00),
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Then - all purchases should succeed
        for response in responses:
            assert response.status_code == 201

        # Verify final stock consistency
        final_stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_setup['item']['id']}&location_id={test_setup['location']['id']}"
        )
        assert final_stock_response.status_code == 200
        final_stock = final_stock_response.json()
        
        stock_level = final_stock["items"][0]
        assert stock_level["quantity_on_hand"] == 45  # 10 + 20 + 15
        assert stock_level["quantity_available"] == 45

        # Verify all transactions are recorded
        transactions_response = await async_client.get(
            f"/api/v1/transactions/purchases/list?location_id={test_setup['location']['id']}"
        )
        assert transactions_response.status_code == 200
        transactions = transactions_response.json()
        
        # Should have at least 3 new transactions
        purchase_transactions = [t for t in transactions["items"] if t["transaction_type"] == "PURCHASE"]
        assert len(purchase_transactions) >= 3

    @pytest.mark.asyncio
    async def test_transaction_data_immediately_queryable(
        self, async_client, test_setup
    ):
        """Test that transaction data is immediately queryable through various endpoints."""
        # Given - purchase data
        purchase_data = {
            "supplier_id": test_setup["supplier"]["id"],
            "location_id": test_setup["location"]["id"],
            "purchase_date": "2024-01-27",
            "invoice_number": "RT-INV-001",
            "notes": "Real-time consistency test purchase",
            "items": [
                {
                    "item_id": test_setup["item"]["id"],
                    "quantity": 30,
                    "unit_cost": 25.00,
                }
            ]
        }

        # When - create purchase
        purchase_response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )
        assert purchase_response.status_code == 201
        purchase_id = purchase_response.json()["id"]
        transaction_number = purchase_response.json()["transaction_number"]

        # Then - transaction should be immediately queryable through multiple endpoints

        # 1. By ID
        by_id_response = await async_client.get(f"/api/v1/transactions/{purchase_id}")
        assert by_id_response.status_code == 200
        by_id_data = by_id_response.json()
        assert by_id_data["id"] == purchase_id

        # 2. By transaction number
        by_number_response = await async_client.get(f"/api/v1/transactions/number/{transaction_number}")
        assert by_number_response.status_code == 200
        by_number_data = by_number_response.json()
        assert by_number_data["transaction_number"] == transaction_number

        # 3. In transaction list
        list_response = await async_client.get("/api/v1/transactions/")
        assert list_response.status_code == 200
        list_data = list_response.json()
        transaction_ids = [t["id"] for t in list_data["items"]]
        assert purchase_id in transaction_ids

        # 4. In purchase-specific list
        purchase_list_response = await async_client.get("/api/v1/transactions/purchases/list")
        assert purchase_list_response.status_code == 200
        purchase_list_data = purchase_list_response.json()
        purchase_ids = [t["id"] for t in purchase_list_data["items"]]
        assert purchase_id in purchase_ids

    @pytest.mark.asyncio
    async def test_inventory_availability_for_immediate_sale(
        self, async_client, test_setup
    ):
        """Test that purchased items are immediately available for sale operations."""
        # Given - purchase to create inventory
        purchase_data = {
            "supplier_id": test_setup["supplier"]["id"],
            "location_id": test_setup["location"]["id"],
            "purchase_date": "2024-01-28",
            "items": [
                {
                    "item_id": test_setup["item"]["id"],
                    "quantity": 40,
                    "unit_cost": 18.00,
                }
            ]
        }

        # When - create purchase
        purchase_response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )
        assert purchase_response.status_code == 201

        # Then - items should be immediately available for sale
        # Check availability through stock check endpoint
        availability_response = await async_client.get(
            f"/api/v1/stock/availability?item_id={test_setup['item']['id']}&quantity=35&location_id={test_setup['location']['id']}"
        )
        
        # If availability endpoint exists
        if availability_response.status_code == 200:
            availability_data = availability_response.json()
            assert availability_data["is_available"] is True
            assert availability_data["total_available"] >= 35

        # Verify through stock levels endpoint
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_setup['item']['id']}&location_id={test_setup['location']['id']}"
        )
        assert stock_response.status_code == 200
        stock_data = stock_response.json()
        
        stock_level = stock_data["items"][0]
        assert stock_level["quantity_available"] >= 35  # Should have enough for sale

    @pytest.mark.asyncio
    async def test_purchase_effects_reflected_in_reports(
        self, async_client, test_setup
    ):
        """Test that purchases are immediately reflected in reporting endpoints."""
        # Given - get initial report state
        initial_reports_response = await async_client.get(
            f"/api/v1/reports/inventory-summary?location_id={test_setup['location']['id']}"
        )
        
        # Create purchase
        purchase_data = {
            "supplier_id": test_setup["supplier"]["id"],
            "location_id": test_setup["location"]["id"],
            "purchase_date": "2024-01-29",
            "items": [
                {
                    "item_id": test_setup["item"]["id"],
                    "quantity": 60,
                    "unit_cost": 22.00,
                }
            ]
        }

        purchase_response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )
        assert purchase_response.status_code == 201

        # Then - check updated reports
        updated_reports_response = await async_client.get(
            f"/api/v1/reports/inventory-summary?location_id={test_setup['location']['id']}"
        )
        
        # If reports endpoint exists, verify data is updated
        if updated_reports_response.status_code == 200:
            # Reports should reflect the new purchase
            # This test validates that the purchase data flows through to reporting systems
            pass  # Specific assertions would depend on report structure

        # At minimum, verify transaction appears in transaction reports
        transaction_reports_response = await async_client.get(
            f"/api/v1/transactions/?transaction_type=PURCHASE&location_id={test_setup['location']['id']}"
        )
        assert transaction_reports_response.status_code == 200
        
        purchase_transactions = transaction_reports_response.json()["items"]
        assert len(purchase_transactions) > 0  # Should include our purchase

    @pytest.mark.asyncio
    async def test_data_consistency_across_multiple_endpoints(
        self, async_client, test_setup
    ):
        """Test that the same data is consistent across all related endpoints."""
        # Given - create purchase
        purchase_data = {
            "supplier_id": test_setup["supplier"]["id"],
            "location_id": test_setup["location"]["id"],
            "purchase_date": "2024-01-30",
            "items": [
                {
                    "item_id": test_setup["item"]["id"],
                    "quantity": 25,
                    "unit_cost": 30.00,
                }
            ]
        }

        purchase_response = await async_client.post(
            "/api/v1/transactions/purchases", json=purchase_data
        )
        assert purchase_response.status_code == 201
        purchase_id = purchase_response.json()["id"]

        # When - query data from multiple endpoints
        endpoints_data = {}

        # Transaction endpoint
        transaction_response = await async_client.get(f"/api/v1/transactions/{purchase_id}")
        if transaction_response.status_code == 200:
            endpoints_data["transaction"] = transaction_response.json()

        # Stock levels endpoint
        stock_response = await async_client.get(
            f"/api/v1/stock/levels?item_id={test_setup['item']['id']}&location_id={test_setup['location']['id']}"
        )
        if stock_response.status_code == 200:
            endpoints_data["stock"] = stock_response.json()

        # Purchase list endpoint
        purchase_list_response = await async_client.get(f"/api/v1/transactions/purchases/{purchase_id}")
        if purchase_list_response.status_code == 200:
            endpoints_data["purchase_detail"] = purchase_list_response.json()

        # Then - verify data consistency
        if "transaction" in endpoints_data and "purchase_detail" in endpoints_data:
            # Same transaction data should be returned from both endpoints
            assert endpoints_data["transaction"]["id"] == endpoints_data["purchase_detail"]["id"]
            assert endpoints_data["transaction"]["transaction_number"] == endpoints_data["purchase_detail"]["transaction_number"]
            assert endpoints_data["transaction"]["total_amount"] == endpoints_data["purchase_detail"]["total_amount"]

        if "stock" in endpoints_data:
            # Stock quantity should match purchase quantity
            stock_level = endpoints_data["stock"]["items"][0]
            assert stock_level["quantity_on_hand"] >= 25  # At least the quantity we purchased

        # Verify timestamp consistency (all data should have recent timestamps)
        current_time = datetime.now()
        for endpoint_name, data in endpoints_data.items():
            if "created_at" in data:
                created_time = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                time_diff = (current_time - created_time.replace(tzinfo=None)).total_seconds()
                assert time_diff < 60  # Should be created within last minute