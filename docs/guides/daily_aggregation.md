# Daily Metrics Aggregation System

## Overview

The Daily Metrics Aggregation system is a batch processing service that calculates and stores tutor performance metrics on a scheduled basis. It processes all active tutors in the system and computes metrics across three time windows: 7-day, 30-day, and 90-day.

## Architecture

### Components

1. **DailyMetricsAggregator** (`src/evaluation/daily_aggregator.py`)
   - Core service class for batch processing
   - Handles tutor retrieval, metric calculation, and database persistence
   - Includes retry logic and error handling
   - Processes tutors in configurable batches

2. **CLI Script** (`scripts/run_daily_aggregation.py`)
   - Command-line interface for manual execution
   - Supports various options for customization
   - Designed for cron scheduling

3. **Demo Script** (`scripts/demo_daily_aggregation.py`)
   - Interactive demonstration of the aggregation system
   - Shows before/after database state
   - Displays detailed results and statistics

## How It Works

### Processing Flow

```
1. Initialize Aggregator
   ├─ Set reference date (defaults to today)
   ├─ Configure batch size and retry settings
   └─ Set time windows to process (7d, 30d, 90d)

2. Retrieve Tutors
   ├─ Query active tutors from database
   ├─ Optional: Filter by specific tutor IDs
   └─ Optional: Include inactive tutors

3. Process in Batches
   └─ For each batch:
       ├─ For each tutor:
       │   ├─ For each time window (7d, 30d, 90d):
       │   │   ├─ Calculate performance metrics
       │   │   └─ Save to database
       │   └─ Record result (success/failure)
       └─ Commit batch to database

4. Generate Summary
   ├─ Count successes and failures
   ├─ Calculate success rate
   ├─ Compile error list
   └─ Log final statistics
```

### Metrics Calculated

For each tutor and each time window, the following metrics are calculated:

1. **Sessions Completed** - Count of completed sessions
2. **Average Rating** - Mean student rating (1-5 scale)
3. **First Session Success Rate** - % of first sessions rated ≥4
4. **Reschedule Rate** - % of tutor-initiated reschedules
5. **No-Show Count** - Number of no-show sessions
6. **Engagement Score** - Composite engagement metric (0-100)
7. **Learning Objectives Met %** - % of sessions meeting objectives
8. **Response Time Average** - Average response time in minutes
9. **Performance Tier** - Assigned tier (Exemplary, Strong, Developing, Needs Attention, At Risk)

### Database Schema

Metrics are stored in the `tutor_performance_metrics` table:

```sql
CREATE TABLE tutor_performance_metrics (
    metric_id VARCHAR(50) PRIMARY KEY,
    tutor_id VARCHAR(50) REFERENCES tutors(tutor_id),
    calculation_date TIMESTAMP WITH TIME ZONE,
    window VARCHAR(10),  -- '7day', '30day', '90day'
    sessions_completed INTEGER,
    avg_rating FLOAT,
    first_session_success_rate FLOAT,
    reschedule_rate FLOAT,
    no_show_count INTEGER,
    engagement_score FLOAT,
    learning_objectives_met_pct FLOAT,
    response_time_avg_minutes FLOAT,
    performance_tier VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## Usage

### Manual Execution

```bash
# Run for today (all active tutors)
python scripts/run_daily_aggregation.py

# Run for specific date
python scripts/run_daily_aggregation.py --date 2025-11-01

# Run for specific tutors
python scripts/run_daily_aggregation.py --tutors tutor_001,tutor_002,tutor_003

# Include inactive tutors
python scripts/run_daily_aggregation.py --include-inactive

# With cleanup of old metrics (90-day retention)
python scripts/run_daily_aggregation.py --cleanup --retention-days 90

# Verbose logging
python scripts/run_daily_aggregation.py --verbose

# Quiet mode (errors only)
python scripts/run_daily_aggregation.py --quiet
```

### Scheduled Execution (Cron)

Add to your crontab (`crontab -e`):

```bash
# Run daily at 2:00 AM
0 2 * * * cd /path/to/tutormax && python scripts/run_daily_aggregation.py >> /var/log/tutormax/aggregation.log 2>&1

# Run daily at 2:00 AM with cleanup
0 2 * * * cd /path/to/tutormax && python scripts/run_daily_aggregation.py --cleanup >> /var/log/tutormax/aggregation.log 2>&1
```

See `scripts/cron_example.txt` for more examples.

### Programmatic Usage

```python
from src.evaluation import run_daily_aggregation
from datetime import datetime

# Run aggregation
summary = await run_daily_aggregation(
    reference_date=datetime(2025, 11, 1),
    tutor_ids=None,  # All active tutors
    include_inactive=False,
    cleanup_old_metrics=True,
    retention_days=90,
)

# Check results
print(f"Processed {summary.total_tutors} tutors")
print(f"Success rate: {summary.success_rate}%")
print(f"Metrics saved: {summary.total_metrics_saved}")
```

### Demo Mode

Run the interactive demo to see the system in action:

```bash
python scripts/demo_daily_aggregation.py
```

This will:
1. Show current database state
2. Run full aggregation
3. Display detailed results
4. Show updated database state with sample metrics

## Configuration

### Environment Variables

Set in `.env` file:

```bash
# Database connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=tutormax
POSTGRES_PASSWORD=your_password
POSTGRES_DB=tutormax
```

### Aggregator Settings

Configure via constructor:

```python
aggregator = DailyMetricsAggregator(
    reference_date=datetime.utcnow(),  # Date to calculate for
    max_retries=3,                     # Retry attempts per tutor
    retry_delay_seconds=5,             # Delay between retries
    batch_size=50,                     # Tutors per database commit
)
```

## Error Handling

### Retry Logic

- Failed calculations are retried up to `max_retries` times
- Configurable delay between retries
- Individual tutor failures don't stop the batch
- All errors are logged and included in the summary

### Error Types

1. **Database Errors**
   - Connection failures → retry with delay
   - Transaction failures → rollback and continue

2. **Calculation Errors**
   - Missing data → log warning, set metric to NULL
   - Invalid data → log error, skip metric

3. **System Errors**
   - Out of memory → reduce batch size
   - Timeout → increase retry delay

### Monitoring

Check logs for:
- Success/failure counts
- Error messages
- Processing time
- Metrics saved

Example log output:

```
2025-11-07 02:00:01 - INFO - Starting daily metrics aggregation...
2025-11-07 02:00:01 - INFO - Found 150 tutors to process
2025-11-07 02:00:05 - INFO - Processing batch 1/3 (50 tutors)
2025-11-07 02:00:25 - INFO - Batch 1/3 committed
...
2025-11-07 02:01:30 - INFO - ================================================================================
2025-11-07 02:01:30 - INFO - DAILY AGGREGATION SUMMARY
2025-11-07 02:01:30 - INFO - ================================================================================
2025-11-07 02:01:30 - INFO - Run date: 2025-11-07
2025-11-07 02:01:30 - INFO - Total tutors: 150
2025-11-07 02:01:30 - INFO - Successful: 148
2025-11-07 02:01:30 - INFO - Failed: 2
2025-11-07 02:01:30 - INFO - Total metrics saved: 444
2025-11-07 02:01:30 - INFO - Success rate: 98.67%
2025-11-07 02:01:30 - INFO - Total runtime: 89.45s
```

## Performance

### Benchmarks

Approximate processing times (depends on data volume and hardware):

| Tutors | Sessions/Tutor | Processing Time |
|--------|----------------|-----------------|
| 100    | 50             | ~30 seconds     |
| 500    | 50             | ~2 minutes      |
| 1,000  | 50             | ~4 minutes      |
| 5,000  | 50             | ~20 minutes     |

### Optimization Tips

1. **Batch Size**
   - Larger batches = fewer commits, faster processing
   - Smaller batches = better error isolation
   - Recommended: 50-100 tutors per batch

2. **Database Connection**
   - Use connection pooling (configured in `database/connection.py`)
   - Ensure pool size matches concurrent load
   - Enable `pool_pre_ping` for connection health checks

3. **Scheduling**
   - Run during low-traffic hours (e.g., 2:00 AM)
   - Avoid running during peak session times
   - Consider splitting large batches across multiple runs

## Maintenance

### Cleanup Old Metrics

Automatically delete metrics older than retention period:

```bash
python scripts/run_daily_aggregation.py --cleanup --retention-days 90
```

Or programmatically:

```python
from src.evaluation import DailyMetricsAggregator
from src.database.connection import get_session

async with get_session() as session:
    aggregator = DailyMetricsAggregator()
    deleted_count = await aggregator.cleanup_old_metrics(
        session,
        retention_days=90
    )
    print(f"Deleted {deleted_count} old metrics")
```

### Database Maintenance

1. **Indexing**
   - Ensure indexes on `tutor_id`, `calculation_date`, `window`
   - Monitor query performance with `EXPLAIN ANALYZE`

2. **Vacuuming**
   - Run `VACUUM ANALYZE tutor_performance_metrics` periodically
   - Consider autovacuum tuning for high-write tables

3. **Archiving**
   - Export old metrics to cold storage
   - Keep recent data (90 days) in hot database

## Troubleshooting

### Common Issues

**Problem:** Aggregation fails with "no tutors found"
- **Solution:** Check database connection and tutor table data

**Problem:** Metrics are NULL for many tutors
- **Solution:** Verify session data exists for the time windows

**Problem:** Processing is very slow
- **Solution:** Reduce batch size, check database indexes, optimize queries

**Problem:** High failure rate
- **Solution:** Check logs for specific errors, verify data integrity

### Debugging

Enable verbose logging:

```bash
python scripts/run_daily_aggregation.py --verbose
```

Check specific tutor:

```bash
python scripts/run_daily_aggregation.py --tutors tutor_123 --verbose
```

## API Reference

### DailyMetricsAggregator

```python
class DailyMetricsAggregator:
    """Batch processing service for daily metrics."""

    def __init__(
        self,
        reference_date: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 5,
        batch_size: int = 50,
    ): ...

    async def run(
        self,
        tutor_ids: Optional[List[str]] = None,
        include_inactive: bool = False,
    ) -> AggregationSummary: ...

    async def cleanup_old_metrics(
        self,
        session: AsyncSession,
        retention_days: int = 90,
    ) -> int: ...
```

### AggregationSummary

```python
@dataclass
class AggregationSummary:
    """Results summary."""
    run_date: datetime
    total_tutors: int
    successful: int
    failed: int
    total_metrics_saved: int
    total_runtime_seconds: float
    errors: List[Dict[str, str]]
    results: List[AggregationResult]

    @property
    def success_rate(self) -> float: ...
    def to_dict(self) -> Dict: ...
```

## Future Enhancements

1. **Parallel Processing**
   - Use asyncio task groups for concurrent tutor processing
   - Improve throughput for large tutor populations

2. **Incremental Updates**
   - Only recalculate for tutors with new data
   - Track last calculation date per tutor

3. **Real-time Metrics**
   - Stream processing for immediate metric updates
   - Event-driven architecture

4. **Advanced Monitoring**
   - Prometheus metrics export
   - Grafana dashboards
   - Alerting on failure thresholds

5. **Data Quality Checks**
   - Validate metric consistency
   - Detect and flag anomalies
   - Generate data quality reports

## References

- [Performance Calculator Documentation](../src/evaluation/performance_calculator.py)
- [Database Models](../src/database/models.py)
- [PRD Section on Performance Evaluation](../docs/prd.txt)
- [Cron Configuration Examples](../scripts/cron_example.txt)
