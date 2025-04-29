# Use Python 3.10 base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.8.2

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set work directory and copy project files
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN pip install python-dotenv
RUN test -f .env || (echo "SECRET_KEY=temp-key-please-regenerate" > .env && echo "WARNING: Temporary secret key generated - regenerate for production!")

# Install project dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy project files
COPY . /app

# Create required directories and collect static files
RUN mkdir -p manager/data && \
    mkdir -p manager/staticfiles && \
    python manager/manage.py collectstatic --noinput

# Expose port and run Gunicorn
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--pythonpath", "manager", "manager.wsgi:application"]
