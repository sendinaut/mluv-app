#!/bin/sh

set -e

echo "Waiting for database..."
uv run manage.py wait_for_db

echo "Applying database migrations..."
uv run manage.py migrate

echo "Collecting static files..."
uv run manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
exec uv run gunicorn crm_for_yasya.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --threads 3
