# Architecture Overview

This repository contains two main components:

- `backend/` — Flask application (REST API), SQLAlchemy models, services and routes. Uses Flask-JWT-Extended for auth and Flask-Migrate for database migrations.
- `frontend/` — Vite + React + TypeScript single-page application. Tests use Vitest and Testing Library.

Key runtime pieces:

- Postgres database in production (docker-compose.prod.yml uses `postgres:15-alpine`).
- Backend served by `gunicorn` in the container (see `backend/Dockerfile`).
- Frontend built with Vite and served as static files by `nginx` (see `frontend/Dockerfile`).

Data & auth

- JWT: `JWT_SECRET_KEY` signs access tokens (access: 1h by default). Tokens required for protected endpoints.
- Database URL provided via `DATABASE_URL` env var (Postgres recommended in production).

Deployment flow

1. Build backend image, run migrations, seed DB (if needed).
2. Build frontend bundle and serve via nginx or a static hosting service (Netlify, Vercel, S3+CloudFront).
3. Wire services together via `docker-compose.prod.yml` or orchestration platform.
