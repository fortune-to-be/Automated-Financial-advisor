# Backend

Flask-based REST API for the Automated Financial Advisor platform.

## Features

- Health check endpoint
- Advisor information endpoint
- Recommendations generation endpoint
- CORS support
- Comprehensive test suite

## Development

### Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

### Test

```bash
pytest
pytest --cov  # With coverage
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/advisor` - Get advisor info
- `POST /api/recommendations` - Get recommendations

## Environment Variables

See `.env.example` at project root.
