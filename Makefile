# Makefile for local dev / production compose helpers
COMPOSE_FILE=docker-compose.prod.yml

.PHONY: build up down ps logs migrate seed

build:
	docker compose -f $(COMPOSE_FILE) build --pull --no-cache

up:
	docker compose -f $(COMPOSE_FILE) up -d --remove-orphans

down:
	docker compose -f $(COMPOSE_FILE) down

ps:
	docker compose -f $(COMPOSE_FILE) ps

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

migrate:
	# Run migrations in backend container
	docker compose -f $(COMPOSE_FILE) exec backend flask db upgrade --directory migrations

seed:
	# Seed the database using the manage script
	docker compose -f $(COMPOSE_FILE) exec backend python manage.py seed_db
