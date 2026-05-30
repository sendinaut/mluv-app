#!/bin/sh

set -e

echo "Waiting for database..."
uv run manage.py wait_for_db

echo "Starting worker..."
exec uv run manage.py qcluster
