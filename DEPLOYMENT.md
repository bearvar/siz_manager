# SIZ Manager Deployment Guide

## Production Deployment (Docker)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.20+

### First-time Setup
```bash
# Build and start containers
docker compose build
docker compose up -d

# Verify container status
docker compose ps

# View logs
docker compose logs -f web
```

### Routine Maintenance
```bash
# Create database backup
docker compose exec web python manager/manage.py dumpdata --indent 2 > backup_$(date +%Y%m%d).json

# Update containers
docker compose build
docker compose down
docker compose up -d
```

## Docker Image Publishing
```bash
# Login to Docker Hub
docker login

# Tag and push image
docker tag siz_manager:latest yourusername/siz_manager:1.0.0
docker push yourusername/siz_manager:1.0.0
```

## Environment Configuration
Required `.env` file contents:
```ini
SECRET_KEY=your-secure-key-here
ALLOWED_HOSTS=localhost,web
CSRF_TRUSTED_ORIGINS=http://localhost
DEBUG=False
```

## Post-Deployment Verification
1. Check container health: `docker compose ps`
2. Test application endpoint: `curl -I http://localhost`
3. Verify static files: `ls -l staticfiles/`
4. Check logs: `docker compose logs web`

Note: The SQLite database will persist in the `./data` directory between deployments.
