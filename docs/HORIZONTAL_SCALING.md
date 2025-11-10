# Horizontal Scaling Guide for TutorMax

This guide covers deploying and managing TutorMax in a horizontally scaled configuration for high availability and performance.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Component Details](#component-details)
4. [Scaling Operations](#scaling-operations)
5. [Monitoring & Health Checks](#monitoring--health-checks)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

---

## Architecture Overview

### Scaled Deployment Components

```
┌─────────────────┐
│   NGINX Load    │  ← Entry point (Port 80/443)
│    Balancer     │     - Distributes requests
└────────┬────────┘     - Health checks
         │              - Rate limiting
         │
    ┌────┴────┬─────────┬─────────┐
    │         │         │         │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐    │
│ API-1 │ │ API-2 │ │ API-3 │    │  ← Stateless FastAPI instances
└───┬───┘ └───┬───┘ └───┬───┘    │
    └─────────┴─────────┘         │
              │                   │
    ┌─────────┴─────────┐         │
    │                   │         │
┌───▼───────┐     ┌─────▼──────┐ │
│ PostgreSQL│     │   Redis    │ │  ← Data layer
│  Primary  │────►│   Master   │ │
└───┬───────┘     └─────┬──────┘ │
    │                   │         │
┌───▼───────┐     ┌─────▼──────┐ │
│PostgreSQL │     │   Redis    │ │  ← Replicas
│  Replica  │     │  Replica   │ │
└───────────┘     └────────────┘ │
                                  │
                  ┌───────────────┘
                  │
          ┌───────▼────────┐
          │ Celery Workers │  ← Background tasks
          │   (2+ nodes)   │
          └────────────────┘
```

### Key Features

- **Load Balancing**: NGINX distributes traffic across 3+ API instances
- **Database Replication**: PostgreSQL primary + read replica
- **Cache Redundancy**: Redis master + replica with Sentinel
- **Stateless APIs**: All API instances are identical and stateless
- **Horizontal Scalability**: Add more API instances as needed
- **High Availability**: Automatic failover for Redis and PostgreSQL

---

## Quick Start

### Prerequisites

```bash
# Required tools
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM recommended
- Multi-core CPU recommended
```

### 1. Start Scaled Deployment

```bash
# Clone repository
git clone https://github.com/your-org/tutormax.git
cd tutormax

# Start all services
docker-compose -f compose.scaled.yml up -d

# Check status
docker-compose -f compose.scaled.yml ps

# View logs
docker-compose -f compose.scaled.yml logs -f
```

### 2. Verify Deployment

```bash
# Test load balancer
curl http://localhost/health

# Check API instances
curl http://localhost/api/health

# Verify database replication
docker exec tutormax-postgres-primary psql -U tutormax -c "SELECT * FROM replication_status;"

# Check Redis replication
docker exec tutormax-redis-master redis-cli INFO replication
```

### 3. Stop Deployment

```bash
# Stop all services
docker-compose -f compose.scaled.yml down

# Stop and remove volumes (⚠️ destroys data)
docker-compose -f compose.scaled.yml down -v
```

---

## Component Details

### NGINX Load Balancer

**Configuration**: `nginx/nginx.conf`

**Features**:
- Least-connection load balancing algorithm
- Health checks on all API instances
- Rate limiting (100 req/min per IP)
- Gzip compression
- WebSocket support with sticky sessions
- Security headers

**Endpoints**:
- `http://localhost` - Main entry point
- `http://localhost/health` - Health check
- `http://localhost/api/*` - API routes
- `http://localhost/ws` - WebSocket endpoint

**Monitoring**:
```bash
# View NGINX logs
docker logs tutormax-nginx -f

# Check active connections
docker exec tutormax-nginx nginx -V

# Reload configuration
docker exec tutormax-nginx nginx -s reload
```

### API Instances

**Count**: 3 (scalable to N instances)

**Characteristics**:
- ✅ Stateless - no session storage
- ✅ Identical - same code, same config
- ✅ Independent - can be deployed/restarted independently
- ✅ Auto-recovery - Docker restart policies

**Scaling**:
```bash
# Scale to 5 instances
docker-compose -f compose.scaled.yml up -d --scale api=5

# Scale down to 2 instances
docker-compose -f compose.scaled.yml up -d --scale api=2
```

**Environment Variables**:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis cache URL
- `CELERY_BROKER_URL` - Task queue broker
- `API_INSTANCE_ID` - Unique instance identifier
- `WORKERS` - Number of Uvicorn workers per container

### PostgreSQL Replication

**Architecture**: Primary (read/write) + Replica (read-only)

**Primary Server** (`postgres-primary`):
- Port: 5432
- Accepts all write operations
- Streams WAL to replica
- Handles DDL migrations

**Replica Server** (`postgres-replica`):
- Port: 5433
- Read-only queries
- Automatically syncs from primary
- Used for analytics and reporting

**Replication Status**:
```bash
# Check replication lag
docker exec tutormax-postgres-primary psql -U tutormax -d tutormax -c \
  "SELECT * FROM replication_status;"

# Verify replica is receiving data
docker exec tutormax-postgres-replica psql -U tutormax -d tutormax -c \
  "SELECT pg_is_in_recovery();"
# Should return 't' (true)
```

**Read/Write Splitting** (application code):
```python
# Write operations → Primary
engine_write = create_async_engine("postgresql+asyncpg://...@postgres-primary:5432/...")

# Read operations → Replica
engine_read = create_async_engine("postgresql+asyncpg://...@postgres-replica:5432/...")
```

### Redis High Availability

**Architecture**: Master + Replica + Sentinel

**Redis Master** (`redis-master`):
- Port: 6379
- Handles all write operations
- Replicates to replica server

**Redis Replica** (`redis-replica`):
- Port: 6380
- Read-only access
- Automatic sync from master

**Redis Sentinel** (`redis-sentinel`):
- Port: 26379
- Monitors master health
- Automatic failover on master failure
- Promotes replica to master if needed

**Failover Testing**:
```bash
# Simulate master failure
docker stop tutormax-redis-master

# Watch Sentinel logs
docker logs tutormax-redis-sentinel -f
# Should show: "+failover-triggered", "+promoted-slave"

# Restart original master (becomes replica)
docker start tutormax-redis-master
```

### Celery Workers

**Purpose**: Process background tasks asynchronously

**Worker Types**:
- `celery-worker-1`, `celery-worker-2` - Task processors
- `celery-beat` - Scheduled task coordinator

**Tasks**:
- Daily metrics aggregation
- Performance calculations
- Email notifications
- Data exports
- Model training

**Scaling Workers**:
```bash
# Add more workers
docker-compose -f compose.scaled.yml up -d --scale celery-worker=4

# Monitor tasks
docker exec tutormax-celery-worker-1 celery -A src.workers.celery_app inspect active
```

---

## Scaling Operations

### Vertical Scaling (More Resources)

**Increase Container Resources**:

```yaml
# In compose.scaled.yml
services:
  api-1:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Horizontal Scaling (More Instances)

**Scale API Instances**:
```bash
# Gradually increase
docker-compose -f compose.scaled.yml up -d --scale api=5   # 5 instances
docker-compose -f compose.scaled.yml up -d --scale api=10  # 10 instances

# Monitor performance
watch -n 1 'docker stats --no-stream | grep api'
```

**Scale Celery Workers**:
```bash
# Add more background task processors
docker-compose -f compose.scaled.yml up -d --scale celery-worker=5
```

### Auto-Scaling (Cloud Platforms)

**AWS ECS Example**:
```json
{
  "scalingPolicies": [
    {
      "targetTrackingScaling": {
        "targetValue": 70.0,
        "predefinedMetricType": "ECSServiceAverageCPUUtilization"
      }
    }
  ]
}
```

**Kubernetes HPA Example**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tutormax-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tutormax-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring & Health Checks

### Application Health

**Health Check Endpoints**:
```bash
# Load balancer health
curl http://localhost/health

# Individual API instance health
docker exec tutormax-api-1 curl http://localhost:8000/health
docker exec tutormax-api-2 curl http://localhost:8000/health
docker exec tutormax-api-3 curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0",
  "instance_id": "api-1"
}
```

### Database Monitoring

```bash
# Active connections
docker exec tutormax-postgres-primary psql -U tutormax -c \
  "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Replication lag
docker exec tutormax-postgres-primary psql -U tutormax -c \
  "SELECT pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes FROM replication_status;"

# Slow queries
docker exec tutormax-postgres-primary psql -U tutormax -c \
  "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Redis Monitoring

```bash
# Memory usage
docker exec tutormax-redis-master redis-cli INFO memory | grep used_memory_human

# Hit rate
docker exec tutormax-redis-master redis-cli INFO stats | grep keyspace

# Connected clients
docker exec tutormax-redis-master redis-cli CLIENT LIST
```

### Container Resource Usage

```bash
# Real-time stats
docker stats

# CPU and memory usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## Troubleshooting

### API Instance Not Responding

```bash
# Check logs
docker logs tutormax-api-1 --tail=100

# Restart instance
docker restart tutormax-api-1

# NGINX will automatically route around failed instances
```

### Database Replication Lag

```bash
# Check lag
docker exec tutormax-postgres-primary psql -U tutormax -c \
  "SELECT pg_wal_lsn_diff(sent_lsn, replay_lsn) FROM replication_status;"

# If lag > 100MB, investigate:
# 1. Network bandwidth
# 2. Replica disk I/O
# 3. Replica CPU usage
```

### Redis Failover Issues

```bash
# Check Sentinel status
docker exec tutormax-redis-sentinel redis-cli -p 26379 SENTINEL master tutormax-master

# Manual failover
docker exec tutormax-redis-sentinel redis-cli -p 26379 SENTINEL failover tutormax-master
```

### High CPU Usage

```bash
# Identify high-CPU containers
docker stats --no-stream | sort -k 3 -h

# Check slow queries (if database is high)
docker exec tutormax-postgres-primary psql -U tutormax -c \
  "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Memory Leaks

```bash
# Monitor memory over time
watch -n 5 'docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"'

# If memory keeps growing:
# 1. Check application logs
# 2. Review connection pooling
# 3. Verify cache TTLs
# 4. Restart affected instances
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Load testing completed (Task 11.5)
- [ ] Monitoring dashboard configured (Task 11.7)
- [ ] Database backups configured
- [ ] SSL certificates obtained
- [ ] Environment variables secured
- [ ] Resource limits set
- [ ] Logging aggregation configured
- [ ] Alerting rules configured

### Deployment Steps

1. **Prepare Environment**:
   ```bash
   # Set production environment variables
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

2. **Deploy Infrastructure**:
   ```bash
   # Start services
   docker-compose -f compose.scaled.yml --env-file .env.production up -d
   ```

3. **Run Migrations**:
   ```bash
   docker exec tutormax-api-1 alembic upgrade head
   ```

4. **Verify Deployment**:
   ```bash
   # Health checks
   curl https://your-domain.com/health

   # Load test
   ./scripts/load_tests/run_baseline_test.sh
   ```

5. **Monitor**:
   ```bash
   # Watch logs
   docker-compose -f compose.scaled.yml logs -f --tail=100
   ```

### Blue-Green Deployment

```bash
# Deploy new version to "green" environment
docker-compose -f compose.scaled.green.yml up -d

# Run smoke tests
curl http://green-loadbalancer/health

# Switch DNS/load balancer to green
# Update DNS: tutormax.com → green-loadbalancer

# Monitor for issues
# If problems: switch back to blue
# If stable: decommission blue
```

### Rolling Updates

```bash
# Update one instance at a time
docker-compose -f compose.scaled.yml up -d --no-deps --build api-1
# Wait 30 seconds, verify health
docker-compose -f compose.scaled.yml up -d --no-deps --build api-2
# Wait 30 seconds, verify health
docker-compose -f compose.scaled.yml up -d --no-deps --build api-3
```

---

## Performance Tuning

### NGINX Tuning

```nginx
# Increase worker connections for high traffic
worker_connections 4096;

# Adjust buffer sizes
proxy_buffer_size 8k;
proxy_buffers 16 8k;
```

### Database Connection Pooling

```python
# SQLAlchemy connection pool settings
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Base pool size
    max_overflow=40,       # Additional connections under load
    pool_pre_ping=True,    # Verify connections
    pool_recycle=3600      # Recycle connections every hour
)
```

### Redis Memory Optimization

```bash
# Increase maxmemory if needed
docker exec tutormax-redis-master redis-cli CONFIG SET maxmemory 1gb

# Adjust eviction policy
docker exec tutormax-redis-master redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## Next Steps

1. **Set up monitoring dashboard** → See Task 11.7
2. **Configure auto-scaling** → Cloud-specific
3. **Implement CI/CD pipeline** → GitHub Actions
4. **Set up log aggregation** → ELK stack or similar
5. **Configure alerting** → PagerDuty, Opsgenie, etc.

---

## Resources

- [NGINX Load Balancing](https://nginx.org/en/docs/http/load_balancing.html)
- [PostgreSQL Replication](https://www.postgresql.org/docs/current/runtime-config-replication.html)
- [Redis Sentinel](https://redis.io/docs/management/sentinel/)
- [Docker Compose Scaling](https://docs.docker.com/compose/compose-file/deploy/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/optimizing.html)
