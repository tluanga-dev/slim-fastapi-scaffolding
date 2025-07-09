# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the Rental Management System backend.

## Project Overview

This is a **production-ready Rental Management System** built with FastAPI, implementing Domain-Driven Design (DDD) principles. The system manages multi-location rental and sales operations, supporting complex workflows for inventory tracking, customer management, transaction processing, and rental returns with inspection capabilities.

### Key Features
- Multi-location inventory management
- Dual-mode operations (rental and sales)
- Customer lifecycle management with tier system
- Supplier relationship management
- Comprehensive rental workflow with returns and inspections
- Real-time inventory tracking
- Financial management with deposits and fees
- Performance monitoring and analytics-ready architecture
- Authentication and authorization with JWT
- Role-Based Access Control (RBAC)

## Essential Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Database Management
```bash
# Initialize database (first time setup)
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations to database
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration history
alembic history

# Initialize database for development (alternative method)
python -c "from app.startup import init_db; import asyncio; asyncio.run(init_db())"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m e2e              # End-to-end tests
pytest -m auth             # Authentication tests
pytest -m api              # API tests
pytest -m performance      # Performance tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/modules/customers/test_service.py

# Run single test
pytest app/tests/modules/items/test_routes.py::test_create_item

# Run tests in parallel
pytest -n auto

# Run tests with verbose output
pytest -v
```

### Development Server
```bash
# Start development server with auto-reload
uvicorn app.main:app --reload

# Start with custom port and host
uvicorn app.main:app --reload --port 8001 --host 0.0.0.0

# Start with environment file
uvicorn app.main:app --reload --env-file .env
```

### Code Quality
```bash
# Format code with black
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type checking
mypy app/

# Security scanning
bandit -r app/

# Run all quality checks
black app/ && isort app/ && flake8 app/ && mypy app/
```

### Performance Monitoring
```bash
# Start with Prometheus metrics
uvicorn app.main:app --reload

# Access metrics endpoint
curl http://localhost:8000/metrics

# Run performance tests
pytest -m performance
```

## Architecture Overview

### Domain-Driven Design Implementation
The system follows DDD principles with clear separation of concerns:

```
API Layer (Routes)
    ↓
Application Layer (Services)
    ↓
Domain Layer (Models & Business Logic)
    ↓
Infrastructure Layer (Repository & Database)
```

### Layered Architecture

#### 1. **API Layer** (`routes.py`)
- FastAPI endpoints
- Request/response handling
- Input validation via Pydantic schemas
- OpenAPI documentation
- Authentication/authorization enforcement

#### 2. **Application Layer** (`service.py`)
- Business logic orchestration
- Transaction management
- Cross-domain coordination
- Business rule enforcement
- Complex workflow implementation

#### 3. **Domain Layer** (`models.py`)
- Domain entities
- Business invariants
- Value objects
- Domain events (future)
- Entity relationships

#### 4. **Infrastructure Layer** (`repository.py`)
- Data persistence
- Query optimization
- Caching strategies
- External service integration
- Database transaction management

### Module Structure Pattern
Each domain module follows this consistent structure:
```
app/modules/{domain}/
├── __init__.py          # Module initialization
├── models.py            # SQLAlchemy domain models
├── schemas.py           # Pydantic schemas (request/response)
├── repository.py        # Data access layer
├── service.py           # Business logic layer
├── routes.py            # API endpoints
├── dependencies.py      # Module-specific dependencies
├── validators.py        # Custom validation logic (optional)
└── utils.py            # Module utilities (optional)
```

### File Structure Overview
```
project-root/
├── app/
│   ├── core/
│   │   ├── config.py              # Pydantic settings with .env support
│   │   ├── errors.py              # Centralized exception handling
│   │   ├── security.py            # JWT and password handling
│   │   ├── cache.py               # Redis caching implementation
│   │   ├── database_optimization.py # Query optimization
│   │   ├── logging_config.py      # Structured logging
│   │   └── middleware.py          # Custom middleware
│   ├── modules/
│   │   ├── auth/                  # Authentication & authorization
│   │   ├── customers/             # Customer management
│   │   ├── suppliers/             # Supplier management
│   │   ├── inventory/             # Inventory tracking
│   │   ├── transactions/          # Transaction processing
│   │   ├── rentals/               # Rental operations
│   │   ├── master_data/           # Brands, categories, locations
│   │   ├── analytics/             # Business intelligence
│   │   └── system/                # System administration
│   ├── shared/
│   │   ├── dependencies.py        # Dependency injection
│   │   ├── pagination.py          # Pagination utilities
│   │   ├── filters.py             # Query filters
│   │   └── validators/            # Shared validators
│   ├── db/
│   │   ├── session.py             # Async database sessions
│   │   └── base.py                # SQLAlchemy declarative base
│   ├── tests/
│   │   ├── unit/                  # Unit tests
│   │   ├── integration/           # Integration tests
│   │   ├── e2e/                   # End-to-end tests
│   │   └── conftest.py            # Test configuration
│   ├── main.py                    # FastAPI application entry
│   └── startup.py                 # Database initialization
├── alembic/                       # Database migrations
├── docs/                          # API documentation
├── scripts/                       # Utility scripts
├── monitoring/                    # Grafana dashboards
├── deployment/                    # Kubernetes configs
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── alembic.ini                   # Alembic configuration
├── pytest.ini                    # Pytest configuration
├── Dockerfile                    # Container definition
└── docker-compose.yml            # Development stack
```

## Business Domain Model

### Core Domains

#### 1. **Customer Management**
- **Entity**: Customer
- **Key Features**:
  - Customer types (Individual/Business)
  - Tier system (Bronze/Silver/Gold/Platinum)
  - Blacklist management (Clear/Warning/Blacklisted)
  - Credit limit tracking
  - Lifetime value calculation
  - Contact information management
  - Tax ID support
- **Business Rules**:
  - Blacklisted customers cannot create new transactions
  - Business customers require business name
  - Individual customers require first and last names
  - Credit limits enforce maximum exposure

#### 2. **Inventory Management**
- **Entities**: Item, InventoryUnit, StockLevel
- **Item Features**:
  - Dual mode support (rental-only, sale-only, or both)
  - Multiple pricing structures (purchase, rental rates, sale price)
  - Security deposit requirements
  - Minimum/maximum rental periods
  - Brand and category classification
  - Reorder level management
- **InventoryUnit Features**:
  - Individual unit tracking with serial numbers
  - Status tracking (Available/Rented/Sold/Maintenance/Damaged/Retired)
  - Condition monitoring (New/Excellent/Good/Fair/Poor/Damaged)
  - Warranty and maintenance scheduling
- **StockLevel Features**:
  - Location-based quantity tracking
  - Available vs reserved quantities
  - Reorder point alerts
  - Multi-location support

#### 3. **Transaction Processing**
- **Entities**: TransactionHeader, TransactionLine
- **Transaction Types**:
  - Sale - Direct product sales
  - Rental - Rental transactions with dates
  - Return - Rental returns
  - Exchange - Product exchanges
  - Refund - Money refunds
  - Adjustment - Inventory adjustments
  - Purchase - Supplier purchases
- **Status Flow**:
  ```
  Draft → Pending → Confirmed → In Progress → Completed
  (Cancelled can occur from any state except Completed)
  ```
- **Features**:
  - Multiple payment method support
  - Partial payment handling
  - Discount application
  - Tax calculation
  - Deposit management
  - Multi-line item support

#### 4. **Rental Operations**
- **Entities**: RentalReturn, RentalReturnLine, InspectionReport
- **Return Process**:
  - Full or partial returns
  - Item inspection workflow
  - Damage assessment (None/Minor/Moderate/Major/Total Loss)
  - Fee calculation (late fees, damage fees)
  - Deposit release management
- **Inspection Features**:
  - Detailed damage documentation
  - Repair cost estimation
  - Photo attachment support (future)
  - Dispute resolution workflow

#### 5. **Supplier Management**
- **Entity**: Supplier
- **Supplier Types**:
  - Manufacturer
  - Distributor
  - Wholesaler
  - Retailer
  - Service Provider
  - Direct Supplier
- **Features**:
  - Tier classification (Premium/Standard/Basic/Trial)
  - Performance tracking (quality rating, delivery rating)
  - Payment terms (Immediate/NET15/30/45/60/90/COD)
  - Contract management
  - Insurance tracking
  - Credit limit management
- **Status Management**:
  - Active/Inactive/Pending/Approved/Suspended/Blacklisted

#### 6. **Master Data**
- **Brand Management**: Product brand catalog
- **Category Management**: 
  - Hierarchical categorization
  - Parent-child relationships
  - Path tracking (e.g., "Electronics/Computers/Laptops")
- **Location Management**:
  - Store/Warehouse/Service Center types
  - Full address and contact information
  - Manager assignment
- **Units of Measurement**: Standard unit catalog

### Key Business Workflows

#### Rental Transaction Flow
```mermaid
graph LR
    A[Customer Selection] --> B[Blacklist Check]
    B -->|Clear| C[Item Selection]
    B -->|Blacklisted| X[Transaction Denied]
    C --> D[Availability Check]
    D -->|Available| E[Create Transaction]
    D -->|Unavailable| Y[Show Alternatives]
    E --> F[Calculate Fees & Deposit]
    F --> G[Process Payment]
    G --> H[Update Inventory Status]
    H --> I[Issue Receipt]
```

#### Rental Return Flow
```mermaid
graph LR
    A[Return Initiation] --> B[Verify Transaction]
    B --> C[Item Reception]
    C --> D[Inspection Process]
    D --> E[Damage Assessment]
    E --> F[Calculate Fees]
    F --> G[Deposit Release]
    G --> H[Update Inventory]
    H --> I[Complete Return]
```

#### Inventory Replenishment Flow
```mermaid
graph LR
    A[Monitor Stock Levels] --> B[Detect Low Stock]
    B --> C[Check Reorder Point]
    C -->|Below Threshold| D[Generate PO]
    C -->|Adequate| A
    D --> E[Supplier Selection]
    E --> F[Order Placement]
    F --> G[Receive Goods]
    G --> H[Update Inventory]
```

## Database Architecture

### Database Technology
- **Type**: SQLite with async support (development), PostgreSQL (production-ready)
- **ORM**: SQLAlchemy with async sessions
- **Migrations**: Alembic
- **Driver**: aiosqlite (SQLite), asyncpg (PostgreSQL)

### Key Design Patterns

#### 1. **Repository Pattern**
```python
class CustomerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, customer_id: int) -> Customer:
        result = await self.session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, customer_data: dict) -> Customer:
        customer = Customer(**customer_data)
        self.session.add(customer)
        await self.session.commit()
        return customer
```

#### 2. **Unit of Work Pattern**
```python
async with get_session() as session:
    # All operations in transaction
    customer_repo = CustomerRepository(session)
    customer = await customer_repo.create(data)
    # Auto-commit on context exit
```

#### 3. **Specification Pattern**
```python
class ActiveRentalSpec:
    def apply(self, query):
        return query.filter(
            TransactionHeader.type == "rental",
            TransactionHeader.status == "in_progress"
        )
```

### Model Registration for Migrations
When adding new models, they must be imported in `alembic/env.py`:
```python
from app.db.base import Base
# Import all models for Alembic to detect
from app.modules.customers.models import Customer
from app.modules.suppliers.models import Supplier
from app.modules.inventory.models import Item, InventoryUnit, StockLevel
from app.modules.transactions.models import TransactionHeader, TransactionLine
from app.modules.rentals.models import RentalReturn, RentalReturnLine, InspectionReport
from app.modules.master_data.brands.models import Brand
from app.modules.master_data.categories.models import Category
from app.modules.master_data.locations.models import Location
from app.modules.auth.models import User, Role, Permission
# Add new model imports here

target_metadata = Base.metadata
```

### Performance Optimizations
- Indexed columns for frequent queries
- Eager loading for related entities
- Query result caching with Redis
- Connection pooling
- Bulk operations for batch processing
- Optimized N+1 query prevention

## API Design Principles

### RESTful Conventions
```
GET    /api/v1/{resource}          # List with pagination/filtering
GET    /api/v1/{resource}/{id}     # Get single resource
POST   /api/v1/{resource}          # Create new resource
PUT    /api/v1/{resource}/{id}     # Full update
PATCH  /api/v1/{resource}/{id}     # Partial update
DELETE /api/v1/{resource}/{id}     # Delete resource

# Special actions
POST   /api/v1/{resource}/{id}/{action}  # Resource actions
GET    /api/v1/{resource}/{id}/{relation} # Related resources
```

### Pagination Standard
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

### Filter Query Parameters
```
GET /api/v1/customers?status=active&tier=gold&created_after=2024-01-01
GET /api/v1/inventory?location_id=1&status=available&category=electronics
```

### Error Response Format
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
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Authentication & Security

### JWT Authentication
- Access token expiry: 30 minutes
- Refresh token expiry: 7 days
- Token rotation on refresh
- Blacklist for revoked tokens

### Security Headers
```python
# Implemented in middleware
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

### RBAC Implementation
```python
# Roles
- Admin: Full system access
- Manager: Location-based access
- Staff: Operational access
- Viewer: Read-only access

# Permissions
- customers:read, customers:write, customers:delete
- inventory:read, inventory:write, inventory:delete
- transactions:read, transactions:write, transactions:delete
- reports:read, reports:generate
```

## Testing Strategy

### Test Pyramid
```
         /\
        /E2E\       (10%) - Complete workflows
       /------\
      /  API   \    (20%) - API contracts
     /----------\
    /Integration \  (30%) - Component interactions
   /--------------\
  /   Unit Tests   \ (40%) - Business logic
 /------------------\
```

### Test Organization
```
app/tests/
├── unit/
│   ├── test_customer_service.py
│   ├── test_inventory_calculations.py
│   └── test_rental_rules.py
├── integration/
│   ├── test_transaction_workflow.py
│   ├── test_rental_return_process.py
│   └── test_inventory_updates.py
├── e2e/
│   ├── test_complete_rental_cycle.py
│   └── test_customer_journey.py
├── performance/
│   ├── test_api_load.py
│   └── test_database_queries.py
├── fixtures/
│   ├── customers.py
│   ├── inventory.py
│   └── transactions.py
└── conftest.py
```

### Test Database Strategy
- Separate test database (`test.db`)
- Automatic table creation/destruction per test
- Transaction rollback for test isolation
- Fixtures for common test data

### Testing Best Practices
```python
# Use descriptive test names
async def test_blacklisted_customer_cannot_create_rental_transaction():
    # Arrange
    customer = await create_blacklisted_customer()
    
    # Act
    result = await rental_service.create_rental(customer.id, item_id)
    
    # Assert
    assert result.error == "CUSTOMER_BLACKLISTED"
```

## Performance Monitoring

### Metrics Collection
```python
# Prometheus metrics
rental_transactions_total = Counter('rental_transactions_total')
inventory_availability_gauge = Gauge('inventory_availability_gauge')
api_request_duration = Histogram('api_request_duration_seconds')
database_query_duration = Histogram('database_query_duration_seconds')
```

### Key Metrics
- Request rate and latency
- Error rates by endpoint
- Database query performance
- Cache hit rates
- Business metrics (rentals/day, revenue/location)

### Monitoring Endpoints
- `/metrics` - Prometheus metrics
- `/health` - Basic health check
- `/ready` - Readiness probe
- `/api/v1/system/status` - Detailed system status

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Stack
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/rental
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=rental
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7-alpine
```

### Environment Variables
```bash
# Application
APP_NAME=RentalManagementSystem
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/rental
TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# Redis Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=true
SENTRY_DSN=your-sentry-dsn

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@rental.com
SMTP_PASSWORD=your-password

# Storage (for uploads)
UPLOAD_PATH=/app/uploads
MAX_UPLOAD_SIZE=10485760  # 10MB
```

## Development Guidelines

### Code Style
```python
# Follow PEP 8
# Use type hints everywhere
from typing import Optional, List

async def get_available_items(
    location_id: int,
    category_id: Optional[int] = None,
    limit: int = 100
) -> List[Item]:
    """Get available items at location with optional category filter."""
    ...
```

### Commit Conventions
```
feat: Add customer tier upgrade logic
fix: Resolve inventory count mismatch on returns
docs: Update rental workflow documentation
test: Add edge cases for damage assessment
refactor: Optimize rental availability query
chore: Update dependencies to latest versions
perf: Add index on transaction date columns
```

### Error Handling
```python
# Use custom exceptions
class CustomerBlacklistedException(BusinessException):
    def __init__(self, customer_id: int):
        super().__init__(
            f"Customer {customer_id} is blacklisted",
            error_code="CUSTOMER_BLACKLISTED",
            status_code=403
        )

# Handle in service layer
try:
    customer = await customer_service.get_by_id(customer_id)
    if customer.blacklist_status == "blacklisted":
        raise CustomerBlacklistedException(customer_id)
except CustomerBlacklistedException:
    # Log and return appropriate response
    raise
```

## Common Development Tasks

### Adding a New Domain Module
1. Create module directory structure
2. Define SQLAlchemy models
3. Create Pydantic schemas
4. Implement repository layer
5. Build service layer with business logic
6. Add API routes
7. Write comprehensive tests
8. Update dependencies
9. Import models in alembic/env.py
10. Generate and apply migration
11. Update API documentation

### Implementing a Business Rule
```python
# Example: Minimum rental period enforcement
class RentalService:
    async def create_rental(
        self,
        customer_id: int,
        item_id: int,
        start_date: date,
        end_date: date
    ) -> TransactionHeader:
        # Get item details
        item = await self.item_repo.get_by_id(item_id)
        
        # Enforce minimum rental period
        rental_days = (end_date - start_date).days
        if rental_days < item.min_rental_days:
            raise ValidationException(
                f"Minimum rental period is {item.min_rental_days} days"
            )
        
        # Continue with rental creation...
```

### Performance Optimization Checklist
- [ ] Add database indexes on frequently queried columns
- [ ] Implement eager loading for related entities
- [ ] Use select_related/prefetch_related patterns
- [ ] Add Redis caching for slow queries
- [ ] Implement pagination for list endpoints
- [ ] Use bulk operations for batch processing
- [ ] Profile slow endpoints with middleware
- [ ] Monitor query execution times

## Troubleshooting

### Common Issues

#### 1. Database Migration Conflicts
```bash
# Solution
alembic downgrade -1
# Fix model issues
alembic revision --autogenerate -m "Fix migration"
alembic upgrade head
```

#### 2. Async Context Errors
```python
# Wrong
result = session.execute(query)  # Missing await

# Correct
result = await session.execute(query)
```

#### 3. N+1 Query Problems
```python
# Problem
rentals = await rental_repo.get_all()
for rental in rentals:
    customer = await customer_repo.get_by_id(rental.customer_id)  # N queries

# Solution
rentals = await rental_repo.get_all_with_customers()  # Eager loading
```

#### 4. Test Database Isolation
```python
# Ensure rollback in tests
@pytest.fixture
async def test_session():
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()
```

## Future Roadmap

### Planned Features
1. **Advanced Analytics**
   - Revenue forecasting
   - Inventory optimization
   - Customer behavior analysis
   - Location performance comparison

2. **Mobile API**
   - Optimized endpoints
   - Offline sync support
   - Push notifications

3. **Integration APIs**
   - Webhook support
   - Third-party integrations
   - API versioning strategy

4. **Advanced Features**
   - Multi-currency support
   - Reservation system
   - Maintenance scheduling
   - Loyalty program

### Technical Improvements
1. **Architecture Evolution**
   - Event sourcing for audit trail
   - CQRS for read/write separation
   - GraphQL API option
   - Microservices migration path

2. **Performance Enhancements**
   - Database read replicas
   - Advanced caching strategies
   - CDN integration
   - Query optimization

3. **Developer Experience**
   - API SDK generation
   - Interactive API playground
   - Development containers
   - CI/CD improvements

## Support Resources

### Documentation
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Postman Collection: `docs/postman/rental-api.json`
- Architecture Diagrams: `docs/architecture/`

### Monitoring
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Application Logs: `logs/app.log`

### Development Tools
- pgAdmin: Database management
- Redis Commander: Cache inspection
- Swagger Editor: API design
- Postman: API testing

This system represents a comprehensive rental management solution with robust architecture, scalable design, and production-ready features. Follow these guidelines to maintain code quality and system reliability.