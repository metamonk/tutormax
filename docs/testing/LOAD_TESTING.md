# Load Testing Guide for TutorMax

This guide covers load testing the TutorMax platform using Locust.

## Overview

**Target Capacity**: 30,000 sessions/day (~21 sessions/minute, ~0.35 sessions/second)

**Testing Tool**: Locust (Python-based load testing framework)

## Prerequisites

```bash
# Install Locust
pip install locust

# Or use requirements.txt
pip install -r requirements.txt
```

## Quick Start

### 1. Start the API Server

```bash
# Terminal 1: Start FastAPI backend
cd /path/to/tutormax
source venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Run Load Tests

```bash
# Terminal 2: Run Locust with Web UI
locust -f locustfile.py --host=http://localhost:8000

# Then open: http://localhost:8089
```

**Web UI Parameters**:
- **Number of users**: Start with 50, increase to 100-200 for stress testing
- **Spawn rate**: 5-10 users/second
- **Host**: http://localhost:8000

## Test Scenarios

The `locustfile.py` defines 6 realistic user behaviors:

### 1. Dashboard User (40% of traffic)
- **Behavior**: Operations manager viewing real-time dashboard
- **Endpoints**:
  - `GET /api/dashboard/metrics`
  - `GET /api/performance/analytics`
  - `GET /api/alerts?status=active`
  - `GET /api/interventions?status=pending`
- **Wait time**: 5-15 seconds between requests

### 2. Session Creator (20% of traffic)
- **Behavior**: Creating and updating tutoring sessions
- **Endpoints**:
  - `POST /api/sessions` - Create new session
  - `PATCH /api/sessions/{id}` - Update session
- **Wait time**: 10-30 seconds between requests
- **Target**: Simulates 30,000 sessions/day creation rate

### 3. Tutor Performance Viewer (15% of traffic)
- **Behavior**: Viewing tutor profiles and metrics
- **Endpoints**:
  - `GET /api/tutors?include_metrics=true`
  - `GET /api/tutors/{id}`
  - `GET /api/tutors/{id}/sessions`
  - `GET /api/tutors/{id}/recommendations`
- **Wait time**: 8-20 seconds between requests

### 4. Intervention Manager (15% of traffic)
- **Behavior**: Managing and assigning interventions
- **Endpoints**:
  - `GET /api/interventions?status=pending`
  - `GET /api/interventions/{id}`
  - `POST /api/interventions/{id}/assign`
  - `POST /api/interventions/{id}/outcome`
- **Wait time**: 10-25 seconds between requests

### 5. Admin User (5% of traffic)
- **Behavior**: User management operations
- **Endpoints**:
  - `GET /api/admin/users`
  - `GET /api/admin/users/{id}`
  - `PATCH /api/admin/users/{id}/roles`
- **Wait time**: 15-40 seconds between requests

### 6. Student Feedback User (5% of traffic)
- **Behavior**: Submitting post-session feedback
- **Endpoints**:
  - `POST /api/feedback/{token}`
- **Wait time**: 60-180 seconds between requests

## Running Tests

### Web UI Mode (Recommended for Development)

```bash
# Start with web UI
locust -f locustfile.py --host=http://localhost:8000

# Open http://localhost:8089 and configure:
# - Number of users: 100
# - Spawn rate: 10
# - Host: http://localhost:8000
```

### Headless Mode (Recommended for CI/CD)

```bash
# Light load test (baseline performance)
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --html reports/load-test-light.html

# Medium load test (normal operations)
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless \
  --html reports/load-test-medium.html

# Heavy load test (stress test)
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 200 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless \
  --html reports/load-test-heavy.html

# Peak load test (simulate 10x traffic)
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 500 \
  --spawn-rate 20 \
  --run-time 15m \
  --headless \
  --html reports/load-test-peak.html
```

### Distributed Mode (For Very High Load)

```bash
# Master node
locust -f locustfile.py --master --host=http://localhost:8000

# Worker nodes (run on multiple machines/terminals)
locust -f locustfile.py --worker --master-host=localhost
locust -f locustfile.py --worker --master-host=localhost
locust -f locustfile.py --worker --master-host=localhost
```

## Performance Targets

### Response Time Targets (p95)
- **Dashboard endpoints**: < 200ms
- **Session creation**: < 300ms
- **User queries**: < 150ms
- **Analytics endpoints**: < 500ms
- **Feedback submission**: < 200ms

### Throughput Targets
- **Sessions/day**: 30,000 (21/min, 0.35/sec)
- **Dashboard requests**: 500/min peak
- **Concurrent users**: 100-200 simultaneous
- **Request success rate**: > 99.5%

### Resource Targets
- **CPU usage**: < 70% under normal load
- **Memory usage**: < 80% of available
- **Database connections**: < 50% of pool
- **Cache hit rate**: > 80%

## Analyzing Results

### Key Metrics to Monitor

1. **Response Times**
   - Median (50th percentile)
   - 95th percentile
   - 99th percentile
   - Maximum

2. **Request Stats**
   - Requests per second (RPS)
   - Failures per second
   - Success rate %

3. **System Resources** (use separate monitoring)
   - CPU usage
   - Memory usage
   - Database query times
   - Redis cache hit rate

### HTML Reports

Locust generates detailed HTML reports with:
- Response time charts
- Request distribution
- Failure analysis
- Percentile breakdown

```bash
# Reports are saved to:
reports/load-test-{type}.html

# Open in browser:
open reports/load-test-medium.html
```

### Interpreting Results

**Good Performance Indicators**:
- ✅ p95 response time < 200ms for most endpoints
- ✅ Failure rate < 0.5%
- ✅ Stable performance over test duration
- ✅ No memory leaks (flat memory usage)
- ✅ No connection pool exhaustion

**Warning Signs**:
- ⚠️ Response times increasing over time
- ⚠️ Failure rate > 1%
- ⚠️ CPU usage > 80%
- ⚠️ Database connections approaching limit
- ⚠️ Memory usage growing linearly

**Critical Issues**:
- 🔴 p95 response time > 1000ms
- 🔴 Failure rate > 5%
- 🔴 CPU at 100%
- 🔴 Out of memory errors
- 🔴 Database connection exhaustion

## Bottleneck Identification

### Common Bottlenecks

1. **Database Queries**
   - **Symptom**: High database CPU, slow queries
   - **Check**: `EXPLAIN ANALYZE` slow queries
   - **Fix**: Add indexes, optimize queries

2. **Unindexed Queries**
   - **Symptom**: Query time increases with data volume
   - **Check**: PostgreSQL slow query log
   - **Fix**: Add strategic indexes

3. **N+1 Queries**
   - **Symptom**: Many small queries for related data
   - **Check**: SQLAlchemy query logs
   - **Fix**: Use `joinedload()` or `selectinload()`

4. **Insufficient Caching**
   - **Symptom**: Repeated expensive computations
   - **Check**: Redis cache hit rate
   - **Fix**: Implement Redis caching for hot data

5. **Blocking I/O**
   - **Symptom**: High response times, low throughput
   - **Check**: Async/await usage
   - **Fix**: Ensure all I/O is async

6. **Memory Leaks**
   - **Symptom**: Memory usage growing over time
   - **Check**: Memory profiling tools
   - **Fix**: Review object lifecycle, connection cleanup

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Testing

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install locust

      - name: Start API server
        run: |
          uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
          sleep 5

      - name: Run load tests
        run: |
          locust -f locustfile.py \
            --host=http://localhost:8000 \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --headless \
            --html reports/load-test.html \
            --csv reports/load-test

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-reports
          path: reports/

      - name: Check performance thresholds
        run: |
          # Parse CSV and fail if p95 > 500ms
          python scripts/check_performance_thresholds.py
```

## Best Practices

### 1. Test Incrementally
- Start with low user count (10-20)
- Gradually increase to target load
- Identify breaking points

### 2. Test Realistic Scenarios
- Mix different user behaviors
- Use realistic wait times
- Simulate actual data patterns

### 3. Monitor System Resources
- Use `htop`, `docker stats`, or cloud monitoring
- Watch database connections
- Check Redis memory usage

### 4. Run Tests Regularly
- Weekly performance regression tests
- Before major releases
- After infrastructure changes

### 5. Isolate Test Environment
- Don't run against production
- Use representative test data
- Match production resource allocation

### 6. Document Baselines
- Record performance benchmarks
- Track improvements over time
- Set up alerts for degradation

## Troubleshooting

### Connection Refused Errors
```bash
# Ensure API is running
curl http://localhost:8000/health

# Check port binding
lsof -i :8000
```

### High Failure Rates
```bash
# Check API logs
tail -f logs/api.log

# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis connectivity
redis-cli ping
```

### Memory Issues
```bash
# Monitor memory during test
watch -n 1 'free -h'

# Check for memory leaks
python -m memory_profiler src/api/main.py
```

### Slow Response Times
```bash
# Profile slow endpoints
python -m cProfile -o profile.stats src/api/main.py

# Analyze with snakeviz
snakeviz profile.stats
```

## Resources

- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/performance/)
- [PostgreSQL Query Optimization](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Performance Tuning](https://redis.io/topics/optimization)

## Next Steps

After establishing load testing:
1. Set up performance monitoring dashboard (Task 11.7)
2. Implement horizontal scaling (Task 11.6)
3. Configure auto-scaling based on metrics
4. Set up alerting for performance degradation
