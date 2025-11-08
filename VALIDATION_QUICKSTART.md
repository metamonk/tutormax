# Data Validation Module - Quick Start Guide

## Installation

No additional dependencies needed beyond project requirements.

## Quick Start

### 1. Start Redis (if not already running)

```bash
# Using Docker
docker-compose up -d redis

# Or native Redis
redis-server
```

### 2. Run the Validation Worker

```bash
python run_validation_worker.py
```

### 3. Send Test Data

Use the API ingestion endpoints (from Task 2.1):

```bash
# Send tutor data
curl -X POST http://localhost:8000/api/v1/ingest/tutor \
  -H "Content-Type: application/json" \
  -d '{
    "tutor_id": "tutor_00001",
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "age": 28,
    ...
  }'
```

### 4. Monitor Validation

Watch the worker logs for validation results:

```
INFO - Processing 1 messages from tutormax:tutors
INFO - Valid tutor: tutor_00001
INFO - Stats: processed=1, valid=1, invalid=0
```

## Common Use Cases

### Validate Data Programmatically

```python
from src.pipeline.validation import ValidationEngine

engine = ValidationEngine()

# Validate tutor data
tutor_data = {...}
result = engine.validate_tutor(tutor_data)

if result.valid:
    print("Data is valid!")
else:
    for error in result.errors:
        print(f"Error in {error.field}: {error.message}")
```

### Custom Validation

```python
from src.pipeline.validation import TutorValidator

validator = TutorValidator()
result = validator.validate(tutor_data)

# Check warnings
for warning in result.warnings:
    print(f"Warning: {warning.message}")
```

## Validation Rules at a Glance

### Tutors
- Email: Valid format
- Age: 22-65
- Baseline sessions: 5-30/week
- Subjects: 1-10 from approved list

### Sessions
- Engagement: 0.0-1.0
- Duration: 30/45/60/90 minutes (recommended)
- No-shows: Must not have actual_start

### Feedback
- Ratings: 1-5
- First sessions: Must have would_recommend
- Low ratings: Should have feedback text

## Troubleshooting

### Worker Not Starting

1. Check Redis connection:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. Check environment variables:
   ```bash
   echo $REDIS_HOST
   echo $REDIS_PORT
   ```

### Messages Not Being Validated

1. Check queue has messages:
   ```bash
   redis-cli XLEN tutormax:tutors
   ```

2. Check consumer group exists:
   ```bash
   redis-cli XINFO GROUPS tutormax:tutors
   ```

### High Invalid Message Rate

1. Check dead letter queue:
   ```bash
   redis-cli XLEN tutormax:dead_letter
   ```

2. Inspect failed messages:
   ```python
   from src.queue.consumer import MessageConsumer
   from src.queue.client import RedisClient

   client = RedisClient()
   consumer = MessageConsumer(client)
   messages = consumer.consume("tutormax:dead_letter", count=10)

   for msg in messages:
       print(msg.get("metadata", {}).get("validation_errors"))
   ```

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Worker settings
REDIS_WORKER_BATCH_SIZE=10
REDIS_WORKER_POLL_INTERVAL_MS=1000
```

### Code Configuration

Edit `src/queue/config.py` for advanced settings:
- Message TTL
- Max retries
- Batch sizes
- Timeouts

## Testing

### Run All Tests

```bash
pytest tests/pipeline/validation/ -v
```

### Run Specific Test

```bash
pytest tests/pipeline/validation/test_tutor_validator.py::TestTutorValidator::test_valid_tutor_data -v
```

### Run Demo

```bash
python demo_validation.py
```

## Integration with Other Components

### Upstream: FastAPI (Task 2.1)

Validation worker consumes from:
- `tutormax:tutors`
- `tutormax:sessions`
- `tutormax:feedback`

### Downstream: Enrichment (Task 2.3)

Validation worker publishes to:
- `tutormax:tutors:enrichment`
- `tutormax:sessions:enrichment`
- `tutormax:feedback:enrichment`

## Performance Tips

### Scale Horizontally

Run multiple workers:

```bash
# Terminal 1
python run_validation_worker.py

# Terminal 2
python run_validation_worker.py

# Terminal 3
python run_validation_worker.py
```

Redis automatically distributes messages across workers.

### Optimize Batch Size

For high throughput, increase batch size:

```bash
export REDIS_WORKER_BATCH_SIZE=50
python run_validation_worker.py
```

### Monitor Performance

```python
from src.pipeline.validation.validation_worker import ValidationWorker

worker = ValidationWorker()
stats = worker.get_stats()

print(f"Messages/sec: {stats['messages_processed'] / uptime}")
```

## Next Steps

1. Start validation worker
2. Send test data via API
3. Monitor logs for validation results
4. Check enrichment queues for valid data
5. Check dead letter queue for invalid data

For detailed information, see `TASK_2.2_VALIDATION_REPORT.md`.
