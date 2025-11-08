# TutorMax API Quick Start Guide

This guide will help you get the FastAPI data ingestion service up and running.

## Prerequisites

1. **Python 3.11+** installed
2. **Redis** server installed and running
3. **Dependencies** installed

## Step 1: Install Redis

### macOS (using Homebrew):
```bash
brew install redis
brew services start redis
```

### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
```

### Verify Redis is running:
```bash
redis-cli ping
# Should respond with: PONG
```

## Step 2: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

## Step 3: Configure Environment (Optional)

The API works with default settings, but you can customize by creating a `.env` file:

```bash
cp .env.example .env
# Edit .env if needed
```

Default settings:
- API Host: `0.0.0.0`
- API Port: `8000`
- Redis URL: `redis://localhost:6379/0`

## Step 4: Start the FastAPI Server

### Option A: Using Uvicorn directly (recommended for development)
```bash
cd /Users/zeno/Projects/tutormax
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Using Python module
```bash
cd /Users/zeno/Projects/tutormax
python -m src.api.main
```

### Option C: Production mode (multiple workers)
```bash
cd /Users/zeno/Projects/tutormax
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Step 5: Verify the API is Running

### Check health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-05-14T10:00:00",
  "redis_connected": true,
  "version": "0.1.0"
}
```

### View API documentation:
Open in your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Step 6: Run the Demo

The demo generates synthetic data and sends it to the API:

```bash
cd /Users/zeno/Projects/tutormax
python demo_api_ingestion.py
```

This will:
1. Check API health
2. Generate and ingest 15 tutors (5 individual + 10 batch)
3. Generate and ingest 30 sessions
4. Generate and ingest 25 feedback entries
5. Show queue statistics

## Step 7: Test Manual Data Ingestion

### Ingest a tutor profile:
```bash
curl -X POST http://localhost:8000/api/tutors \
  -H "Content-Type: application/json" \
  -d '{
    "tutor_id": "tutor_test_001",
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "age": 30,
    "location": "Boston",
    "education_level": "PhD",
    "subjects": ["Physics", "Chemistry"],
    "subject_type": "STEM",
    "onboarding_date": "2024-01-01T00:00:00",
    "tenure_days": 150,
    "behavioral_archetype": "high_performer",
    "baseline_sessions_per_week": 25,
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-05-14T00:00:00"
  }'
```

### Check queue statistics:
```bash
curl http://localhost:8000/api/queue/stats
```

## Step 8: Run Tests

```bash
cd /Users/zeno/Projects/tutormax
pytest tests/test_api.py -v
```

## Troubleshooting

### Issue: "Connection refused" when accessing API
**Solution**: Make sure the FastAPI server is running on port 8000

### Issue: "Redis unavailable" in health check
**Solution**:
1. Check if Redis is running: `redis-cli ping`
2. If not running, start it: `brew services start redis` (macOS) or `sudo systemctl start redis` (Linux)

### Issue: Import errors
**Solution**: Ensure all dependencies are installed: `pip install -r requirements.txt`

### Issue: Port 8000 already in use
**Solution**:
1. Find process: `lsof -i :8000`
2. Kill it: `kill -9 <PID>`
3. Or use a different port: `uvicorn src.api.main:app --port 8001`

## Next Steps

1. **Explore the API documentation** at http://localhost:8000/docs
2. **Monitor Redis queues** using `redis-cli`:
   ```bash
   redis-cli
   > LLEN tutormax:queue:tutors
   > LLEN tutormax:queue:sessions
   > LLEN tutormax:queue:feedbacks
   ```
3. **Integrate with data generation** from Task 1
4. **Build the data validation module** (Task 2.2)
5. **Set up PostgreSQL storage** (Task 2.4)

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with Redis status |
| GET | `/` | API information |
| GET | `/api/queue/stats` | Queue statistics |
| POST | `/api/tutors` | Ingest single tutor |
| POST | `/api/tutors/batch` | Ingest multiple tutors |
| POST | `/api/sessions` | Ingest single session |
| POST | `/api/sessions/batch` | Ingest multiple sessions |
| POST | `/api/feedback` | Ingest single feedback |
| POST | `/api/feedback/batch` | Ingest multiple feedbacks |

## Monitoring Queue Processing

To monitor what's in the Redis queues:

```bash
# Connect to Redis CLI
redis-cli

# Check queue lengths
LLEN tutormax:queue:tutors
LLEN tutormax:queue:sessions
LLEN tutormax:queue:feedbacks

# Peek at the next item (without removing)
LINDEX tutormax:queue:sessions -1

# Count total items across all queues
EVAL "return redis.call('LLEN', 'tutormax:queue:tutors') + redis.call('LLEN', 'tutormax:queue:sessions') + redis.call('LLEN', 'tutormax:queue:feedbacks')" 0
```

## Performance Notes

- The API is designed to handle **3,000 sessions/day** (very low volume)
- Uses **async/await** for non-blocking I/O
- **Redis queuing** ensures reliable delivery
- Can scale horizontally with multiple workers
- Target latency: **<1 hour** from ingestion to processing

## Support

For detailed API documentation, see: `/Users/zeno/Projects/tutormax/src/api/README.md`
