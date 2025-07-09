# Rental Management System - Production Deployment Guide

This guide covers production deployment options for the Rental Management System API.

## Quick Start

### 1. Docker Compose (Recommended for Small-Medium Deployments)

```bash
# Clone repository
git clone <repository-url>
cd rental-backend

# Copy environment file and configure
cp .env.example .env
# Edit .env with your production values

# Generate secure secret key
openssl rand -hex 32

# Start services
docker-compose up -d

# Run database migrations
docker-compose exec rental-api alembic upgrade head

# Create admin user
docker-compose exec rental-api python scripts/create_admin.py
```

### 2. Kubernetes (Recommended for Large Deployments)

```bash
# Apply Kubernetes manifests
kubectl apply -f deployment/k8s/namespace.yaml
kubectl apply -f deployment/k8s/configmap.yaml
kubectl apply -f deployment/k8s/secret.yaml
kubectl apply -f deployment/k8s/pvc.yaml
kubectl apply -f deployment/k8s/deployment.yaml
kubectl apply -f deployment/k8s/service.yaml
kubectl apply -f deployment/k8s/ingress.yaml

# Check deployment status
kubectl get pods -n rental-management
```

## Prerequisites

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 50GB minimum for database and uploads
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Software Dependencies

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- OpenSSL (for SSL certificates)

## Environment Configuration

### Core Settings

```bash
# Application
APP_NAME="Rental Management System"
ENVIRONMENT=production
DEBUG=false

# Security (REQUIRED)
SECRET_KEY=your-super-secure-secret-key-here
ALGORITHM=HS256

# Database (Choose one)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rental_management
# DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/rental_management

# Redis Cache
REDIS_URL=redis://localhost:6379/0
```

### Security Configuration

```bash
# CORS (Configure for your domain)
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/fullchain.pem
SSL_KEY_PATH=/etc/ssl/private/privkey.pem
```

### External Services

```bash
# Email (Optional)
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Payment Gateway
STRIPE_PUBLIC_KEY=pk_live_your_stripe_public_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key

# File Storage (Production)
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
```

## Database Setup

### PostgreSQL (Recommended)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE rental_management;
CREATE USER rental_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE rental_management TO rental_user;
\q

# Configure connection
DATABASE_URL=postgresql+asyncpg://rental_user:secure_password@localhost:5432/rental_management
```

### MySQL (Alternative)

```bash
# Install MySQL
sudo apt update
sudo apt install mysql-server

# Create database and user
sudo mysql
CREATE DATABASE rental_management;
CREATE USER 'rental_user'@'%' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON rental_management.* TO 'rental_user'@'%';
FLUSH PRIVILEGES;
EXIT;

# Configure connection
DATABASE_URL=mysql+aiomysql://rental_user:secure_password@localhost:3306/rental_management
```

## SSL/TLS Configuration

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (add to crontab)
0 12 * * * /usr/bin/certbot renew --quiet
```

### Using Custom Certificates

```bash
# Copy certificates to appropriate locations
sudo cp fullchain.pem /etc/ssl/certs/
sudo cp privkey.pem /etc/ssl/private/
sudo chmod 644 /etc/ssl/certs/fullchain.pem
sudo chmod 600 /etc/ssl/private/privkey.pem
```

## Performance Optimization

### Application Settings

```bash
# Worker Configuration
WORKERS=4  # Number of CPU cores

# Database Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Cache Settings
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/rental-management
upstream rental_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;
    
    # Performance
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    
    location / {
        proxy_pass http://rental_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Logging

### Application Logs

```bash
# Configure logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/rental-management/app.log

# Log rotation
sudo nano /etc/logrotate.d/rental-management
```

### Health Monitoring

```bash
# Health check endpoint
curl https://yourdomain.com/health

# Prometheus metrics
curl https://yourdomain.com/metrics
```

### Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
```

## Backup and Recovery

### Automated Backups

```bash
# Database backup script
./scripts/backup.sh

# Schedule with cron
0 2 * * * /path/to/backup.sh
```

### Backup Verification

```bash
# Test backup restoration
./scripts/restore.sh backup_file.sql.gz
```

## Security Hardening

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### Application Security

```bash
# Security headers
SECURITY_HEADERS_ENABLED=true

# Rate limiting
RATE_LIMIT_ENABLED=true
MAX_LOGIN_ATTEMPTS=5

# Content Security Policy
CSP_ENABLED=true
```

## Scaling and High Availability

### Horizontal Scaling

```bash
# Multiple application instances
WORKERS=4
REPLICAS=3

# Load balancer configuration
# See nginx.conf for upstream configuration
```

### Database Scaling

```bash
# Read replicas
DATABASE_READ_URL=postgresql+asyncpg://user:pass@read-replica:5432/db
DATABASE_WRITE_URL=postgresql+asyncpg://user:pass@master:5432/db

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
docker-compose logs rental-api

# Verify environment variables
docker-compose exec rental-api env | grep -E "(DATABASE|SECRET)"

# Test database connection
docker-compose exec rental-api python -c "from app.db.session import engine; print('OK')"
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U rental_user -d rental_management

# Check connection limits
SELECT * FROM pg_stat_activity;
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor slow queries
tail -f /var/log/postgresql/postgresql-15-main.log

# Application metrics
curl https://yourdomain.com/metrics
```

### Debug Mode (Development Only)

```bash
# Enable debug mode
DEBUG=true
LOG_LEVEL=DEBUG
LOG_SQL_QUERIES=true

# Restart application
docker-compose restart rental-api
```

## Maintenance

### Regular Maintenance Tasks

```bash
# Weekly tasks
./scripts/cleanup_logs.sh
./scripts/optimize_database.sh

# Monthly tasks
./scripts/backup_verification.sh
./scripts/security_update.sh

# Quarterly tasks
./scripts/performance_review.sh
```

### Updates and Upgrades

```bash
# Update application
git pull origin main
docker-compose build rental-api
docker-compose up -d rental-api

# Database migrations
docker-compose exec rental-api alembic upgrade head

# Verify deployment
curl https://yourdomain.com/health
```

## Support and Monitoring

### Health Checks

- **Application**: `https://yourdomain.com/health`
- **Database**: Connection pool status
- **Cache**: Redis connectivity
- **External APIs**: Payment gateway, email service

### Monitoring Dashboards

- **Grafana**: `https://yourdomain.com:3000`
- **Prometheus**: `https://yourdomain.com:9090`
- **Application Logs**: Centralized logging solution

### Emergency Contacts

- **System Administrator**: admin@yourdomain.com
- **Database Administrator**: dba@yourdomain.com
- **Security Team**: security@yourdomain.com

## Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database created and configured
- [ ] Backup strategy implemented
- [ ] Monitoring setup
- [ ] Security hardening completed

### Post-Deployment

- [ ] Health checks passing
- [ ] SSL certificate valid
- [ ] Monitoring alerts configured
- [ ] Backup verification
- [ ] Performance baseline established
- [ ] Documentation updated

### Security Verification

- [ ] Secret keys rotated
- [ ] HTTPS enforced
- [ ] Rate limiting active
- [ ] Firewall configured
- [ ] Security headers enabled
- [ ] Vulnerability scan completed

---

For additional support, contact the development team or refer to the [API Documentation](./docs/README.md).