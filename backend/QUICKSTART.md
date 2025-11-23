# Quick Start Guide - Backend

## Installation & Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db upgrade

# Seed database (creates admin user and categories)
flask seed-db
```

## Running the Server

```bash
# Development server
python app.py

# Server runs on http://localhost:5000
```

## Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov

# Specific test class
pytest test_app.py::TestAuthentication

# Verbose output
pytest -v
```

## API Usage Examples

### 1. Register User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

Response:
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "created_at": "2025-11-23T10:00:00",
    "updated_at": "2025-11-23T10:00:00"
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

### 2. Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

### 3. Get User Profile (Protected)

```bash
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer {access_token}"
```

### 4. Refresh Access Token

```bash
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

## Default Test User (After Seeding)

- **Email**: admin@advisor.local
- **Username**: admin
- **Password**: admin123
- **Role**: admin

## Project Structure Quick Reference

```
backend/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration classes
│   ├── database.py          # SQLAlchemy initialization
│   ├── models/              # Database models
│   ├── schemas/             # Validation schemas
│   ├── routes/              # API blueprints
│   └── services/            # Business logic
├── migrations/              # Database migrations
├── app.py                   # WSGI entry point
├── manage.py                # CLI commands
├── requirements.txt         # Dependencies
└── test_app.py              # Test suite
```

## Database Commands

```bash
# Create initial migration
flask db init

# Generate migration after model changes
flask db migrate -m "Description of changes"

# Apply pending migrations
flask db upgrade

# Downgrade last migration
flask db downgrade

# View migration status
flask db current

# Seed initial data
flask seed-db

# Drop all tables (careful!)
flask drop-db
```

## Environment Configuration

Create `.env` file in backend directory:

```
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///advisor.db
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

## Troubleshooting

### Port Already in Use
```bash
# Windows: Find and kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Database Lock
```bash
# Delete SQLite database and reinitialize
rm advisor.db
flask db upgrade
flask seed-db
```

### Import Errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

1. Test API endpoints using Postman or curl
2. Implement account management endpoints
3. Add transaction endpoints
4. Implement budget and goal management
5. Create automated rule processing
6. Add file upload for statements
7. Integrate ML recommendations
