# Daily Metrics Aggregation - Quick Start Guide

## 5-Minute Setup

### 1. Verify Database Connection

Ensure your `.env` file has database credentials:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=tutormax
POSTGRES_PASSWORD=tutormax_dev
POSTGRES_DB=tutormax
```

### 2. Run the Demo

```bash
python scripts/demo_daily_aggregation.py
```

This will show you:
- Current state of the database
- Live aggregation process
- Results and metrics saved
- Sample metrics from the database

### 3. Manual Execution

```bash
# Run for all active tutors
python scripts/run_daily_aggregation.py

# Run with verbose output
python scripts/run_daily_aggregation.py --verbose

# Run for specific date
python scripts/run_daily_aggregation.py --date 2025-11-01
```

### 4. Schedule with Cron

Add to crontab (`crontab -e`):

```bash
# Run daily at 2:00 AM
0 2 * * * cd /path/to/tutormax && python scripts/run_daily_aggregation.py >> /var/log/tutormax/aggregation.log 2>&1
```

## Common Use Cases

### Process Specific Tutors

```bash
python scripts/run_daily_aggregation.py --tutors tutor_001,tutor_002,tutor_003
```

### Include Inactive Tutors

```bash
python scripts/run_daily_aggregation.py --include-inactive
```

### Clean Up Old Data

```bash
python scripts/run_daily_aggregation.py --cleanup --retention-days 90
```

### Run for Historical Date

```bash
python scripts/run_daily_aggregation.py --date 2025-10-01
```

## Programmatic Usage

```python
import asyncio
from src.evaluation import run_daily_aggregation
from datetime import datetime

async def main():
    # Run aggregation
    summary = await run_daily_aggregation(
        reference_date=datetime.utcnow(),
        tutor_ids=None,  # All active tutors
        include_inactive=False,
        cleanup_old_metrics=True,
        retention_days=90,
    )

    # Check results
    print(f"Processed: {summary.total_tutors} tutors")
    print(f"Success rate: {summary.success_rate}%")
    print(f"Metrics saved: {summary.total_metrics_saved}")

    if summary.errors:
        print("Errors encountered:")
        for error in summary.errors:
            print(f"  - {error['tutor_id']}: {error['error']}")

    return summary

if __name__ == "__main__":
    asyncio.run(main())
```

## Monitoring

### Check Last Run

```sql
SELECT
    calculation_date,
    COUNT(*) as metrics_count,
    window
FROM tutor_performance_metrics
WHERE calculation_date >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY calculation_date, window
ORDER BY calculation_date DESC;
```

### View Recent Metrics

```sql
SELECT
    t.name,
    m.window,
    m.sessions_completed,
    m.avg_rating,
    m.performance_tier
FROM tutor_performance_metrics m
JOIN tutors t ON m.tutor_id = t.tutor_id
WHERE m.calculation_date >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY m.calculation_date DESC
LIMIT 10;
```

### Check for Errors

```bash
# View last 50 lines of log
tail -50 /var/log/tutormax/aggregation.log

# Search for errors
grep ERROR /var/log/tutormax/aggregation.log

# Follow live log
tail -f /var/log/tutormax/aggregation.log
```

## Troubleshooting

### No Tutors Found

```bash
# Check database connection
python -c "from src.database.connection import get_session; import asyncio; asyncio.run(get_session().__anext__())"

# Check tutor count
python -c "
from src.database.connection import get_session
from src.database.models import Tutor
from sqlalchemy import select, func
import asyncio

async def check():
    async with get_session() as session:
        result = await session.execute(select(func.count(Tutor.tutor_id)))
        print(f'Total tutors: {result.scalar()}')

asyncio.run(check())
"
```

### Metrics Are NULL

Check if there's session data:

```sql
SELECT
    tutor_id,
    COUNT(*) as session_count,
    MIN(scheduled_start) as earliest_session,
    MAX(scheduled_start) as latest_session
FROM sessions
GROUP BY tutor_id
LIMIT 10;
```

### Slow Performance

```bash
# Process fewer tutors per batch
python scripts/run_daily_aggregation.py --batch-size 25

# Process specific tutors
python scripts/run_daily_aggregation.py --tutors tutor_001,tutor_002
```

## What Gets Calculated

For each tutor, the system calculates metrics across three time windows:

1. **7-Day Window** - Recent performance
2. **30-Day Window** - Monthly performance
3. **90-Day Window** - Quarterly performance

### Metrics Calculated

- Sessions completed count
- Average student rating (1-5)
- First session success rate (%)
- Reschedule rate (%)
- No-show count
- Engagement score (0-100)
- Learning objectives met (%)
- Response time average (minutes)
- Performance tier assignment

## Expected Output

```
================================================================================
DAILY AGGREGATION SUMMARY
================================================================================
Run date: 2025-11-07
Total tutors: 150
Successful: 148
Failed: 2
Skipped: 0
Total metrics saved: 444
Success rate: 98.67%
Total runtime: 89.45s
================================================================================
```

## Next Steps

1. **Set up scheduled execution** - Add to crontab for daily runs
2. **Configure log rotation** - Prevent log files from growing too large
3. **Set up monitoring** - Create alerts for failures
4. **Review metrics** - Check calculated metrics for accuracy

For more details, see [Daily Aggregation Documentation](./daily_aggregation.md).
