# Grafana SLA Dashboard Integration Guide

This guide explains how to set up Grafana to visualize TutorMax SLA metrics.

## Overview

TutorMax provides comprehensive SLA tracking via API endpoints that can be integrated with Grafana for advanced visualization and alerting.

**Key SLA Metrics:**
- **Insight Latency**: <60 minutes from session end to dashboard update (PRD requirement)
- **System Uptime**: >99.5% availability (PRD requirement)
- **API Response Times**: p95 <500ms, p99 <1000ms

## Quick Access

**Built-in HTML Dashboard:** http://localhost:8000/api/sla/dashboard/view

**API Endpoints:**
- `GET /api/sla/dashboard` - Complete SLA dashboard data
- `GET /api/sla/insight-latency` - Insight latency metrics
- `GET /api/sla/api-response-times` - API response time stats
- `GET /api/sla/violations` - SLA violations

## Grafana Setup

### 1. Install Grafana

```bash
# macOS (via Homebrew)
brew install grafana
brew services start grafana

# Linux (Ubuntu/Debian)
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana
sudo systemctl start grafana-server

# Docker
docker run -d -p 3000:3000 --name=grafana grafana/grafana
```

Access Grafana at: http://localhost:3000 (default login: admin/admin)

### 2. Configure PostgreSQL Data Source

1. Navigate to **Configuration → Data Sources**
2. Click **Add data source**
3. Select **PostgreSQL**
4. Configure:
   ```
   Name: TutorMax DB
   Host: localhost:5432
   Database: tutormax
   User: tutormax
   Password: tutormax_dev
   SSL Mode: disable (for local development)
   ```
5. Click **Save & Test**

### 3. Configure JSON API Data Source (Optional)

For real-time API data:

1. Install JSON API plugin:
   ```bash
   grafana-cli plugins install marcusolsson-json-datasource
   ```
2. Restart Grafana
3. Add data source:
   ```
   Name: TutorMax API
   URL: http://localhost:8000
   ```

### 4. Import SLA Dashboard

#### Option A: Create from Template

Use the provided dashboard JSON (see below) or create manually.

#### Option B: Manual Creation

Create a new dashboard with the following panels:

## Dashboard Panels

### Panel 1: Overall SLA Status
**Type:** Stat
**Query:**
```sql
SELECT
  CASE
    WHEN overall_sla_met THEN 100
    ELSE 0
  END as sla_status
FROM (
  SELECT
    (
      SELECT COUNT(*) * 100.0 / NULLIF(COUNT(*), 0)
      FROM sla_metrics
      WHERE metric_name = 'insight_latency'
        AND meets_sla = true
        AND recorded_at > NOW() - INTERVAL '24 hours'
    ) >= 95 AS overall_sla_met
) t;
```

**Display:**
- Thresholds: Red (0-99), Green (100)
- Unit: Percent (0-100)
- Decimals: 0

### Panel 2: Insight Latency (Average)
**Type:** Time Series
**Query:**
```sql
SELECT
  recorded_at as time,
  metric_value as "Latency (minutes)",
  60 as "SLA Target"
FROM sla_metrics
WHERE metric_name = 'insight_latency'
  AND recorded_at > NOW() - INTERVAL '$__interval'
ORDER BY recorded_at;
```

**Display:**
- Y-axis: Minutes
- Thresholds: Green (0-60), Red (60+)
- Legend: Show

### Panel 3: Insight Latency Distribution
**Type:** Stat
**Query:**
```sql
SELECT
  AVG(metric_value) as "Average",
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY metric_value) as "P50",
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY metric_value) as "P95",
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY metric_value) as "P99"
FROM sla_metrics
WHERE metric_name = 'insight_latency'
  AND recorded_at > NOW() - INTERVAL '24 hours';
```

### Panel 4: System Uptime
**Type:** Gauge
**Query:**
```sql
SELECT
  (COUNT(*) FILTER (WHERE status = 'up') * 100.0 / COUNT(*)) as uptime_percentage
FROM service_health_checks
WHERE checked_at > NOW() - INTERVAL '24 hours';
```

**Display:**
- Min: 0, Max: 100
- Thresholds: Red (0-99.5), Green (99.5-100)
- Unit: Percent

### Panel 5: API Response Time (P95)
**Type:** Time Series
**Query:**
```sql
SELECT
  DATE_TRUNC('minute', recorded_at) as time,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY metric_value) as "P95 Latency (ms)",
  500 as "SLA Target (P95)"
FROM sla_metrics
WHERE metric_name LIKE 'api_response_time_%'
  AND recorded_at > NOW() - INTERVAL '$__interval'
GROUP BY DATE_TRUNC('minute', recorded_at)
ORDER BY time;
```

### Panel 6: API Response Time (P99)
**Type:** Time Series
**Query:**
```sql
SELECT
  DATE_TRUNC('minute', recorded_at) as time,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY metric_value) as "P99 Latency (ms)",
  1000 as "SLA Target (P99)"
FROM sla_metrics
WHERE metric_name LIKE 'api_response_time_%'
  AND recorded_at > NOW() - INTERVAL '$__interval'
GROUP BY DATE_TRUNC('minute', recorded_at)
ORDER BY time;
```

### Panel 7: SLA Violations (Last 24 Hours)
**Type:** Table
**Query:**
```sql
SELECT
  recorded_at as "Time",
  metric_name as "Metric",
  metric_value as "Value",
  metric_unit as "Unit",
  threshold as "Threshold"
FROM sla_metrics
WHERE meets_sla = false
  AND recorded_at > NOW() - INTERVAL '24 hours'
ORDER BY recorded_at DESC
LIMIT 50;
```

### Panel 8: SLA Compliance Rate
**Type:** Bar Gauge
**Query:**
```sql
SELECT
  'Insight Latency' as metric,
  (COUNT(*) FILTER (WHERE meets_sla = true) * 100.0 / COUNT(*)) as compliance_rate
FROM sla_metrics
WHERE metric_name = 'insight_latency'
  AND recorded_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
  'API Response Time' as metric,
  (COUNT(*) FILTER (WHERE meets_sla = true) * 100.0 / COUNT(*)) as compliance_rate
FROM sla_metrics
WHERE metric_name LIKE 'api_response_time_%'
  AND recorded_at > NOW() - INTERVAL '24 hours';
```

**Display:**
- Orientation: Horizontal
- Thresholds: Red (0-95), Yellow (95-99), Green (99-100)

## Alert Configuration

### Alert 1: Insight Latency SLA Violation

**Condition:**
```sql
SELECT AVG(metric_value)
FROM sla_metrics
WHERE metric_name = 'insight_latency'
  AND recorded_at > NOW() - INTERVAL '1 hour'
```

**Alert Rule:**
- Condition: WHEN avg() OF query(A, 1h, now) IS ABOVE 60
- Frequency: Every 5m
- For: 10m

**Notification:**
- Send to: Email, Slack, PagerDuty
- Message: "Insight latency exceeds 60 minute SLA target"

### Alert 2: Uptime Below Target

**Condition:**
```sql
SELECT
  (COUNT(*) FILTER (WHERE status = 'up') * 100.0 / COUNT(*)) as uptime
FROM service_health_checks
WHERE checked_at > NOW() - INTERVAL '1 hour';
```

**Alert Rule:**
- Condition: WHEN avg() OF query(A, 1h, now) IS BELOW 99.5
- Frequency: Every 1m
- For: 5m

### Alert 3: API Response Time Degradation

**Condition:**
```sql
SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY metric_value)
FROM sla_metrics
WHERE metric_name LIKE 'api_response_time_%'
  AND recorded_at > NOW() - INTERVAL '15 minutes';
```

**Alert Rule:**
- Condition: WHEN percentile(0.95) OF query(A, 15m, now) IS ABOVE 500
- Frequency: Every 1m
- For: 5m

## Using the JSON API Data Source

For real-time data from API endpoints:

### Insight Latency Panel
**Query URL:** `http://localhost:8000/api/sla/insight-latency?hours=24`
**Path:** `$.average_latency_minutes`

### API Response Times Panel
**Query URL:** `http://localhost:8000/api/sla/api-response-times?hours=24`
**Paths:**
- P50: `$.p50_ms`
- P95: `$.p95_ms`
- P99: `$.p99_ms`

### Complete Dashboard Panel
**Query URL:** `http://localhost:8000/api/sla/dashboard?hours=24`
**Use JSONPath to extract specific metrics**

## Best Practices

1. **Refresh Intervals:**
   - Real-time panels: 10s-30s
   - Historical panels: 1m-5m
   - Summary panels: 5m-15m

2. **Time Ranges:**
   - Overview dashboard: Last 24 hours
   - Detailed analysis: Last 7 days with drill-down
   - Trend analysis: Last 30 days

3. **Alert Thresholds:**
   - Insight Latency: Alert if >60 min for >10 minutes
   - Uptime: Alert immediately if <99.5%
   - API Response: Alert if P95 >500ms for >5 minutes

4. **Performance:**
   - Use time-series aggregation for long periods
   - Limit table queries to recent data
   - Cache dashboard queries when possible

## Dashboard Export/Import

Save this dashboard JSON template:

```json
{
  "dashboard": {
    "title": "TutorMax SLA Dashboard",
    "tags": ["tutormax", "sla", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Overall SLA Status",
        "type": "stat",
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "title": "Insight Latency",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 18, "x": 6, "y": 0}
      }
    ],
    "refresh": "30s",
    "time": {"from": "now-24h", "to": "now"}
  }
}
```

## Troubleshooting

### No Data in Panels
- Verify PostgreSQL connection
- Check that SLA tracking is running
- Ensure health checks are recording data

### Slow Queries
- Add indexes on `recorded_at` and `metric_name`
- Use time-series aggregation
- Reduce time range for complex queries

### Alerts Not Triggering
- Verify alert conditions
- Check notification channels
- Review Grafana logs: `/var/log/grafana/`

## Additional Resources

- Grafana Documentation: https://grafana.com/docs/
- TutorMax API Docs: http://localhost:8000/docs
- SLA Dashboard API: http://localhost:8000/api/sla/dashboard/view
