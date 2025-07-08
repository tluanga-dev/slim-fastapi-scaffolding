# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a slim FastAPI scaffolding project designed for rapid development with commercial-grade architecture. It follows domain-driven design principles with a repository pattern, async SQLAlchemy, comprehensive pytest setup, and clean separation of concerns. The project includes no authentication, no admin accounts, and uses SQLite for simplicity.

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

# Initialize database for development (alternative method)
python -c "from app.startup import init_db; import asyncio; asyncio.run(init_db())"
```

### Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test module
pytest app/tests/modules/items/test_service.py

# Run single test
pytest app/tests/modules/items/test_routes.py::test_create_item

# Run tests with coverage
pytest --cov=app
```

### Development Server
```bash
# Start development server
uvicorn app.main:app --reload

# Start on specific port
uvicorn app.main:app --reload --port 8001
```

### Verification Checklist
```bash
# Complete setup verification
pytest                              # Verify all tests pass
uvicorn app.main:app --reload      # Start server
# Test endpoints:
# POST /items/ with {"name": "Test", "description": "Test Description"}
# GET /items/{id}
alembic revision --autogenerate -m "Test migration"  # Verify Alembic works
```

## Architecture Overview

This scaffolding implements a **commercial-grade, slimmed-down architecture** with clean separation of concerns:

### Repository Pattern Flow
```
FastAPI Route → Service → Repository → Database Model
      ↓           ↓           ↓
   Schemas   Business     Data Access
             Logic       Layer
```

### Dependency Injection Chain
The application uses FastAPI's dependency injection system:

1. **Database Session**: `get_session()` provides async database sessions
2. **Repository Layer**: `get_item_repository(session)` injects session into repository  
3. **Service Layer**: `get_item_service(repo)` injects repository into service
4. **Route Layer**: Routes depend on services via `Depends(get_item_service)`

This chain is defined in `app/shared/dependencies.py` and allows for clean testing via dependency overrides.

### Core Design Principles
- **No Authentication**: Simplified for rapid prototyping
- **No Admin Accounts**: Focus on core business logic
- **Async SQLAlchemy**: Modern async/await patterns throughout
- **Vertical Slicing**: Each domain module is self-contained
- **Test Isolation**: Separate test database with automatic cleanup

### Module Structure
Each domain module follows this exact pattern (using `items` as the example):
```
app/modules/{domain}/
├── models.py      # SQLAlchemy models with Base inheritance
├── schemas.py     # Pydantic request/response schemas with ConfigDict
├── repository.py  # Data access layer with async session management
├── service.py     # Business logic layer
└── routes.py      # FastAPI endpoint definitions with APIRouter
```

### File Structure Overview
```
project-root/
├── app/
│   ├── core/
│   │   ├── config.py          # Pydantic settings with .env support
│   │   └── errors.py          # Centralized exception handling
│   ├── modules/
│   │   └── items/             # Example domain module
│   ├── shared/
│   │   └── dependencies.py    # Dependency injection definitions
│   ├── db/
│   │   ├── session.py         # Async database session management
│   │   └── base.py            # SQLAlchemy declarative base
│   ├── tests/
│   │   ├── conftest.py        # Test configuration and fixtures
│   │   └── modules/items/     # Domain-specific tests
│   ├── main.py                # FastAPI application entry point
│   └── startup.py             # Database initialization utilities
├── alembic/                   # Database migrations
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── alembic.ini               # Alembic configuration
└── pytest.ini               # Pytest configuration
```

## Database Architecture

### SQLite + Async SQLAlchemy Setup
- **Production Database**: `app.db` (SQLite with aiosqlite driver)
- **Test Database**: `test.db` (separate database for testing)
- **Connection String**: `sqlite+aiosqlite:///./app.db`
- **Session Management**: Async context managers with proper cleanup

### Model Registration for Migrations
**Critical**: When adding new models, they must be imported in `alembic/env.py` for migrations to work:
```python
from app.db.base import Base
# Import all models so they are registered with Base
from app.modules.items.models import Item
from app.modules.new_domain.models import NewModel  # Add new imports here
target_metadata = Base.metadata
```

### Migration Workflow
1. **Modify models** in `models.py`
2. **Import new models** in `alembic/env.py`
3. **Generate migration**: `alembic revision --autogenerate -m "Description"`
4. **Review generated migration** file in `alembic/versions/`
5. **Apply migration**: `alembic upgrade head`

## Testing Architecture

### Complete Pytest Setup with Async Support
The testing system provides full database isolation and async support:

### Test Database Strategy
- **Separate Test Database**: `test.db` (completely isolated from production)
- **Automatic Table Management**: Tables created/destroyed per test
- **Dependency Overrides**: Test database injected via FastAPI dependency system
- **Async Test Support**: `asyncio_mode = auto` in `pytest.ini`

### Test Structure
```
app/tests/
├── conftest.py                    # Global test configuration & fixtures
└── modules/{domain}/
    ├── test_routes.py            # API endpoint tests using test_client
    └── test_service.py           # Business logic tests using test_session
```

### Key Test Fixtures
- **`test_client`**: FastAPI TestClient with dependency overrides
- **`test_session`**: Direct async database session for unit tests
- **`setup_test_db`**: Auto-used fixture for table creation/cleanup

### Test Configuration Details
```python
# pytest.ini
[pytest]
testpaths = app/tests
asyncio_mode = auto

# conftest.py highlights
app.dependency_overrides[get_session] = override_get_session
```

## Adding New Domain Modules

Follow the scaffolding pattern using the `items` module as a template:

### Step-by-Step Module Creation

1. **Create module structure**:
   ```bash
   mkdir -p app/modules/new_domain
   touch app/modules/new_domain/{models,schemas,repository,service,routes}.py
   ```

2. **Define model** in `models.py` (following items example):
   ```python
   from app.db.base import Base
   from sqlalchemy import Column, Integer, String
   
   class NewModel(Base):
       __tablename__ = "new_models"
       id = Column(Integer, primary_key=True, index=True)
       name = Column(String, index=True)
       # ... other columns
   ```

3. **Create schemas** in `schemas.py` (use ConfigDict pattern):
   ```python
   from pydantic import BaseModel, ConfigDict
   
   class NewModelCreate(BaseModel):
       name: str
   
   class NewModelResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       name: str
   ```

4. **Implement repository** in `repository.py` (async pattern):
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   
   class NewModelRepository:
       def __init__(self, session: AsyncSession):
           self.session = session
       
       async def create_item(self, item_data: dict) -> NewModel:
           # Follow items repository pattern
   ```

5. **Add dependencies** in `app/shared/dependencies.py`:
   ```python
   async def get_new_repository(session=Depends(get_session)):
       return NewRepository(session)
   
   async def get_new_service(repo=Depends(get_new_repository)):
       return NewService(repo)
   ```

6. **Register routes** in `app/main.py`:
   ```python
   from app.modules.new_domain import routes as new_routes
   app.include_router(new_routes.router, prefix="/new-domain")
   ```

7. **Import model** in `alembic/env.py`:
   ```python
   from app.modules.new_domain.models import NewModel
   ```

8. **Create and apply migration**:
   ```bash
   alembic revision --autogenerate -m "Add new_domain module"
   alembic upgrade head
   ```

9. **Add tests** following the `items` test pattern in `app/tests/modules/new_domain/`

## Configuration Management

### Pydantic Settings with .env Support
```python
# app/core/config.py
class Settings(BaseSettings):
    APP_NAME: str = "SlimFastAPI"
    SQLALCHEMY_DATABASE_URI: str = "sqlite+aiosqlite:///./app.db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    
    class Config:
        env_file = ".env"
```

### Environment Variables
- Create `.env` file for local development
- Environment variables override defaults
- Separate database URLs for production and testing

## Implementation Rules & Best Practices

### Required Patterns
- **No Authentication**: This scaffold excludes authentication deliberately
- **No Admin Accounts**: Focus on core business logic
- **Async/Await**: All database operations must use async patterns
- **Repository Pattern**: Maintain service → repository → model flow
- **Dependency Injection**: Use FastAPI's Depends system throughout

### Modern Python Patterns
- **Schema Validation**: Use `model_dump()` instead of deprecated `dict()` method
- **Type Hints**: Use modern union syntax (`str | None` instead of `Optional[str]`)
- **ConfigDict**: Use `model_config = ConfigDict(from_attributes=True)` for Pydantic models
- **Async Context Managers**: Proper session management with `async with`

### Development Guidelines
- **Error Handling**: Centralized in `app/core/errors.py`
- **Import Paths**: Use absolute imports from `app.` root
- **Test Isolation**: Each test gets a fresh database automatically
- **Vertical Slicing**: Keep domain modules self-contained
- **Clean Architecture**: Maintain clear separation between layers