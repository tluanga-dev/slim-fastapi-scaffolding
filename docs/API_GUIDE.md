# API Guide

## Overview

The Rental Management System API is a RESTful API built with FastAPI. It provides comprehensive endpoints for managing customers, inventory, transactions, and rental operations. This guide covers authentication, common patterns, and detailed endpoint documentation.

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.yourdomain.com/api/v1
```

## Authentication

The API uses JWT (JSON Web Token) based authentication.

### Obtaining Tokens

```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your-password"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Tokens

Include the access token in the Authorization header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Refreshing Tokens

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

## Common Patterns

### Pagination

List endpoints support pagination:
```http
GET /customers?page=1&size=20
```

Response format:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5,
  "has_next": true,
  "has_prev": false
}
```

### Filtering

Use query parameters for filtering:
```http
GET /customers?status=active&tier=gold&created_after=2024-01-01
```

### Sorting

Use the `sort` parameter:
```http
GET /customers?sort=created_at:desc,name:asc
```

### Field Selection

Use the `fields` parameter to limit returned fields:
```http
GET /customers/123?fields=id,name,email,tier
```

### Error Responses

All errors follow a consistent format:
```json
{
  "detail": "Validation error",
  "status_code": 422,
  "error_code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format",
      "code": "invalid_format"
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-20T10:00:00Z"
}
```

## Core Endpoints

### Customer Management

#### List Customers
```http
GET /customers
```

Query Parameters:
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 20)
- `type` (string): Filter by type (individual/business)
- `tier` (string): Filter by tier (bronze/silver/gold/platinum)
- `status` (string): Filter by status (active/inactive)
- `blacklist_status` (string): Filter by blacklist status
- `search` (string): Search in name, email, phone

Example:
```bash
curl -X GET "http://localhost:8000/api/v1/customers?tier=gold&status=active" \
  -H "Authorization: Bearer <token>"
```

#### Get Customer
```http
GET /customers/{customer_id}
```

Example:
```bash
curl -X GET "http://localhost:8000/api/v1/customers/123" \
  -H "Authorization: Bearer <token>"
```

#### Create Customer
```http
POST /customers
```

Request Body (Individual):
```json
{
  "type": "individual",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "country": "USA"
  },
  "tier": "silver",
  "credit_limit": 5000.00
}
```

Request Body (Business):
```json
{
  "type": "business",
  "business_name": "Acme Corp",
  "tax_id": "12-3456789",
  "email": "contact@acme.com",
  "phone": "+1234567890",
  "address": {
    "street": "456 Business Ave",
    "city": "New York",
    "state": "NY",
    "zip_code": "10002",
    "country": "USA"
  },
  "tier": "gold",
  "credit_limit": 25000.00
}
```

#### Update Customer
```http
PUT /customers/{customer_id}
```

Request Body: Same as create, all fields required

#### Partial Update Customer
```http
PATCH /customers/{customer_id}
```

Request Body: Only fields to update
```json
{
  "tier": "platinum",
  "credit_limit": 50000.00
}
```

#### Delete Customer
```http
DELETE /customers/{customer_id}
```

### Inventory Management

#### List Items
```http
GET /inventory/items
```

Query Parameters:
- `page`, `size`: Pagination
- `type` (string): Filter by type (rental/sale/both)
- `category_id` (int): Filter by category
- `brand_id` (int): Filter by brand
- `available` (bool): Show only available items
- `location_id` (int): Filter by location

#### Get Item
```http
GET /inventory/items/{item_id}
```

#### Create Item
```http
POST /inventory/items
```

Request Body:
```json
{
  "name": "Power Drill Professional",
  "description": "Heavy-duty power drill for construction",
  "sku": "PWR-DRL-001",
  "type": "rental",
  "brand_id": 1,
  "category_id": 5,
  "unit_of_measurement_id": 1,
  "purchase_price": 299.99,
  "rental_price_daily": 25.00,
  "rental_price_weekly": 150.00,
  "rental_price_monthly": 500.00,
  "sale_price": 399.99,
  "security_deposit": 100.00,
  "min_rental_days": 1,
  "max_rental_days": 30,
  "reorder_level": 5,
  "reorder_quantity": 10
}
```

#### Check Availability
```http
POST /inventory/items/{item_id}/check-availability
```

Request Body:
```json
{
  "location_id": 1,
  "start_date": "2024-01-20",
  "end_date": "2024-01-27",
  "quantity": 2
}
```

Response:
```json
{
  "available": true,
  "available_quantity": 5,
  "conflicts": []
}
```

#### List Inventory Units
```http
GET /inventory/units
```

Query Parameters:
- `item_id` (int): Filter by item
- `status` (string): Filter by status
- `condition` (string): Filter by condition
- `location_id` (int): Filter by location
- `serial_number` (string): Search by serial number

### Transaction Processing

#### Create Sale Transaction
```http
POST /transactions
```

Request Body:
```json
{
  "type": "sale",
  "customer_id": 123,
  "location_id": 1,
  "lines": [
    {
      "item_id": 456,
      "quantity": 2,
      "unit_price": 399.99,
      "discount_amount": 20.00
    }
  ],
  "payment_method": "credit_card",
  "notes": "Customer requested gift wrapping"
}
```

#### Create Rental Transaction
```http
POST /transactions
```

Request Body:
```json
{
  "type": "rental",
  "customer_id": 123,
  "location_id": 1,
  "rental_start_date": "2024-01-20",
  "rental_end_date": "2024-01-27",
  "lines": [
    {
      "item_id": 456,
      "inventory_unit_id": 789,
      "quantity": 1,
      "rental_rate_type": "daily",
      "rental_rate": 25.00,
      "security_deposit": 100.00
    }
  ],
  "payment_method": "credit_card",
  "deposit_amount": 100.00
}
```

#### Get Transaction
```http
GET /transactions/{transaction_id}
```

#### List Transactions
```http
GET /transactions
```

Query Parameters:
- `page`, `size`: Pagination
- `type` (string): Filter by type
- `status` (string): Filter by status
- `customer_id` (int): Filter by customer
- `location_id` (int): Filter by location
- `date_from` (date): Filter by date range
- `date_to` (date): Filter by date range

#### Update Transaction Status
```http
POST /transactions/{transaction_id}/status
```

Request Body:
```json
{
  "status": "confirmed",
  "notes": "Payment verified"
}
```

### Rental Operations

#### Create Rental Return
```http
POST /rentals/returns
```

Request Body:
```json
{
  "transaction_id": 123,
  "return_type": "full",
  "lines": [
    {
      "transaction_line_id": 456,
      "inventory_unit_id": 789,
      "returned_quantity": 1,
      "condition": "good",
      "notes": "Minor scratches on surface"
    }
  ]
}
```

#### Process Inspection
```http
POST /rentals/returns/{return_id}/inspection
```

Request Body:
```json
{
  "lines": [
    {
      "return_line_id": 456,
      "damage_level": "minor",
      "damage_description": "Small dent on corner",
      "repair_cost": 25.00,
      "can_repair": true
    }
  ],
  "overall_notes": "Items generally in good condition"
}
```

#### Complete Return
```http
POST /rentals/returns/{return_id}/complete
```

Request Body:
```json
{
  "late_fees": 15.00,
  "damage_fees": 25.00,
  "deposit_released": 60.00,
  "final_notes": "Late fee applied for 1 day overdue"
}
```

### Master Data

#### Brands
```http
GET /master-data/brands
POST /master-data/brands
GET /master-data/brands/{brand_id}
PUT /master-data/brands/{brand_id}
DELETE /master-data/brands/{brand_id}
```

#### Categories
```http
GET /master-data/categories
POST /master-data/categories
GET /master-data/categories/{category_id}
PUT /master-data/categories/{category_id}
DELETE /master-data/categories/{category_id}
```

Categories support hierarchical structure:
```json
{
  "name": "Power Tools",
  "description": "Electric and battery-powered tools",
  "parent_id": 5,
  "is_active": true
}
```

#### Locations
```http
GET /master-data/locations
POST /master-data/locations
GET /master-data/locations/{location_id}
PUT /master-data/locations/{location_id}
DELETE /master-data/locations/{location_id}
```

Location structure:
```json
{
  "name": "Downtown Store",
  "type": "store",
  "address": {
    "street": "789 Commerce St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10003",
    "country": "USA"
  },
  "phone": "+1234567890",
  "email": "downtown@rental.com",
  "manager_name": "Jane Smith",
  "is_active": true
}
```

## Advanced Features

### Batch Operations

#### Batch Create Inventory Units
```http
POST /inventory/units/batch
```

Request Body:
```json
{
  "item_id": 123,
  "location_id": 1,
  "units": [
    {
      "serial_number": "SN001",
      "condition": "new",
      "purchase_date": "2024-01-15",
      "purchase_price": 299.99
    },
    {
      "serial_number": "SN002",
      "condition": "new",
      "purchase_date": "2024-01-15",
      "purchase_price": 299.99
    }
  ]
}
```

### Reporting Endpoints

#### Revenue Report
```http
GET /reports/revenue
```

Query Parameters:
- `date_from` (date): Start date
- `date_to` (date): End date
- `location_id` (int): Filter by location
- `group_by` (string): day/week/month/location

#### Inventory Utilization Report
```http
GET /reports/inventory-utilization
```

Query Parameters:
- `date_from` (date): Start date
- `date_to` (date): End date
- `item_id` (int): Filter by item
- `location_id` (int): Filter by location

### Webhook Configuration

#### Register Webhook
```http
POST /webhooks
```

Request Body:
```json
{
  "url": "https://your-domain.com/webhook",
  "events": ["transaction.created", "return.completed"],
  "is_active": true,
  "secret": "your-webhook-secret"
}
```

## Best Practices

### Rate Limiting

The API implements rate limiting:
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- Premium: 10000 requests/hour

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642684800
```

### Idempotency

For critical operations, use idempotency keys:
```http
POST /transactions
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

### Versioning

The API uses URL versioning. When upgrading:
1. New version released at `/api/v2`
2. Previous version supported for 6 months
3. Deprecation warnings in headers
4. Migration guide provided

### Error Handling

Common error codes:
- `400` Bad Request - Invalid input
- `401` Unauthorized - Invalid or missing token
- `403` Forbidden - Insufficient permissions
- `404` Not Found - Resource doesn't exist
- `409` Conflict - Business rule violation
- `422` Unprocessable Entity - Validation error
- `429` Too Many Requests - Rate limit exceeded
- `500` Internal Server Error - Server error

### SDK Usage

Python SDK example:
```python
from rental_sdk import RentalClient

client = RentalClient(
    base_url="https://api.yourdomain.com",
    api_key="your-api-key"
)

# Create customer
customer = client.customers.create(
    type="individual",
    first_name="John",
    last_name="Doe",
    email="john@example.com"
)

# Create rental
rental = client.transactions.create_rental(
    customer_id=customer.id,
    item_id=123,
    start_date="2024-01-20",
    end_date="2024-01-27"
)
```

## Testing

### Sandbox Environment

Test environment available at:
```
https://sandbox.api.yourdomain.com/api/v1
```

Test credentials:
- Username: `test@rental.com`
- Password: `test123`

### Postman Collection

Import the Postman collection from:
```
https://api.yourdomain.com/docs/postman-collection.json
```

### cURL Examples

See the [examples directory](./examples/) for comprehensive cURL examples.

---

For additional support, contact api-support@rental.com or visit our [developer portal](https://developers.rental.com).