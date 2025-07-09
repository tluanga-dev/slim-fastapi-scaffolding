# Architecture Documentation

## Overview

The Rental Management System is built using Domain-Driven Design (DDD) principles with a clean, layered architecture. This document provides a comprehensive overview of the system's architectural decisions, patterns, and design principles.

## Architectural Principles

### 1. Domain-Driven Design (DDD)
The system is organized around business domains (bounded contexts), with each domain having clear boundaries and responsibilities.

### 2. Clean Architecture
Dependencies flow inward, with the domain layer at the center, independent of external concerns like databases or web frameworks.

### 3. SOLID Principles
- **Single Responsibility**: Each class/module has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable for base types
- **Interface Segregation**: Clients shouldn't depend on interfaces they don't use
- **Dependency Inversion**: Depend on abstractions, not concretions

### 4. Async-First Design
All I/O operations use async/await for optimal performance and scalability.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Presentation Layer                     │
│                    (FastAPI Routes & Schemas)                 │
├─────────────────────────────────────────────────────────────┤
│                      Application Layer                        │
│                    (Services & Use Cases)                     │
├─────────────────────────────────────────────────────────────┤
│                        Domain Layer                           │
│                   (Entities & Business Rules)                 │
├─────────────────────────────────────────────────────────────┤
│                     Infrastructure Layer                      │
│              (Repository, Database, External APIs)            │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Presentation Layer (API)
- **Location**: `app/modules/*/routes.py`
- **Responsibilities**:
  - HTTP request/response handling
  - Input validation using Pydantic schemas
  - Authentication/authorization enforcement
  - API documentation generation
  - Error response formatting

### Application Layer (Services)
- **Location**: `app/modules/*/service.py`
- **Responsibilities**:
  - Business use case orchestration
  - Transaction management
  - Cross-domain coordination
  - Business rule enforcement
  - Data transformation between layers

### Domain Layer (Models)
- **Location**: `app/modules/*/models.py`
- **Responsibilities**:
  - Domain entity definitions
  - Business invariants
  - Entity relationships
  - Domain-specific validations
  - Value objects (future enhancement)

### Infrastructure Layer (Repository)
- **Location**: `app/modules/*/repository.py`
- **Responsibilities**:
  - Data persistence
  - Query implementation
  - External service integration
  - Caching logic
  - Database transaction handling

## Domain Model

### Bounded Contexts

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Customer      │     │   Inventory     │     │  Transaction    │
│   Management    │────▶│   Management    │◀────│  Processing     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         │                       ▼                        │
         │              ┌─────────────────┐              │
         └─────────────▶│     Rental      │◀─────────────┘
                        │   Operations    │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Master Data   │
                        │   Management    │
                        └─────────────────┘
```

### Key Aggregates

1. **Customer Aggregate**
   - Root: Customer
   - Value Objects: Address, ContactInfo
   - Business Rules: Tier management, blacklist enforcement

2. **Inventory Aggregate**
   - Root: Item
   - Entities: InventoryUnit, StockLevel
   - Business Rules: Availability checking, reorder management

3. **Transaction Aggregate**
   - Root: TransactionHeader
   - Entities: TransactionLine
   - Business Rules: Status transitions, payment validation

4. **Rental Return Aggregate**
   - Root: RentalReturn
   - Entities: RentalReturnLine, InspectionReport
   - Business Rules: Damage assessment, fee calculation

## Data Flow Architecture

### Request Flow

```
Client Request
     │
     ▼
FastAPI Route
     │
     ├─> Input Validation (Pydantic Schema)
     │
     ├─> Authentication/Authorization
     │
     ▼
Service Layer
     │
     ├─> Business Logic
     │
     ├─> Domain Model Operations
     │
     ▼
Repository Layer
     │
     ├─> Database Query/Command
     │
     ▼
Database
```

### Response Flow

```
Database Result
     │
     ▼
Repository Layer
     │
     ├─> Entity Construction
     │
     ▼
Service Layer
     │
     ├─> Business Logic Application
     │
     ├─> DTO Transformation
     │
     ▼
FastAPI Route
     │
     ├─> Response Schema Serialization
     │
     ▼
Client Response
```

## Design Patterns

### 1. Repository Pattern
Abstracts data access logic and provides a more object-oriented view of the persistence layer.

```python
class CustomerRepository:
    async def get_by_id(self, id: int) -> Customer:
        # Implementation
    
    async def save(self, customer: Customer) -> Customer:
        # Implementation
    
    async def find_by_email(self, email: str) -> Optional[Customer]:
        # Implementation
```

### 2. Service Layer Pattern
Encapsulates business logic and orchestrates operations across multiple repositories.

```python
class RentalService:
    def __init__(self, 
                 customer_repo: CustomerRepository,
                 inventory_repo: InventoryRepository,
                 transaction_repo: TransactionRepository):
        # Dependency injection
    
    async def create_rental(self, data: RentalCreateSchema) -> Transaction:
        # Business logic orchestration
```

### 3. Dependency Injection
Uses FastAPI's built-in DI system for loose coupling and testability.

```python
async def get_customer_service(
    repo: CustomerRepository = Depends(get_customer_repository)
) -> CustomerService:
    return CustomerService(repo)
```

### 4. Unit of Work Pattern
Implemented via SQLAlchemy's session management for transaction consistency.

```python
async with get_session() as session:
    # All operations within this block are in the same transaction
    customer = await customer_repo.create(data)
    await inventory_repo.update_stock(item_id, -1)
    # Auto-commit on success, rollback on failure
```

### 5. Specification Pattern (Future Enhancement)
For complex query building and business rule evaluation.

```python
class ActiveRentalSpecification:
    def is_satisfied_by(self, rental: Rental) -> bool:
        return rental.status == "active" and rental.end_date > datetime.now()
```

## Database Architecture

### Schema Design Principles

1. **Normalization**: 3NF for transactional data
2. **Denormalization**: Strategic denormalization for read performance
3. **Indexing**: Indexes on foreign keys and frequently queried columns
4. **Constraints**: Database-level constraints for data integrity

### Key Design Decisions

1. **Async SQLAlchemy**: For non-blocking database operations
2. **Alembic Migrations**: Version-controlled schema changes
3. **Optimistic Locking**: Via version columns for concurrent updates
4. **Soft Deletes**: Maintain audit trail with deleted_at timestamps

### Performance Optimizations

1. **Connection Pooling**: Reuse database connections
2. **Query Optimization**: Eager loading for N+1 prevention
3. **Caching Strategy**: Redis for frequently accessed data
4. **Batch Operations**: Bulk inserts/updates where applicable

## API Design

### RESTful Principles

1. **Resource-Based URLs**: `/api/v1/customers`, `/api/v1/inventory`
2. **HTTP Verbs**: GET, POST, PUT, PATCH, DELETE
3. **Status Codes**: Consistent use of HTTP status codes
4. **HATEOAS**: Links to related resources (where applicable)

### Versioning Strategy

- URL versioning: `/api/v1/`, `/api/v2/`
- Backward compatibility for at least one version
- Deprecation notices in headers

### Response Format

```json
{
  "data": {
    // Resource data
  },
  "meta": {
    "timestamp": "2024-01-20T10:00:00Z",
    "version": "1.0"
  },
  "links": {
    "self": "/api/v1/customers/123",
    "related": {
      "transactions": "/api/v1/customers/123/transactions"
    }
  }
}
```

### Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Security Architecture

### Authentication Flow

```
┌────────┐      ┌────────┐      ┌─────────┐      ┌──────────┐
│ Client │─────▶│  API   │─────▶│  Auth   │─────▶│ Database │
└────────┘      └────────┘      │ Service │      └──────────┘
     ▲               │          └─────────┘           │
     │               │               │                │
     │               │               ▼                │
     │               │          ┌─────────┐           │
     │               └─────────▶│  JWT    │◀──────────┘
     │                          │ Token   │
     └──────────────────────────┤ (Redis) │
                                └─────────┘
```

### Authorization Model

- **Role-Based Access Control (RBAC)**
- **Resource-Based Permissions**
- **Hierarchical Roles**: Admin > Manager > Staff > Viewer
- **Location-Based Access**: Managers can only access their locations

### Security Measures

1. **Password Security**: Bcrypt hashing with salt
2. **JWT Tokens**: Short-lived access tokens, longer refresh tokens
3. **Rate Limiting**: Prevent brute force attacks
4. **Input Validation**: Prevent injection attacks
5. **CORS Policy**: Configured for allowed origins
6. **HTTPS Only**: Enforce encrypted connections

## Scalability Considerations

### Horizontal Scaling

1. **Stateless Services**: No server-side session storage
2. **Database Replication**: Read replicas for scaling reads
3. **Load Balancing**: Distribute traffic across instances
4. **Caching Layer**: Redis for reducing database load

### Vertical Scaling

1. **Async Operations**: Non-blocking I/O for better resource utilization
2. **Connection Pooling**: Efficient database connection management
3. **Query Optimization**: Indexes and efficient queries
4. **Resource Monitoring**: Track and optimize resource usage

### Future Microservices Path

The current modular architecture allows for future decomposition:

1. **Customer Service**: Customer management microservice
2. **Inventory Service**: Inventory tracking microservice
3. **Transaction Service**: Order processing microservice
4. **Notification Service**: Email/SMS notifications
5. **Analytics Service**: Reporting and analytics

## Development Practices

### Code Organization

```
app/modules/{domain}/
├── __init__.py          # Module exports
├── models.py            # Domain models
├── schemas.py           # Pydantic schemas
├── repository.py        # Data access
├── service.py           # Business logic
├── routes.py            # API endpoints
├── dependencies.py      # DI configuration
├── validators.py        # Custom validators
└── utils.py            # Utility functions
```

### Testing Strategy

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **E2E Tests**: Test complete user workflows
4. **Performance Tests**: Ensure system meets performance requirements

### CI/CD Pipeline

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   Code   │────▶│   Test   │────▶│  Build   │────▶│  Deploy  │
│  Commit  │     │   Suite  │     │  Docker  │     │   Stage  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │                                  │
                       ▼                                  ▼
                 ┌──────────┐                      ┌──────────┐
                 │  Quality │                      │  Deploy  │
                 │   Gate   │                      │   Prod   │
                 └──────────┘                      └──────────┘
```

## Monitoring and Observability

### Metrics Collection

- **Application Metrics**: Request rates, response times, error rates
- **Business Metrics**: Rentals per day, revenue, inventory turnover
- **Infrastructure Metrics**: CPU, memory, disk usage
- **Custom Metrics**: Domain-specific measurements

### Logging Strategy

- **Structured Logging**: JSON format for easy parsing
- **Log Levels**: ERROR, WARN, INFO, DEBUG
- **Correlation IDs**: Track requests across services
- **Log Aggregation**: Centralized log management

### Distributed Tracing

- **Request Tracing**: Track requests through all layers
- **Performance Profiling**: Identify bottlenecks
- **Error Tracking**: Capture and analyze errors
- **Service Dependencies**: Visualize service interactions

## Technology Stack

### Core Technologies

- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy with async support
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache**: Redis
- **Message Queue**: RabbitMQ/Celery (future)

### Development Tools

- **Testing**: pytest, pytest-asyncio
- **Code Quality**: black, isort, flake8, mypy
- **Documentation**: Swagger/OpenAPI, MkDocs
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions / GitLab CI

### Monitoring Stack

- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logs**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **APM**: OpenTelemetry (future)

## Deployment Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Load Balancer                      │
└─────────────────────────────────────────────────────┘
                           │
        ┌─────────────────┴─────────────────┐
        │                                    │
┌───────▼────────┐                ┌─────────▼────────┐
│   FastAPI      │                │    FastAPI       │
│   Container 1  │                │   Container 2    │
└────────────────┘                └──────────────────┘
        │                                    │
        └─────────────────┬─────────────────┘
                          │
                ┌─────────▼────────┐
                │    PostgreSQL    │
                │    (Primary)     │
                └─────────┬────────┘
                          │
                ┌─────────▼────────┐
                │    PostgreSQL    │
                │    (Replica)     │
                └──────────────────┘
```

### Kubernetes Architecture (Future)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rental-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rental-api
  template:
    spec:
      containers:
      - name: api
        image: rental-api:latest
        ports:
        - containerPort: 8000
```

## Decision Records

### ADR-001: Async SQLAlchemy
- **Status**: Accepted
- **Context**: Need non-blocking database operations
- **Decision**: Use SQLAlchemy with async support
- **Consequences**: Better performance, more complex error handling

### ADR-002: Domain-Driven Design
- **Status**: Accepted
- **Context**: Complex business domain with multiple contexts
- **Decision**: Organize code around business domains
- **Consequences**: Better maintainability, clear boundaries

### ADR-003: JWT Authentication
- **Status**: Accepted
- **Context**: Need stateless authentication
- **Decision**: Use JWT tokens with refresh mechanism
- **Consequences**: Scalable auth, token management complexity

## Future Enhancements

### Technical Debt

1. **Event Sourcing**: Implement for complete audit trail
2. **CQRS**: Separate read and write models
3. **GraphQL**: Alternative API for flexible queries
4. **WebSockets**: Real-time updates

### Performance Improvements

1. **Database Sharding**: For massive scale
2. **Read Replicas**: Distribute read load
3. **CDN Integration**: Static asset delivery
4. **Edge Computing**: Reduce latency

### Feature Enhancements

1. **Multi-tenancy**: Support multiple businesses
2. **Internationalization**: Multi-language support
3. **Advanced Analytics**: ML-based insights
4. **Mobile Apps**: Native mobile applications

---

This architecture provides a solid foundation for a scalable, maintainable rental management system while allowing for future growth and evolution.