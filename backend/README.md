# Backend

Flask-based REST API for the Automated Financial Advisor platform.

## Features

- JWT authentication with access & refresh tokens
- Complete database models (User, Account, Category, Transaction, Budget, Goal, Rule, AuditLog)
- Request/response validation with marshmallow schemas
- Password hashing with bcrypt
- Database migrations with Alembic
- Comprehensive test suite
- Seeder script for initial data

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Marshmallow validation schemas
│   ├── routes/          # API endpoint blueprints
│   ├── services/        # Business logic services
│   ├── config.py        # Configuration management
│   ├── database.py      # Database initialization
│   └── __init__.py      # App factory
├── migrations/          # Alembic database migrations
├── manage.py            # CLI commands (db, seed)
├── app.py               # WSGI entry point
├── requirements.txt     # Python dependencies
├── pytest.ini           # Pytest configuration
├── conftest.py          # Pytest fixtures
├── test_app.py          # Test suite
└── .flaskenv            # Flask environment variables
```

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL or SQLite (SQLite by default for development)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp ../.env.example .env
```

Environment variables:
- `FLASK_ENV` - Environment (development, testing, production)
- `DATABASE_URL` - Database connection URL
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key

## Database Management

### Initialize Database

```bash
flask db init
```

### Create Migrations

```bash
flask db migrate -m "Description of changes"
```

### Apply Migrations

```bash
flask db upgrade
```

### Seed Database

```bash
flask seed-db
```

This creates:
- Admin user (admin/admin123)
- Default categories (Grocery, Utilities, Transportation, etc.)
- Grocery auto-categorization rule

## Running

### Development Server

```bash
python app.py
```

Server runs on `http://localhost:5000`

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov
```

### Run Specific Test

```bash
pytest test_app.py::TestAuthentication::test_register_user
```

## API Endpoints

### Health & Info

- `GET /health` - Health check
- `GET /api/advisor` - Advisor information

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/profile` - Get current user profile (requires auth)
- `PUT /api/auth/profile` - Update user profile (requires auth)

## Authentication

All protected endpoints require JWT token in Authorization header:

```
Authorization: Bearer <access_token>
```

### Register Example

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login Example

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

### Protected Endpoint Example

```bash
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer <access_token>"
```

## Database Models

### User
- Email, username, password (hashed)
- First/last name, role, is_active
- Relationships: accounts, transactions, budgets, goals, rules, audit_logs

### Account
- Account name, type (checking, savings, credit_card, investment)
- Balance, currency
- Relationships: transactions

### Category
- Name, description, color (hex), icon
- Used for transaction categorization

### Transaction
- Amount, type (income, expense, transfer)
- Description, transaction date, tags
- Relationships: account, category

### Budget
- Limit amount, period (monthly, yearly)
- Start/end dates, is_active
- Relationships: category

### Goal
- Name, target amount, current amount
- Target date, category, priority
- Relationships: user

### Rule
- Name, condition (JSON), action (JSON)
- Priority, is_active
- Used for automation (e.g., auto-categorize)

### AuditLog
- Action, resource type, resource ID
- Old/new values (JSON)
- IP address, user agent

## Development Commands

```bash
# Create database
flask db init

# Generate migration
flask db migrate -m "Add new field"

# Apply migration
flask db upgrade

# Drop all tables
flask drop-db

# Seed initial data
flask seed-db

# Run tests
pytest

# Run with coverage
pytest --cov

# Format code (if using black)
black .

# Check code style (if using flake8)
flake8 .
```

