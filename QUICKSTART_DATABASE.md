# TutorMax Database Quick Start

Get the PostgreSQL database running in 5 minutes.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ OR Docker

## 1. Choose Your Database Setup

### Option A: Docker (Easiest)

```bash
# Start PostgreSQL in Docker
docker run -d \
  --name tutormax-postgres \
  -e POSTGRES_USER=tutormax \
  -e POSTGRES_PASSWORD=tutormax_dev \
  -e POSTGRES_DB=tutormax \
  -p 5432:5432 \
  postgres:14

# Verify it's running
docker ps | grep tutormax-postgres
```

### Option B: Local PostgreSQL

```bash
# macOS (Homebrew)
brew install postgresql@14
brew services start postgresql@14
createdb tutormax

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb tutormax
```

## 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Installs:
- SQLAlchemy 2.0.25
- asyncpg 0.29.0
- alembic 1.13.1
- pydantic-settings 2.1.0

## 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env (use defaults for Docker setup)
# POSTGRES_USER=tutormax
# POSTGRES_PASSWORD=tutormax_dev
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=tutormax
```

## 4. Run Database Migrations

```bash
# Apply all migrations (creates all tables)
alembic upgrade head
```

## 5. Verify Setup

```bash
# Connect to database
psql -U tutormax -d tutormax

# List tables (should see 8 tables)
\dt

# Expected output:
#  public | churn_predictions
#  public | interventions
#  public | sessions
#  public | student_feedback
#  public | students
#  public | tutor_events
#  public | tutor_performance_metrics
#  public | tutors

# Exit
\q
```

## 6. Test Database Connection

```bash
# Run database tests
pytest tests/test_database.py -v
```

All tests should pass ✅

## 7. Populate with Sample Data

```bash
# Run synthetic data generator
python demo_data_generation.py
```

## Quick Commands Reference

### Database Management

```bash
# Start Docker PostgreSQL
docker start tutormax-postgres

# Stop Docker PostgreSQL
docker stop tutormax-postgres

# View database logs
docker logs tutormax-postgres

# Access psql in Docker
docker exec -it tutormax-postgres psql -U tutormax -d tutormax
```

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current
```

### Testing

```bash
# Run all database tests
pytest tests/test_database.py

# Run with coverage
pytest tests/test_database.py --cov=src.database

# Run specific test
pytest tests/test_database.py::test_create_tutor -v
```

## Troubleshooting

### "Connection refused"

PostgreSQL isn't running. Start it:
```bash
# Docker
docker start tutormax-postgres

# macOS
brew services start postgresql@14

# Linux
sudo systemctl start postgresql
```

### "Database does not exist"

Create the database:
```bash
createdb tutormax
```

### "Authentication failed"

Check `.env` credentials match your PostgreSQL setup.

## What's Next?

1. ✅ Database is running
2. ✅ Tables are created
3. ✅ Tests pass

Now you can:
- Build API endpoints (see `src/database/README.md` for FastAPI examples)
- Implement business logic (performance evaluation, churn prediction)
- Generate synthetic data
- Build the dashboard UI

## Full Documentation

- **Setup Guide**: `docs/DATABASE_SETUP.md`
- **Schema Reference**: `docs/DATABASE_SCHEMA.md`
- **Developer Guide**: `src/database/README.md`
- **Completion Report**: `TASK_2.4_COMPLETION_REPORT.md`

## Need Help?

Check the comprehensive documentation in the `docs/` and `src/database/` directories.
