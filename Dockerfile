# Build stage
FROM python:3.10-slim AS builder

ENV POETRY_VERSION=1.8.2 \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    DJANGO_SETTINGS_MODULE="manager.settings"

RUN apt-get update && apt-get install -y \
    curl gcc python3-dev bash coreutils openssl && \
    pip install "poetry==$POETRY_VERSION" && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --only main --no-interaction --no-ansi

# Runtime stage
FROM python:3.10-slim AS production

RUN apt-get update && apt-get install -y \
    dumb-init cron libsqlite3-0 && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home appuser && \
    mkdir -p /app/manager/data /app/backups && \
    chown -R appuser:appuser /app


RUN mkdir -p /var/log/cron && \
    touch /var/log/cron/cron.log && \
    chown -R appuser:appuser /var/log/cron

USER appuser
WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --chown=appuser:appuser manager manager
COPY --chown=appuser:appuser static static
COPY --chown=appuser:appuser --chmod=755 entrypoint.sh backups/backup_db.sh ./

ENV PATH="/app/.venv/bin:$PATH" \
    SQLITE_DB_PATH="/app/manager/data/db.sqlite3" \
    SQLITE_TIMEOUT=60 \
    SQLITE_MMAP_SIZE=268435456 \
    SQLITE_JOURNAL_MODE=WAL

RUN python manager/manage.py collectstatic --noinput --clear

EXPOSE 8000
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["./entrypoint.sh"]
