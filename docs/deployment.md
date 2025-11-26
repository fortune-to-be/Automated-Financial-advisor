# Deployment Guide (Docker / Render / Heroku / AWS)

This document describes how to deploy the Automated Financial Advisor using Docker (production), and contains notes for Render, Heroku, and a generic AWS ECS/EC2 deployment.

Prerequisites
- Docker & Docker Compose installed (for local prod-compose testing)
- A Postgres instance (the `docker-compose.prod.yml` uses a Postgres service)
- A production-ready secrets store (set `SECRET_KEY`, `JWT_SECRET_KEY`, DB credentials)

Quick local production test (Docker Compose)

1. Copy the example env and fill values:

```powershell
cp .env.example .env
# edit .env and set secure secrets
```

2. Start services:

```powershell
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

3. Run migrations and seed (one-time):

The backend Dockerfile already runs `flask db upgrade` at container start. To seed the DB manually, exec into the container:

```powershell
docker compose -f docker-compose.prod.yml exec backend sh
python manage.py seed_db
```

Notes for Render
- Create a Postgres managed database on Render.
- Create two services: a Web Service for the backend and a Static Site for the frontend (or one web service to serve both).
- Set required environment variables in the Render dashboard from your `.env` values.
- Backend start command: `gunicorn "app:create_app()" -b 0.0.0.0:5000 --workers 3`

Notes for Heroku
- Provision a Heroku Postgres add-on.
- Set `SECRET_KEY`, `JWT_SECRET_KEY` and other env vars using `heroku config:set`.
- Add a `Procfile` with a web command for the backend:

```
web: gunicorn "app:create_app()" -b 0.0.0.0:$PORT --workers 3
```

- Use the frontend `npm run build` and serve the `dist` via an nginx buildpack or a separate static site hosting service (Netlify/Vercel).

Notes for AWS (ECS / Fargate or EC2)
- Push the backend and frontend images to ECR.
- Create ECS task definitions for backend (gunicorn) and frontend (nginx), attach to an Application Load Balancer.
- Use AWS RDS Postgres for production DB; populate DB connection in `DATABASE_URL`.

Database migrations & seeding
- Migrations: use `flask db migrate` and `flask db upgrade` (Flask-Migrate / Alembic is configured).
- Seed script: `python manage.py seed_db` or `backend/scripts/seed_direct.py` (example seeder). Run once after migrations.

Additional notes
- Ensure `SECRET_KEY` and `JWT_SECRET_KEY` are secure and rotated.
- Use an external object store for large uploads (S3) if import volumes grow.
- Configure logging and monitoring (Sentry, Prometheus, etc.).
