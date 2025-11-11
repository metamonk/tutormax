# Performance Optimization Quick Start Guide

## TL;DR

TutorMax has been optimized to handle 10x load (30,000 sessions/day). Follow these steps to deploy and monitor.

## Quick Deploy (5 minutes)

### 1. Database Indexes

```bash
cd /Users/zeno/Projects/tutormax
alembic upgrade head
```

### 2. Enable PostgreSQL Extensions

```bash
psql -U tutormax -d tutormax
```

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
\q
```

### 3. Restart API

```bash
# The API will automatically use the new cache and performance middleware
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 4. Verify Performance Features

```bash
# Check cache stats
curl http://localhost:8000/api/performance/cache/stats

# Check query stats
curl http://localhost:8000/api/performance/query/stats

# Get overall health
curl http://localhost:8000/api/performance/summary
```

## Performance Monitoring Dashboard

### Key Endpoints

```bash
# Overall performance summary with recommendations
GET /api/performance/summary

# Cache effectiveness
GET /api/performance/cache/stats

# Query performance
GET /api/performance/query/stats

# Slow queries report
GET /api/performance/database/slow-queries?min_duration_ms=100

# Table statistics
GET /api/performance/database/table/{table_name}/stats

# Index analysis
GET /api/performance/database/table/{table_name}/indexes
```

### Example Response

```json
{
  "timestamp": "2025-11-09T18:00:00Z",
  "health_score": 95.5,
  "cache": {
    "hits": 8542,
    "misses": 1234,
    "hit_rate_percent": 87.4,
    "connected": true
  },
  "queries": {
    "total_queries": 15234,
    "slow_queries": 234,
    "slow_query_rate": 1.54,
    "avg_time_ms": 45.2,
    "p95_time_ms": 89.3
  },
  "recommendations": [
    {
      "type": "general",
      "severity": "info",
      "message": "Performance metrics are healthy",
      "suggestion": "Continue monitoring for degradation"
    }
  ]
}
```

## Load Testing

### Install Locust

```bash
pip install locust
```

### Run Load Test

```bash
# Terminal 1: Start API
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start load test
locust -f tests/load_testing/locustfile.py --host=http://localhost:8000
```

Open http://localhost:8089 and configure:
- **Users:** 100-500
- **Spawn rate:** 10/second
- **Duration:** 10-60 minutes

### Headless Load Test

```bash
locust -f tests/load_testing/locustfile.py \
  --host=http://localhost:8000 \
  --users 300 \
  --spawn-rate 10 \
  --run-time 30m \
  --headless \
  --html load_test_results.html
```

## Performance Targets

| Metric | Target | How to Check |
|--------|--------|--------------|
| Cache hit rate | > 80% | `GET /api/performance/cache/stats` |
| p95 API time | < 200ms | Response header: `X-Response-Time` |
| p95 query time | < 100ms | `GET /api/performance/query/stats` |
| Dashboard load | < 2s | Browser DevTools Network tab |
| Throughput | 200+ req/sec | Locust load test results |

## Scaling Checklist

### When to Scale

Monitor these metrics and scale when you hit these thresholds:

- ✅ API CPU > 70% consistently
- ✅ Database CPU > 80% consistently
- ✅ Cache hit rate < 70%
- ✅ p95 response time > 200ms
- ✅ Queue depth > 1000 items

### Horizontal Scaling

**API Tier:**
```bash
# Deploy additional API instances behind load balancer
# Example with Docker:
docker run -d -p 8001:8000 tutormax-api
docker run -d -p 8002:8000 tutormax-api

# Configure nginx load balancer
upstream api_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

**Database Tier:**
```bash
# Add read replicas for dashboard/analytics queries
# Update connection string for read operations:
DATABASE_READ_URL=postgresql+asyncpg://user:pass@read-replica:5432/tutormax
```

**Cache Tier:**
```bash
# Deploy Redis cluster
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  --cluster-replicas 1
```

## Troubleshooting

### High Cache Miss Rate (< 70%)

**Symptoms:**
- Cache hit rate < 70% in `/api/performance/cache/stats`
- High database load

**Solutions:**
1. Check Redis connection: `GET /health`
2. Review cache TTLs (may be too short)
3. Warm cache for popular data: `POST /api/performance/cache/warm`
4. Increase Redis memory limit

### Slow API Responses (> 200ms p95)

**Symptoms:**
- `X-Response-Time` header > 200ms
- Slow query rate > 10% in query stats

**Solutions:**
1. Check slow queries: `GET /api/performance/database/slow-queries`
2. Verify indexes are applied: `alembic current`
3. Check database CPU utilization
4. Review recent schema changes

### High Database Load

**Symptoms:**
- Database CPU > 80%
- Connection pool exhausted
- Query timeouts

**Solutions:**
1. Verify indexes are applied: `alembic upgrade head`
2. Check for missing indexes: `GET /api/performance/database/table/{table}/index-suggestions`
3. Increase connection pool size in `src/database/database.py`
4. Add read replicas for heavy read operations

### Frontend Performance Issues

**Symptoms:**
- Dashboard load time > 2s
- Large bundle sizes
- Poor Lighthouse scores

**Solutions:**
1. Verify build optimization: `npm run build`
2. Check bundle sizes: `npm run build -- --analyze`
3. Enable Next.js production mode: `npm start`
4. Review component lazy loading

## Cache Management

### Clear Cache

```bash
# Clear all cache
curl -X POST http://localhost:8000/api/performance/cache/clear

# Clear specific pattern
curl -X POST "http://localhost:8000/api/performance/cache/clear?pattern=tutormax:cache:dashboard:*"
```

### Warm Cache

During deployment or after cache clear, warm frequently accessed data:

```bash
# Implement cache warming script
python scripts/warm_cache.py
```

## Database Maintenance

### Weekly Maintenance

```sql
-- Vacuum and analyze all tables
VACUUM ANALYZE;

-- Update statistics
ANALYZE;

-- Check for bloat
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Monitor Index Usage

```sql
-- Check unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexname NOT LIKE 'pg_toast%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Production Checklist

Before deploying to production:

- [ ] Run database migrations: `alembic upgrade head`
- [ ] Enable pg_stat_statements extension
- [ ] Configure PostgreSQL settings (shared_buffers, work_mem)
- [ ] Set up Redis persistence (RDB + AOF)
- [ ] Configure environment variables for caching
- [ ] Run baseline load test
- [ ] Set up monitoring alerts
- [ ] Configure backup schedule
- [ ] Document rollback procedure
- [ ] Test cache invalidation on data updates
- [ ] Verify rate limiting is enabled
- [ ] Test with production-like data volume

## Monitoring Alerts

Set up alerts for these conditions:

```bash
# Alert when cache hit rate < 70%
if cache_hit_rate < 70:
    alert("Cache performance degraded")

# Alert when p95 API time > 300ms
if p95_response_time > 300:
    alert("API response time degraded")

# Alert when slow query rate > 15%
if slow_query_rate > 15:
    alert("Database performance degraded")

# Alert when error rate > 1%
if error_rate > 1:
    alert("High error rate detected")
```

## Getting Help

If you encounter issues:

1. Check performance summary: `GET /api/performance/summary`
2. Review recommendations in summary response
3. Check logs for errors: `tail -f logs/api.log`
4. Run database diagnostics: `GET /api/performance/database/slow-queries`
5. Verify all optimizations are deployed

## Additional Resources

- Full documentation: `/docs/TASK_11_PERFORMANCE_OPTIMIZATION.md`
- Load testing guide: `/tests/load_testing/locustfile.py`
- Database optimization: `/src/database/query_optimizer.py`
- Cache configuration: `/src/api/cache_service.py`
