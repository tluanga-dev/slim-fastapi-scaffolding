# Docker Setup Guide - Rental Management System

This guide covers running the Rental Management System with Docker, including Redis for caching and optional monitoring services.

## Quick Start

### 1. Prerequisites
- Docker Desktop installed (includes Docker and Docker Compose)
- Git installed
- 4GB+ RAM available

### 2. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd rental-backend

# Copy environment file
cp .env.example .env

# Update .env with your settings (optional)
nano .env
```

### 3. Run with Docker Compose

#### Option A: Basic Setup (App + Redis)
```bash
# Start the application and Redis
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option B: Full Stack with Monitoring
```bash
# Start everything including monitoring
docker-compose -f docker-compose.full.yml up -d

# Check all services
docker-compose -f docker-compose.full.yml ps
```

## 📋 Available Docker Compose Files

### 1. **docker-compose.yml** (Basic Development)
- ✅ Rental Management API
- ✅ Redis Cache
- ✅ SQLite Database
- Perfect for development and testing

### 2. **docker-compose.full.yml** (Full Stack)
- ✅ Rental Management API
- ✅ Redis Cache
- ✅ Prometheus Monitoring
- ✅ Grafana Dashboards
- ✅ Alertmanager
- ✅ Node Exporter
- ✅ Redis Exporter
- ✅ cAdvisor
- ✅ Nginx (optional)
- Complete production-ready stack

## 🚀 Service Endpoints

### Basic Setup
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Redis**: localhost:6379

### Full Stack Setup
- **API**: http://localhost:8000
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **cAdvisor**: http://localhost:8080

## 🔧 Common Docker Commands

### Starting Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d rental-api

# Start with build
docker-compose up -d --build

# Start and follow logs
docker-compose up
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop rental-api
```

### Viewing Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs rental-api

# Follow logs
docker-compose logs -f rental-api

# Last 100 lines
docker-compose logs --tail=100 rental-api
```

### Executing Commands
```bash
# Run database migrations
docker-compose exec rental-api alembic upgrade head

# Access container shell
docker-compose exec rental-api /bin/sh

# Run tests
docker-compose exec rental-api pytest

# Create admin user
docker-compose exec rental-api python scripts/create_admin.py
```

## 📝 Environment Configuration

### Essential Variables
```bash
# Application
ENVIRONMENT=development
DEBUG=true

# Database (SQLite for development)
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Redis
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here
```

### Production Variables
```bash
# Change these for production
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-secure-key>

# Use PostgreSQL for production
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/rental_db
```

## 🏗️ Building and Deployment

### Building the Image
```bash
# Build the Docker image
docker build -t rental-management:latest .

# Build with no cache
docker build --no-cache -t rental-management:latest .

# Tag for registry
docker tag rental-management:latest your-registry/rental-management:latest
```

### Running Without Compose
```bash
# Run Redis
docker run -d --name rental-redis -p 6379:6379 redis:7-alpine

# Run the application
docker run -d \
  --name rental-api \
  -p 8000:8000 \
  -e REDIS_URL=redis://rental-redis:6379/0 \
  -e DATABASE_URL=sqlite+aiosqlite:///./app.db \
  --link rental-redis:redis \
  rental-management:latest
```

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs rental-api

# Check container status
docker ps -a

# Inspect container
docker inspect rental-api
```

### Database Issues
```bash
# Reset database
docker-compose exec rental-api alembic downgrade base
docker-compose exec rental-api alembic upgrade head

# Access database
docker-compose exec rental-api sqlite3 /app/app.db
```

### Redis Connection Issues
```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis

# Connect to Redis CLI
docker-compose exec redis redis-cli
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Limit resources in docker-compose.yml
services:
  rental-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 📊 Monitoring Setup

### Accessing Monitoring Tools

1. **Grafana** (http://localhost:3001)
   ```
   Username: admin
   Password: admin123
   ```

2. **Prometheus** (http://localhost:9090)
   - Query metrics
   - Check targets
   - View alerts

3. **View Metrics**
   ```bash
   # Application metrics
   curl http://localhost:8000/prometheus
   
   # System metrics
   curl http://localhost:9100/metrics
   ```

### Adding Custom Alerts
Edit `monitoring/prometheus/rules/rental-alerts.yml` and restart Prometheus.

## 🔒 Security Considerations

### Production Checklist
- [ ] Change default passwords
- [ ] Use secrets management
- [ ] Enable HTTPS/TLS
- [ ] Restrict port exposure
- [ ] Use non-root user
- [ ] Enable security scanning

### Secure Environment
```bash
# Use Docker secrets
echo "my-secret-key" | docker secret create rental_secret_key -

# Use in compose file
secrets:
  rental_secret_key:
    external: true
```

## 🚀 Scaling

### Horizontal Scaling
```bash
# Scale the API service
docker-compose up -d --scale rental-api=3

# With load balancer (nginx)
docker-compose -f docker-compose.full.yml up -d
```

### Resource Limits
```yaml
services:
  rental-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 📚 Additional Resources

### Useful Commands
```bash
# Remove all containers
docker-compose down --rmi all

# Clean up everything
docker system prune -a

# View disk usage
docker system df

# Export/Import data
docker-compose exec rental-api python scripts/export_data.py
docker-compose exec rental-api python scripts/import_data.py
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Redis health
docker-compose exec redis redis-cli ping

# Overall status
docker-compose ps
```

## 💡 Tips

1. **Development**: Use `docker-compose.yml` for quick development
2. **Testing**: Add `--build` flag to rebuild after code changes
3. **Production**: Use `docker-compose.full.yml` with monitoring
4. **Debugging**: Use `docker-compose logs -f` to follow logs
5. **Performance**: Monitor with Grafana dashboards

## 🆘 Getting Help

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Verify environment: `docker-compose config`
3. Test connectivity: `docker network ls`
4. Review documentation: See main README.md

---

Ready to start? Run `docker-compose up -d` and access the API at http://localhost:8000/docs!