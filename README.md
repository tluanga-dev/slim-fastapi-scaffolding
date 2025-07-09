# Rental Management System Backend

A comprehensive, production-ready rental and sales management system built with FastAPI, implementing Domain-Driven Design (DDD) principles. This system manages multi-location operations for businesses that rent and sell inventory items.

## 🚀 Features

### Core Functionality
- **Multi-Location Support**: Manage inventory across multiple stores, warehouses, and service centers
- **Dual-Mode Operations**: Support for both rental and direct sales transactions
- **Customer Management**: Tiered customer system with credit limits and blacklist management
- **Inventory Tracking**: Real-time tracking of individual units with serial numbers
- **Rental Workflows**: Complete rental lifecycle from booking to return with inspection
- **Financial Management**: Deposits, late fees, damage assessments, and payment processing
- **Supplier Management**: Track suppliers, purchase orders, and performance metrics

### Technical Features
- **Modern Architecture**: Domain-Driven Design with clean separation of concerns
- **Async/Await**: Built on FastAPI with full async support for high performance
- **Authentication**: JWT-based auth with Role-Based Access Control (RBAC)
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Monitoring**: Prometheus metrics and health endpoints
- **Testing**: Comprehensive test suite with 80%+ coverage requirement
- **Database**: SQLAlchemy with Alembic migrations, supports SQLite and PostgreSQL

## 📋 Prerequisites

- Python 3.11 or higher
- pip or Poetry for dependency management
- SQLite (default) or PostgreSQL for production
- Redis (optional, for caching)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/rental-management-system.git
cd rental-management-system/rental-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
# Application
APP_NAME=RentalManagementSystem
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./app.db
TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis (optional)
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
```

### 5. Initialize Database
```bash
# Run migrations
alembic upgrade head

# (Optional) Seed initial data
python scripts/seed_data.py
```

## 🚀 Quick Start

### Run Development Server
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
```

## 📁 Project Structure

```
rental-backend/
├── app/
│   ├── core/              # Core functionality (config, security, etc.)
│   ├── modules/           # Domain modules (DDD bounded contexts)
│   │   ├── auth/         # Authentication & authorization
│   │   ├── customers/    # Customer management
│   │   ├── inventory/    # Inventory & stock management
│   │   ├── transactions/ # Sales & rental transactions
│   │   ├── rentals/      # Rental returns & inspections
│   │   └── ...          # Other domain modules
│   ├── shared/           # Shared utilities and dependencies
│   ├── db/              # Database configuration
│   └── tests/           # Test suite
├── alembic/             # Database migrations
├── docs/                # Additional documentation
├── scripts/             # Utility scripts
└── deployment/          # Deployment configurations
```

## 🔧 Development

### Code Quality Tools
```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/

# Type checking
mypy app/

# Run all checks
black app/ && isort app/ && flake8 app/ && mypy app/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding New Features

1. **Create Domain Module**
   ```bash
   mkdir -p app/modules/new_feature
   touch app/modules/new_feature/{__init__.py,models.py,schemas.py,repository.py,service.py,routes.py}
   ```

2. **Follow DDD Pattern**
   - Define domain models in `models.py`
   - Create Pydantic schemas in `schemas.py`
   - Implement repository pattern in `repository.py`
   - Add business logic in `service.py`
   - Expose API endpoints in `routes.py`

3. **Register Module**
   - Import models in `alembic/env.py`
   - Add routes to `app/main.py`
   - Update dependencies in `app/shared/dependencies.py`

## 🧪 Testing

The project follows a comprehensive testing strategy:

- **Unit Tests (40%)**: Test individual components and business logic
- **Integration Tests (30%)**: Test component interactions
- **API Tests (20%)**: Test API contracts and responses
- **E2E Tests (10%)**: Test complete user workflows

### Writing Tests
```python
# Example test structure
async def test_customer_cannot_rent_when_blacklisted():
    # Arrange
    customer = await create_test_customer(blacklist_status="blacklisted")
    item = await create_test_item()
    
    # Act
    with pytest.raises(CustomerBlacklistedException):
        await rental_service.create_rental(customer.id, item.id)
    
    # Assert - exception was raised
```

## 📊 API Examples

### Create Customer
```bash
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "type": "individual",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "tier": "silver"
  }'
```

### Create Rental Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "type": "rental",
    "customer_id": 1,
    "location_id": 1,
    "rental_start_date": "2024-01-20",
    "rental_end_date": "2024-01-27",
    "lines": [
      {
        "item_id": 1,
        "quantity": 1,
        "rental_rate_type": "daily"
      }
    ]
  }'
```

### Process Return
```bash
curl -X POST http://localhost:8000/api/v1/rentals/returns \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "transaction_id": 123,
    "return_type": "full",
    "lines": [
      {
        "transaction_line_id": 1,
        "returned_quantity": 1,
        "condition": "good"
      }
    ]
  }'
```

## 🚢 Deployment

### Docker Deployment
```bash
# Build image
docker build -t rental-backend .

# Run container
docker run -p 8000:8000 --env-file .env rental-backend
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Production Considerations
1. Use PostgreSQL instead of SQLite
2. Enable Redis for caching
3. Set up proper monitoring (Prometheus/Grafana)
4. Configure reverse proxy (Nginx)
5. Implement backup strategies
6. Set up CI/CD pipeline

## 📈 Monitoring

### Health Endpoints
- `/health` - Basic health check
- `/ready` - Readiness probe
- `/metrics` - Prometheus metrics

### Key Metrics
- Request rate and latency
- Error rates by endpoint
- Database query performance
- Business metrics (rentals/day, revenue)

## 🔒 Security

- JWT-based authentication
- Role-Based Access Control (RBAC)
- Input validation and sanitization
- SQL injection prevention via ORM
- Rate limiting on sensitive endpoints
- Secure password hashing (bcrypt)

## 📚 Additional Documentation

- [API Reference](./docs/api/README.md)
- [Architecture Guide](./docs/architecture/README.md)
- [Business Logic Documentation](./docs/business/README.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Contributing Guidelines](./CONTRIBUTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention
We follow conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Database ORM: [SQLAlchemy](https://www.sqlalchemy.org/)
- Testing: [pytest](https://pytest.org/)
- Documentation: [Swagger/OpenAPI](https://swagger.io/)

## 📞 Support

For support, email support@rentalsystem.com or create an issue in the GitHub repository.

---

**Note**: This is a reference implementation. Ensure you review and adapt security settings, error handling, and business logic to match your specific requirements before deploying to production.