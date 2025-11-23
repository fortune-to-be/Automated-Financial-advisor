# Automated Financial Advisor

An intelligent financial advisory platform combining backend analytics with frontend visualization and optional machine learning capabilities.

## Project Structure

```
automated-financial-advisor/
├── backend/              # Python Flask backend API
├── frontend/             # React frontend application
├── docs/                 # Documentation
├── sample-data/          # Sample datasets for development and testing
├── docker-compose.yml    # Docker orchestration
└── README.md             # This file
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+ (for local development)
- Node.js 16+ (for local development)

### Using Docker

Build and run all services:

```bash
docker-compose up --build
```

Services will be available at:
- Backend API: http://localhost:5000
- Frontend: http://localhost:3000

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest
python app.py
```

#### Frontend

```bash
cd frontend
npm install
npm start
```

## Testing

Run backend tests:

```bash
pytest
```

## Environment Setup

Copy `.env.example` to `.env` and configure as needed:

```bash
cp .env.example .env
```

## Branches

- `main` - Production ready code
- `develop` - Integration branch
- `backend-starter` - Backend development
- `frontend-starter` - Frontend development
- `optional-ml` - Machine learning features

## License

MIT
