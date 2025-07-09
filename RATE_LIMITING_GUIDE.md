# Rate Limiting Configuration Guide

## Overview

This guide explains the rate limiting implementation in the Rental Management System API and how to configure it to avoid hitting rate limits unintentionally.

## Problem Solved

The system was hitting rate limits (100 requests/minute) due to automated monitoring and health check requests from:
- Docker health checks (every 30 seconds)
- Prometheus metrics scraping (every 15 seconds)
- Multiple monitoring services making frequent requests

## Solution Implemented

### 1. **Exempt Monitoring Endpoints**

The following endpoints are now exempt from rate limiting:
- `/health` - Health check endpoint
- `/metrics` - JSON metrics endpoint
- `/prometheus` - Prometheus metrics endpoint
- `/api-status` - API status endpoint
- `/api-validation-metrics` - Validation metrics
- `/api-documentation-info` - Documentation info
- `/docs`, `/redoc`, `/openapi.json` - API documentation

### 2. **Intelligent Request Detection**

The rate limiter now identifies and exempts:

#### Monitoring User Agents
- prometheus
- grafana
- alertmanager
- docker
- kube-probe
- blackbox_exporter
- node_exporter
- cadvisor

#### Internal Network Requests
- Docker internal networks (172.16.0.0/12)
- Docker swarm networks (10.0.0.0/8)
- Localhost (127.0.0.1)

### 3. **Tiered Rate Limits**

Different rate limits for different user types:
- **Public**: 100 requests/minute (default)
- **Authenticated**: 300 requests/minute
- **Premium**: 1000 requests/minute
- **Internal/Monitoring**: Unlimited

### 4. **Custom Path Limits**

Stricter limits for sensitive endpoints:
- `/api/v1/auth/login`: 20 requests/minute
- `/api/v1/auth/register`: 10 requests/minute
- `/api/v1/auth/reset-password`: 5 requests/minute

### 5. **Reduced Monitoring Frequencies**

Updated intervals to reduce request load:
- Docker health checks: 30s → 2 minutes
- Prometheus scraping: 15s → 60 seconds
- Prometheus health checks: 30s → 2 minutes

## Configuration

### Rate Limit Configuration File

The configuration is centralized in `/app/core/rate_limit_config.py`:

```python
from app.core.rate_limit_config import RateLimitConfig

# Check if a path is exempt
is_exempt = RateLimitConfig.is_exempt_path("/health")

# Get rate limit for a tier
limit = RateLimitConfig.get_rate_limit("/api/v1/users", RateLimitTier.AUTHENTICATED)
```

### Adding New Exemptions

1. **Exempt a new path**:
   ```python
   # In rate_limit_config.py
   EXEMPT_PATHS = {
       "/health",
       "/metrics",
       "/your-new-endpoint",  # Add here
   }
   ```

2. **Exempt a new monitoring tool**:
   ```python
   MONITORING_USER_AGENTS = {
       "prometheus",
       "grafana",
       "your-monitoring-tool",  # Add here
   }
   ```

3. **Add custom path limit**:
   ```python
   CUSTOM_PATH_LIMITS = {
       "/api/v1/auth/login": 20,
       "/your/sensitive/endpoint": 10,  # Add here
   }
   ```

## Monitoring Your Rate Limit Status

### Check Rate Limit Status

Visit the rate limit status endpoint to see your current status:

```bash
curl http://localhost:8000/api/v1/system/rate-limit-status
```

Response:
```json
{
  "request_info": {
    "client_ip": "172.20.0.1",
    "user_agent": "curl/7.64.1",
    "path": "/api/v1/system/rate-limit-status",
    "is_exempt": false
  },
  "configuration": {
    "tier_limits": {
      "public": 100,
      "authenticated": 300,
      "premium": 1000,
      "internal": null,
      "monitoring": null
    },
    "exempt_paths": ["/health", "/metrics", ...],
    "custom_path_limits": {...},
    "monitoring_agents": ["prometheus", "grafana", ...],
    "exempt_ip_ranges": ["172.16.0.0/12", ...]
  },
  "your_status": {
    "would_be_rate_limited": true,
    "rate_limit": 100,
    "reason_for_exemption": null
  }
}
```

### Rate Limit Headers

All responses include rate limit headers:
- `X-RateLimit-Limit`: Your rate limit
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## Best Practices

1. **Use Authentication**: Authenticated users get 3x higher rate limits
2. **Batch Requests**: Combine multiple operations when possible
3. **Cache Responses**: Use client-side caching for static data
4. **Monitor Headers**: Watch the rate limit headers to avoid hitting limits
5. **Use Webhooks**: For monitoring, consider webhooks instead of polling

## Troubleshooting

### Still Hitting Rate Limits?

1. **Check your client IP**:
   ```bash
   curl http://localhost:8000/api/v1/system/rate-limit-status
   ```

2. **Verify exemptions are working**:
   - Check `is_exempt` in the response
   - Verify `reason_for_exemption`

3. **Review Docker logs**:
   ```bash
   docker-compose logs rental-api | grep "rate limit"
   ```

4. **Common issues**:
   - Using external IP instead of Docker network
   - Missing or incorrect User-Agent header
   - Accessing non-exempt endpoints

### Adjusting Limits

To adjust rate limits, modify `/app/core/rate_limit_config.py`:

```python
TIER_LIMITS = {
    RateLimitTier.PUBLIC: 200,  # Increase public limit
    RateLimitTier.AUTHENTICATED: 500,  # Increase auth limit
}
```

Then restart the application:
```bash
docker-compose restart rental-api
```

## Docker Compose Optimizations

The `docker-compose.yml` has been optimized with:
- 2-minute health check intervals (was 30s)
- Proper health check endpoints
- Network isolation for monitoring services

## Prometheus Configuration

The `prometheus.yml` has been updated with:
- 60-second scrape intervals (was 15s)
- 2-minute health check intervals (was 30s)
- Optimized job configurations

## Summary

With these changes, monitoring and health check requests no longer count against your rate limit, allowing you to use the full 100 requests/minute for actual API calls. The system intelligently identifies and exempts monitoring traffic while maintaining security for public endpoints.