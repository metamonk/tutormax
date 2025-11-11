# Enrichment Module - Quick Start Guide

## Installation

No additional packages needed beyond base requirements.

## Running the Enrichment Worker

### 1. Start Dependencies

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Ensure PostgreSQL is running
psql -U tutormax -d tutormax -c "SELECT 1;"
```

### 2. Configure Environment

Create `.env` file:

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

### 3. Start Enrichment Worker

```bash
python -m src.pipeline.enrichment.enrichment_worker
```

Expected output:
```
Starting TutorMax Enrichment Worker
Consumer group: enrichment-workers
Queues: ['tutormax:tutors:enrichment', 'tutormax:sessions:enrichment', 'tutormax:feedback:enrichment']
Batch size: 10
Poll interval: 100ms
```

## Testing

### Run All Tests

```bash
pytest tests/pipeline/enrichment/ -v
```

### Run Integration Test

```bash
python scripts/test_enrichment_pipeline.py
```

## Usage Examples

### Enrich Data Programmatically

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

print(f"Success: {result.success}")
print(f"Derived fields: {result.derived_fields}")
# Output:
# Success: True
# Derived fields: {
#     'tenure_days': 297,
#     'is_new_tutor': False,
#     'experience_level': 'mid',
#     'subject_count': 2,
#     'is_active_today': False
# }
```

## Derived Fields Reference

### Tutors

| Field | Formula | Example |
|-------|---------|---------|
| `tenure_days` | Days since onboarding | 297 |
| `is_new_tutor` | tenure_days < 30 | False |
| `experience_level` | Based on tenure (see below) | "mid" |
| `subject_count` | len(subjects) | 2 |
| `is_active_today` | updated_at.date() == today | False |

**Experience Levels:**
- `junior`: < 90 days
- `mid`: 90-364 days
- `senior`: >= 365 days

### Sessions

| Field | Formula | Example |
|-------|---------|---------|
| `is_weekend` | Day is Sat/Sun | True |
| `time_of_day` | Hour category (see below) | "afternoon" |
| `is_late_start` | late_start_minutes > 5 | False |
| `actual_duration_minutes` | From actual_start if available | 60 |
| `week_of_year` | ISO week number | 45 |
| `month_of_year` | Month (1-12) | 11 |

**Time of Day:**
- `morning`: 5:00-11:59
- `afternoon`: 12:00-16:59
- `evening`: 17:00-21:59
- `night`: 22:00-4:59

### Feedback

| Field | Formula | Example |
|-------|---------|---------|
| `is_positive` | overall_rating >= 4 | True |
| `is_poor` | overall_rating < 3 | False |
| `avg_category_rating` | Mean of 5 category ratings | 4.2 |
| `category_variance` | Variance of ratings | 0.4 |
| `has_text_feedback` | len(free_text) > 0 | True |
| `feedback_delay_hours` | Hours since session | 12.5 |

## Monitoring

### Check Worker Stats

Worker logs stats every 10 batches:

```
Stats: processed=100, enriched=98, persisted=97, failed=3, batches=10, rate=50.0 msg/s
```

### Check Dead Letter Queue

```bash
redis-cli XLEN tutormax:dead_letter
```

## Troubleshooting

### Worker Not Starting

**Problem:** Worker fails to connect to Redis

**Solution:**
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check Redis config
echo $REDIS_HOST
echo $REDIS_PORT
```

### No Messages Being Processed

**Problem:** Worker starts but processes no messages

**Solution:**
```bash
# Check if enrichment queues have messages
redis-cli XLEN tutormax:tutors:enrichment
redis-cli XLEN tutormax:sessions:enrichment
redis-cli XLEN tutormax:feedback:enrichment

# If empty, check if validation worker is running
```

### Database Persistence Failures

**Problem:** Messages enriched but not persisted

**Solution:**
```bash
# Check PostgreSQL connection
psql -U tutormax -d tutormax -c "SELECT COUNT(*) FROM tutors;"

# Check database logs for foreign key violations
# Sessions/Feedback need tutors/students to exist first
```

## Next Steps

After enrichment worker is running:

1. Start validation worker (feeds enrichment queues)
2. Send data via FastAPI endpoints
3. Monitor PostgreSQL for enriched data
4. Check dead letter queue for failures

## Documentation

- Full documentation: `/src/pipeline/enrichment/README.md`
- Task summary: `/TASK_2.3_COMPLETION_SUMMARY.md`
- Test examples: `/tests/pipeline/enrichment/`
