"""
Background workers infrastructure for TutorMax.

This package provides Celery-based background workers for:
- Synthetic data generation (continuous)
- Performance evaluation (cron: every 15 min)
- Churn prediction (event-driven + daily batch)
- ML model training (cron: daily at 2am)
"""

from .celery_app import celery_app

__all__ = ["celery_app"]
