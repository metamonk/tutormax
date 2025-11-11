# TutorMax Presentation Demo Data Generator

## Overview

This script generates realistic demo data for your TutorMax presentation, creating the exact tutors and scenarios mentioned in your presentation script.

## What It Creates

### Key Tutors
- **Sarah Chen** - At-Risk tutor with 72% churn probability
  - 120 days tenure
  - 15 sessions in last 30 days (down from 25)
  - Average rating: 4.1 (declining)
  - Engagement score: 0.32 (low)
  - Multiple interventions assigned

- **Mike Ross** - New tutor with low first session success
  - 10 days tenure
  - Only 5 sessions completed
  - Average rating: 3.8
  - First session success rate: 40%
  - Moderate churn risk

- **3 High Performers** - Jessica Pearson, Harvey Specter, Rachel Zane
  - Exemplary performance tier
  - 4.7-5.0 ratings
  - 45-60 sessions per month
  - Low churn risk (3-10%)

### Supporting Data
- 20 demo students
- Realistic sessions with temporal distribution
- Student feedback (85% feedback rate)
- Performance metrics for all tutors
- Churn predictions with multiple time windows
- Interventions for at-risk tutors

## How to Use

### Prerequisites
1. Database must be running and migrated
2. Environment variables configured (`.env` file)
3. Python virtual environment activated

### Steps

1. **Ensure database is running:**
   ```bash
   # Check PostgreSQL is running
   psql -U tutormax -d tutormax_db -c "SELECT 1"
   ```

2. **Run the script:**
   ```bash
   cd /Users/zeno/Projects/tutormax
   python scripts/generate_presentation_demo_data.py
   ```

3. **Confirm when prompted:**
   ```
   ▶️  Continue? (y/N): y
   ```

4. **Wait for completion** (~30 seconds)
   - Creates tutors with metrics and predictions
   - Generates sessions and feedback
   - Creates interventions
   - Prints summary

## What You'll See

The script will output:
```
============================================================
🎬 TutorMax Presentation Demo Data Generator
============================================================

1️⃣  Creating Sarah Chen (At-Risk)...
   ✓ Sarah Chen - Churn Risk: 72% (CRITICAL)
   - Average Rating: 4.1 (declining)
   - Engagement: 0.32 (low)
   - 15 sessions last 30 days (down from 25)

2️⃣  Creating Mike Ross (New Tutor)...
   ✓ Mike Ross - First Session Risk: HIGH
   - Average Rating: 3.8
   - First Session Success: 40%
   - Only 5 sessions completed (NEW)

[... continues with high performers, students, sessions, etc ...]

============================================================
📊 PRESENTATION DEMO DATA SUMMARY
============================================================

👥 Tutors: 5

🎯 Key Demo Tutors:

   Sarah Chen:
   - Email: sarah.chen@tutormax.com
   - Tutor ID: sarah_chen_001
   - Churn Risk (30d): 72%
   - Risk Level: Critical
   - Average Rating: 4.1
   - Engagement: 0.32
   - First Session Success: 75%
   - Sessions (last 30day): 15

   Mike Ross:
   - Email: mike.ross@tutormax.com
   - Tutor ID: mike_ross_001
   - Churn Risk (30d): 35%
   - Risk Level: Medium
   - Average Rating: 3.8
   - Engagement: 0.55
   - First Session Success: 40%
   - Sessions (last 7day): 5

📅 Sessions: 200+
⭐ Feedback Records: 170+
🚨 Interventions: 5+
```

## Viewing the Data

### 1. Start the Application

**Backend:**
```bash
python -m uvicorn src.main:app --reload
```

**Frontend:**
```bash
cd frontend
pnpm dev
```

### 2. Login

- URL: http://localhost:3000
- Email: `admin@tutormax.com`
- Password: `admin123`

### 3. Navigate to Key Pages

- **Main Dashboard:** http://localhost:3000/dashboard
  - View overall system health
  - See critical alerts
  - Check performance tiers
  - View churn heatmap

- **Sarah Chen Profile:** http://localhost:3000/tutor/sarah_chen_001
  - See 72% churn risk
  - View declining metrics
  - Check intervention history
  - Review flags and alerts

- **Mike Ross Profile:** http://localhost:3000/tutor/mike_ross_001
  - See low first session success rate
  - View new tutor metrics
  - Check session history

- **Interventions:** http://localhost:3000/interventions
  - See intervention queue
  - Check SLA timers
  - View assigned interventions

- **System Monitoring:** http://localhost:3000/monitoring
  - View system health
  - Check model training status
  - See Celery job metrics

## Matching Your Presentation Script

The generated data matches your presentation script exactly:

| Script Reference | Generated Data | Location |
|-----------------|----------------|----------|
| "Sarah Chen, 72% churn" | ✓ Sarah with 72% 30-day churn | `/tutor/sarah_chen_001` |
| "15 sessions in last 30 days" | ✓ 15 sessions | Sessions table |
| "Average rating: 4.1" | ✓ 4.1 rating | Performance metrics |
| "Engagement: 0.32" | ✓ 0.32 engagement | Performance metrics |
| "Mike Ross, 5 sessions" | ✓ 5 sessions | `/tutor/mike_ross_001` |
| "Average rating: 3.8" | ✓ 3.8 rating | Performance metrics |
| "40% first session success" | ✓ 0.40 success rate | Performance metrics |
| "High Performers" | ✓ 3 exemplary tutors | Dashboard performance tiers |

## Cleaning Up (Optional)

To remove demo data and start fresh:

```bash
# Drop and recreate database
dropdb tutormax_db
createdb tutormax_db
alembic upgrade head

# Or truncate tables
psql -U tutormax -d tutormax_db -c "TRUNCATE tutors, students, sessions, student_feedback, tutor_performance_metrics, churn_predictions, interventions CASCADE"
```

## Troubleshooting

### "Database connection error"
- Check PostgreSQL is running
- Verify `.env` DATABASE_URL is correct
- Run: `psql -U tutormax -d tutormax_db -c "SELECT 1"`

### "Tutor already exists"
- The script will fail if Sarah Chen or Mike Ross already exist
- Either delete existing data or modify tutor_id in the script

### "Import errors"
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`

### "No data showing in dashboard"
- Wait for backend to fully start
- Check browser console for errors
- Verify API is accessible: `curl http://localhost:8000/api/analytics/overview`

## Notes

- All data is synthetic and for demo purposes only
- Churn predictions use hardcoded values (not ML-generated)
- Performance metrics are manually set to match your script
- Sessions are distributed randomly across the time period
- Feedback ratings are based on tutor performance tier

## Support

If you encounter issues:
1. Check database connection
2. Verify all migrations are applied
3. Review script output for specific errors
4. Check backend logs for API errors
