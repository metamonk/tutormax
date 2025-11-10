# TutorMax - Tutor Performance Evaluation System

TutorMax is a comprehensive tutor performance evaluation and management system designed to track, analyze, and improve tutor effectiveness in educational settings.

## Features

- **Performance Analytics**: Real-time tracking of tutor performance metrics
- **Student Feedback System**: Secure, anonymous feedback collection with COPPA/FERPA compliance
- **Intervention Management**: Automated identification and tracking of at-risk tutors
- **Compliance**: Built-in GDPR, COPPA, and FERPA compliance features
- **Security**: Enterprise-grade security with audit logging and data encryption
- **PWA Support**: Progressive Web App with offline capabilities

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+ (for frontend)
- pnpm (for frontend package management)

### Local Setup

See [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) for detailed setup instructions.

### Deployment

See [DEPLOYMENT_OVERVIEW.md](DEPLOYMENT_OVERVIEW.md) and [RENDER_SETUP_GUIDE.md](RENDER_SETUP_GUIDE.md) for deployment instructions.

## Documentation

- **Setup & Deployment**
  - [Local Setup Guide](LOCAL_SETUP_GUIDE.md)
  - [Deployment Overview](DEPLOYMENT_OVERVIEW.md)
  - [Render Setup Guide](RENDER_SETUP_GUIDE.md)
  - [Test Users](TEST_USERS_README.md)

- **Compliance & Security**
  - [COPPA Compliance](docs/COPPA_COMPLIANCE.md)
  - [FERPA Compliance](docs/FERPA_COMPLIANCE.md)
  - [GDPR Compliance](docs/GDPR_COMPLIANCE.md)
  - [Security Hardening](docs/SECURITY_HARDENING.md)
  - [Data Encryption](docs/DATA_ENCRYPTION_AND_PRIVACY.md)

- **Features & APIs**
  - [Worker System](docs/WORKER_SYSTEM_README.md)
  - [Data Retention System](docs/DATA_RETENTION_SYSTEM.md)
  - [Audit Logging](docs/AUDIT_LOGGING_QUICKSTART.md)
  - [Feedback Authentication](docs/FEEDBACK_AUTH_QUICKSTART.md)

- **Frontend**
  - [Frontend README](frontend/README.md)
  - [Environment Setup](frontend/ENV_SETUP.md)
  - [PWA Quick Reference](frontend/PWA_QUICK_REFERENCE.md)

## Architecture

TutorMax is built with:
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 16 with React 19
- **Database**: PostgreSQL with Alembic migrations
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Deployment**: Render.com (recommended)

## Project Structure

```
tutormax/
├── src/              # Backend source code
│   ├── api/          # FastAPI routes and services
│   ├── database/     # Database models and utilities
│   ├── evaluation/   # Performance evaluation logic
│   └── workers/      # Celery workers
├── frontend/         # Next.js frontend application
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── tests/            # Test suite
└── alembic/          # Database migrations
```

## Development

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the API server
uvicorn src.api.main:app --reload
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### Workers

```bash
# Start Celery worker
celery -A src.workers.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A src.workers.celery_app beat --loglevel=info
```

## Testing

```bash
# Backend tests
pytest

# Frontend tests
cd frontend
pnpm test
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For questions or issues, please [open an issue](https://github.com/your-org/tutormax/issues).
