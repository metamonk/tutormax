# Data Enrichment Module

The enrichment module handles the enrichment of validated data with derived fields and additional context before database persistence.

## Architecture

```
Redis Enrichment Queues → Enrichment Engine → Database Persister → PostgreSQL
                             ↓ (failures)
                        Dead Letter Queue
```

## Components

### 1. Base Enricher (`base_enricher.py`)

Abstract base class providing common functionality for all enrichers:
- Field validation
- Safe value extraction
- Datetime field calculations
- Statistics tracking

### 2. Data Type Enrichers

#### TutorEnricher (`tutor_enricher.py`)

Enriches tutor data with derived fields:
- `tenure_days`: Days since onboarding
- `is_new_tutor`: True if tenure_days < 30
- `experience_level`: junior (<90 days), mid (90-365 days), senior (>365 days)
- `subject_count`: Number of subjects taught
- `is_active_today`: True if updated today

#### SessionEnricher (`session_enricher.py`)

Enriches session data with derived fields:
- `is_weekend`: True if scheduled on Saturday/Sunday
- `time_of_day`: morning (5-11), afternoon (12-16), evening (17-21), night (22-4)
- `is_late_start`: True if late_start_minutes > 5
- `actual_duration_minutes`: Calculated from actual_start if available
- `week_of_year`: ISO week number
- `month_of_year`: Month (1-12)

#### FeedbackEnricher (`feedback_enricher.py`)

Enriches feedback data with derived fields:
- `is_positive`: True if overall_rating >= 4
- `is_poor`: True if overall_rating < 3
- `avg_category_rating`: Average of all category ratings
- `category_variance`: Variance across category ratings
- `has_text_feedback`: True if free_text_feedback provided
- `feedback_delay_hours`: Hours between session and feedback submission

### 3. Enrichment Engine (`enrichment_engine.py`)

Coordinates the enrichment process:
- Routes data to appropriate enrichers
- Tracks statistics across all enrichers
- Provides unified enrichment interface

### 4. Database Persister (`db_persister.py`)

Handles database persistence:
- Upsert operations (insert or update if exists)
- Foreign key validation
- Batch processing with transactions
- Error handling with rollback

### 5. Enrichment Worker (`enrichment_worker.py`)

Background worker that:
- Consumes from Redis enrichment queues
- Enriches data using EnrichmentEngine
- Persists enriched data using DatabasePersister
- Handles failures with dead letter queue
- Provides graceful shutdown

## Redis Queue Configuration

The enrichment worker consumes from these queues:

- `tutormax:tutors:enrichment` → Validated tutor data
- `tutormax:sessions:enrichment` → Validated session data
- `tutormax:feedback:enrichment` → Validated feedback data

Failed enrichments are sent to:
- `tutormax:dead_letter` → Failed messages for manual review

## Database Integration

### Upsert Logic

All persistence operations use PostgreSQL upsert (INSERT ... ON CONFLICT DO UPDATE):
- If record exists (by primary key): UPDATE
- If record doesn't exist: INSERT

### Foreign Key Validation

Before persisting sessions or feedback, the persister verifies that referenced entities exist:
- Sessions: Verifies tutor_id and student_id exist
- Feedback: Verifies tutor_id, student_id, and session_id exist

If foreign keys don't exist, the record is skipped and logged as failed.

## Running the Enrichment Worker

### Command Line

```bash
# Run worker directly
python -m src.pipeline.enrichment.enrichment_worker

# Or use Python import
python -c "from src.pipeline.enrichment.enrichment_worker import main; main()"
```

### Worker Configuration

The worker uses configuration from `src/queue/config.py`:

```python
# Redis connection
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Worker settings
WORKER_BATCH_SIZE = 10          # Messages per batch
WORKER_POLL_INTERVAL_MS = 100   # Polling interval
```

### Environment Variables

Set these in `.env`:

```bash
# Database
POSTGRES_USER=tutormax
POSTGRES_PASSWORD=tutormax_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tutormax

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Usage Examples

### Using Enrichers Directly

```python
from src.pipeline.enrichment import TutorEnricher

enricher = TutorEnricher()

tutor_data = {
    "tutor_id": "T001",
    "name": "John Doe",
    "email": "john@example.com",
    "onboarding_date": "2024-01-15T00:00:00Z",
    "status": "active",
    "subjects": ["Math", "Physics"],
    "updated_at": "2024-11-07T12:00:00Z"
}

result = enricher.enrich(tutor_data)

if result.success:
    print(f"Enriched data: {result.data}")
    print(f"Derived fields: {result.derived_fields}")
else:
    print(f"Errors: {result.errors}")
```

### Using Enrichment Engine

```python
from src.pipeline.enrichment import EnrichmentEngine

engine = EnrichmentEngine()

# Enrich different data types
tutor_result = engine.enrich(tutor_data, "tutor")
session_result = engine.enrich(session_data, "session")
feedback_result = engine.enrich(feedback_data, "feedback")

# Get statistics
stats = engine.get_stats()
print(f"Total enriched: {stats['total_enriched']}")
print(f"Total failed: {stats['total_failed']}")
```

### Using Database Persister

```python
import asyncio
from src.pipeline.enrichment.db_persister import DatabasePersister

persister = DatabasePersister()

# Persist batch of tutors
tutor_batch = [tutor1_data, tutor2_data, tutor3_data]

results = asyncio.run(
    persister.persist_batch(tutor_batch, "tutor")
)

print(f"Success: {results['success']}, Failed: {results['failed']}")
```

## Monitoring

### Worker Statistics

The worker logs statistics every 10 batches:

```
Stats: processed=100, enriched=98, persisted=97, failed=3, batches=10, rate=50.0 msg/s
```

### Enrichment Engine Statistics

```python
{
    "total_enriched": 100,
    "total_failed": 5,
    "by_type": {
        "tutor": {
            "success": 30,
            "failed": 1,
            "enricher_stats": {
                "enrichments_attempted": 31,
                "enrichments_successful": 30,
                "enrichments_failed": 1
            }
        },
        "session": {...},
        "feedback": {...}
    }
}
```

### Database Persister Statistics

```python
{
    "total_persisted": 95,
    "total_failed": 5,
    "by_type": {
        "tutor": {"inserted": 0, "updated": 0, "failed": 0},
        "session": {"inserted": 0, "updated": 0, "failed": 2},
        "feedback": {"inserted": 0, "updated": 0, "failed": 3}
    }
}
```

## Testing

Run the test suite:

```bash
# All enrichment tests
pytest tests/pipeline/enrichment/ -v

# Specific enricher tests
pytest tests/pipeline/enrichment/test_tutor_enricher.py -v
pytest tests/pipeline/enrichment/test_session_enricher.py -v
pytest tests/pipeline/enrichment/test_feedback_enricher.py -v

# With coverage
pytest tests/pipeline/enrichment/ --cov=src.pipeline.enrichment --cov-report=html
```

## Error Handling

### Enrichment Failures

When enrichment fails:
1. Error is logged
2. Original data + errors sent to dead letter queue
3. Message is acknowledged (won't retry)

### Database Persistence Failures

When database persistence fails:
1. Entire batch is rolled back
2. Error is logged with details
3. Individual failures are tracked in stats

### Foreign Key Violations

When foreign keys don't exist:
1. Record is skipped (not persisted)
2. Warning is logged
3. Counted as failed in statistics

## Performance

### Batch Processing

The worker processes messages in batches for optimal performance:
- Default batch size: 10 messages
- Database commits are batched
- Reduces database round trips

### Async Database Operations

All database operations use SQLAlchemy async for non-blocking I/O:
- Multiple enrichment workers can run in parallel
- Database connection pooling
- Automatic session management

## Future Enhancements

Potential improvements:
1. Caching for foreign key lookups
2. Parallel enrichment of independent messages
3. Retry logic for transient database failures
4. Metrics export to Prometheus/Grafana
5. Support for partial batch commits
6. Enrichment result caching
