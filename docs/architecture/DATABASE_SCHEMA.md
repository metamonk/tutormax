# TutorMax Database Schema

Complete entity-relationship diagram and schema documentation based on PRD lines 562-703.

## Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                              TUTORS                                 │
├─────────────────────────────────────────────────────────────────────┤
│ PK: tutor_id VARCHAR(50)                                            │
│     name VARCHAR(200)                                               │
│     email VARCHAR(255) UNIQUE                                       │
│     onboarding_date TIMESTAMP                                       │
│     status VARCHAR(50) [active, inactive, churned]                  │
│     subjects VARCHAR[] (array)                                      │
│     education_level VARCHAR(100)                                    │
│     location VARCHAR(200)                                           │
│     baseline_sessions_per_week FLOAT                                │
│     behavioral_archetype VARCHAR(50)                                │
│     created_at TIMESTAMP                                            │
│     updated_at TIMESTAMP                                            │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 │ 1:N
                 │
    ┌────────────┼─────────────┬──────────────┬──────────────┬─────────────┐
    │            │             │              │              │             │
    ▼            ▼             ▼              ▼              ▼             ▼
┌───────────┐ ┌────────┐ ┌──────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────┐
│ SESSIONS  │ │FEEDBACK│ │ METRICS  │ │ PREDICTIONS │ │INTERVENE │ │  EVENTS  │
└───────────┘ └────────┘ └──────────┘ └─────────────┘ └──────────┘ └──────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                            STUDENTS                                 │
├─────────────────────────────────────────────────────────────────────┤
│ PK: student_id VARCHAR(50)                                          │
│     name VARCHAR(200)                                               │
│     age INTEGER                                                     │
│     grade_level VARCHAR(50)                                         │
│     subjects_interested VARCHAR[] (array)                           │
│     created_at TIMESTAMP                                            │
│     updated_at TIMESTAMP                                            │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 │ 1:N
                 │
    ┌────────────┼─────────────┐
    │            │             │
    ▼            ▼             ▼
┌───────────┐ ┌────────┐
│ SESSIONS  │ │FEEDBACK│
└───────────┘ └────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                            SESSIONS                                 │
├─────────────────────────────────────────────────────────────────────┤
│ PK: session_id VARCHAR(50)                                          │
│ FK: tutor_id → tutors.tutor_id (CASCADE)                            │
│ FK: student_id → students.student_id (CASCADE)                      │
│     session_number INTEGER                                          │
│     scheduled_start TIMESTAMP                                       │
│     actual_start TIMESTAMP                                          │
│     duration_minutes INTEGER                                        │
│     subject VARCHAR(100)                                            │
│     session_type VARCHAR(50) [1-on-1, group]                        │
│     tutor_initiated_reschedule BOOLEAN                              │
│     no_show BOOLEAN                                                 │
│     late_start_minutes INTEGER                                      │
│     engagement_score FLOAT                                          │
│     learning_objectives_met BOOLEAN                                 │
│     technical_issues BOOLEAN                                        │
│     created_at TIMESTAMP                                            │
│     updated_at TIMESTAMP                                            │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 │ 1:1
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       STUDENT_FEEDBACK                              │
├─────────────────────────────────────────────────────────────────────┤
│ PK: feedback_id VARCHAR(50)                                         │
│ FK: session_id → sessions.session_id UNIQUE (CASCADE)               │
│ FK: student_id → students.student_id (CASCADE)                      │
│ FK: tutor_id → tutors.tutor_id (CASCADE)                            │
│     overall_rating INTEGER (1-5)                                    │
│     is_first_session BOOLEAN                                        │
│     subject_knowledge_rating INTEGER                                │
│     communication_rating INTEGER                                    │
│     patience_rating INTEGER                                         │
│     engagement_rating INTEGER                                       │
│     helpfulness_rating INTEGER                                      │
│     would_recommend BOOLEAN                                         │
│     improvement_areas VARCHAR[] (array)                             │
│     free_text_feedback TEXT                                         │
│     submitted_at TIMESTAMP                                          │
│     created_at TIMESTAMP                                            │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                  TUTOR_PERFORMANCE_METRICS                          │
├─────────────────────────────────────────────────────────────────────┤
│ PK: metric_id VARCHAR(50)                                           │
│ FK: tutor_id → tutors.tutor_id (CASCADE)                            │
│     calculation_date TIMESTAMP                                      │
│     window VARCHAR(20) [7day, 30day, 90day]                         │
│     sessions_completed INTEGER                                      │
│     avg_rating FLOAT                                                │
│     first_session_success_rate FLOAT                                │
│     reschedule_rate FLOAT                                           │
│     no_show_count INTEGER                                           │
│     engagement_score FLOAT                                          │
│     learning_objectives_met_pct FLOAT                               │
│     response_time_avg_minutes FLOAT                                 │
│     performance_tier VARCHAR(50) [Exemplary, Strong, etc.]          │
│     created_at TIMESTAMP                                            │
│     updated_at TIMESTAMP                                            │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                      CHURN_PREDICTIONS                              │
├─────────────────────────────────────────────────────────────────────┤
│ PK: prediction_id VARCHAR(50)                                       │
│ FK: tutor_id → tutors.tutor_id (CASCADE)                            │
│     prediction_date TIMESTAMP                                       │
│     churn_score INTEGER (0-100)                                     │
│     risk_level VARCHAR(20) [Low, Medium, High, Critical]            │
│     window_1day_probability FLOAT                                   │
│     window_7day_probability FLOAT                                   │
│     window_30day_probability FLOAT                                  │
│     window_90day_probability FLOAT                                  │
│     contributing_factors JSONB                                      │
│     model_version VARCHAR(50)                                       │
│     created_at TIMESTAMP                                            │
│     updated_at TIMESTAMP                                            │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                        INTERVENTIONS                                │
├─────────────────────────────────────────────────────────────────────┤
│ PK: intervention_id VARCHAR(50)                                     │
│ FK: tutor_id → tutors.tutor_id (CASCADE)                            │
│     intervention_type VARCHAR(100)                                  │
│       [automated_coaching, peer_mentoring, PIP, etc.]               │
│     trigger_reason TEXT                                             │
│     recommended_date TIMESTAMP                                      │
│     assigned_to VARCHAR(50)                                         │
│     status VARCHAR(50) [pending, in_progress, completed, cancelled] │
│     due_date TIMESTAMP                                              │
│     completed_date TIMESTAMP                                        │
│     outcome VARCHAR(50) [improved, no_change, declined, churned]    │
│     notes TEXT                                                      │
│     created_at TIMESTAMP                                            │
│     updated_at TIMESTAMP                                            │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                        TUTOR_EVENTS                                 │
├─────────────────────────────────────────────────────────────────────┤
│ PK: event_id VARCHAR(50)                                            │
│ FK: tutor_id → tutors.tutor_id (CASCADE)                            │
│     event_type VARCHAR(100)                                         │
│       [login, reschedule_request, availability_change, etc.]        │
│     event_timestamp TIMESTAMP                                       │
│     metadata JSONB                                                  │
│     created_at TIMESTAMP                                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Indexes

### Performance-Critical Indexes

```sql
-- Tutors
CREATE UNIQUE INDEX ix_tutors_email ON tutors(email);
CREATE INDEX ix_tutors_status ON tutors(status);

-- Sessions
CREATE INDEX ix_sessions_tutor_id ON sessions(tutor_id);
CREATE INDEX ix_sessions_student_id ON sessions(student_id);
CREATE INDEX ix_sessions_scheduled_start ON sessions(scheduled_start);
CREATE INDEX ix_sessions_subject ON sessions(subject);

-- Student Feedback
CREATE UNIQUE INDEX ix_student_feedback_session_id ON student_feedback(session_id);
CREATE INDEX ix_student_feedback_student_id ON student_feedback(student_id);
CREATE INDEX ix_student_feedback_tutor_id ON student_feedback(tutor_id);

-- Tutor Performance Metrics
CREATE INDEX ix_tutor_performance_metrics_tutor_id ON tutor_performance_metrics(tutor_id);
CREATE INDEX ix_tutor_performance_metrics_calculation_date ON tutor_performance_metrics(calculation_date);

-- Churn Predictions
CREATE INDEX ix_churn_predictions_tutor_id ON churn_predictions(tutor_id);
CREATE INDEX ix_churn_predictions_prediction_date ON churn_predictions(prediction_date);
CREATE INDEX ix_churn_predictions_risk_level ON churn_predictions(risk_level);

-- Interventions
CREATE INDEX ix_interventions_tutor_id ON interventions(tutor_id);
CREATE INDEX ix_interventions_status ON interventions(status);

-- Tutor Events
CREATE INDEX ix_tutor_events_tutor_id ON tutor_events(tutor_id);
CREATE INDEX ix_tutor_events_event_type ON tutor_events(event_type);
CREATE INDEX ix_tutor_events_event_timestamp ON tutor_events(event_timestamp);
```

## Data Types & Constraints

### PostgreSQL-Specific Types

| Type | Usage | Example |
|------|-------|---------|
| `VARCHAR[]` | Array fields | `subjects`, `improvement_areas` |
| `JSONB` | Flexible metadata | `contributing_factors`, event `metadata` |
| `TIMESTAMP WITH TIME ZONE` | All timestamps | `created_at`, `scheduled_start` |
| `BOOLEAN` | Flags | `no_show`, `is_first_session` |
| `FLOAT` | Scores/rates | `engagement_score`, `avg_rating` |

### Enums (Stored as VARCHAR)

```python
# Tutor Status
TutorStatus = ["active", "inactive", "churned"]

# Behavioral Archetype
BehavioralArchetype = ["high_performer", "at_risk", "new_tutor", "steady", "churner"]

# Session Type
SessionType = ["1-on-1", "group"]

# Performance Tier
PerformanceTier = ["Exemplary", "Strong", "Developing", "Needs Attention", "At Risk"]

# Risk Level
RiskLevel = ["Low", "Medium", "High", "Critical"]

# Intervention Type
InterventionType = [
    "automated_coaching",
    "training_module",
    "first_session_checkin",
    "rescheduling_alert",
    "manager_coaching",
    "peer_mentoring",
    "performance_improvement_plan",
    "retention_interview",
    "recognition"
]

# Intervention Status
InterventionStatus = ["pending", "in_progress", "completed", "cancelled"]

# Intervention Outcome
InterventionOutcome = ["improved", "no_change", "declined", "churned"]

# Metric Window
MetricWindow = ["7day", "30day", "90day"]
```

## Foreign Key Relationships

### Cascade Behavior

All foreign keys use `ON DELETE CASCADE`:
- When a tutor is deleted, all related sessions, feedback, metrics, predictions, interventions, and events are automatically deleted
- When a student is deleted, all related sessions and feedback are deleted
- When a session is deleted, related feedback is deleted

### Referential Integrity

```sql
-- Sessions reference tutors and students
ALTER TABLE sessions
  ADD CONSTRAINT fk_sessions_tutor
  FOREIGN KEY (tutor_id) REFERENCES tutors(tutor_id) ON DELETE CASCADE;

ALTER TABLE sessions
  ADD CONSTRAINT fk_sessions_student
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE;

-- Feedback references sessions, tutors, and students
ALTER TABLE student_feedback
  ADD CONSTRAINT fk_feedback_session
  FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE;

-- And so on for all foreign keys...
```

## Sample Queries

### Get tutor with recent sessions
```sql
SELECT t.*, s.*
FROM tutors t
LEFT JOIN sessions s ON t.tutor_id = s.tutor_id
WHERE t.tutor_id = 'tutor_123'
  AND s.scheduled_start >= NOW() - INTERVAL '30 days'
ORDER BY s.scheduled_start DESC;
```

### Find high-risk tutors
```sql
SELECT t.name, t.email, cp.churn_score, cp.risk_level
FROM tutors t
JOIN churn_predictions cp ON t.tutor_id = cp.tutor_id
WHERE cp.prediction_date = (
  SELECT MAX(prediction_date)
  FROM churn_predictions
  WHERE tutor_id = t.tutor_id
)
AND cp.churn_score >= 51
ORDER BY cp.churn_score DESC;
```

### Calculate average rating for tutor
```sql
SELECT t.tutor_id, t.name, AVG(sf.overall_rating) as avg_rating
FROM tutors t
JOIN sessions s ON t.tutor_id = s.tutor_id
JOIN student_feedback sf ON s.session_id = sf.session_id
WHERE s.scheduled_start >= NOW() - INTERVAL '30 days'
GROUP BY t.tutor_id, t.name
HAVING COUNT(sf.feedback_id) >= 5;
```

### Get pending interventions by risk level
```sql
SELECT i.*, t.name, cp.risk_level
FROM interventions i
JOIN tutors t ON i.tutor_id = t.tutor_id
JOIN churn_predictions cp ON t.tutor_id = cp.tutor_id
WHERE i.status = 'pending'
  AND cp.prediction_date = (
    SELECT MAX(prediction_date)
    FROM churn_predictions
    WHERE tutor_id = t.tutor_id
  )
ORDER BY cp.churn_score DESC;
```

## Data Volume Estimates

Based on 3,000 sessions/day:

| Table | Daily Inserts | 90-day Total | Disk Space (est.) |
|-------|---------------|--------------|-------------------|
| tutors | ~5 | ~450 | 100 KB |
| students | ~50 | ~4,500 | 1 MB |
| sessions | 3,000 | 270,000 | 50 MB |
| student_feedback | 2,700 | 243,000 | 100 MB |
| tutor_performance_metrics | 1,350 | 40,500 | 10 MB |
| churn_predictions | 450 | 40,500 | 15 MB |
| interventions | ~50 | ~4,500 | 2 MB |
| tutor_events | ~5,000 | 450,000 | 80 MB |
| **Total** | | **~1M rows** | **~360 MB** |

## Maintenance

### Regular Tasks

```sql
-- Analyze tables for query optimization
ANALYZE tutors;
ANALYZE sessions;
ANALYZE student_feedback;

-- Vacuum to reclaim space
VACUUM ANALYZE;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Archival Strategy

For production:
- Archive sessions older than 2 years
- Archive feedback older than 2 years
- Keep performance metrics indefinitely (for trend analysis)
- Keep churn predictions for 1 year
- Archive completed interventions after 1 year

## Schema Evolution

All schema changes should be managed through Alembic migrations:

```bash
# After modifying models.py
alembic revision --autogenerate -m "Description of changes"

# Review generated migration in alembic/versions/
# Edit if necessary

# Apply migration
alembic upgrade head
```

## References

- PRD Lines 562-703: Data Model Specification
- SQLAlchemy 2.0 Documentation
- PostgreSQL 14 Documentation
- Alembic Migration Guide
