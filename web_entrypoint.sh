#!/bin/sh

set -e

echo "Waiting for database..."
uv run python manage.py wait_for_db

echo "Running migrations..."
uv run python manage.py makemigrations --noinput
uv run python manage.py migrate --noinput

echo "Collecting static files..."
uv run python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec uv run gunicorn crm_for_yasya.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 3
