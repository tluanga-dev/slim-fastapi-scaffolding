from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.core.cache import cache_manager
from app.core.middleware import setup_middleware
from app.core.openapi import setup_openapi_enhancements
from app.core.interactive_docs import setup_interactive_docs
from app.core.validation import create_validation_error_response, get_validation_metrics
from app.core.logging_config import configure_logging, LogLevel
from app.core.error_handlers import setup_error_handlers
from app.core.monitoring_alerts import setup_error_alert_integration
from app.db.session import engine
from app.db.base import Base

# Import modules to ensure they are registered with SQLAlchemy
from app.modules.master_data.brands import models as brand_models
from app.modules.master_data.categories import models as category_models
from app.modules.master_data.locations import models as location_models
from app.modules.auth import models as auth_models
from app.modules.customers import models as customer_models
from app.modules.inventory import models as inventory_models
from app.modules.transactions import models as transaction_models
from app.modules.rentals import models as rental_models
from app.modules.analytics import models as analytics_models
from app.modules.system import models as system_models

# Import routes
from app.modules.auth import routes as auth_routes
from app.modules.customers import routes as customer_routes
from app.modules.suppliers import routes as supplier_routes
from app.modules.master_data.brands import routes as brand_routes
from app.modules.master_data.categories import routes as category_routes
from app.modules.master_data.locations import routes as location_routes
from app.modules.inventory import routes as inventory_routes
from app.modules.transactions import routes as transaction_routes
from app.modules.rentals import routes as rental_routes
from app.modules.analytics import routes as analytics_routes
from app.modules.system import routes as system_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting Rental Management System API...")
    
    # Configure logging
    configure_logging(
        log_level=LogLevel.INFO,
        enable_console=True,
        enable_file=True,
        enable_json=True,
        enable_rotation=True
    )
    print("✅ Logging system configured")
    
    # Setup error alert integration
    setup_error_alert_integration()
    print("✅ Error alerting system configured")
    
    # Database initialization
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")
    
    # Initialize cache
    if settings.REDIS_ENABLED:
        try:
            await cache_manager.connect()
            print("✅ Redis cache connected successfully")
        except Exception as e:
            print(f"⚠️  Redis cache connection failed: {e}")
    
    # Initialize database optimizations
    try:
        from app.core.database_optimization import initialize_database_optimizations
        await initialize_database_optimizations()
        print("✅ Database optimizations initialized")
    except Exception as e:
        print(f"⚠️  Database optimization failed: {e}")
    
    print("🎉 Rental Management System API started successfully!")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Rental Management System API...")
    await engine.dispose()
    if settings.REDIS_ENABLED:
        await cache_manager.disconnect()
    print("✅ Shutdown complete")


app = FastAPI(
    title="Rental Management System API",
    description="""
# Rental Management System API

A comprehensive rental management system built with Domain-Driven Design (DDD) principles.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **Customer Management**: Complete customer lifecycle management with credit scoring
- **Supplier Management**: Supplier relationship management with performance tracking
- **Master Data Management**: Brands, categories, and location management
- **Inventory Management**: Real-time inventory tracking with stock levels
- **Transaction Processing**: Complete transaction workflow with payment processing
- **Rental Operations**: Rental booking, tracking, and return management
- **Analytics & Reporting**: Business intelligence and performance metrics
- **System Management**: Configuration, monitoring, and maintenance tools

## Architecture

The system follows Domain-Driven Design (DDD) principles with clean architecture:

- **Domain Layer**: Business entities, value objects, and repository interfaces
- **Application Layer**: Use cases and business logic orchestration
- **Infrastructure Layer**: Database models, repository implementations
- **API Layer**: FastAPI endpoints, schemas, and dependencies

## Security

- JWT tokens for authentication
- Role-based access control (RBAC)
- Permission-based authorization
- Input validation and sanitization
- SQL injection protection

## Database

- SQLite with async SQLAlchemy
- Alembic for database migrations
- Optimized queries with proper indexing
- Foreign key constraints and data integrity

## API Standards

- RESTful API design
- OpenAPI 3.0 specification
- Consistent error handling
- Comprehensive input validation
- Standardized response formats
    """,
    version="2.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "Rental Management System Support",
        "url": "https://example.com/contact/",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication, registration, and authorization operations",
        },
        {
            "name": "Customer Management",
            "description": "Customer lifecycle management, profiles, and relationship tracking",
        },
        {
            "name": "Supplier Management", 
            "description": "Supplier relationship management, performance tracking, and contracts",
        },
        {
            "name": "Master Data - Brands",
            "description": "Brand management for inventory categorization",
        },
        {
            "name": "Master Data - Categories",
            "description": "Hierarchical category management for items and services",
        },
        {
            "name": "Master Data - Locations",
            "description": "Location and warehouse management for inventory tracking",
        },
        {
            "name": "Inventory Management",
            "description": "Real-time inventory tracking, stock levels, and item management",
        },
        {
            "name": "Transaction Processing",
            "description": "Complete transaction workflow with payment processing and receipts",
        },
        {
            "name": "Rental Operations",
            "description": "Rental booking, tracking, returns, and availability management",
        },
        {
            "name": "Analytics & Reporting",
            "description": "Business intelligence, performance metrics, and data analytics",
        },
        {
            "name": "System Management",
            "description": "Configuration, monitoring, maintenance, and administrative tools",
        },
    ],
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up performance and caching middleware
setup_middleware(app)

# Set up exception handlers
setup_exception_handlers(app)

# Set up OpenAPI enhancements
setup_openapi_enhancements(app)

# Set up interactive documentation
setup_interactive_docs(app)

# Include API routes
# Authentication
app.include_router(auth_routes.router, prefix="/api/v1", tags=["Authentication"])

# Customer Management
app.include_router(customer_routes.router, prefix="/api/v1", tags=["Customer Management"])

# Supplier Management
app.include_router(supplier_routes.router, prefix="/api/v1", tags=["Supplier Management"])

# Master Data Management
app.include_router(brand_routes.router, prefix="/api/v1", tags=["Master Data - Brands"])
app.include_router(category_routes.router, prefix="/api/v1", tags=["Master Data - Categories"])
app.include_router(location_routes.router, prefix="/api/v1", tags=["Master Data - Locations"])

# Inventory Management
app.include_router(inventory_routes.router, prefix="/api/v1", tags=["Inventory Management"])

# Transaction Processing
app.include_router(transaction_routes.router, prefix="/api/v1", tags=["Transaction Processing"])

# Rental Operations
app.include_router(rental_routes.router, prefix="/api/v1", tags=["Rental Operations"])

# Analytics & Reporting
app.include_router(analytics_routes.router, prefix="/api/v1", tags=["Analytics & Reporting"])

# System Management
app.include_router(system_routes.router, prefix="/api/v1", tags=["System Management"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "2.0.0",
        "description": "Complete Rental Management System with Domain-Driven Design",
        "features": [
            "Authentication & User Management",
            "Customer & Supplier Management", 
            "Master Data Management",
            "Inventory Management",
            "Transaction Processing",
            "Rental Operations",
            "Analytics & Reporting",
            "System Management"
        ],
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    cache_health = await cache_manager.get_health() if settings.REDIS_ENABLED else {"status": "disabled"}
    
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "2.0.0",
        "architecture": "Domain-Driven Design",
        "modules": [
            "auth", "customers", "suppliers", "inventory", 
            "master_data", "transactions", "rentals", 
            "analytics", "system"
        ],
        "endpoints": 200,
        "database": "SQLite with async SQLAlchemy",
        "cache": cache_health
    }


@app.get("/metrics")
async def metrics():
    """Performance metrics endpoint."""
    from app.core.middleware import get_performance_metrics, get_slow_requests
    from app.core.database_optimization import get_database_performance_metrics
    from datetime import datetime
    from fastapi.responses import JSONResponse
    
    try:
        metrics_data = {"timestamp": datetime.utcnow().isoformat() + "Z"}
        
        # Get cache and request metrics
        if settings.REDIS_ENABLED:
            try:
                performance_metrics = await get_performance_metrics()
                slow_requests = await get_slow_requests(limit=5)
                cache_stats = await cache_manager.get_health()
                
                metrics_data.update({
                    "performance": performance_metrics,
                    "slow_requests": slow_requests,
                    "cache": cache_stats
                })
            except Exception as e:
                metrics_data["cache_error"] = str(e)
        else:
            metrics_data["cache"] = {"status": "disabled"}
        
        # Get database metrics
        try:
            db_metrics = await get_database_performance_metrics()
            metrics_data["database"] = db_metrics
        except Exception as e:
            metrics_data["database_error"] = str(e)
        
        return JSONResponse(
            content=metrics_data,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Content-Type": "application/json"
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": "Failed to generate metrics", "detail": str(e)},
            status_code=500,
            headers={
                "Cache-Control": "no-cache",
                "Content-Type": "application/json"
            }
        )


@app.get("/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    from app.core.prometheus_metrics import get_prometheus_metrics
    return await get_prometheus_metrics()


@app.get("/api-validation-metrics")
async def validation_metrics():
    """API validation metrics endpoint."""
    return {
        "validation_metrics": get_validation_metrics(),
        "description": "API request validation statistics",
        "timestamp": "2024-01-01T12:00:00Z"
    }


@app.get("/api-documentation-info")
async def api_documentation_info():
    """API documentation information endpoint."""
    from app.core.api_docs import get_api_documentation_summary
    return get_api_documentation_summary()


@app.get("/api-status")
async def api_status():
    """Comprehensive API status endpoint."""
    from app.core.api_docs import get_api_documentation_summary
    
    status_info = {
        "api_status": "operational",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": "2024-01-01T12:00:00Z",
        "features": {
            "authentication": True,
            "authorization": True,
            "caching": settings.REDIS_ENABLED,
            "rate_limiting": True,
            "input_validation": True,
            "api_documentation": True,
            "interactive_docs": True,
            "monitoring": True,
            "error_tracking": True
        },
        "documentation": {
            "openapi_spec": "/openapi.json",
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "api_playground": "/api-playground",
            "code_samples": "/code-samples",
            "api_guide": "/api-guide"
        },
        "validation_metrics": get_validation_metrics(),
        "api_summary": get_api_documentation_summary()
    }
    
    return status_info