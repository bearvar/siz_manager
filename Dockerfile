FROM python:3.10-slim

# Container metadata
LABEL org.opencontainers.image.title="SIZ Manager"
LABEL org.opencontainers.image.description="Django application for safety equipment management"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Your Organization <support@example.com>"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.8.2
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_RETRIES=5

# Install runtime and build dependencies
RUN apt-get update && apt-get install -y \
    curl dumb-init \
    gcc libpq-dev python3-dev openssl && \
    pip install "poetry==$POETRY_VERSION" && \
    rm -rf /var/lib/apt/lists/*

# Create initialization script and directories
COPY --chmod=+x entrypoint.sh /app/entrypoint.sh
RUN mkdir -p /app/manager/data && \
    chmod 755 /app/manager/data

# Set work directory and copy project files
WORKDIR /app
COPY pyproject.toml poetry.lock /app/

# Install python-dotenv and ensure .env exists
RUN pip install python-dotenv && \
    (test -f .env || (echo "SECRET_KEY=temp-insecure-key-$(openssl rand -hex 32)" > .env && \
    echo "DJANGO_DEBUG=False" >> .env && \
    echo "WARNING: Temporary configuration generated - update .env for production!"))

# Install core numerical packages first with pip
RUN pip install --retries 5 --trusted-host pypi.python.org \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org \
    numpy==1.26.4 pandas==2.2.1

# Install project dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-cache

# Copy application code
COPY manager /app/manager
COPY static /app/static

# Create and collect static files with proper permissions
RUN mkdir -p /app/manager/staticfiles && \
    chmod -R 755 /app/manager/staticfiles && \
    python manager/manage.py collectstatic --noinput --clear

# Expose port and run Gunicorn
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--pythonpath", "manager", "manager.wsgi:application"]
