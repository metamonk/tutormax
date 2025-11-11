# TutorMax Database Setup Guide

Complete guide for setting up and initializing the PostgreSQL database for TutorMax.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ installed and running
- pip (Python package manager)

## Installation Steps

### 1. Install PostgreSQL

#### macOS (using Homebrew)
```bash
brew install postgresql@14
brew services start postgresql@14
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Docker (Recommended for Development)
```bash
docker run -d \
  --name tutormax-postgres \
  -e POSTGRES_USER=tutormax \
  -e POSTGRES_PASSWORD=tutormax_dev \
  -e POSTGRES_DB=tutormax \
  -p 5432:5432 \
  postgres:14
```

### 2. Create Database

#### Using psql
```bash
# Connect as postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE tutormax;
CREATE USER tutormax WITH PASSWORD 'tutormax_dev';
GRANT ALL PRIVILEGES ON DATABASE tutormax TO tutormax;
\q
```

#### Using createdb (if you have local postgres user)
```bash
createdb tutormax
```

### 3. Install Python Dependencies

```bash
# From project root
pip install -r requirements.txt
```

This installs:
- `sqlalchemy==2.0.25` - ORM
- `asyncpg==0.29.0` - Async PostgreSQL driver
- `psycopg2-binary==2.9.9` - Sync driver (for Alembic)
- `alembic==1.13.1` - Database migrations
- `pydantic-settings==2.1.0` - Configuration management

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

Required settings:
```env
POSTGRES_USER=tutormax
POSTGRES_PASSWORD=tutormax_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tutormax
```

### 5. Initialize Database

#### Option A: Using Alembic (Recommended)
```bash
# Run migrations
alembic upgrade head
```

#### Option B: Using Init Script
```bash
# Interactive initialization
python src/database/init_db.py
```

### 6. Verify Setup

```bash
# Connect to database
psql -U tutormax -d tutormax

# List tables
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

# Describe a table
\d tutors

# Exit
\q
```

## Database Schema Overview

### Tables

1. **tutors** (8 columns + timestamps)
   - Primary key: `tutor_id`
   - Indexes: email (unique), status
   - Contains: tutor profiles, subjects, behavioral archetype

2. **students** (5 columns + timestamps)
   - Primary key: `student_id`
   - Contains: student profiles, subjects of interest

3. **sessions** (15 columns + timestamps)
   - Primary key: `session_id`
   - Foreign keys: `tutor_id`, `student_id`
   - Indexes: tutor_id, student_id, scheduled_start, subject
   - Contains: session details, attendance, engagement

4. **student_feedback** (14 columns + created_at)
   - Primary key: `feedback_id`
   - Foreign keys: `session_id`, `student_id`, `tutor_id`
   - Unique index: session_id (one feedback per session)
   - Contains: ratings, recommendations, free-text feedback

5. **tutor_performance_metrics** (13 columns + timestamps)
   - Primary key: `metric_id`
   - Foreign key: `tutor_id`
   - Indexes: tutor_id, calculation_date
   - Contains: aggregated performance metrics (7d, 30d, 90d)

6. **churn_predictions** (11 columns + timestamps)
   - Primary key: `prediction_id`
   - Foreign key: `tutor_id`
   - Indexes: tutor_id, prediction_date, risk_level
   - Contains: ML predictions, churn scores, probabilities

7. **interventions** (11 columns + timestamps)
   - Primary key: `intervention_id`
   - Foreign key: `tutor_id`
   - Indexes: tutor_id, status
   - Contains: intervention tasks, assignments, outcomes

8. **tutor_events** (5 columns + created_at)
   - Primary key: `event_id`
   - Foreign key: `tutor_id`
   - Indexes: tutor_id, event_type, event_timestamp
   - Contains: behavioral events (logins, reschedules, etc.)

### Relationships

```
tutors (1) ─┬─── (N) sessions ────── (1) students
            │           │
            │           └─── (1) student_feedback
            │
            ├─── (N) tutor_performance_metrics
            ├─── (N) churn_predictions
            ├─── (N) interventions
            └─── (N) tutor_events
```

## Common Commands

### Alembic Migrations

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history --verbose

# Generate SQL without executing
alembic upgrade head --sql
```

### Database Management

```bash
# Backup database
pg_dump -U tutormax tutormax > backup.sql

# Restore database
psql -U tutormax tutormax < backup.sql

# Drop and recreate (WARNING: destroys data)
dropdb tutormax
createdb tutormax
alembic upgrade head

# Check database size
psql -U tutormax -d tutormax -c "SELECT pg_size_pretty(pg_database_size('tutormax'));"

# List all connections
psql -U tutormax -d tutormax -c "SELECT * FROM pg_stat_activity WHERE datname='tutormax';"
```

### Testing Database

```bash
# Run database tests
pytest tests/test_database.py -v

# Run with coverage
pytest tests/test_database.py --cov=src.database --cov-report=html
```

## Troubleshooting

### Issue: "Connection refused"

**Cause**: PostgreSQL not running

**Solution**:
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL (macOS/Homebrew)
brew services start postgresql@14

# Start PostgreSQL (Linux)
sudo systemctl start postgresql

# Start Docker container
docker start tutormax-postgres
```

### Issue: "FATAL: password authentication failed"

**Cause**: Incorrect credentials in .env

**Solution**:
```bash
# Check .env file
cat .env | grep POSTGRES

# Reset password if needed
psql -U postgres
ALTER USER tutormax WITH PASSWORD 'new_password';
\q
```

### Issue: "database does not exist"

**Cause**: Database not created

**Solution**:
```bash
createdb tutormax
# or
psql -U postgres -c "CREATE DATABASE tutormax;"
```

### Issue: Alembic migration conflicts

**Cause**: Migration state out of sync

**Solution**:
```bash
# Check current revision
alembic current

# Stamp database with current code version (use with caution)
alembic stamp head

# Or rollback and reapply
alembic downgrade base
alembic upgrade head
```

### Issue: "Too many connections"

**Cause**: Connection pool exhausted

**Solution**:
```bash
# Edit .env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Or increase PostgreSQL max_connections
# Edit postgresql.conf:
max_connections = 100
```

## Performance Tuning

### Indexes

All critical foreign keys and query columns are indexed:
- tutors: email, status
- sessions: tutor_id, student_id, scheduled_start, subject
- student_feedback: session_id, tutor_id, student_id
- tutor_performance_metrics: tutor_id, calculation_date
- churn_predictions: tutor_id, prediction_date, risk_level
- interventions: tutor_id, status
- tutor_events: tutor_id, event_type, event_timestamp

### Query Optimization

```python
# Use eager loading to prevent N+1 queries
from sqlalchemy.orm import selectinload

tutors = await db.execute(
    select(Tutor)
    .options(selectinload(Tutor.sessions))
    .where(Tutor.status == "active")
)

# Limit results
tutors = await db.execute(
    select(Tutor).limit(100)
)

# Use indexes in WHERE clauses
sessions = await db.execute(
    select(Session)
    .where(Session.tutor_id == "tutor_123")  # Uses index
    .where(Session.scheduled_start >= cutoff_date)  # Uses index
)
```

### Connection Pooling

Configured in `src/database/connection.py`:
- Pool size: 5 connections
- Max overflow: 10 additional connections
- Timeout: 30 seconds
- Recycle: 3600 seconds

## Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore`
2. **Use strong passwords** - Change default password in production
3. **Limit user permissions** - Grant only necessary privileges
4. **Enable SSL** - For production PostgreSQL connections
5. **Regular backups** - Automate with cron jobs
6. **Monitor connections** - Watch for connection leaks

## Production Deployment

### Render PostgreSQL

1. Create PostgreSQL instance in Render dashboard
2. Copy connection details to `.env`:
   ```env
   POSTGRES_USER=<from_render>
   POSTGRES_PASSWORD=<from_render>
   POSTGRES_HOST=<from_render>
   POSTGRES_PORT=5432
   POSTGRES_DB=<from_render>
   ```
3. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Environment-Specific Settings

```python
# Development
DB_ECHO=true
DB_POOL_SIZE=5

# Production
DB_ECHO=false
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

## Next Steps

After database setup:

1. **Populate with synthetic data**:
   ```bash
   python demo_data_generation.py
   ```

2. **Verify data**:
   ```bash
   psql -U tutormax -d tutormax
   SELECT COUNT(*) FROM tutors;
   SELECT COUNT(*) FROM sessions;
   \q
   ```

3. **Build API endpoints** using FastAPI + database models

4. **Implement performance evaluation engine** to calculate metrics

5. **Implement churn prediction service** using ML models

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [asyncpg Performance Guide](https://magicstack.github.io/asyncpg/current/usage.html)
