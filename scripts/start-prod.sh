#!/usr/bin/env sh
# Start production compose and tail logs
set -e
COMPOSE_FILE="docker-compose.prod.yml"

if [ -f .env ]; then
  echo "Using .env file"
fi

echo "Bringing up services..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

echo "Running migrations..."
docker compose -f "$COMPOSE_FILE" exec backend flask db upgrade --directory migrations || true

echo "Seeding DB (if available)..."
docker compose -f "$COMPOSE_FILE" exec backend python manage.py seed_db || true

echo "Tailing logs (Ctrl+C to exit)"
docker compose -f "$COMPOSE_FILE" logs -f
