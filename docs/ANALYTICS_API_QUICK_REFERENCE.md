# Analytics API Quick Reference

Quick reference guide for TutorMax Advanced Analytics API endpoints.

## Base URL

```
http://localhost:8000/api/analytics
```

## Endpoints

### 1. Overview & Summary

#### Get Analytics Overview
```bash
GET /overview
```

Returns comprehensive dashboard overview with key metrics.

**Response time:** < 2 seconds

**Example:**
```bash
curl http://localhost:8000/api/analytics/overview
```

---

#### Get Performance Summary
```bash
GET /performance-summary?period=30d
```

**Parameters:**
- `period` (string): Time period (7d, 30d, 90d)

**Example:**
```bash
curl "http://localhost:8000/api/analytics/performance-summary?period=30d"
```

---

### 2. Churn Heatmaps

#### Get Churn Heatmap
```bash
GET /churn-heatmap?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&granularity=weekly
```

**Parameters:**
- `start_date` (optional): Start date (default: 90 days ago)
- `end_date` (optional): End date (default: today)
- `granularity` (string): daily | weekly | monthly

**Response time:** < 500ms

**Example:**
```bash
curl "http://localhost:8000/api/analytics/churn-heatmap?granularity=weekly"
```

**Response:**
```json
{
  "matrix": [[2.5, 3.1, 4.2], [1.8, 2.3, 3.5]],
  "x_labels": ["W1 2025", "W2 2025", "W3 2025"],
  "y_labels": ["Low", "Medium", "High", "Critical"],
  "metadata": {
    "start_date": "2025-08-01T00:00:00",
    "end_date": "2025-11-01T00:00:00",
    "granularity": "weekly",
    "max_churn_rate": 4.2,
    "avg_churn_rate": 2.73
  }
}
```

---

#### Get Churn Heatmap by Tier
```bash
GET /churn-heatmap/by-tier?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

Shows churn patterns across performance tiers.

**Example:**
```bash
curl "http://localhost:8000/api/analytics/churn-heatmap/by-tier"
```

---

### 3. Cohort Analysis

#### Get Cohort Analysis
```bash
GET /cohort-analysis?cohort_by=month&metric=retention&period=monthly
```

**Parameters:**
- `cohort_by` (string): month | quarter | subject
- `metric` (string): retention | churn | performance
- `period` (string): weekly | monthly | quarterly

**Example:**
```bash
curl "http://localhost:8000/api/analytics/cohort-analysis?cohort_by=month&metric=retention&period=monthly"
```

---

#### Get Retention Curve
```bash
GET /cohort-analysis/retention-curve?cohort_id=2025-01
```

**Parameters:**
- `cohort_id` (optional): Specific cohort ID

**Example:**
```bash
curl "http://localhost:8000/api/analytics/cohort-analysis/retention-curve"
```

**Response:**
```json
{
  "time_points_days": [7, 14, 30, 60, 90, 180, 365],
  "retention_rates": [98.5, 95.2, 92.1, 88.5, 85.0, 80.2, 75.5],
  "metadata": {
    "cohort_id": null,
    "curve_type": "retention"
  }
}
```

---

### 4. Intervention Effectiveness

#### Get Intervention Effectiveness
```bash
GET /intervention-effectiveness?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&intervention_type=automated_coaching
```

**Parameters:**
- `start_date` (optional): Start date (default: 90 days ago)
- `end_date` (optional): End date (default: today)
- `intervention_type` (optional): Filter by type

**Example:**
```bash
curl "http://localhost:8000/api/analytics/intervention-effectiveness"
```

**Response:**
```json
{
  "interventions": [
    {
      "intervention_type": "automated_coaching",
      "total_interventions": 150,
      "completion_rate": 85.5,
      "success_rate": 62.3,
      "churn_rate": 8.2,
      "avg_time_to_complete_days": 14.5,
      "effectiveness_score": 75.8
    }
  ],
  "summary": {
    "total_interventions": 450,
    "date_range": {
      "start": "2025-08-01",
      "end": "2025-11-01"
    }
  }
}
```

---

#### Get Intervention Comparison
```bash
GET /intervention-effectiveness/comparison
```

Compares all intervention types side-by-side.

**Example:**
```bash
curl "http://localhost:8000/api/analytics/intervention-effectiveness/comparison"
```

---

#### Get Intervention Funnel
```bash
GET /intervention-effectiveness/funnel?intervention_type=manager_coaching
```

**Parameters:**
- `intervention_type` (required): Type of intervention

**Example:**
```bash
curl "http://localhost:8000/api/analytics/intervention-effectiveness/funnel?intervention_type=manager_coaching"
```

**Response:**
```json
{
  "intervention_type": "manager_coaching",
  "stages": [
    {"stage": "Triggered", "count": 100, "percentage": 100.0},
    {"stage": "In Progress", "count": 75, "percentage": 75.0},
    {"stage": "Completed", "count": 60, "percentage": 60.0},
    {"stage": "Improved", "count": 45, "percentage": 45.0}
  ]
}
```

---

### 5. Predictive Insights

#### Get Predictive Trends
```bash
GET /predictive-insights/trends?forecast_days=30
```

**Parameters:**
- `forecast_days` (integer): Days to forecast (7-90)

**Example:**
```bash
curl "http://localhost:8000/api/analytics/predictive-insights/trends?forecast_days=30"
```

**Response:**
```json
{
  "historical_data": {
    "values": [2.5, 2.7, 2.3, ...],
    "dates": ["2025-10-01", "2025-10-02", ...]
  },
  "forecast": {
    "values": [2.8, 2.9, 3.0, ...],
    "dates": ["2025-11-01", "2025-11-02", ...],
    "confidence_interval": {
      "upper": [3.5, 3.6, 3.8, ...],
      "lower": [2.1, 2.2, 2.2, ...]
    }
  },
  "metadata": {
    "trend": "increasing",
    "slope": 0.0023,
    "forecast_days": 30
  }
}
```

---

#### Get Risk Segments
```bash
GET /predictive-insights/risk-segments
```

Segments tutors by risk level with recommendations.

**Example:**
```bash
curl "http://localhost:8000/api/analytics/predictive-insights/risk-segments"
```

---

### 6. Cache Management

#### Clear Analytics Cache
```bash
POST /cache/clear?cache_key=analytics:overview:abc123
```

**Parameters:**
- `cache_key` (optional): Specific cache key (clears all if not provided)

**Example:**
```bash
# Clear all analytics caches
curl -X POST "http://localhost:8000/api/analytics/cache/clear"

# Clear specific cache
curl -X POST "http://localhost:8000/api/analytics/cache/clear?cache_key=analytics:heatmap:xyz789"
```

---

## Common Workflows

### Daily Ops Dashboard Check
```bash
# Get overview
curl http://localhost:8000/api/analytics/overview

# Check recent intervention effectiveness
curl http://localhost:8000/api/analytics/intervention-effectiveness

# View 30-day churn forecast
curl "http://localhost:8000/api/analytics/predictive-insights/trends?forecast_days=30"
```

### Weekly Analytics Review
```bash
# Get weekly churn heatmap
curl "http://localhost:8000/api/analytics/churn-heatmap?granularity=weekly"

# Review cohort retention
curl "http://localhost:8000/api/analytics/cohort-analysis/retention-curve"

# Compare intervention effectiveness
curl "http://localhost:8000/api/analytics/intervention-effectiveness/comparison"
```

### Monthly Strategic Planning
```bash
# Get 90-day performance summary
curl "http://localhost:8000/api/analytics/performance-summary?period=90d"

# Get monthly churn heatmap
curl "http://localhost:8000/api/analytics/churn-heatmap?granularity=monthly"

# Get risk segmentation
curl "http://localhost:8000/api/analytics/predictive-insights/risk-segments"

# 90-day forecast
curl "http://localhost:8000/api/analytics/predictive-insights/trends?forecast_days=90"
```

---

## Performance Benchmarks

| Endpoint | Target | Typical |
|----------|--------|---------|
| `/overview` | < 2s | ~1.2s |
| `/churn-heatmap` | < 500ms | ~350ms |
| `/cohort-analysis` | < 1s | ~750ms |
| `/intervention-effectiveness` | < 1s | ~600ms |
| `/predictive-insights/trends` | < 800ms | ~500ms |

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid date format: ..."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to generate churn heatmap: ..."
}
```

## Caching Information

All analytics endpoints use Redis caching with the following TTLs:

- **Heatmap:** 5 minutes
- **Cohort:** 10 minutes
- **Intervention:** 5 minutes
- **Overview:** 2 minutes

Cache keys follow pattern: `analytics:{type}:{hash}`

## Notes

- All dates should be in ISO format: `YYYY-MM-DD`
- Default date ranges are last 90 days
- Timestamps in responses are in ISO 8601 format
- All percentage values are returned as floats (e.g., 85.5 = 85.5%)
- Cache can be cleared manually via the cache management endpoint
