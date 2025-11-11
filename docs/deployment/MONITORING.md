# TutorMax Monitoring & Logging Guide

This document describes the monitoring and logging setup for TutorMax in production.

## Table of Contents

- [Overview](#overview)
- [Built-in Monitoring](#built-in-monitoring)
- [Application Metrics](#application-metrics)
- [Celery Worker Monitoring](#celery-worker-monitoring)
- [Log Aggregation](#log-aggregation)
- [Alerting](#alerting)
- [External Monitoring (Optional)](#external-monitoring-optional)
- [Performance Monitoring](#performance-monitoring)

## Overview

TutorMax uses a multi-layered monitoring approach:

1. **Render Built-in Monitoring**: CPU, memory, request metrics
2. **FastAPI Health Endpoints**: Application-level health checks
3. **Celery Flower**: Worker monitoring dashboard
4. **Structured Logging**: JSON-formatted logs for analysis
5. **External Integrations**: Optional Sentry, Datadog, etc.

## Built-in Monitoring

### Render Dashboard Metrics

Every service in Render provides built-in metrics:

**Available Metrics:**
- CPU usage (%)
- Memory usage (MB)
- Request rate (req/s)
- Response time (ms)
- Error rate (%)
- Network I/O

**Accessing Metrics:**
1. Log in to Render Dashboard
2. Navigate to service (e.g., tutormax-api)
3. Click "Metrics" tab
4. View real-time and historical data

**Alerts:**
Configure alerts in Render Dashboard:
- Settings → Notifications
- Set thresholds for CPU, memory, response time
- Configure notification channels (email, Slack, PagerDuty)

### Service Health Checks

Render performs automatic health checks on web services.

**FastAPI Health Endpoint:**
```
GET https://tutormax-api.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

**Health Check Configuration (in render.yaml):**
```yaml
healthCheckPath: /health
```

Render will restart the service if health checks fail repeatedly.

## Application Metrics

### FastAPI Metrics Endpoints

TutorMax provides several monitoring endpoints:

**1. Basic Health Check**
```bash
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

**2. Database Health Check**
```bash
GET /api/health/database

Response:
{
  "status": "healthy",
  "database": "connected",
  "latency_ms": 5.2
}
```

**3. Redis Health Check**
```bash
GET /api/health/redis

Response:
{
  "status": "healthy",
  "redis": "connected",
  "latency_ms": 1.8
}
```

**4. System Metrics**
```bash
GET /api/metrics

Response:
{
  "uptime_seconds": 86400,
  "requests_total": 12345,
  "requests_per_second": 10.5,
  "active_connections": 42,
  "database": {
    "pool_size": 5,
    "connections_active": 2,
    "connections_idle": 3
  },
  "redis": {
    "connected_clients": 8,
    "used_memory_mb": 15.6,
    "hit_rate": 0.95
  }
}
```

### Custom Metrics Implementation

Add custom metrics to your application:

```python
# src/api/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request counter
request_counter = Counter(
    'tutormax_requests_total',
    'Total requests by endpoint',
    ['method', 'endpoint', 'status']
)

# Response time histogram
request_duration = Histogram(
    'tutormax_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# Active users gauge
active_users = Gauge(
    'tutormax_active_users',
    'Number of currently active users'
)

# Usage in FastAPI
from fastapi import Request
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    request_counter.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    return response
```

## Celery Worker Monitoring

### Flower Dashboard

Flower is a web-based tool for monitoring Celery workers.

**Deployment (Optional):**

Add to render.yaml:

```yaml
- type: web
  name: tutormax-flower
  runtime: python
  region: oregon
  plan: starter
  buildCommand: pip install -r requirements.txt
  startCommand: celery -A src.workers.celery_app flower --port=$PORT --url_prefix=flower
  envVars:
    - key: POSTGRES_HOST
      fromDatabase:
        name: tutormax-postgres
        property: host
    # ... (same as workers)
```

**Access:** `https://tutormax-api.onrender.com/flower`

**Flower Features:**
- Real-time task monitoring
- Worker status and statistics
- Task history and details
- Task retry and revoke
- Broker monitoring (Redis)

### Worker Health Endpoints

Built-in worker monitoring endpoints:

**1. Worker Health Status**
```bash
GET /api/workers/health

Response:
{
  "status": "healthy",
  "workers": {
    "data_generation": {
      "status": "online",
      "tasks_active": 2,
      "tasks_processed": 1245
    },
    "evaluation": {
      "status": "online",
      "tasks_active": 1,
      "tasks_processed": 856
    },
    "prediction": {
      "status": "online",
      "tasks_active": 0,
      "tasks_processed": 432
    },
    "training": {
      "status": "online",
      "tasks_active": 1,
      "tasks_processed": 12
    }
  },
  "beat": {
    "status": "online",
    "scheduled_tasks": 5
  }
}
```

**2. Worker Dashboard**
```bash
GET /api/workers/dashboard

Returns HTML dashboard with worker statistics
```

**3. Worker Statistics**
```bash
GET /api/workers/stats

Response:
{
  "tasks_pending": 15,
  "tasks_active": 4,
  "tasks_completed_today": 1250,
  "tasks_failed_today": 3,
  "average_task_duration_seconds": 12.5,
  "queues": {
    "data_generation": 5,
    "evaluation": 3,
    "prediction": 2,
    "training": 1,
    "default": 4
  }
}
```

### Worker Monitoring Script

Monitor workers from command line:

```bash
# Check worker status
celery -A src.workers.celery_app inspect active

# Check registered tasks
celery -A src.workers.celery_app inspect registered

# Check worker stats
celery -A src.workers.celery_app inspect stats

# Check scheduled tasks
celery -A src.workers.celery_app inspect scheduled

# Check reserved tasks
celery -A src.workers.celery_app inspect reserved
```

## Log Aggregation

### Structured Logging

TutorMax uses structured JSON logging for easy parsing and analysis.

**Log Configuration (src/api/config.py):**

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# Apply JSON formatter
for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())
```

**Usage in Application:**

```python
import logging

logger = logging.getLogger(__name__)

# Basic logging
logger.info("User logged in", extra={"user_id": 123})

# Error logging
try:
    # ... some operation
    pass
except Exception as e:
    logger.error(
        "Failed to process task",
        extra={"task_id": task.id, "user_id": user.id},
        exc_info=True
    )
```

### Accessing Logs in Render

**Live Logs:**
1. Render Dashboard → Service → Logs
2. Click "Live" to stream real-time logs
3. Use search/filter to find specific entries

**Log Retention:**
- Free tier: 7 days
- Starter: 7 days
- Standard: 30 days
- Pro: 90 days

**Download Logs:**
```bash
# Via Render CLI
render logs tutormax-api --tail=1000 > logs.txt
```

### Log Levels

Configure via `LOG_LEVEL` environment variable:

- `DEBUG`: Verbose logging (development only)
- `INFO`: General information (production default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

**Production Recommendation:** `INFO` or `WARNING`

## Alerting

### Render Alerts

Configure alerts in Render Dashboard:

**Available Alert Types:**
- Service down
- High CPU usage (> 80%)
- High memory usage (> 80%)
- High error rate (> 5%)
- Slow response time (> 1000ms)
- Failed deployments

**Notification Channels:**
- Email
- Slack
- PagerDuty
- Webhook

**Setup:**
1. Render Dashboard → Service → Settings
2. Navigate to "Notifications"
3. Add notification channel
4. Configure alert thresholds

### Application-Level Alerts

Implement custom alerting in application:

```python
# src/api/alert_service.py
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertService:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("ALERT_WEBHOOK_URL")

    async def send_alert(
        self,
        message: str,
        severity: AlertSeverity,
        context: dict = None
    ):
        """Send alert to configured channel"""
        alert_data = {
            "message": message,
            "severity": severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "tutormax-api",
            "context": context or {}
        }

        # Log alert
        logger.warning(f"Alert: {message}", extra=context)

        # Send to webhook (Slack, Teams, etc.)
        if self.webhook_url:
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.webhook_url,
                    json=alert_data,
                    timeout=5.0
                )

# Usage
alert_service = AlertService()

# Send alert on error
await alert_service.send_alert(
    message="High error rate detected",
    severity=AlertSeverity.ERROR,
    context={"error_count": 50, "timeframe": "5m"}
)
```

## External Monitoring (Optional)

### Sentry (Error Tracking)

**Setup:**

```bash
pip install sentry-sdk[fastapi]
```

```python
# src/api/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "production"),
    integrations=[
        FastApiIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% of transactions
)
```

**Environment Variable:**
```bash
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

### Datadog (Full-Stack Monitoring)

**Setup:**

```bash
pip install ddtrace
```

**Run with Datadog:**
```bash
ddtrace-run uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
DD_SERVICE=tutormax-api
DD_ENV=production
DD_VERSION=1.0.0
DD_AGENT_HOST=localhost
DD_TRACE_ENABLED=true
DD_LOGS_INJECTION=true
```

### New Relic

**Setup:**

```bash
pip install newrelic
```

```bash
newrelic-admin run-program uvicorn src.api.main:app
```

**Configuration:** `newrelic.ini`

## Performance Monitoring

### Database Query Monitoring

Monitor slow queries:

```python
# src/database/database.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging
import time

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start_time"].pop(-1)

    # Log slow queries (> 1 second)
    if total > 1.0:
        logger.warning(
            f"Slow query detected: {total:.2f}s",
            extra={
                "query": statement[:200],
                "duration_seconds": total
            }
        )
```

### API Response Time Tracking

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:
        logger.warning(
            f"Slow request: {request.url.path}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "duration_seconds": process_time
            }
        )

    return response
```

### Memory Usage Monitoring

```python
import psutil
import os

def get_memory_usage():
    """Get current process memory usage"""
    process = psutil.Process(os.getpid())
    return {
        "rss_mb": process.memory_info().rss / 1024 / 1024,
        "percent": process.memory_percent()
    }

# Log periodically
@app.on_event("startup")
async def log_memory_usage():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        memory = get_memory_usage()
        logger.info("Memory usage", extra=memory)
```

## Monitoring Checklist

Production monitoring checklist:

- [ ] Render alerts configured for all services
- [ ] Health check endpoints responding correctly
- [ ] Log level set to INFO or WARNING
- [ ] Structured logging (JSON) enabled
- [ ] Worker monitoring endpoints accessible
- [ ] Flower dashboard deployed (optional)
- [ ] Database query monitoring enabled
- [ ] Slow request logging enabled
- [ ] Error tracking configured (Sentry)
- [ ] External monitoring integrated (Datadog/New Relic)
- [ ] Alert webhooks tested (Slack/PagerDuty)
- [ ] Log aggregation tested
- [ ] Performance baselines established
- [ ] Monitoring documentation updated

---

**Monitoring configured successfully!** 📊

For questions or issues, refer to:
- Render Docs: https://render.com/docs/monitoring
- Celery Flower: https://flower.readthedocs.io/
- Sentry: https://docs.sentry.io/
