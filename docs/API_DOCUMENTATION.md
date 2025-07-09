# Rental Management System API Documentation

## Overview

The Rental Management System API is a comprehensive RESTful API built with FastAPI and follows Domain-Driven Design (DDD) principles. It provides complete functionality for managing rental operations, from customer onboarding to analytics and reporting.

## Base URL

```
http://localhost:8000
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting Started

1. **Register a user**: `POST /api/v1/auth/register`
2. **Login**: `POST /api/v1/auth/login`
3. **Use the returned token** in subsequent requests

## API Endpoints

### Authentication Module

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | User login | No |
| POST | `/api/v1/auth/refresh` | Refresh JWT token | Yes |
| POST | `/api/v1/auth/logout` | User logout | Yes |
| GET | `/api/v1/auth/me` | Get current user | Yes |
| PUT | `/api/v1/auth/me` | Update current user | Yes |
| POST | `/api/v1/auth/change-password` | Change password | Yes |
| GET | `/api/v1/auth/users` | List users | Admin |
| POST | `/api/v1/auth/users` | Create user | Admin |
| GET | `/api/v1/auth/users/{id}` | Get user by ID | Admin |
| PUT | `/api/v1/auth/users/{id}` | Update user | Admin |
| DELETE | `/api/v1/auth/users/{id}` | Delete user | Admin |

#### Example: User Registration

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "john_doe",
       "email": "john@example.com",
       "password": "SecurePass123!",
       "first_name": "John",
       "last_name": "Doe"
     }'
```

**Response:**
```json
{
  "id": "uuid-here",
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "status": "ACTIVE",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### Example: User Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "john_doe",
       "password": "SecurePass123!"
     }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Customer Management Module

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/customers` | List customers | Yes |
| POST | `/api/v1/customers` | Create customer | Yes |
| GET | `/api/v1/customers/{id}` | Get customer by ID | Yes |
| PUT | `/api/v1/customers/{id}` | Update customer | Yes |
| DELETE | `/api/v1/customers/{id}` | Delete customer | Yes |
| POST | `/api/v1/customers/search` | Search customers | Yes |
| GET | `/api/v1/customers/{id}/transactions` | Customer transactions | Yes |
| PUT | `/api/v1/customers/{id}/status` | Update customer status | Yes |
| PUT | `/api/v1/customers/{id}/blacklist` | Update blacklist status | Yes |

#### Example: Create Customer

```bash
curl -X POST "http://localhost:8000/api/v1/customers" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "customer_type": "INDIVIDUAL",
       "first_name": "Jane",
       "last_name": "Smith",
       "email": "jane@example.com",
       "phone_number": "+1234567890",
       "address": "123 Main St",
       "city": "New York",
       "state": "NY",
       "postal_code": "10001",
       "country": "USA"
     }'
```

### Master Data Management

#### Brands

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/brands` | List brands |
| POST | `/api/v1/brands` | Create brand |
| GET | `/api/v1/brands/{id}` | Get brand by ID |
| PUT | `/api/v1/brands/{id}` | Update brand |
| DELETE | `/api/v1/brands/{id}` | Delete brand |

#### Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/categories` | List categories |
| POST | `/api/v1/categories` | Create category |
| GET | `/api/v1/categories/{id}` | Get category by ID |
| PUT | `/api/v1/categories/{id}` | Update category |
| DELETE | `/api/v1/categories/{id}` | Delete category |
| GET | `/api/v1/categories/tree` | Get category tree |
| GET | `/api/v1/categories/{id}/children` | Get child categories |

#### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/locations` | List locations |
| POST | `/api/v1/locations` | Create location |
| GET | `/api/v1/locations/{id}` | Get location by ID |
| PUT | `/api/v1/locations/{id}` | Update location |
| DELETE | `/api/v1/locations/{id}` | Delete location |

### Inventory Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/inventory/items` | List inventory items |
| POST | `/api/v1/inventory/items` | Create inventory item |
| GET | `/api/v1/inventory/items/{id}` | Get item by ID |
| PUT | `/api/v1/inventory/items/{id}` | Update item |
| DELETE | `/api/v1/inventory/items/{id}` | Delete item |
| GET | `/api/v1/inventory/items/{id}/stock` | Get stock levels |
| POST | `/api/v1/inventory/items/{id}/adjust-stock` | Adjust stock |
| GET | `/api/v1/inventory/items/low-stock` | Get low stock items |

### Transaction Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/transactions` | List transactions |
| POST | `/api/v1/transactions` | Create transaction |
| GET | `/api/v1/transactions/{id}` | Get transaction by ID |
| PUT | `/api/v1/transactions/{id}` | Update transaction |
| POST | `/api/v1/transactions/{id}/payments` | Add payment |
| POST | `/api/v1/transactions/{id}/refund` | Process refund |
| GET | `/api/v1/transactions/{id}/receipt` | Get receipt |

### Rental Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/rentals` | List rentals |
| POST | `/api/v1/rentals` | Create rental |
| GET | `/api/v1/rentals/{id}` | Get rental by ID |
| PUT | `/api/v1/rentals/{id}` | Update rental |
| POST | `/api/v1/rentals/{id}/checkin` | Check in rental |
| POST | `/api/v1/rentals/{id}/checkout` | Check out rental |
| GET | `/api/v1/rentals/availability` | Check availability |

### Analytics & Reporting

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard` | Dashboard metrics |
| GET | `/api/v1/analytics/revenue` | Revenue analytics |
| GET | `/api/v1/analytics/customers` | Customer analytics |
| GET | `/api/v1/analytics/inventory` | Inventory analytics |
| GET | `/api/v1/analytics/rentals` | Rental analytics |
| GET | `/api/v1/analytics/reports` | Generate reports |

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "data": {
    // Response data here
  },
  "message": "Success message",
  "status": "success"
}
```

### Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      // Additional error details
    }
  },
  "status": "error"
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request data |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |

## Pagination

List endpoints support pagination with the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page |
| `sort_by` | string | varies | Sort field |
| `sort_order` | string | asc | Sort order (asc/desc) |

### Pagination Response
```json
{
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 100,
      "total_pages": 5,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

## Filtering and Search

Many endpoints support filtering and search:

### Query Parameters
```
GET /api/v1/customers?search=john&status=ACTIVE&page=1&page_size=10
```

### Search Request Body
```json
{
  "search_term": "john",
  "filters": {
    "status": "ACTIVE",
    "created_after": "2024-01-01"
  },
  "sort_by": "created_at",
  "sort_order": "desc"
}
```

## Rate Limiting

API requests are rate limited to prevent abuse:

- **Authenticated users**: 1000 requests per hour
- **Unauthenticated users**: 100 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Webhooks

The system supports webhooks for real-time notifications:

### Supported Events
- `customer.created`
- `customer.updated`
- `transaction.completed`
- `rental.checked_in`
- `rental.checked_out`
- `inventory.low_stock`

### Webhook Payload
```json
{
  "event": "customer.created",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    // Event-specific data
  }
}
```

## SDKs and Libraries

### Python SDK
```bash
pip install rental-management-sdk
```

```python
from rental_management import RentalClient

client = RentalClient(base_url="http://localhost:8000", token="your-token")
customers = client.customers.list()
```

### JavaScript SDK
```bash
npm install @rental-management/sdk
```

```javascript
import { RentalClient } from '@rental-management/sdk';

const client = new RentalClient({
  baseUrl: 'http://localhost:8000',
  token: 'your-token'
});

const customers = await client.customers.list();
```

## Testing

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Postman Collection
Download the Postman collection: [rental-management-api.postman_collection.json](./postman/rental-management-api.postman_collection.json)

### cURL Examples

See the [examples](./examples/) directory for comprehensive cURL examples for all endpoints.

## Support

For API support and questions:

- **Documentation**: http://localhost:8000/docs
- **Email**: support@example.com
- **GitHub Issues**: https://github.com/example/rental-management/issues

## Changelog

### Version 2.0.0
- Complete rewrite with Domain-Driven Design
- Enhanced authentication and authorization
- Improved performance and scalability
- Comprehensive API documentation
- Added analytics and reporting modules

### Version 1.0.0
- Initial release
- Basic CRUD operations
- Simple authentication