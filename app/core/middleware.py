"""
Middleware for performance optimization and monitoring.

This module provides middleware for caching, performance monitoring, and request tracking.
"""

import time
import uuid
from typing import Callable, Dict, Any, Optional, List
from contextlib import asynccontextmanager
import json
import hashlib

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.cache import cache_manager, CacheConfig


class CacheMiddleware(BaseHTTPMiddleware):
    """HTTP caching middleware for GET requests."""
    
    def __init__(self, app: ASGIApp, cache_ttl: int = CacheConfig.DEFAULT_TTL):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cacheable_methods = {"GET"}
        self.cache_headers = {
            "Cache-Control": f"public, max-age={cache_ttl}",
            "X-Cache": "HIT"
        }
    
    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached."""
        # Only cache GET requests
        if request.method not in self.cacheable_methods:
            return False
        
        # Skip caching for authenticated requests with sensitive data
        if "authorization" in request.headers:
            return False
        
        # Skip caching for certain paths
        skip_paths = ["/health", "/metrics", "/prometheus", "/docs", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return False
        
        # Skip caching if query parameters indicate dynamic content
        skip_params = ["nocache", "timestamp", "random"]
        if any(param in request.query_params for param in skip_params):
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        # Include method, path, and query parameters
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # Add user context if available (for user-specific caching)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            key_parts.append(f"user:{user_id}")
        
        key_string = "|".join(key_parts)
        return f"http_cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching logic."""
        if not cache_manager.connected or not self._should_cache_request(request):
            return await call_next(request)
        
        cache_key = self._generate_cache_key(request)
        
        # Try to get cached response
        cached_response = await cache_manager.get(cache_key)
        if cached_response:
            # Return cached response
            response = JSONResponse(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"]
            )
            response.headers.update(self.cache_headers)
            response.headers["X-Cache-Key"] = cache_key
            return response
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200 and hasattr(response, 'body'):
            try:
                # Extract response data
                response_data = {
                    "content": json.loads(response.body.decode()),
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
                
                # Cache the response
                await cache_manager.set(cache_key, response_data, self.cache_ttl)
                
                # Add cache headers
                response.headers["X-Cache"] = "MISS"
                response.headers["X-Cache-Key"] = cache_key
                
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Skip caching if response is not JSON
                pass
        
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and request tracking."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.slow_request_threshold = 1.0  # seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Track request start time
        start_time = time.time()
        
        # Add request ID to logs context
        request.state.start_time = start_time
        
        # Process request
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            await self._log_slow_request(request, response, duration)
        
        # Update metrics
        await self._update_metrics(request, response, duration)
        
        return response
    
    async def _log_slow_request(self, request: Request, response: Response, duration: float):
        """Log slow request for analysis."""
        slow_request_data = {
            "request_id": request.state.request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration": duration,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": time.time()
        }
        
        # Store in cache for monitoring dashboard
        cache_key = f"slow_requests:{request.state.request_id}"
        await cache_manager.set(cache_key, slow_request_data, CacheConfig.DAILY_TTL)
    
    async def _update_metrics(self, request: Request, response: Response, duration: float):
        """Update performance metrics."""
        # Increment request counters
        await cache_manager.increment("metrics:requests:total", 1)
        await cache_manager.increment(f"metrics:requests:status:{response.status_code}", 1)
        await cache_manager.increment(f"metrics:requests:method:{request.method}", 1)
        
        # Track response times
        response_time_key = f"metrics:response_times:{int(time.time() // 60)}"  # Per minute
        await cache_manager.set(response_time_key, duration, CacheConfig.LONG_TTL)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.rate_limit_window = 60  # seconds
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from request state
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        client_id = self._get_client_identifier(request)
        rate_limit_key = f"rate_limit:{client_id}"
        
        # Check rate limit
        current_requests = await cache_manager.increment(
            rate_limit_key, 1, self.rate_limit_window
        )
        
        if current_requests > self.requests_per_minute:
            # Rate limit exceeded
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": self.rate_limit_window
                },
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + self.rate_limit_window)),
                    "Retry-After": str(self.rate_limit_window)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - current_requests)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.rate_limit_window))
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression middleware."""
    
    def __init__(self, app: ASGIApp, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compressible_types = {
            "application/json",
            "application/javascript",
            "text/html",
            "text/css",
            "text/plain",
            "text/xml"
        }
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """Determine if response should be compressed."""
        # Skip compression for metrics endpoints
        skip_compression_paths = ["/metrics", "/prometheus", "/health"]
        if any(request.url.path.startswith(path) for path in skip_compression_paths):
            return False
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in self.compressible_types):
            return False
        
        # Check content length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply compression to response."""
        response = await call_next(request)
        
        # Note: In production, you would implement actual gzip compression here
        # This is a placeholder for compression logic
        if self._should_compress(request, response):
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Vary"] = "Accept-Encoding"
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


# Middleware configuration
def setup_middleware(app):
    """Setup all middleware for the application."""
    
    # Add middleware in reverse order (last added = first executed)
    
    # Security headers (outermost)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Performance monitoring
    app.add_middleware(PerformanceMonitoringMiddleware)
    
    # Rate limiting
    if settings.REDIS_ENABLED:
        app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    
    # Compression
    app.add_middleware(CompressionMiddleware)
    
    # HTTP caching (innermost - closest to business logic)
    if settings.REDIS_ENABLED:
        app.add_middleware(CacheMiddleware, cache_ttl=settings.CACHE_TTL)


# Monitoring utilities
async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics from cache."""
    if not cache_manager.connected:
        return {"status": "cache_disabled"}
    
    metrics = {}
    
    # Get basic counters
    metrics["requests_total"] = await cache_manager.get("metrics:requests:total", 0)
    
    # Get status code distribution
    status_codes = {}
    for code in [200, 201, 400, 401, 403, 404, 422, 500]:
        count = await cache_manager.get(f"metrics:requests:status:{code}", 0)
        if count > 0:
            status_codes[str(code)] = count
    metrics["status_codes"] = status_codes
    
    # Get method distribution
    methods = {}
    for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
        count = await cache_manager.get(f"metrics:requests:method:{method}", 0)
        if count > 0:
            methods[method] = count
    metrics["methods"] = methods
    
    return metrics


async def get_slow_requests(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent slow requests."""
    if not cache_manager.connected:
        return []
    
    # Get slow request keys
    slow_request_keys = await cache_manager.redis.keys("slow_requests:*")
    
    # Get slow request data
    slow_requests = []
    for key in slow_request_keys[-limit:]:  # Get recent ones
        request_data = await cache_manager.get(key)
        if request_data:
            slow_requests.append(request_data)
    
    # Sort by duration (slowest first)
    slow_requests.sort(key=lambda x: x.get("duration", 0), reverse=True)
    
    return slow_requests