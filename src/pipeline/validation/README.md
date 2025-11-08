# Data Validation Module

Comprehensive data validation system for TutorMax pipeline.

## Overview

This module validates tutors, sessions, and feedback data from Redis queues before enrichment and database storage. It ensures data integrity, enforces business rules, and routes invalid data to a dead letter queue.

## Components

- **base_validator.py** - Base validator class with common utilities
- **tutor_validator.py** - Tutor profile validation
- **session_validator.py** - Session data validation
- **feedback_validator.py** - Feedback data validation
- **validation_engine.py** - Orchestrates all validators
- **validation_worker.py** - Redis queue integration worker

## Quick Start

```python
from src.pipeline.validation import ValidationEngine

# Initialize engine
engine = ValidationEngine()

# Validate data
result = engine.validate_tutor(tutor_data)

if result.valid:
    print("Data is valid!")
else:
    for error in result.errors:
        print(f"{error.field}: {error.message}")
```

## Running the Worker

```bash
python run_validation_worker.py
```

## Validation Rules

### Tutors
- Email: Valid format
- Age: 22-65
- Tenure: >= 0 days
- Baseline sessions: 5-30/week
- Subjects: 1-10 from approved list
- Valid behavioral archetype
- Valid subject type

### Sessions
- Session number: >= 1
- Duration: 30/45/60/90 minutes (recommended)
- Engagement: 0.0-1.0
- No-shows must not have actual_start
- Late start <= duration
- Scheduled date max 30 days in future

### Feedback
- Ratings: 1-5
- First sessions need would_recommend
- Low ratings should have feedback text
- Overall rating should align with individual ratings

## Testing

```bash
pytest tests/pipeline/validation/ -v
```

## Documentation

See:
- `/TASK_2.2_VALIDATION_REPORT.md` - Complete technical documentation
- `/VALIDATION_QUICKSTART.md` - Quick reference guide
- `/demo_validation.py` - Usage examples
