#!/usr/bin/env sh
set -e
# Demo script: run migrations, seed demo data and start backend (development)

echo "Running migrations..."
if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
fi

python -m pip install -r backend/requirements.txt || true

echo "Seeding demo data..."
python backend/scripts/seed_demo.py

echo "Starting backend (development server)..."
python backend/app.py
