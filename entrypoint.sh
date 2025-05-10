#!/bin/sh
set -eo pipefail

export DJANGO_SETTINGS_MODULE="manager.settings"

# SQLite database initialization
SQLITE_DB_DIR="/app/manager/data"
SQLITE_DB_FILE="${SQLITE_DB_DIR}/db.sqlite3"

# Create directory with proper permissions
mkdir -p "${SQLITE_DB_DIR}"
chmod 755 "${SQLITE_DB_DIR}"

# Initialize database if not exists
if [ ! -f "${SQLITE_DB_FILE}" ]; then
  echo "Initializing SQLite database..."
  touch "${SQLITE_DB_FILE}"
  chmod 664 "${SQLITE_DB_FILE}"
  sqlite3 "${SQLITE_DB_FILE}" "PRAGMA journal_mode=WAL;"
fi

# Apply database migrations
python manager/manage.py makemigrations core users --noinput
python manager/manage.py migrate --noinput

# Set ownership for SQLite database
chown appuser:appuser "${SQLITE_DB_DIR}" "${SQLITE_DB_FILE}"

# Collect static files
python manager/manage.py collectstatic --noinput --clear

# Verify directory permissions
find /app/manager -type d -exec chmod 755 {} \;
find /app/manager -type f -exec chmod 644 {} \;

exec "$@"
