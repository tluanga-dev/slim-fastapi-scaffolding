# Rental Management System API Documentation

Welcome to the comprehensive documentation for the Rental Management System API. This documentation provides everything you need to integrate with and use our API effectively.

## Quick Start

1. **Start the API server**:
   ```bash
   cd rental-backend
   uvicorn app.main:app --reload
   ```

2. **Access interactive documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Test with example scripts**:
   ```bash
   ./docs/examples/auth_examples.sh
   ./docs/examples/customers_examples.sh
   ```

## Documentation Structure

### 📁 Core Documentation
- [`API_DOCUMENTATION.md`](./API_DOCUMENTATION.md) - Complete API reference with examples
- [`README.md`](./README.md) - This overview and quick start guide

### 📁 Interactive Testing
- [`postman/`](./postman/) - Postman collection for API testing
- [`examples/`](./examples/) - cURL example scripts for all modules

### 📁 Schema References
- OpenAPI spec available at: http://localhost:8000/openapi.json
- Interactive exploration via Swagger UI and ReDoc

## Key Features

### 🔐 Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Permission-based authorization
- Secure password hashing with bcrypt

### 👥 Customer Management
- Individual and business customer types
- Complete customer lifecycle management
- Credit scoring and blacklist management
- Address and contact management

### 🏪 Supplier Management
- Supplier relationship management
- Performance tracking and ratings
- Contract and pricing management
- Payment terms and conditions

### 📊 Master Data Management
- **Brands**: Product brand categorization
- **Categories**: Hierarchical item categorization
- **Locations**: Warehouse and location management

### 📦 Inventory Management
- Real-time stock tracking
- Multi-location inventory
- Item condition and status tracking
- Automated low-stock alerts

### 💰 Transaction Processing
- Complete transaction workflow
- Multiple payment methods
- Receipt generation
- Refund processing

### 🏠 Rental Operations
- Rental booking and scheduling
- Check-in/check-out processes
- Availability checking
- Rental status tracking

### 📈 Analytics & Reporting
- Business intelligence dashboards
- Revenue and profitability analysis
- Customer behavior analytics
- Inventory performance metrics

### ⚙️ System Management
- Configuration management
- Health monitoring
- Audit logging
- Backup and maintenance

## API Standards

### RESTful Design
- Standard HTTP methods (GET, POST, PUT, DELETE)
- Resource-based URLs
- Stateless operations
- Proper HTTP status codes

### Request/Response Format
- JSON for all requests and responses
- Consistent error handling
- Standardized pagination
- ISO 8601 date formats

### Security
- HTTPS in production
- Input validation and sanitization
- SQL injection protection
- Rate limiting and throttling

## Testing Tools

### 1. Interactive Documentation
Access comprehensive interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 2. Postman Collection
Import the complete Postman collection for testing:
```json
docs/postman/rental-management-api.postman_collection.json
```

### 3. cURL Examples
Run example scripts for different modules:
```bash
# Authentication examples
./docs/examples/auth_examples.sh

# Customer management examples  
./docs/examples/customers_examples.sh

# Master data examples
./docs/examples/master_data_examples.sh

# Inventory examples
./docs/examples/inventory_examples.sh
```

## Response Examples

### Success Response
```json
{
  "data": {
    "id": "uuid-here",
    "name": "Resource Name",
    "created_at": "2024-01-01T12:00:00Z"
  },
  "message": "Operation successful",
  "status": "success"
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "status": "error"
}
```

### Paginated Response
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

## Rate Limiting

API requests are limited to prevent abuse:
- **Authenticated users**: 1000 requests/hour
- **Anonymous users**: 100 requests/hour

Headers included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Server Error |

## Pagination

List endpoints support pagination:

### Query Parameters
```
GET /api/v1/customers?page=1&page_size=20&sort_by=created_at&sort_order=desc
```

### Parameters
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `sort_by`: Sort field (varies by endpoint)
- `sort_order`: Sort direction (asc/desc)

## Filtering and Search

### Query String Filtering
```
GET /api/v1/customers?status=ACTIVE&customer_type=INDIVIDUAL
```

### Advanced Search
```bash
curl -X POST /api/v1/customers/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "john",
    "filters": {
      "status": "ACTIVE",
      "created_after": "2024-01-01"
    },
    "sort_by": "created_at",
    "sort_order": "desc"
  }'
```

## Webhooks

Real-time notifications for key events:

### Supported Events
- `customer.created`
- `customer.updated`
- `transaction.completed`
- `rental.checked_in`
- `rental.checked_out`
- `inventory.low_stock`

### Webhook Configuration
```bash
curl -X POST /api/v1/webhooks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["customer.created", "transaction.completed"],
    "secret": "your-webhook-secret"
  }'
```

## SDKs and Libraries

### Python SDK
```bash
pip install rental-management-sdk
```

```python
from rental_management import RentalClient

client = RentalClient(
    base_url="http://localhost:8000",
    token="your-jwt-token"
)

# List customers
customers = client.customers.list(page=1, page_size=20)

# Create customer
customer = client.customers.create({
    "customer_type": "INDIVIDUAL",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
})
```

### JavaScript/TypeScript SDK
```bash
npm install @rental-management/sdk
```

```typescript
import { RentalClient } from '@rental-management/sdk';

const client = new RentalClient({
  baseUrl: 'http://localhost:8000',
  token: 'your-jwt-token'
});

// List customers
const customers = await client.customers.list({
  page: 1,
  pageSize: 20
});

// Create customer
const customer = await client.customers.create({
  customerType: 'INDIVIDUAL',
  firstName: 'John',
  lastName: 'Doe',
  email: 'john@example.com'
});
```

## Architecture Overview

### Domain-Driven Design
The API follows DDD principles with clear separation of concerns:

```
┌─────────────────┐
│   API Layer     │ ← FastAPI Routes & Schemas
├─────────────────┤
│ Application     │ ← Use Cases & Business Logic
│ Layer           │
├─────────────────┤
│ Domain Layer    │ ← Entities & Value Objects
├─────────────────┤
│ Infrastructure  │ ← Database & External Services
│ Layer           │
└─────────────────┘
```

### Database Design
- **SQLite** with async SQLAlchemy
- **Alembic** for migrations
- **Foreign key constraints** for data integrity
- **Indexes** for optimal performance

### Security Architecture
- **JWT tokens** for stateless authentication
- **Role-based access control** (RBAC)
- **Permission-based authorization**
- **Input validation** at multiple layers
- **SQL injection prevention**

## Support and Community

### Getting Help
- **Documentation**: This comprehensive guide
- **Interactive Docs**: http://localhost:8000/docs
- **GitHub Issues**: Report bugs and request features
- **Email Support**: support@example.com

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### License
This project is licensed under the MIT License. See LICENSE file for details.

## Changelog

### Version 2.0.0 (Current)
- ✨ Complete rewrite with Domain-Driven Design
- 🔐 Enhanced authentication and authorization
- 📊 Added analytics and reporting modules
- 🚀 Improved performance and scalability
- 📚 Comprehensive API documentation
- 🧪 Complete test suite

### Version 1.0.0
- 🎉 Initial release
- ✅ Basic CRUD operations
- 🔑 Simple authentication

---

**Happy coding!** 🚀

For more detailed information, see the complete [API Documentation](./API_DOCUMENTATION.md).