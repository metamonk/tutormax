# Real-Time Metrics System Architecture

## System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SESSION COMPLETION EVENT FLOW                        │
└─────────────────────────────────────────────────────────────────────────────┘

1. SESSION COMPLETES
   ────────────────
   ┌──────────────┐
   │  Tutoring    │
   │  Session     │  Tutor completes session with student
   │  Ends        │
   └──────┬───────┘
          │
          │ Session data
          ▼
   ┌──────────────┐
   │  FastAPI     │
   │  Endpoint    │  POST /api/sessions/{id}/complete
   └──────┬───────┘
          │
          │
          ▼


2. DATA PIPELINE (Existing)
   ────────────────────────
   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
   │  Validation  │────────►│ Enrichment   │────────►│  Database    │
   │  Worker      │         │ Worker       │         │  Persister   │
   └──────┬───────┘         └──────┬───────┘         └──────┬───────┘
          │                        │                        │
          │                        │                        │
          ▼                        ▼                        ▼
   tutormax:sessions      tutormax:sessions:       sessions table
          :validation            enrichment          student_feedback


3. REAL-TIME METRICS UPDATE (New)
   ────────────────────────────────
          │
          │ Consumes enriched session events
          ▼
   ┌─────────────────────────────────────┐
   │  MetricsUpdateWorker                │
   │                                     │
   │  ┌──────────────────────────────┐  │
   │  │ 1. Consume Session Event     │  │
   │  └───────────┬──────────────────┘  │
   │              │                      │
   │              ▼                      │
   │  ┌──────────────────────────────┐  │
   │  │ 2. Extract tutor_id          │  │
   │  └───────────┬──────────────────┘  │
   │              │                      │
   │              ▼                      │
   │  ┌──────────────────────────────┐  │
   │  │ 3. Debounce (optional)       │  │
   │  │    Wait 30s for more events  │  │
   │  └───────────┬──────────────────┘  │
   │              │                      │
   │              ▼                      │
   │  ┌──────────────────────────────┐  │
   │  │ 4. Calculate Metrics         │  │
   │  │    - 7-day window            │  │
   │  │    - 30-day window           │  │
   │  │    - 90-day window           │  │
   │  └───────────┬──────────────────┘  │
   │              │                      │
   │              ▼                      │
   │  ┌──────────────────────────────┐  │
   │  │ 5. Save to Database          │  │
   │  └───────────┬──────────────────┘  │
   │              │                      │
   │  ┌───────────▼──────────────────┐  │
   │  │ 6. Acknowledge Event         │  │
   │  └──────────────────────────────┘  │
   └─────────────────────────────────────┘
          │
          │
          ▼
   ┌─────────────────────────────────────┐
   │  tutor_performance_metrics table    │
   │                                     │
   │  - metric_id (PK)                   │
   │  - tutor_id                         │
   │  - window (7day/30day/90day)        │
   │  - calculation_date                 │
   │  - sessions_completed               │
   │  - avg_rating                       │
   │  - first_session_success_rate       │
   │  - reschedule_rate                  │
   │  - no_show_count                    │
   │  - engagement_score                 │
   │  - learning_objectives_met_pct      │
   │  - performance_tier                 │
   └─────────────────────────────────────┘


4. API CONSUMPTION
   ───────────────
          │
          │ REST API queries latest metrics
          ▼
   ┌─────────────────────────────────────┐
   │  GET /api/tutors/{id}/metrics       │
   │                                     │
   │  Returns latest calculated metrics  │
   │  from tutor_performance_metrics     │
   └─────────────────────────────────────┘
```

## Data Flow Timeline

```
Time: 0s
│
│  Session completes
│  ────────────────
│  [Session 1234 with Tutor ABC]
│
▼

Time: 0.1s
│
│  Data Pipeline
│  ─────────────
│  ┌─► Validation (schema check)
│  │
│  ├─► Enrichment (derived fields)
│  │
│  └─► Database (persist session)
│
▼

Time: 0.5s
│
│  Event Published
│  ───────────────
│  Redis: tutormax:sessions:enrichment
│  Message: { tutor_id: "ABC", session_id: "1234", ... }
│
▼

Time: 0.6s
│
│  Worker Consumes
│  ───────────────
│  MetricsUpdateWorker reads event
│  Extracts tutor_id: "ABC"
│
▼

Time: 0.6s - 30.6s
│
│  Debouncing Window (optional)
│  ─────────────────────────────
│  Collecting events for tutor ABC
│  ┌─ Session 1234 (0.6s)
│  ├─ Session 1235 (5.2s)
│  └─ Session 1236 (15.8s)
│
▼

Time: 30.6s
│
│  Metrics Calculation
│  ───────────────────
│  PerformanceCalculator.calculate_metrics()
│  │
│  ├─► 7-day window  (200ms)
│  ├─► 30-day window (350ms)
│  └─► 90-day window (500ms)
│
▼

Time: 31.7s
│
│  Database Persistence
│  ────────────────────
│  INSERT 3 rows into tutor_performance_metrics
│  COMMIT transaction
│
▼

Time: 31.8s
│
│  Event Acknowledged
│  ──────────────────
│  Redis: XACK tutormax:sessions:enrichment
│
▼

Total Latency: 31.8s (well under 60s requirement)
```

## Scaling Strategy

### Horizontal Scaling

```
┌────────────────────────────────────────────────────────┐
│                    Redis Stream                        │
│         tutormax:sessions:enrichment                   │
│                                                        │
│  Messages: [1] [2] [3] [4] [5] [6] [7] [8] [9] [10]  │
└────────────────────────────────────────────────────────┘
                         │
                         │ Consumer Group: metrics-workers
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
         ▼               ▼               ▼               ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ Worker 1 │    │ Worker 2 │    │ Worker 3 │    │ Worker 4 │
   │          │    │          │    │          │    │          │
   │ Msg 1,5,9│    │ Msg 2,6,10│   │ Msg 3,7  │    │ Msg 4,8  │
   └──────────┘    └──────────┘    └──────────┘    └──────────┘
         │               │               │               │
         └───────────────┴───────────────┴───────────────┘
                         │
                         ▼
              tutor_performance_metrics
```

**Benefits:**
- Each event processed by exactly one worker
- Linear scaling with number of workers
- Automatic load balancing via Redis
- Fault tolerance (workers can fail/restart)

### Performance Characteristics

```
┌─────────────────────┬──────────────────┬─────────────────┐
│ Metric              │ Single Worker    │ 4 Workers       │
├─────────────────────┼──────────────────┼─────────────────┤
│ Events/sec          │ 10-15            │ 40-60           │
│ Tutors updated/min  │ 20-30            │ 80-120          │
│ Avg latency         │ 30-45s           │ 15-25s          │
│ Database writes/sec │ 30-45 (3/tutor)  │ 120-180         │
└─────────────────────┴──────────────────┴─────────────────┘
```

## Debouncing Strategy

### Without Debouncing
```
Session 1 (10:00:00) ──► Calculate ──► DB Write (3 rows)
Session 2 (10:00:05) ──► Calculate ──► DB Write (3 rows)
Session 3 (10:00:10) ──► Calculate ──► DB Write (3 rows)
Session 4 (10:00:15) ──► Calculate ──► DB Write (3 rows)

Total: 4 calculations, 12 DB writes
```

### With Debouncing (30s window)
```
Session 1 (10:00:00) ──┐
Session 2 (10:00:05) ──┤
Session 3 (10:00:10) ──┼─► Wait 30s ──► Calculate ──► DB Write (3 rows)
Session 4 (10:00:15) ──┘

Total: 1 calculation, 3 DB writes
Reduction: 75% fewer operations
```

## Integration Points

### 1. With Existing Data Pipeline

```python
# EnrichmentWorker (existing)
# After persisting session to database...
self.publisher.publish(
    "tutormax:sessions:enrichment",
    session_data,
    metadata={"source": "enrichment"}
)

# MetricsUpdateWorker (new)
# Consumes from same queue
messages = self.consumer.consume(
    "tutormax:sessions:enrichment",
    count=10
)
```

### 2. With Performance Calculator

```python
# Worker uses existing calculator
async with get_session() as db:
    calculator = PerformanceCalculator(db)

    metrics = await calculator.calculate_metrics(
        tutor_id=tutor_id,
        window=MetricWindow.THIRTY_DAY
    )

    await calculator.save_metrics(metrics)
```

### 3. With FastAPI Endpoints

```python
# API queries metrics calculated by worker
@app.get("/tutors/{tutor_id}/metrics")
async def get_metrics(tutor_id: str, db: AsyncSession):
    # Get latest metrics from worker calculations
    query = select(TutorPerformanceMetric).where(
        TutorPerformanceMetric.tutor_id == tutor_id
    ).order_by(
        TutorPerformanceMetric.calculation_date.desc()
    ).limit(3)

    result = await db.execute(query)
    return result.scalars().all()
```

## Deployment Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    Production Deployment                   │
└───────────────────────────────────────────────────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FastAPI    │     │   Redis     │     │ PostgreSQL  │
│  Server     │────►│   Cluster   │     │   Primary   │
│  (4 procs)  │     │  (HA mode)  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           │                    │
                    ┌──────┴──────┐            │
                    │             │            │
              ┌─────▼────┐  ┌────▼─────┐      │
              │ Enrichmt │  │ Metrics  │      │
              │ Workers  │  │ Workers  │──────┘
              │ (3 inst) │  │ (2 inst) │
              └──────────┘  └──────────┘

Managed by:
- Systemd (process management)
- Nginx (load balancing for API)
- Prometheus + Grafana (monitoring)
```

## Monitoring & Observability

### Key Metrics to Track

```python
# Worker Health
- events_processed / time         # Throughput
- metrics_calculated / time        # Calculation rate
- errors / events_processed        # Error rate
- pending_updates                  # Queue depth

# Performance
- avg_processing_time_ms           # Latency
- calculation_date - session_start # End-to-end latency
- db_write_time_ms                # Database performance

# Business
- tutors_updated_count            # Coverage
- metrics_staleness               # Data freshness
- performance_tier_distribution   # Tutor health
```

### Alerting Rules

```yaml
# High error rate
alert: MetricsWorkerHighErrorRate
expr: (errors / events_processed) > 0.05
for: 5m
severity: warning

# Processing lag
alert: MetricsWorkerLag
expr: pending_updates > 100
for: 10m
severity: critical

# Worker down
alert: MetricsWorkerDown
expr: up{job="metrics-worker"} == 0
for: 2m
severity: critical
```

## Future Optimizations

1. **Incremental Metrics**
   - Only recalculate when needed
   - Track last calculation per window
   - Update deltas instead of full recalc

2. **Multi-Window Optimization**
   - Single database query for all windows
   - Reuse session data across windows
   - Reduce query overhead by 67%

3. **Predictive Prefetching**
   - Pre-calculate for active tutors
   - Cache frequently accessed metrics
   - Reduce latency to <5s

4. **Real-Time Streaming**
   - WebSocket updates to dashboard
   - Live metric updates in UI
   - No polling required
