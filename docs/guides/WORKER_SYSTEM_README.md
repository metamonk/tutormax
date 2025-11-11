# TutorMax Background Worker System

Complete documentation for the TutorMax Celery-based background worker infrastructure.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Workers](#workers)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Error Handling](#error-handling)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Overview

The TutorMax worker system provides scalable background job processing using **Celery** with **Redis** as the message broker. The system is designed to handle the PRD requirements of **3,000 sessions per day** with room for growth.

### Key Features

✅ **Four Specialized Workers**:
- Synthetic Data Generator (continuous)
- Performance Evaluator (every 15 minutes)
- Churn Predictor (event-driven + daily batch)
- ML Model Trainer (daily at 2am)

✅ **Production-Ready Infrastructure**:
- Automatic retry with exponential backoff
- Circuit breaker pattern for external services
- Comprehensive error handling and logging
- Health checks and monitoring
- Graceful shutdown handling

✅ **Scalability**:
- Horizontal scaling via multiple workers
- Queue-based task routing
- Rate limiting (125/min = 3000/day capacity)
- Connection pooling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                  (Port 8000)                                 │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Worker Monitoring API                                │   │
│  │  - /api/workers/health                                │   │
│  │  - /api/workers/metrics                               │   │
│  │  - /api/workers/queues                                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Redis Broker                              │
│                  (Port 6379)                                 │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ data_gen     │  │ evaluation   │  │ prediction   │      │
│  │ queue        │  │ queue        │  │ queue        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ training     │  │ default      │                         │
│  │ queue        │  │ queue        │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Celery Workers                              │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Data Generation Worker (2 concurrent)                │   │
│  │  - generate_synthetic_data                            │   │
│  │  - generate_data_continuous                           │   │
│  │  - cleanup_old_data                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Evaluation Worker (2 concurrent)                     │   │
│  │  - evaluate_tutor_performance (every 15 min)         │   │
│  │  - evaluate_single_tutor (on-demand)                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Prediction Worker (2 concurrent)                     │   │
│  │  - batch_predict_churn (daily at midnight)           │   │
│  │  - predict_churn_for_tutor (event-driven)            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Training Worker (1 concurrent)                       │   │
│  │  - train_models (daily at 2am)                        │   │
│  │  - train_models_on_demand                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                         │
│                  (Port 5432)                                 │
│                                                               │
│  - Tutors, Sessions, Students                                │
│  - Performance Metrics                                        │
│  - Churn Predictions                                          │
└─────────────────────────────────────────────────────────────┘

     Monitoring: Flower (Port 5555) + Prometheus + API
```

## Workers

### 1. Synthetic Data Generator

**Purpose**: Generate synthetic tutoring session data continuously.

**Tasks**:
- `generate_synthetic_data` - Generate batch of data on-demand
- `generate_data_continuous` - Scheduled continuous generation
- `cleanup_old_data` - Cleanup old data (retention management)

**Configuration**:
```python
# Environment variables
WORKER_DATA_GEN_BATCH_SIZE=100  # Sessions per batch
WORKER_DATA_GEN_INTERVAL_SECONDS=60  # Generation interval
```

**Usage**:
```python
from src.workers.tasks.data_generator import generate_synthetic_data

# Generate 500 sessions
result = generate_synthetic_data.delay(
    num_tutors=50,
    num_sessions=500,
    target_date="2025-01-08"
)
```

### 2. Performance Evaluator

**Purpose**: Calculate tutor performance metrics every 15 minutes.

**Tasks**:
- `evaluate_tutor_performance` - Scheduled evaluation (every 15 min)
- `evaluate_single_tutor` - On-demand single tutor evaluation

**Metrics Calculated**:
- Sessions completed
- Average rating
- First session success rate
- Reschedule rate
- No-show count
- Engagement score
- Learning objectives met %
- Response time average
- Performance tier

**Configuration**:
```python
WORKER_PERF_EVAL_LOOKBACK_MINUTES=15
WORKER_PERF_EVAL_BATCH_SIZE=100
```

### 3. Churn Predictor

**Purpose**: Predict tutor churn using ML model.

**Tasks**:
- `batch_predict_churn` - Daily batch prediction (midnight)
- `predict_churn_for_tutor` - Event-driven single prediction

**Model**:
- XGBoost classifier
- 58 engineered features
- SHAP explanations included
- Risk levels: LOW, MEDIUM, HIGH, CRITICAL

**Configuration**:
```python
WORKER_CHURN_PREDICTION_THRESHOLD=0.5
WORKER_CHURN_PREDICTION_LOOKBACK_DAYS=30
WORKER_CHURN_BATCH_SIZE=100
```

### 4. ML Model Trainer

**Purpose**: Train and update ML models daily.

**Tasks**:
- `train_models` - Scheduled training (daily at 2am)
- `train_models_on_demand` - Manual training trigger

**Models Trained**:
- Churn prediction model (XGBoost)
- Future: Performance prediction, recommendation models

**Output**:
- Versioned models in `output/models/YYYYMMDD_HHMMSS/`
- Latest model symlink: `output/models/churn_model_latest.pkl`
- Evaluation metrics JSON
- Training history log

**Configuration**:
```python
WORKER_MODEL_TRAINING_MIN_SAMPLES=100
WORKER_MODEL_TRAINING_TEST_SPLIT=0.2
WORKER_MODEL_SAVE_PATH=output/models
```

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
redis-server

# Start PostgreSQL
# (Configure connection in .env)
```

### Start All Workers

```bash
# Start all workers and Celery Beat
./scripts/start_all_workers.sh
```

This starts:
- 5 Celery worker processes (one per queue)
- Celery Beat scheduler
- Flower monitoring (http://localhost:5555)

### Start Individual Workers

```bash
# Data generation worker
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=data_generation \
    --concurrency=2

# Evaluation worker
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=evaluation \
    --concurrency=2

# Prediction worker
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=prediction \
    --concurrency=2

# Training worker
celery -A src.workers.celery_app worker \
    --loglevel=info \
    --queues=training \
    --concurrency=1

# Start scheduler (required for scheduled tasks)
celery -A src.workers.celery_app beat --loglevel=info
```

### Stop All Workers

```bash
./scripts/stop_all_workers.sh
```

## Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# PostgreSQL
POSTGRES_USER=tutormax
POSTGRES_PASSWORD=tutormax_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tutormax

# Worker settings
WORKER_DATA_GEN_BATCH_SIZE=100
WORKER_PERF_EVAL_BATCH_SIZE=100
WORKER_CHURN_BATCH_SIZE=100
WORKER_MAX_TASK_RETRIES=3
WORKER_RETRY_BACKOFF=60
```

### Celery Configuration

Edit `src/workers/celery_app.py` to modify:
- Task time limits
- Retry policies
- Queue configurations
- Beat schedules

Example - Change evaluation interval:
```python
beat_schedule={
    "evaluate-performance-every-15-min": {
        "task": "src.workers.tasks.performance_evaluator.evaluate_tutor_performance",
        "schedule": crontab(minute="*/30"),  # Changed to 30 minutes
    },
}
```

## Monitoring

### Flower Dashboard

Access at: **http://localhost:5555**

Features:
- Real-time task monitoring
- Worker status
- Task history
- Performance metrics
- Task retry/revoke controls

### API Monitoring

The FastAPI application exposes worker monitoring endpoints:

#### Health Checks

```bash
# Overall health
curl http://localhost:8000/api/workers/health

# Redis health
curl http://localhost:8000/api/workers/health/redis

# Celery workers health
curl http://localhost:8000/api/workers/health/celery

# Database health
curl http://localhost:8000/api/workers/health/database
```

#### Metrics

```bash
# All task metrics
curl http://localhost:8000/api/workers/metrics/tasks

# Specific task metrics
curl http://localhost:8000/api/workers/metrics/tasks/evaluate_tutor_performance
```

#### Queue Status

```bash
# All queues
curl http://localhost:8000/api/workers/queues

# Queue lengths
curl http://localhost:8000/api/workers/queues/lengths
```

#### Dashboard Data

```bash
# Complete monitoring dashboard
curl http://localhost:8000/api/workers/dashboard
```

### Prometheus Integration

Celery exports metrics that can be scraped by Prometheus:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'celery'
    static_configs:
      - targets: ['localhost:5555']
```

## Error Handling

### Automatic Retry

All tasks automatically retry on failure:

```python
# Default retry configuration
autoretry_for = (
    DatabaseConnectionError,
    ExternalServiceError,
    RetryableError,
)
max_retries = 3
retry_backoff = True  # Exponential backoff
retry_backoff_max = 3600  # 1 hour max
retry_jitter = True  # Add randomness
```

### Circuit Breaker

Prevents cascading failures:

```python
from src.workers.error_handling import CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,  # Open after 5 failures
    recovery_timeout=60,  # Wait 60s before retry
)

result = circuit_breaker.call(external_api_call, arg1, arg2)
```

### Custom Exceptions

```python
from src.workers.error_handling import (
    DatabaseConnectionError,  # Retryable
    ModelLoadError,  # Retryable
    DataValidationError,  # Non-retryable
    NonRetryableError,  # Non-retryable
)
```

### Logging

All workers log to:
- Console (INFO level)
- Log files (configurable location)

Log format:
```
2025-01-08 10:30:45 - worker.data_generator - INFO - Generated 100 sessions
```

## Deployment

### Production Checklist

- [ ] Set secure `SECRET_KEY` in environment
- [ ] Use production Redis instance (not localhost)
- [ ] Use production PostgreSQL instance
- [ ] Configure proper logging (centralized logging)
- [ ] Set up monitoring alerts (PagerDuty, email, Slack)
- [ ] Configure Flower authentication
- [ ] Set appropriate worker concurrency based on resources
- [ ] Enable result backend persistence (optional)
- [ ] Set up log rotation
- [ ] Configure automatic restart (systemd, supervisord)

### Systemd Service

Create `/etc/systemd/system/tutormax-workers.service`:

```ini
[Unit]
Description=TutorMax Celery Workers
After=network.target redis.service postgresql.service

[Service]
Type=forking
User=tutormax
WorkingDirectory=/opt/tutormax
ExecStart=/opt/tutormax/scripts/start_all_workers.sh
ExecStop=/opt/tutormax/scripts/stop_all_workers.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tutormax-workers
sudo systemctl start tutormax-workers
sudo systemctl status tutormax-workers
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Start workers
CMD ["celery", "-A", "src.workers.celery_app", "worker", "--loglevel=info"]
```

Docker Compose:
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker-data-gen:
    build: .
    command: celery -A src.workers.celery_app worker --queues=data_generation --concurrency=2
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

  worker-eval:
    build: .
    command: celery -A src.workers.celery_app worker --queues=evaluation --concurrency=2
    depends_on:
      - redis

  beat:
    build: .
    command: celery -A src.workers.celery_app beat
    depends_on:
      - redis

  flower:
    build: .
    command: celery -A src.workers.celery_app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
```

### Render.com Deployment

1. Add `Procfile`:
```
worker: celery -A src.workers.celery_app worker --loglevel=info
beat: celery -A src.workers.celery_app beat --loglevel=info
```

2. Configure environment variables in Render dashboard
3. Create separate services for each worker type
4. Add Redis addon

## Troubleshooting

### Workers Not Starting

```bash
# Check Redis connection
redis-cli ping

# Check Celery can import app
python -c "from src.workers.celery_app import celery_app; print(celery_app)"

# Check for syntax errors
python -m py_compile src/workers/tasks/*.py
```

### Tasks Not Being Processed

```bash
# Check worker is registered
celery -A src.workers.celery_app inspect registered

# Check active workers
celery -A src.workers.celery_app inspect active

# Check queue lengths
redis-cli llen celery:queue:data_generation
```

### Database Connection Errors

```bash
# Test database connection
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:pass@host/db')
engine.connect()
print('Connected!')
"
```

### Memory Issues

```bash
# Monitor worker memory
celery -A src.workers.celery_app inspect stats

# Restart workers after N tasks
# (Add to celery_app.py)
worker_max_tasks_per_child = 1000
```

### Task Stuck/Hung

```bash
# Revoke task
celery -A src.workers.celery_app control revoke <task-id> --terminate

# Purge all tasks from queue
celery -A src.workers.celery_app purge
```

## Performance Tuning

### Concurrency

```bash
# CPU-bound tasks: concurrency = CPU cores
celery -A src.workers.celery_app worker --concurrency=4

# I/O-bound tasks: concurrency = 2-4x CPU cores
celery -A src.workers.celery_app worker --concurrency=8
```

### Prefetch Multiplier

```python
# celery_app.py
worker_prefetch_multiplier = 4  # Tasks to prefetch per worker
```

### Time Limits

```python
# celery_app.py
task_time_limit = 3600  # Hard limit (1 hour)
task_soft_time_limit = 3000  # Soft limit (50 minutes)
```

## API Reference

See individual worker documentation:
- [Data Generator](TASK_15.2_DATA_GENERATOR_WORKER.md)
- [Performance Evaluator](TASK_15.3_PERFORMANCE_EVALUATOR_WORKER.md)
- [Churn Predictor](TASK_15.4_CHURN_PREDICTOR.md)
- [Model Trainer](TASK_15.5_MODEL_TRAINER.md)

## Support

For issues or questions:
1. Check this documentation
2. Review worker logs in `logs/workers/`
3. Check Flower dashboard
4. Review task-specific documentation

---

**Version**: 1.0.0
**Last Updated**: 2025-01-08
