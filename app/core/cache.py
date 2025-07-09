"""
Redis Cache Implementation for Rental Management System.

This module provides Redis-based caching with async support for improved performance.
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import asyncio
from functools import wraps

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    Redis = None
from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import CacheError


class CacheConfig:
    """Cache configuration and constants."""
    
    # Default TTL values (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    SHORT_TTL = 60     # 1 minute
    MEDIUM_TTL = 900   # 15 minutes
    LONG_TTL = 3600    # 1 hour
    DAILY_TTL = 86400  # 24 hours
    
    # Cache key prefixes
    CUSTOMER_PREFIX = "customer"
    INVENTORY_PREFIX = "inventory"
    RENTAL_PREFIX = "rental"
    ANALYTICS_PREFIX = "analytics"
    CONFIG_PREFIX = "config"
    SESSION_PREFIX = "session"
    
    # Cache patterns
    CUSTOMER_DETAIL = f"{CUSTOMER_PREFIX}:detail:{{id}}"
    CUSTOMER_LIST = f"{CUSTOMER_PREFIX}:list:{{filters}}"
    INVENTORY_ITEM = f"{INVENTORY_PREFIX}:item:{{id}}"
    INVENTORY_AVAILABILITY = f"{INVENTORY_PREFIX}:availability:{{id}}"
    ANALYTICS_DASHBOARD = f"{ANALYTICS_PREFIX}:dashboard:{{period}}"
    SYSTEM_CONFIG = f"{CONFIG_PREFIX}:system"


class CacheManager:
    """Async Redis cache manager with high-level operations."""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.connected = False
        
    async def connect(self):
        """Initialize Redis connection."""
        if not settings.REDIS_ENABLED or not REDIS_AVAILABLE:
            return
            
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            self.connected = True
            
        except Exception as e:
            self.connected = False
            print(f"Warning: Failed to connect to Redis: {str(e)}")
            # Don't raise error, just disable cache functionality
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.connected = False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if not self.connected:
            return default
            
        try:
            value = await self.redis.get(key)
            if value is None:
                return default
                
            # Try to deserialize JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value.encode('latin-1'))
                
        except Exception as e:
            # Log error but don't fail the application
            print(f"Cache get error for key {key}: {str(e)}")
            return default
    
    async def set(self, key: str, value: Any, ttl: int = CacheConfig.DEFAULT_TTL) -> bool:
        """Set value in cache with TTL."""
        if not self.connected:
            return False
            
        try:
            # Serialize value
            if isinstance(value, (dict, list, bool, int, float, str)):
                serialized = json.dumps(value, default=str)
            else:
                serialized = pickle.dumps(value).decode('latin-1')
            
            await self.redis.setex(key, ttl, serialized)
            return True
            
        except Exception as e:
            print(f"Cache set error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.connected:
            return False
            
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        if not self.connected:
            return 0
            
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error for pattern {pattern}: {str(e)}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.connected:
            return False
            
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1, ttl: int = CacheConfig.DEFAULT_TTL) -> int:
        """Increment a counter in cache."""
        if not self.connected:
            return 0
            
        try:
            result = await self.redis.incr(key, amount)
            await self.redis.expire(key, ttl)
            return result
        except Exception as e:
            print(f"Cache increment error for key {key}: {str(e)}")
            return 0
    
    async def get_or_set(self, key: str, callback, ttl: int = CacheConfig.DEFAULT_TTL) -> Any:
        """Get value from cache or set it using callback."""
        value = await self.get(key)
        if value is not None:
            return value
            
        # Call the callback to get fresh data
        if asyncio.iscoroutinefunction(callback):
            fresh_value = await callback()
        else:
            fresh_value = callback()
            
        await self.set(key, fresh_value, ttl)
        return fresh_value
    
    async def get_health(self) -> Dict[str, Any]:
        """Get cache health information."""
        if not self.connected:
            return {
                "status": "disconnected",
                "connected": False,
                "error": "Redis not connected"
            }
            
        try:
            info = await self.redis.info()
            return {
                "status": "healthy",
                "connected": True,
                "redis_version": info.get("redis_version"),
                "memory_usage": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "hit_ratio": self._calculate_hit_ratio(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
    
    def _calculate_hit_ratio(self, hits: int, misses: int) -> float:
        """Calculate cache hit ratio."""
        total = hits + misses
        return round(hits / total * 100, 2) if total > 0 else 0.0


# Global cache manager instance
cache_manager = CacheManager()


async def get_cache_manager() -> CacheManager:
    """Dependency to get cache manager."""
    return cache_manager


def cache_key_builder(*parts: str) -> str:
    """Build cache key from parts."""
    return ":".join(str(part) for part in parts if part)


def cache_result(
    key_pattern: str,
    ttl: int = CacheConfig.DEFAULT_TTL,
    skip_cache: bool = False
):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if skip_cache or not cache_manager.connected:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            
            # Build cache key
            try:
                cache_key = key_pattern.format(*args, **kwargs)
            except (KeyError, IndexError):
                # If key formatting fails, skip cache
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


class CacheService:
    """High-level cache service for domain-specific operations."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    # Customer caching
    async def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer from cache."""
        key = CacheConfig.CUSTOMER_DETAIL.format(id=customer_id)
        return await self.cache.get(key)
    
    async def set_customer(self, customer_id: str, customer_data: Dict, ttl: int = CacheConfig.MEDIUM_TTL):
        """Cache customer data."""
        key = CacheConfig.CUSTOMER_DETAIL.format(id=customer_id)
        await self.cache.set(key, customer_data, ttl)
    
    async def invalidate_customer(self, customer_id: str):
        """Invalidate customer cache."""
        pattern = f"{CacheConfig.CUSTOMER_PREFIX}:*{customer_id}*"
        await self.cache.delete_pattern(pattern)
    
    # Inventory caching
    async def get_inventory_item(self, item_id: str) -> Optional[Dict]:
        """Get inventory item from cache."""
        key = CacheConfig.INVENTORY_ITEM.format(id=item_id)
        return await self.cache.get(key)
    
    async def set_inventory_item(self, item_id: str, item_data: Dict, ttl: int = CacheConfig.MEDIUM_TTL):
        """Cache inventory item data."""
        key = CacheConfig.INVENTORY_ITEM.format(id=item_id)
        await self.cache.set(key, item_data, ttl)
    
    async def get_item_availability(self, item_id: str) -> Optional[Dict]:
        """Get item availability from cache."""
        key = CacheConfig.INVENTORY_AVAILABILITY.format(id=item_id)
        return await self.cache.get(key)
    
    async def set_item_availability(self, item_id: str, availability_data: Dict, ttl: int = CacheConfig.SHORT_TTL):
        """Cache item availability (short TTL for real-time data)."""
        key = CacheConfig.INVENTORY_AVAILABILITY.format(id=item_id)
        await self.cache.set(key, availability_data, ttl)
    
    async def invalidate_inventory_item(self, item_id: str):
        """Invalidate inventory item cache."""
        pattern = f"{CacheConfig.INVENTORY_PREFIX}:*{item_id}*"
        await self.cache.delete_pattern(pattern)
    
    # Analytics caching
    async def get_analytics_dashboard(self, period: str) -> Optional[Dict]:
        """Get analytics dashboard from cache."""
        key = CacheConfig.ANALYTICS_DASHBOARD.format(period=period)
        return await self.cache.get(key)
    
    async def set_analytics_dashboard(self, period: str, dashboard_data: Dict, ttl: int = CacheConfig.LONG_TTL):
        """Cache analytics dashboard data."""
        key = CacheConfig.ANALYTICS_DASHBOARD.format(period=period)
        await self.cache.set(key, dashboard_data, ttl)
    
    # Session caching
    async def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Get user session from cache."""
        key = cache_key_builder(CacheConfig.SESSION_PREFIX, user_id)
        return await self.cache.get(key)
    
    async def set_user_session(self, user_id: str, session_data: Dict, ttl: int = CacheConfig.LONG_TTL):
        """Cache user session data."""
        key = cache_key_builder(CacheConfig.SESSION_PREFIX, user_id)
        await self.cache.set(key, session_data, ttl)
    
    async def invalidate_user_session(self, user_id: str):
        """Invalidate user session cache."""
        key = cache_key_builder(CacheConfig.SESSION_PREFIX, user_id)
        await self.cache.delete(key)
    
    # Rate limiting support
    async def check_rate_limit(self, key: str, limit: int, window: int = 60) -> Dict[str, Any]:
        """Check rate limit for a key."""
        current_count = await self.cache.increment(key, 1, window)
        
        return {
            "allowed": current_count <= limit,
            "current_count": current_count,
            "limit": limit,
            "window": window,
            "remaining": max(0, limit - current_count)
        }


# Global cache service instance
cache_service = CacheService(cache_manager)


async def get_cache_service() -> CacheService:
    """Dependency to get cache service."""
    return cache_service


# Cache warmup utilities
async def warm_up_cache():
    """Warm up cache with frequently accessed data."""
    if not cache_manager.connected:
        return
    
    # This would typically load commonly accessed data
    # Implementation depends on specific business needs
    pass


# Cache monitoring utilities
async def get_cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache statistics."""
    if not cache_manager.connected:
        return {"status": "disabled"}
    
    health = await cache_manager.get_health()
    
    # Add custom metrics
    stats = {
        **health,
        "cache_prefixes": {
            "customer": len(await cache_manager.redis.keys(f"{CacheConfig.CUSTOMER_PREFIX}:*")),
            "inventory": len(await cache_manager.redis.keys(f"{CacheConfig.INVENTORY_PREFIX}:*")),
            "analytics": len(await cache_manager.redis.keys(f"{CacheConfig.ANALYTICS_PREFIX}:*")),
            "session": len(await cache_manager.redis.keys(f"{CacheConfig.SESSION_PREFIX}:*"))
        }
    }
    
    return stats