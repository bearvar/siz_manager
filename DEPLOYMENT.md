# Deployment Guide

## Requirements
- Docker
- Docker Compose

## Setup Steps

1. Generate secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(f'SECRET_KEY={get_random_secret_key()}')" > .env
```

2. Build and start containers:
```bash
docker-compose up --build -d
```

3. Create admin user (after first launch):
```bash
docker-compose exec web python manager/manage.py createsuperuser
# Follow interactive prompts to set up admin credentials
```

4. Access the application at: http://localhost:80

## Environment Configuration
- Store production secrets in `.env` file
- Never commit `.env` to version control
- Update ALLOWED_HOSTS in `manager/manager/settings.py` for production
