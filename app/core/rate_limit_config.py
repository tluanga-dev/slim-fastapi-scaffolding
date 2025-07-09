"""
Rate limiting configuration and exemptions.

This module defines rate limiting rules and exemptions for different types of requests.
"""

from typing import Set, Dict, Any
from enum import Enum


class RateLimitTier(str, Enum):
    """Rate limit tiers for different types of clients."""
    PUBLIC = "public"  # Default rate limit for public API
    AUTHENTICATED = "authenticated"  # Higher limits for authenticated users
    PREMIUM = "premium"  # Even higher limits for premium users
    INTERNAL = "internal"  # No limits for internal services
    MONITORING = "monitoring"  # No limits for monitoring tools


class RateLimitConfig:
    """Rate limiting configuration."""
    
    # Rate limits per tier (requests per minute)
    TIER_LIMITS = {
        RateLimitTier.PUBLIC: 100,
        RateLimitTier.AUTHENTICATED: 300,
        RateLimitTier.PREMIUM: 1000,
        RateLimitTier.INTERNAL: None,  # No limit
        RateLimitTier.MONITORING: None,  # No limit
    }
    
    # Paths exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
        "/metrics",
        "/prometheus",
        "/api-status",
        "/api-validation-metrics", 
        "/api-documentation-info",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    # Paths with custom rate limits
    CUSTOM_PATH_LIMITS = {
        "/api/v1/auth/login": 20,  # Stricter limit for login attempts
        "/api/v1/auth/register": 10,  # Stricter limit for registration
        "/api/v1/auth/reset-password": 5,  # Very strict for password reset
    }
    
    # User agents that indicate monitoring tools
    MONITORING_USER_AGENTS = {
        "prometheus",
        "grafana", 
        "alertmanager",
        "docker",
        "kube-probe",
        "blackbox_exporter",
        "node_exporter",
        "cadvisor",
    }
    
    # IP ranges exempt from rate limiting (Docker internal networks)
    EXEMPT_IP_RANGES = [
        "172.16.0.0/12",  # Docker default bridge network
        "10.0.0.0/8",     # Docker swarm networks
        "127.0.0.1",      # Localhost
    ]
    
    @classmethod
    def get_rate_limit(cls, path: str, tier: RateLimitTier = RateLimitTier.PUBLIC) -> int:
        """Get rate limit for a specific path and tier."""
        # Check custom path limits first
        if path in cls.CUSTOM_PATH_LIMITS:
            return cls.CUSTOM_PATH_LIMITS[path]
        
        # Return tier limit
        limit = cls.TIER_LIMITS.get(tier, cls.TIER_LIMITS[RateLimitTier.PUBLIC])
        return limit if limit is not None else float('inf')
    
    @classmethod
    def is_exempt_path(cls, path: str) -> bool:
        """Check if a path is exempt from rate limiting."""
        return path in cls.EXEMPT_PATHS
    
    @classmethod
    def is_monitoring_agent(cls, user_agent: str) -> bool:
        """Check if user agent indicates a monitoring tool."""
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        return any(agent in user_agent_lower for agent in cls.MONITORING_USER_AGENTS)
    
    @classmethod
    def is_exempt_ip(cls, ip_address: str) -> bool:
        """Check if IP address is exempt from rate limiting."""
        if not ip_address:
            return False
        
        # Check exact matches
        if ip_address in ["127.0.0.1", "::1", "localhost"]:
            return True
        
        # Check IP ranges
        try:
            import ipaddress
            ip = ipaddress.ip_address(ip_address)
            
            for ip_range in cls.EXEMPT_IP_RANGES:
                if isinstance(ip_range, str) and "/" in ip_range:
                    network = ipaddress.ip_network(ip_range, strict=False)
                    if ip in network:
                        return True
                elif ip_address == ip_range:
                    return True
        except Exception:
            pass
        
        return False


# Export for easy access
RATE_LIMIT_CONFIG = RateLimitConfig()