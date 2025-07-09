"""
Prometheus metrics collection for rental management system.

This module provides comprehensive metrics collection for monitoring and observability.
"""

from typing import Dict, Any, List, Optional
import time
from datetime import datetime
from contextlib import asynccontextmanager

from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum,
    CollectorRegistry, generate_latest,
    multiprocess, values
)
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

from app.core.config import settings


# Create custom registry for the application
registry = CollectorRegistry()

# Application info
app_info = Info(
    'rental_management_app',
    'Rental Management System application information',
    registry=registry
)

# Request metrics
request_count = Counter(
    'rental_management_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

request_duration = Histogram(
    'rental_management_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

# Database metrics
db_connections = Gauge(
    'rental_management_db_connections',
    'Number of database connections',
    ['status'],
    registry=registry
)

db_query_duration = Histogram(
    'rental_management_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    registry=registry
)

db_query_count = Counter(
    'rental_management_db_queries_total',
    'Total number of database queries',
    ['operation', 'table', 'status'],
    registry=registry
)

# Cache metrics
cache_hits = Counter(
    'rental_management_cache_hits_total',
    'Total number of cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses = Counter(
    'rental_management_cache_misses_total',
    'Total number of cache misses',
    ['cache_type'],
    registry=registry
)

cache_size = Gauge(
    'rental_management_cache_size_bytes',
    'Current cache size in bytes',
    ['cache_type'],
    registry=registry
)

# Business metrics
active_rentals = Gauge(
    'rental_management_active_rentals',
    'Number of currently active rentals',
    registry=registry
)

total_customers = Gauge(
    'rental_management_total_customers',
    'Total number of customers',
    ['customer_type'],
    registry=registry
)

inventory_items = Gauge(
    'rental_management_inventory_items',
    'Number of inventory items',
    ['status', 'category'],
    registry=registry
)

revenue_total = Counter(
    'rental_management_revenue_total',
    'Total revenue generated',
    ['currency', 'transaction_type'],
    registry=registry
)

# System metrics
memory_usage = Gauge(
    'rental_management_memory_usage_bytes',
    'Memory usage in bytes',
    ['type'],
    registry=registry
)

cpu_usage = Gauge(
    'rental_management_cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)

disk_usage = Gauge(
    'rental_management_disk_usage_bytes',
    'Disk usage in bytes',
    ['path'],
    registry=registry
)

# Error metrics
error_count = Counter(
    'rental_management_errors_total',
    'Total number of errors',
    ['error_type', 'module'],
    registry=registry
)

# Performance metrics
slow_requests = Counter(
    'rental_management_slow_requests_total',
    'Total number of slow requests',
    ['method', 'endpoint'],
    registry=registry
)

# Authentication metrics
auth_attempts = Counter(
    'rental_management_auth_attempts_total',
    'Total authentication attempts',
    ['result', 'method'],
    registry=registry
)

active_sessions = Gauge(
    'rental_management_active_sessions',
    'Number of active user sessions',
    registry=registry
)


class MetricsCollector:
    """Collect and manage application metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.setup_app_info()
    
    def setup_app_info(self):
        """Setup application information metrics."""
        app_info.info({
            'version': settings.APP_VERSION,
            'name': settings.APP_NAME,
            'environment': settings.ENVIRONMENT,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat()
        })
    
    # Request metrics
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Record slow requests
        if duration > 1.0:  # 1 second threshold
            slow_requests.labels(
                method=method,
                endpoint=endpoint
            ).inc()
    
    # Database metrics
    def record_db_query(self, operation: str, table: str, duration: float, status: str = "success"):
        """Record database query metrics."""
        db_query_count.labels(
            operation=operation,
            table=table,
            status=status
        ).inc()
        
        db_query_duration.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def update_db_connections(self, active: int, idle: int, total: int):
        """Update database connection metrics."""
        db_connections.labels(status="active").set(active)
        db_connections.labels(status="idle").set(idle)
        db_connections.labels(status="total").set(total)
    
    # Cache metrics
    def record_cache_hit(self, cache_type: str):
        """Record cache hit."""
        cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss."""
        cache_misses.labels(cache_type=cache_type).inc()
    
    def update_cache_size(self, cache_type: str, size_bytes: int):
        """Update cache size metrics."""
        cache_size.labels(cache_type=cache_type).set(size_bytes)
    
    # Business metrics
    def update_active_rentals(self, count: int):
        """Update active rentals count."""
        active_rentals.set(count)
    
    def update_customer_count(self, customer_type: str, count: int):
        """Update customer count by type."""
        total_customers.labels(customer_type=customer_type).set(count)
    
    def update_inventory_count(self, status: str, category: str, count: int):
        """Update inventory item count."""
        inventory_items.labels(status=status, category=category).set(count)
    
    def record_revenue(self, amount: float, currency: str, transaction_type: str):
        """Record revenue metrics."""
        revenue_total.labels(
            currency=currency,
            transaction_type=transaction_type
        ).inc(amount)
    
    # System metrics
    def update_memory_usage(self, memory_type: str, usage_bytes: int):
        """Update memory usage metrics."""
        memory_usage.labels(type=memory_type).set(usage_bytes)
    
    def update_cpu_usage(self, usage_percent: float):
        """Update CPU usage metrics."""
        cpu_usage.set(usage_percent)
    
    def update_disk_usage(self, path: str, usage_bytes: int):
        """Update disk usage metrics."""
        disk_usage.labels(path=path).set(usage_bytes)
    
    # Error metrics
    def record_error(self, error_type: str, module: str):
        """Record error occurrence."""
        error_count.labels(
            error_type=error_type,
            module=module
        ).inc()
    
    # Authentication metrics
    def record_auth_attempt(self, result: str, method: str):
        """Record authentication attempt."""
        auth_attempts.labels(
            result=result,
            method=method
        ).inc()
    
    def update_active_sessions(self, count: int):
        """Update active sessions count."""
        active_sessions.set(count)


# Global metrics collector
metrics_collector = MetricsCollector()


class PrometheusMiddleware:
    """Middleware to collect request metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # Create a custom send function to capture response
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Record error
            metrics_collector.record_error(
                error_type=type(e).__name__,
                module="middleware"
            )
            raise
        finally:
            # Record request metrics
            duration = time.time() - start_time
            metrics_collector.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration=duration
            )


async def get_prometheus_metrics() -> PlainTextResponse:
    """Generate Prometheus metrics output."""
    try:
        # Generate metrics data
        metrics_data = generate_latest(registry)
        
        # Ensure proper encoding
        if isinstance(metrics_data, bytes):
            metrics_content = metrics_data.decode('utf-8')
        else:
            metrics_content = str(metrics_data)
        
        # Return PlainTextResponse with proper headers
        return PlainTextResponse(
            content=metrics_content,
            status_code=200,
            headers={
                "Content-Type": CONTENT_TYPE_LATEST,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Content-Encoding": "identity"
            }
        )
    except Exception as e:
        # Return error response for debugging
        error_content = f"# Error generating metrics: {str(e)}\n"
        return PlainTextResponse(
            content=error_content,
            status_code=500,
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "Cache-Control": "no-cache"
            }
        )


class BusinessMetricsCollector:
    """Collect business-specific metrics."""
    
    def __init__(self):
        self.last_collection_time = time.time()
    
    async def collect_business_metrics(self):
        """Collect business metrics from database."""
        from app.db.session import get_session
        from sqlalchemy import text
        
        async with get_session() as session:
            try:
                # Collect active rentals
                result = await session.execute(
                    text("SELECT COUNT(*) FROM rentals WHERE status = 'ACTIVE'")
                )
                active_rental_count = result.scalar() or 0
                metrics_collector.update_active_rentals(active_rental_count)
                
                # Collect customer counts by type
                result = await session.execute(
                    text("SELECT customer_type, COUNT(*) FROM customers GROUP BY customer_type")
                )
                for row in result.fetchall():
                    customer_type, count = row
                    metrics_collector.update_customer_count(customer_type, count)
                
                # Collect inventory counts
                result = await session.execute(
                    text("""
                    SELECT 
                        CASE WHEN is_available THEN 'available' ELSE 'unavailable' END as status,
                        COALESCE(c.name, 'uncategorized') as category,
                        COUNT(*) as count
                    FROM inventory_items i
                    LEFT JOIN categories c ON i.category_id = c.id
                    WHERE i.is_active = 1
                    GROUP BY status, category
                    """)
                )
                for row in result.fetchall():
                    status, category, count = row
                    metrics_collector.update_inventory_count(status, category, count)
                
                # Collect revenue metrics
                result = await session.execute(
                    text("""
                    SELECT 
                        transaction_type,
                        SUM(total_amount) as total_revenue
                    FROM transactions 
                    WHERE transaction_date >= date('now', '-30 days')
                    GROUP BY transaction_type
                    """)
                )
                for row in result.fetchall():
                    transaction_type, total_revenue = row
                    metrics_collector.record_revenue(
                        float(total_revenue), "USD", transaction_type
                    )
                
            except Exception as e:
                metrics_collector.record_error(
                    error_type="database_metrics_collection",
                    module="business_metrics"
                )
                print(f"Error collecting business metrics: {e}")


# Global business metrics collector
business_metrics_collector = BusinessMetricsCollector()


class SystemMetricsCollector:
    """Collect system-level metrics."""
    
    def collect_system_metrics(self):
        """Collect system metrics."""
        import psutil
        import os
        
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            metrics_collector.update_memory_usage("used", memory.used)
            metrics_collector.update_memory_usage("available", memory.available)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics_collector.update_cpu_usage(cpu_percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics_collector.update_disk_usage("/", disk.used)
            
        except ImportError:
            # psutil not available - skip system metrics
            pass
        except Exception as e:
            metrics_collector.record_error(
                error_type="system_metrics_collection",
                module="system_metrics"
            )


# Global system metrics collector
system_metrics_collector = SystemMetricsCollector()


# Metrics collection scheduler
async def collect_all_metrics():
    """Collect all metrics periodically."""
    
    # Collect business metrics
    await business_metrics_collector.collect_business_metrics()
    
    # Collect system metrics
    system_metrics_collector.collect_system_metrics()
    
    # Update cache metrics if Redis is enabled
    if settings.REDIS_ENABLED:
        from app.core.cache import cache_manager
        try:
            cache_stats = await cache_manager.get_health()
            if cache_stats.get("connected"):
                # Update cache size metrics
                memory_usage = cache_stats.get("memory_usage", "0B")
                # Parse memory usage (simplified)
                if memory_usage.endswith("M"):
                    size_mb = float(memory_usage[:-1])
                    size_bytes = int(size_mb * 1024 * 1024)
                    metrics_collector.update_cache_size("redis", size_bytes)
                
        except Exception as e:
            metrics_collector.record_error(
                error_type="cache_metrics_collection",
                module="cache_metrics"
            )


# Utility functions
def get_metrics_summary() -> Dict[str, Any]:
    """Get a summary of current metrics."""
    return {
        "requests_total": request_count._value.sum(),
        "errors_total": error_count._value.sum(),
        "active_rentals": active_rentals._value.get(),
        "cache_hits": cache_hits._value.sum(),
        "cache_misses": cache_misses._value.sum(),
        "collection_time": datetime.now().isoformat()
    }


# Export main components
__all__ = [
    "metrics_collector",
    "PrometheusMiddleware",
    "get_prometheus_metrics",
    "collect_all_metrics",
    "get_metrics_summary"
]