#!/bin/sh
set -e

# Wait for database availability (only needed if using network-dependent DB)
# while ! nc -z $DB_HOST $DB_PORT; do
#   echo "Waiting for database..."
#   sleep 2
# done

# Apply database migrations
python manager/manage.py migrate --noinput

# Create static files directory and collect static files
mkdir -p manager/staticfiles
python manager/manage.py collectstatic --noinput

# Create cache directory
mkdir -p manager/data

exec "$@"
