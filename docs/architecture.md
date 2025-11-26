# Architecture Overview

This document summarizes the main components and how they interact.

Components
- Backend (Flask): provides REST API endpoints for authentication, transactions, budgets, goals, planner, admin rules, and reports. The application uses SQLAlchemy for ORM and Flask-Migrate for database migrations.
- Frontend (Vite + React + TypeScript): single-page application, compiled to static assets and served by `nginx` in production.
- Database: PostgreSQL in production. An embedded SQLite file is used during local development and tests.
- Services: Rule engine, Planner, Transaction importer, and other domain services implemented in Python under `app/services`.

Deployment topology (production)
- `frontend` (nginx static server) exposes port 80 to the public.
- `backend` (gunicorn + Flask) runs on port 5000 behind an internal network and is reachable by the frontend and any API clients.
- `postgres` stores data; backups and managed DBs are recommended for true production.

Data flow
1. User interacts with the SPA running in the browser.
2. SPA sends authenticated requests to backend APIs for CRUD, imports, planner requests.
3. Backend persists transactions & rules in Postgres and uses the RuleEngine and Planner services to compute recommendations.

Security
- Use HTTPS (TLS) for all public endpoints — configure TLS at the load balancer or hosting provider.
- Store secrets in environment variables and a secure secret manager.
- Rotate `SECRET_KEY` and `JWT_SECRET_KEY` regularly.

Scaling notes
- Backend: scale horizontally by increasing Gunicorn workers per container and adding more backend replicas behind a load balancer.
- Database: use a managed Postgres with read replicas for heavy read workloads; enable backups.
