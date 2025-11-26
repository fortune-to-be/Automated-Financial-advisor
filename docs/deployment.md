# Deployment Guide

This document describes how to build and deploy the Automated Financial Advisor application in production using Docker and managed platforms.

1) Using docker-compose (recommended for quick deploy / staging)

- Copy `.env.example` to `.env` and fill secrets.
- Start services:

```powershell
docker compose -f docker-compose.prod.yml --env-file .env up --build -d
```

- Apply database migrations (run once or on upgrade):

```powershell
docker compose -f docker-compose.prod.yml --env-file .env run --rm backend \
  python manage.py db upgrade
# or, if using Flask-Migrate CLI
```

- Seed the DB (optional):

```powershell
docker compose -f docker-compose.prod.yml --env-file .env run --rm backend \
  python -m scripts.seed_direct
```

2) Deploy to Render / Heroku / AWS

- Render: deploy backend as a Docker service using `backend/Dockerfile`, set environment variables in Render web service. Use a managed Postgres instance and set `DATABASE_URL` accordingly. Frontend can be served as a static site using the built `frontend/dist` or use the `frontend/Dockerfile` as a separate service.

- Heroku: Create two apps or use Heroku Container Registry. Push images built from `backend` and `frontend` Dockerfiles. Set `DATABASE_URL` (Heroku will provide it), and set the `SECRET_KEY` and `JWT_SECRET_KEY` config vars. Run migrations via `heroku run`.

- AWS (ECS / Fargate): Build images in ECR from the `backend` and `frontend` Dockerfiles. Configure ECS task definitions and use an RDS Postgres instance. Provide environment variables via secrets/Parameter Store/SSM and run migrations as part of a deploy job or init task.

3) Environment variables

- Required (backend): `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`.
- Optional: `FLASK_ENV`, `GUNICORN_WORKERS`, `VITE_API_BASE_URL`.

4) Migrations & seeding

- We use Flask-Migrate / Alembic. Run migration commands from within the backend container:

```powershell
docker compose -f docker-compose.prod.yml run --rm backend python manage.py db migrate
docker compose -f docker-compose.prod.yml run --rm backend python manage.py db upgrade
```

- Seeding helper: `backend/scripts/seed_direct.py` or `manage.py seed_db` (if provided).
