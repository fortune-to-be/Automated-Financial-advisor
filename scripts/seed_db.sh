#!/usr/bin/env sh
set -e
COMPOSE_FILE="docker-compose.prod.yml"

echo "Running DB migrations..."
docker compose -f "$COMPOSE_FILE" exec backend flask db upgrade --directory migrations || true

echo "Running seed script..."
docker compose -f "$COMPOSE_FILE" exec backend python manage.py seed_db || true

echo "Done."
