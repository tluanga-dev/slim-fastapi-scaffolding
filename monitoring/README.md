# Rental Management System - Monitoring Setup

This directory contains monitoring and observability configuration for the Rental Management System.

## Components

### Prometheus
- **Port**: 9090
- **Purpose**: Metrics collection and alerting
- **Configuration**: `prometheus/prometheus.yml`
- **Alerts**: `prometheus/rules/rental-alerts.yml`

### Grafana
- **Port**: 3001
- **Purpose**: Visualization and dashboards
- **Default Login**: admin/admin123
- **Dashboards**: 
  - System Overview: `grafana/dashboards/rental-system-overview.json`
  - Performance Dashboard: `grafana/dashboards/performance-dashboard.json`

### Redis
- **Port**: 6379
- **Purpose**: Caching and session storage
- **Configuration**: Optimized for performance monitoring

### Alertmanager
- **Port**: 9093
- **Purpose**: Alert routing and notification
- **Configuration**: `alertmanager/alertmanager.yml`

## Quick Start

### 1. Start Monitoring Stack

```bash
# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Check services status
docker-compose -f docker-compose.monitoring.yml ps

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f grafana
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 3. Configure Application

Update your application's `.env` file:

```bash
# Enable Redis caching
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0

# Enable metrics collection
METRICS_ENABLED=true
METRICS_PORT=9090
```

## Dashboards

### System Overview Dashboard
- System health status
- Request rate and error rate
- Active rentals and business metrics
- Database and cache performance

### Performance Dashboard
- Request throughput and latency
- Database query performance
- System resource usage (CPU, memory, disk)
- Cache hit rates and error breakdown

## Metrics Available

### Application Metrics
- `rental_management_requests_total` - Total HTTP requests
- `rental_management_request_duration_seconds` - Request duration
- `rental_management_errors_total` - Total errors
- `rental_management_active_rentals` - Active rentals count

### Database Metrics
- `rental_management_db_connections` - Database connections
- `rental_management_db_query_duration_seconds` - Query duration
- `rental_management_db_queries_total` - Total queries

### Cache Metrics
- `rental_management_cache_hits_total` - Cache hits
- `rental_management_cache_misses_total` - Cache misses
- `rental_management_cache_size_bytes` - Cache size

### System Metrics
- `rental_management_memory_usage_bytes` - Memory usage
- `rental_management_cpu_usage_percent` - CPU usage
- `rental_management_disk_usage_bytes` - Disk usage

## Alerts

### Critical Alerts
- **ServiceDown**: Service is not responding
- **HighErrorRate**: Error rate > 0.1 errors/second

### Warning Alerts
- **HighResponseTime**: 95th percentile > 2 seconds
- **HighMemoryUsage**: Memory usage > 90%
- **HighCPUUsage**: CPU usage > 80%
- **LowCacheHitRate**: Cache hit rate < 50%
- **DatabaseConnectionIssues**: Connection usage > 80%
- **TooManySlowRequests**: Slow request rate > 0.05/second

## Customization

### Adding New Metrics

1. **In Application Code**:
```python
from app.core.prometheus_metrics import metrics_collector

# Record custom metric
metrics_collector.record_custom_metric("metric_name", value)
```

2. **In Prometheus Config**:
```yaml
- job_name: 'custom-metrics'
  static_configs:
    - targets: ['your-service:port']
```

### Adding New Dashboards

1. Create dashboard JSON in `grafana/dashboards/`
2. Restart Grafana or wait for auto-reload
3. Dashboard will appear in Grafana UI

### Modifying Alerts

1. Edit `prometheus/rules/rental-alerts.yml`
2. Restart Prometheus to reload rules
3. Configure notification channels in Alertmanager

## Troubleshooting

### Common Issues

#### Grafana Can't Connect to Prometheus
```bash
# Check Prometheus is running
curl http://localhost:9090/api/v1/query?query=up

# Check network connectivity
docker-compose -f docker-compose.monitoring.yml exec grafana ping prometheus
```

#### No Metrics from Application
```bash
# Check application metrics endpoint
curl http://localhost:8000/prometheus

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

#### Redis Connection Issues
```bash
# Check Redis is running
docker-compose -f docker-compose.monitoring.yml exec redis redis-cli ping

# Check application can connect
curl http://localhost:8000/health
```

### Logs
```bash
# View all logs
docker-compose -f docker-compose.monitoring.yml logs

# View specific service logs
docker-compose -f docker-compose.monitoring.yml logs prometheus
docker-compose -f docker-compose.monitoring.yml logs grafana
docker-compose -f docker-compose.monitoring.yml logs redis
```

## Production Considerations

### Security
- Change default passwords
- Enable authentication
- Use TLS/SSL certificates
- Restrict network access

### Performance
- Adjust scrape intervals
- Configure retention policies
- Optimize dashboard queries
- Use recording rules for expensive queries

### Backup
- Backup Grafana dashboards
- Backup Prometheus data
- Backup alert configurations

### Scaling
- Use Prometheus federation
- Implement horizontal scaling
- Consider external storage
- Use load balancers

## Integration with CI/CD

### Automated Deployment
```yaml
# .github/workflows/monitoring.yml
name: Deploy Monitoring
on:
  push:
    branches: [main]
    paths: ['monitoring/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy monitoring stack
        run: |
          docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

### Health Checks
```bash
# Add to your deployment script
curl -f http://localhost:9090/-/healthy || exit 1
curl -f http://localhost:3001/api/health || exit 1
```

## Support

For issues and questions:
- Check logs first
- Review Prometheus targets
- Verify network connectivity
- Consult official documentation:
  - [Prometheus](https://prometheus.io/docs/)
  - [Grafana](https://grafana.com/docs/)
  - [Redis](https://redis.io/documentation)