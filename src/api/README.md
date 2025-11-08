# TutorMax Data Ingestion API

FastAPI application for receiving and queuing tutor performance data from the synthetic data generation engine.

## Overview

This API provides REST endpoints to ingest:
- **Tutor profiles** - Demographics, subjects, behavioral archetypes
- **Session data** - Session details, engagement scores, behaviors
- **Student feedback** - Ratings, comments, recommendations

All incoming data is validated using Pydantic models and queued in Redis for downstream processing by the data pipeline.

## Features

- **Async/await** for non-blocking I/O
- **Pydantic validation** ensuring data quality
- **Redis message queuing** for reliable data processing
- **CORS support** for frontend access
- **Health checks** for monitoring
- **Batch endpoints** for efficient bulk ingestion
- **Queue statistics** for operational visibility

## Architecture

```
Data Generator → FastAPI → Redis Queue → Data Processing Pipeline
                    ↓
                 Validation
```

## Endpoints

### Health & Monitoring

- `GET /health` - Health check with Redis status
- `GET /` - API information and endpoint list
- `GET /api/queue/stats` - Current queue statistics

### Data Ingestion

#### Tutors
- `POST /api/tutors` - Ingest single tutor profile
- `POST /api/tutors/batch` - Ingest multiple tutor profiles

#### Sessions
- `POST /api/sessions` - Ingest single session
- `POST /api/sessions/batch` - Ingest multiple sessions

#### Feedback
- `POST /api/feedback` - Ingest single feedback
- `POST /api/feedback/batch` - Ingest multiple feedbacks

## Quick Start

### Prerequisites

- Python 3.11+
- Redis server running (default: localhost:6379)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment (optional):
```bash
cp .env.example .env
# Edit .env with your settings
```

### Running the Server

#### Development mode:
```bash
cd src/api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Production mode:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Using the main module:
```bash
python -m src.api.main
```

### Access the API

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Configuration

Configuration is managed through environment variables (optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `False` | Enable debug mode |
| `API_PREFIX` | `/api` | API route prefix |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_MAX_CONNECTIONS` | `10` | Redis connection pool size |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed CORS origins |

## Example Usage

### Ingest a Tutor Profile

```bash
curl -X POST http://localhost:8000/api/tutors \
  -H "Content-Type: application/json" \
  -d '{
    "tutor_id": "tutor_00001",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "age": 28,
    "location": "New York",
    "education_level": "Master'\''s Degree",
    "subjects": ["Mathematics", "Algebra"],
    "subject_type": "STEM",
    "onboarding_date": "2024-01-15T10:00:00",
    "tenure_days": 120,
    "behavioral_archetype": "high_performer",
    "baseline_sessions_per_week": 20,
    "status": "active",
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-05-14T10:00:00"
  }'
```

### Ingest a Session

```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "tutor_id": "tutor_00001",
    "student_id": "student_00042",
    "session_number": 3,
    "is_first_session": false,
    "scheduled_start": "2024-05-14T15:00:00",
    "actual_start": "2024-05-14T15:02:00",
    "duration_minutes": 60,
    "subject": "Algebra",
    "session_type": "1-on-1",
    "tutor_initiated_reschedule": false,
    "no_show": false,
    "late_start_minutes": 2,
    "engagement_score": 0.92,
    "learning_objectives_met": true,
    "technical_issues": false,
    "created_at": "2024-05-14T15:00:00",
    "updated_at": "2024-05-14T16:05:00"
  }'
```

### Check Queue Statistics

```bash
curl http://localhost:8000/api/queue/stats
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_api.py -v

# Run with coverage
pytest tests/test_api.py --cov=src/api --cov-report=html

# Run specific test class
pytest tests/test_api.py::TestTutorEndpoints -v
```

## Redis Queues

The API uses three Redis queues for different data types:

- `tutormax:queue:tutors` - Tutor profiles
- `tutormax:queue:sessions` - Session data
- `tutormax:queue:feedbacks` - Student feedback

Each queued message has the structure:
```json
{
  "data": { /* original data */ },
  "queued_at": "2024-05-14T10:00:00",
  "queue": "tutormax:queue:sessions"
}
```

## Data Models

### Tutor Profile
- **tutor_id**: Unique identifier
- **name**: Full name
- **email**: Email address (validated)
- **age**: 18-100
- **location**: City/location
- **education_level**: Education level
- **subjects**: List of subjects (1-10)
- **subject_type**: STEM, Language, or TestPrep
- **behavioral_archetype**: high_performer, at_risk, new_tutor, steady, churner
- **baseline_sessions_per_week**: 0-50
- **status**: active, inactive, suspended
- **onboarding_date**: ISO datetime
- **tenure_days**: Days since onboarding

### Session Data
- **session_id**: UUID
- **tutor_id**: Reference to tutor
- **student_id**: Reference to student
- **session_number**: Session count for this pairing
- **is_first_session**: Boolean flag
- **scheduled_start**: ISO datetime
- **actual_start**: ISO datetime (null if no-show)
- **duration_minutes**: 0-300
- **subject**: Subject taught
- **session_type**: 1-on-1, group, workshop
- **tutor_initiated_reschedule**: Boolean
- **no_show**: Boolean
- **late_start_minutes**: 0-60
- **engagement_score**: 0.0-1.0
- **learning_objectives_met**: Boolean
- **technical_issues**: Boolean

### Feedback Data
- **feedback_id**: UUID
- **session_id**: Reference to session
- **student_id**: Reference to student
- **tutor_id**: Reference to tutor
- **overall_rating**: 1-5
- **subject_knowledge_rating**: 1-5
- **communication_rating**: 1-5
- **patience_rating**: 1-5
- **engagement_rating**: 1-5
- **helpfulness_rating**: 1-5
- **free_text_feedback**: Text (0-5000 chars)
- **is_first_session**: Boolean
- **would_recommend**: Boolean (first session only)
- **improvement_areas**: List (first session only)

## Performance

- Designed to handle **3,000 sessions/day** (low volume for FastAPI)
- Async/await for concurrent request handling
- Redis queuing ensures <1 hour latency
- Scales horizontally with multiple workers

## Error Handling

- **422 Unprocessable Entity**: Validation errors (detailed in response)
- **503 Service Unavailable**: Redis connection failed
- **500 Internal Server Error**: Unexpected errors
- **400 Bad Request**: Empty batch or malformed request

All error responses include:
```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2024-05-14T10:00:00"
}
```

## Integration with Data Generator

The API is designed to receive data from the synthetic data generation engine (Task 1):

```python
from src.data_generation.tutor_generator import TutorGenerator
from src.data_generation.session_generator import SessionGenerator
from src.data_generation.feedback_generator import FeedbackGenerator
import requests

# Generate data
tutor_gen = TutorGenerator()
tutors = tutor_gen.generate_tutors(count=10)

# Send to API
for tutor in tutors:
    response = requests.post(
        "http://localhost:8000/api/tutors",
        json=tutor
    )
    print(f"Queued: {response.json()}")
```

## Next Steps

After this component (Task 2.1), the pipeline will continue with:
- **Task 2.2**: Data validation module
- **Task 2.3**: Data enrichment process
- **Task 2.4**: PostgreSQL storage setup

## License

Part of the TutorMax Performance Evaluation System.
