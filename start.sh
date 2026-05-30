#!/bin/sh

set -e

uv run manage.py wait_for_db

echo "Running migrations..."
uv run manage.py migrate

uv run gunicorn crm_for_yasya.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 3
