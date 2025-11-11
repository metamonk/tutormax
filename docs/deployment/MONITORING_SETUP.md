# Performance Monitoring Setup Guide

This guide covers setting up comprehensive performance monitoring for TutorMax using Prometheus, Grafana, and custom metrics.

## Table of Contents

1. [Overview](#overview)
2. [Metrics Collection](#metrics-collection)
3. [Prometheus Setup](#prometheus-setup)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Alerting](#alerting)
6. [Custom Metrics](#custom-metrics)

---

## Overview

### Monitoring Stack

```
┌──────────────┐
│  TutorMax    │  Exposes /metrics endpoint
│  FastAPI App │  (Prometheus format)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Prometheus  │  Scrapes metrics every 15s
│   (TSDB)     │  Stores time-series data
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Grafana    │  Visualizes metrics
│ (Dashboards) │  Configures alerts
└──────────────┘
```

### Available Metrics

**HTTP Metrics**:
- `http_requests_total` - Total requests by method/endpoint/status
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Active requests

**Database Metrics**:
- `database_queries_total` - Query count by type
- `database_query_duration_seconds` - Query execution time
- `database_connections_active` - Active connections

**Cache Metrics**:
- `cache_hits_total` / `cache_misses_total` - Cache effectiveness
- `cache_operations_duration_seconds` - Cache operation latency

**Celery Metrics**:
- `celery_tasks_total` - Tasks by name/status
- `celery_task_duration_seconds` - Task execution time
- `celery_queue_length` - Queue backlog

**System Metrics**:
- `system_cpu_usage_percent` - CPU utilization
- `system_memory_usage_bytes` - Memory consumption

**SLA Metrics**:
- `sla_violations_total` - SLA breach count
- `sla_compliance_percent` - Compliance percentage

---

## Metrics Collection

### FastAPI Integration

The metrics are automatically collected via `metrics_exporter.py`:

```python
from src.api.metrics_exporter import setup_metrics

# In main.py
app = FastAPI(...)
setup_metrics(app)  # Enables /metrics endpoint
```

### Accessing Metrics

```bash
# View raw Prometheus metrics
curl http://localhost:8000/metrics

# Sample output:
# http_requests_total{method="GET",endpoint="/api/health",status_code="200"} 1523.0
# http_request_duration_seconds_bucket{method="GET",endpoint="/api/health",le="0.1"} 1450.0
```

---

## Prometheus Setup

### Installation via Docker Compose

Create `prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'tutormax'
    environment: 'production'

# Scrape configurations
scrape_configs:
  - job_name: 'tutormax-api'
    static_configs:
      - targets:
          - 'api-1:8000'
          - 'api-2:8000'
          - 'api-3:8000'
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

# Alerting configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Rule files for alerts
rule_files:
  - 'alerts.yml'
```

### Add to Docker Compose

```yaml
# In compose.scaled.yml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: tutormax-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/alerts.yml:/etc/prometheus/alerts.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - tutormax-network
    restart: unless-stopped

volumes:
  prometheus_data:
    driver: local
```

### Start Prometheus

```bash
docker-compose -f compose.scaled.yml up -d prometheus

# Access Prometheus UI
open http://localhost:9090
```

---

## Grafana Dashboards

### Installation

```yaml
# In compose.scaled.yml
services:
  grafana:
    image: grafana/grafana:latest
    container_name: tutormax-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    depends_on:
      - prometheus
    networks:
      - tutormax-network
    restart: unless-stopped

volumes:
  grafana_data:
    driver: local
```

### Configure Prometheus Datasource

Create `grafana/datasources/prometheus.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

### Pre-built Dashboards

Create `grafana/dashboards/tutormax-dashboard.json`:

**Dashboard Panels**:

1. **HTTP Performance**
   - Request rate (req/s)
   - Response time percentiles (p50, p95, p99)
   - Error rate
   - Active requests

2. **Database Performance**
   - Query rate
   - Connection pool usage
   - Slow queries
   - Replication lag

3. **Cache Performance**
   - Hit rate
   - Operations/second
   - Memory usage
   - Eviction rate

4. **System Resources**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

5. **Celery Tasks**
   - Active tasks
   - Queue length
   - Task success/failure rate
   - Task duration

6. **SLA Compliance**
   - Overall compliance %
   - Violations over time
   - Response time SLA
   - Intervention time SLA

### Access Grafana

```bash
# Start Grafana
docker-compose -f compose.scaled.yml up -d grafana

# Access UI
open http://localhost:3000
# Login: admin / admin
```

### Sample PromQL Queries

```promql
# HTTP request rate
rate(http_requests_total[5m])

# P95 response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate percentage
(rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100

# Cache hit rate
(rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))) * 100

# Database connection usage
(database_connections_active / 100) * 100
```

---

## Alerting

### Alert Manager Setup

```yaml
# In compose.scaled.yml
services:
  alertmanager:
    image: prom/alertmanager:latest
    container_name: tutormax-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./prometheus/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    networks:
      - tutormax-network
    restart: unless-stopped
```

### Alert Manager Configuration

Create `prometheus/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops-team@tutormax.com'
        from: 'alerts@tutormax.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@tutormax.com'
        auth_password: 'your-password'

  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        title: 'TutorMax Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'
```

### Alert Rules

Create `prometheus/alerts.yml`:

```yaml
groups:
  - name: tutormax_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (rate(http_requests_total{status_code=~"5.."}[5m])
          / rate(http_requests_total[5m])) * 100 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High HTTP error rate"
          description: "Error rate is {{ $value }}% (threshold: 5%)"

      # Slow response time
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow API response time"
          description: "P95 latency is {{ $value }}s (threshold: 0.5s)"

      # High database connections
      - alert: DatabaseConnectionPoolExhaustion
        expr: database_connections_active > 80
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearing exhaustion"
          description: "{{ $value }} connections active (limit: 100)"

      # Low cache hit rate
      - alert: LowCacheHitRate
        expr: |
          (rate(cache_hits_total[5m])
          / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))) * 100 < 70
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}% (target: 80%)"

      # High CPU usage
      - alert: HighCPUUsage
        expr: system_cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}% (threshold: 80%)"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (system_memory_usage_bytes
          / (system_memory_usage_bytes + system_memory_available_bytes)) * 100 > 85
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}% (threshold: 85%)"

      # Celery queue backlog
      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 1000
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Large Celery queue backlog"
          description: "{{ $value }} tasks pending in queue"

      # SLA violation
      - alert: SLAViolation
        expr: sla_compliance_percent < 95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "SLA compliance below target"
          description: "SLA compliance is {{ $value }}% (target: 95%)"
```

---

## Custom Metrics

### Adding Application-Specific Metrics

```python
from src.api.metrics_exporter import (
    track_database_query,
    track_cache_operation,
    track_celery_task,
    update_application_metrics,
    track_sla_violation
)

# Track database query
start_time = time.time()
result = await db.execute(query)
duration = time.time() - start_time
track_database_query("SELECT", duration)

# Track cache operation
start_time = time.time()
value = await redis.get(key)
duration = time.time() - start_time
track_cache_operation("get", hit=value is not None, duration=duration)

# Track Celery task
@celery_app.task
def my_task():
    start_time = time.time()
    try:
        # Do work
        duration = time.time() - start_time
        track_celery_task("my_task", "success", duration)
    except Exception as e:
        track_celery_task("my_task", "failure")
        raise

# Update application metrics
update_application_metrics(
    active_users=100,
    active_sessions=250,
    pending_interventions=15
)
```

---

## Best Practices

### 1. Metric Naming

Follow Prometheus conventions:
- `metric_name_unit` (e.g., `http_request_duration_seconds`)
- Use underscores, not dashes
- Include units in metric names
- Use consistent label names

### 2. Cardinality Management

Avoid high-cardinality labels:
- ✅ Good: `{endpoint="/api/users"}`
- ❌ Bad: `{user_id="12345"}` (thousands of unique IDs)

### 3. Dashboard Organization

- Group related metrics together
- Use consistent time ranges
- Set appropriate refresh rates
- Add documentation panels

### 4. Alert Fatigue Prevention

- Set appropriate thresholds
- Use `for` clauses to avoid transient alerts
- Group related alerts
- Define clear runbooks

### 5. Data Retention

```yaml
# Prometheus retention
command:
  - '--storage.tsdb.retention.time=30d'  # Keep 30 days
  - '--storage.tsdb.retention.size=50GB' # Or 50GB max
```

---

## Troubleshooting

### Metrics Not Appearing

```bash
# Check /metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
# UI: http://localhost:9090/targets

# Check Prometheus logs
docker logs tutormax-prometheus
```

### High Cardinality Issues

```bash
# Check cardinality
curl http://localhost:9090/api/v1/label/__name__/values | jq

# Identify high-cardinality metrics
curl http://localhost:9090/api/v1/status/tsdb | jq
```

### Grafana Dashboard Not Loading

```bash
# Check Grafana logs
docker logs tutormax-grafana

# Verify datasource connection
# UI: Grafana > Configuration > Data Sources > Test
```

---

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Alert Manager Guide](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Best Practices](https://prometheus.io/docs/practices/)
