# TutorMax Database Layer

Complete PostgreSQL database schema implementation for the TutorMax Tutor Performance Evaluation System.

## Overview

This package provides:
- SQLAlchemy 2.0+ ORM models for all entities
- Async database connection management
- Alembic migration support
- Database utility functions
- Initialization scripts

## Database Schema

### Core Entities (8 tables)

Based on PRD lines 562-703:

1. **tutors** - Tutor profiles and metadata
2. **students** - Student profiles
3. **sessions** - Individual tutoring sessions
4. **student_feedback** - Session ratings and feedback
5. **tutor_performance_metrics** - Calculated performance metrics (7d, 30d, 90d windows)
6. **churn_predictions** - ML-based churn predictions with multi-window probabilities
7. **interventions** - Intervention tasks and tracking
8. **tutor_events** - Behavioral event tracking (logins, reschedules, etc.)

### Entity Relationships

```
tutors (1) ─────── (N) sessions ─────── (1) students
  │                     │
  │                     │
  │                     └──── (1) student_feedback
  │
  ├─── (N) tutor_performance_metrics
  ├─── (N) churn_predictions
  ├─── (N) interventions
  └─── (N) tutor_events
```

## File Structure

```
src/database/
├── __init__.py           # Package exports
├── models.py             # SQLAlchemy ORM models
├── connection.py         # Connection management
├── utils.py              # Query helper functions
├── init_db.py            # Database initialization script
└── README.md             # This file

alembic/
├── env.py                # Alembic environment
├── script.py.mako        # Migration template
├── versions/             # Migration scripts
│   └── 20251107_0000_initial_schema.py
└── README                # Alembic usage guide
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Edit `.env`:
```env
POSTGRES_USER=tutormax
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tutormax
```

### 3. Create PostgreSQL Database

```bash
# Using psql
createdb tutormax

# Or with docker
docker run -d \
  --name tutormax-postgres \
  -e POSTGRES_USER=tutormax \
  -e POSTGRES_PASSWORD=tutormax_dev \
  -e POSTGRES_DB=tutormax \
  -p 5432:5432 \
  postgres:14
```

### 4. Run Migrations

```bash
# Apply all migrations
alembic upgrade head

# Or use the init script (creates tables directly)
python src/database/init_db.py
```

### 5. Verify Setup

```bash
# Connect to database
psql -U tutormax -d tutormax

# List tables
\dt

# Should show:
# - tutors
# - students
# - sessions
# - student_feedback
# - tutor_performance_metrics
# - churn_predictions
# - interventions
# - tutor_events
```

## Usage Examples

### Basic CRUD Operations

```python
from src.database import get_session, Tutor, Session, StudentFeedback
from datetime import datetime

# Create a tutor
async with get_session() as db:
    tutor = Tutor(
        tutor_id="tutor_001",
        name="Jane Doe",
        email="jane@example.com",
        onboarding_date=datetime.utcnow(),
        status="active",
        subjects=["Mathematics", "Physics"],
        baseline_sessions_per_week=15.0
    )
    db.add(tutor)
    await db.commit()

# Query tutors
async with get_session() as db:
    from sqlalchemy import select

    result = await db.execute(select(Tutor).where(Tutor.status == "active"))
    active_tutors = result.scalars().all()
```

### Using Utility Functions

```python
from src.database import get_session
from src.database.utils import (
    get_tutor_by_id,
    get_tutor_statistics,
    get_high_risk_tutors
)

# Get tutor with relationships
async with get_session() as db:
    tutor = await get_tutor_by_id(db, "tutor_001", with_relations=True)

    # Get 30-day statistics
    stats = await get_tutor_statistics(db, "tutor_001", days_back=30)
    print(stats)
    # {
    #   "tutor_id": "tutor_001",
    #   "total_sessions": 42,
    #   "average_rating": 4.5,
    #   "no_shows": 2,
    #   "reschedules": 5
    # }

    # Get high-risk tutors
    high_risk = await get_high_risk_tutors(db, min_score=51, limit=10)
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db_session, Tutor

app = FastAPI()

@app.get("/tutors/{tutor_id}")
async def get_tutor(
    tutor_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    from sqlalchemy import select
    result = await db.execute(select(Tutor).where(Tutor.tutor_id == tutor_id))
    tutor = result.scalar_one_or_none()
    return tutor
```

## Database Models

### Key Features

- **Type Safety**: Uses SQLAlchemy 2.0 `Mapped` annotations
- **Async Support**: Full async/await compatibility
- **Enums**: Type-safe enums for status fields
- **Relationships**: Proper foreign keys and cascades
- **Timestamps**: Automatic `created_at` and `updated_at`
- **JSONB**: For flexible metadata storage
- **Arrays**: PostgreSQL array support for lists

### Example Model

```python
class Tutor(Base):
    __tablename__ = "tutors"

    tutor_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[TutorStatus] = mapped_column(SQLEnum(TutorStatus))
    subjects: Mapped[List[str]] = mapped_column(ARRAY(String))

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(...)
    performance_metrics: Mapped[List["TutorPerformanceMetric"]] = relationship(...)
```

## Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to tutors"

# Create blank migration
alembic revision -m "Custom migration"
```

### Migration Commands

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade by N steps
alembic upgrade +2

# Downgrade by N steps
alembic downgrade -1

# View current version
alembic current

# View history
alembic history --verbose
```

### Example Migration

```python
def upgrade() -> None:
    op.add_column('tutors', sa.Column('phone', sa.String(20), nullable=True))
    op.create_index('ix_tutors_phone', 'tutors', ['phone'])

def downgrade() -> None:
    op.drop_index('ix_tutors_phone', 'tutors')
    op.drop_column('tutors', 'phone')
```

## Indexes

Optimized for common query patterns:

- **tutors**: email (unique), status
- **sessions**: tutor_id, student_id, scheduled_start, subject
- **student_feedback**: session_id (unique), tutor_id, student_id
- **tutor_performance_metrics**: tutor_id, calculation_date
- **churn_predictions**: tutor_id, prediction_date, risk_level
- **interventions**: tutor_id, status
- **tutor_events**: tutor_id, event_type, event_timestamp

## Data Types

### PostgreSQL-Specific Types

- **ARRAY**: For lists (subjects, improvement_areas)
- **JSONB**: For flexible metadata (contributing_factors, event metadata)
- **DateTime(timezone=True)**: All timestamps are timezone-aware

### Enums

All enum types are stored as strings for flexibility:

```python
class TutorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"

class RiskLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
```

## Performance Considerations

### Connection Pooling

Configured in `connection.py`:
- Pool size: 5 connections
- Max overflow: 10 additional connections
- Pool timeout: 30 seconds
- Pool recycle: 3600 seconds (1 hour)

### Query Optimization

- Use `selectinload()` for eager loading relationships
- Limit result sets with `.limit()`
- Use indexes for common WHERE clauses
- Batch inserts with `add_all()`

### Example Optimized Query

```python
from sqlalchemy.orm import selectinload

async with get_session() as db:
    # Eager load sessions and feedback to avoid N+1 queries
    result = await db.execute(
        select(Tutor)
        .options(
            selectinload(Tutor.sessions).selectinload(Session.feedback),
            selectinload(Tutor.performance_metrics)
        )
        .where(Tutor.status == "active")
        .limit(100)
    )
    tutors = result.scalars().all()
```

## Testing

### Test Database Setup

```python
import pytest
from src.database import get_engine, Base, close_db

@pytest.fixture
async def test_db():
    """Create test database."""
    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await close_db()
```

### Example Test

```python
@pytest.mark.asyncio
async def test_create_tutor(test_db):
    from src.database import get_session, Tutor

    async with get_session() as db:
        tutor = Tutor(
            tutor_id="test_001",
            name="Test Tutor",
            email="test@example.com",
            onboarding_date=datetime.utcnow(),
            status="active",
            subjects=["Math"]
        )
        db.add(tutor)
        await db.commit()

        # Verify
        from sqlalchemy import select
        result = await db.execute(select(Tutor).where(Tutor.tutor_id == "test_001"))
        retrieved = result.scalar_one()
        assert retrieved.name == "Test Tutor"
```

## Troubleshooting

### Connection Issues

```bash
# Test PostgreSQL connection
psql -U tutormax -d tutormax -c "SELECT version();"

# Check if database exists
psql -U tutormax -l | grep tutormax

# Verify environment variables
python -c "from src.database.connection import get_settings; print(get_settings().database_url)"
```

### Migration Conflicts

```bash
# Reset to specific revision
alembic downgrade <revision_id>

# Stamp without running migrations (dangerous!)
alembic stamp head

# View SQL without executing
alembic upgrade head --sql
```

### Performance Issues

```python
# Enable SQL logging
from src.database import get_engine

engine = get_engine(echo=True)  # Logs all SQL queries

# Or set in .env
DB_ECHO=true
```

## Best Practices

1. **Always use async/await** with database operations
2. **Use context managers** (`async with get_session()`) for automatic cleanup
3. **Handle exceptions** properly with try/except
4. **Use migrations** instead of `create_all()` in production
5. **Index foreign keys** and commonly queried columns
6. **Validate data** before inserting (use Pydantic models)
7. **Use transactions** for related operations
8. **Close connections** during shutdown (`await close_db()`)

## Security

- Store credentials in `.env` (never commit to git)
- Use `.gitignore` to exclude `.env` file
- Use strong passwords for database users
- Limit database user permissions (principle of least privilege)
- Enable SSL for production PostgreSQL connections
- Sanitize user input (SQLAlchemy handles this automatically)

## Next Steps

After database setup:

1. Run synthetic data generator to populate tables
2. Implement performance evaluation engine (reads from sessions/feedback)
3. Implement churn prediction service (writes to churn_predictions)
4. Build API endpoints using FastAPI + these models
5. Create dashboard queries using utility functions

## Additional Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
