FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement file and install into a virtual env
COPY backend/requirements.txt ./requirements.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install -r requirements.txt

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY backend/ ./backend/
COPY backend/manage.py ./manage.py

WORKDIR /app/backend

# Expose port
EXPOSE 5000

# Default env vars (can be overridden by docker-compose / env-file)
ENV FLASK_ENV=production
ENV FLASK_APP=app

# Entrypoint: run migrations then start gunicorn using the app factory
CMD ["sh", "-c", "flask db upgrade --directory migrations || true && gunicorn \"app:create_app()\" -b 0.0.0.0:5000 --workers 3"]
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
