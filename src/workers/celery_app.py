"""
Celery application configuration for TutorMax background workers.

This module configures Celery with Redis as the broker and result backend.
It includes task discovery, scheduling, and monitoring configuration.
"""

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

# Import settings
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.api.config import settings

# Initialize Sentry for Celery workers
try:
    from src.workers.sentry_celery import init_sentry_for_celery
    # Sentry is initialized automatically when the module is imported
except ImportError:
    pass  # Sentry SDK not installed

# Create Celery application
celery_app = Celery(
    "tutormax",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "src.workers.tasks.data_generator",
        "src.workers.tasks.performance_evaluator",
        "src.workers.tasks.churn_predictor",
        "src.workers.tasks.model_trainer",
        "src.workers.tasks.uptime_monitor",
        "src.workers.tasks.alerting",
        "src.workers.tasks.email_workflows",
        "src.workers.tasks.scheduled_reports",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Result backend settings
    result_expires=86400,  # 24 hours
    result_backend_transport_options={
        "master_name": "mymaster",
    },

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
    worker_disable_rate_limits=False,

    # Rate limiting (to handle 3,000 sessions/day volume)
    task_default_rate_limit="125/m",  # 3000/day ≈ 125/minute average

    # Queue configuration
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("data_generation", Exchange("data_generation"), routing_key="data.#"),
        Queue("evaluation", Exchange("evaluation"), routing_key="eval.#"),
        Queue("prediction", Exchange("prediction"), routing_key="predict.#"),
        Queue("training", Exchange("training"), routing_key="train.#"),
        Queue("email", Exchange("email"), routing_key="email.#"),
    ),

    # Task routing
    task_routes={
        "src.workers.tasks.data_generator.*": {"queue": "data_generation"},
        "src.workers.tasks.performance_evaluator.*": {"queue": "evaluation"},
        "src.workers.tasks.churn_predictor.*": {"queue": "prediction"},
        "src.workers.tasks.model_trainer.*": {"queue": "training"},
        "email_workflows.*": {"queue": "email"},
    },

    # Beat schedule (periodic tasks)
    beat_schedule={
        # Performance Evaluator - every 15 minutes
        "evaluate-performance-every-15-min": {
            "task": "src.workers.tasks.performance_evaluator.evaluate_tutor_performance",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "evaluation"},
        },

        # Churn Predictor - daily batch at midnight
        "predict-churn-daily": {
            "task": "src.workers.tasks.churn_predictor.batch_predict_churn",
            "schedule": crontab(hour=0, minute=0),
            "options": {"queue": "prediction"},
        },

        # ML Model Trainer - daily at 2am
        "train-models-daily": {
            "task": "src.workers.tasks.model_trainer.train_models",
            "schedule": crontab(hour=2, minute=0),
            "options": {"queue": "training"},
        },

        # Uptime Monitoring - every minute for >99.5% SLA tracking
        "record-health-checks-every-minute": {
            "task": "src.workers.tasks.uptime_monitor.record_health_checks",
            "schedule": crontab(minute="*"),  # Every minute
            "options": {"queue": "default"},
        },

        # Uptime Report - hourly
        "generate-uptime-report-hourly": {
            "task": "src.workers.tasks.uptime_monitor.generate_uptime_report",
            "schedule": crontab(minute=0),  # Every hour
            "kwargs": {"hours": 24},
            "options": {"queue": "default"},
        },

        # SLA Compliance Check - every hour
        "check-sla-compliance-hourly": {
            "task": "src.workers.tasks.uptime_monitor.check_sla_compliance",
            "schedule": crontab(minute=30),  # Every hour at :30
            "kwargs": {"hours": 24},
            "options": {"queue": "default"},
        },

        # Cleanup old health checks - daily at 3am
        "cleanup-old-health-checks-daily": {
            "task": "src.workers.tasks.uptime_monitor.cleanup_old_health_checks",
            "schedule": crontab(hour=3, minute=0),
            "kwargs": {"days_to_keep": 30},
            "options": {"queue": "default"},
        },

        # Alerting - comprehensive check every 5 minutes
        "check-and-send-alerts-every-5-min": {
            "task": "src.workers.tasks.alerting.check_and_send_alerts",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
            "options": {"queue": "default"},
        },

        # SLA violation check - every 5 minutes
        "check-sla-violations-every-5-min": {
            "task": "src.workers.tasks.alerting.check_sla_violations",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
            "options": {"queue": "default"},
        },

        # Infrastructure check - every 2 minutes for faster failure detection
        "check-infrastructure-every-2-min": {
            "task": "src.workers.tasks.alerting.check_infrastructure",
            "schedule": crontab(minute="*/2"),  # Every 2 minutes
            "options": {"queue": "default"},
        },

        # Email Workflows (Task 12 & 22)
        # Feedback reminders - hourly check for sessions 24h+ without feedback
        "send-feedback-reminders-hourly": {
            "task": "email_workflows.send_feedback_reminders",
            "schedule": crontab(minute=0),  # Every hour
            "options": {"queue": "email"},
        },

        # First session check-ins - every 30 minutes
        "send-first-session-checkins-every-30-min": {
            "task": "email_workflows.send_first_session_checkins",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
            "options": {"queue": "email"},
        },

        # Rescheduling alerts - daily at 10am
        "send-rescheduling-alerts-daily": {
            "task": "email_workflows.send_rescheduling_alerts",
            "schedule": crontab(hour=10, minute=0),  # Daily at 10am
            "options": {"queue": "email"},
        },

        # Scheduled campaigns - every 15 minutes
        "send-scheduled-campaigns-every-15-min": {
            "task": "email_workflows.send_scheduled_campaigns",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
            "options": {"queue": "email"},
        },

        # Weekly digests - Monday at 9am
        "send-weekly-digests-monday": {
            "task": "email_workflows.send_weekly_digests",
            "schedule": crontab(hour=9, minute=0, day_of_week=1),  # Monday 9am
            "options": {"queue": "email"},
        },

        # Cleanup old tracking events - weekly on Sunday at 2am
        "cleanup-tracking-events-weekly": {
            "task": "email_workflows.cleanup_old_tracking_events",
            "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2am
            "kwargs": {"days_to_keep": 90},
            "options": {"queue": "email"},
        },

        # Scheduled Reports (Task 24)
        # Weekly performance report - Monday at 9am
        "send-weekly-performance-report": {
            "task": "scheduled_reports.generate_weekly_report",
            "schedule": crontab(hour=9, minute=0, day_of_week=1),  # Monday 9am
            "options": {"queue": "default"},
        },

        # Monthly performance report - 1st of month at 9am
        "send-monthly-performance-report": {
            "task": "scheduled_reports.generate_monthly_report",
            "schedule": crontab(hour=9, minute=0, day_of_month=1),  # 1st day of month
            "options": {"queue": "default"},
        },

        # Weekly intervention effectiveness - Friday at 4pm
        "send-intervention-effectiveness-report": {
            "task": "scheduled_reports.generate_intervention_effectiveness_report",
            "schedule": crontab(hour=16, minute=0, day_of_week=5),  # Friday 4pm
            "options": {"queue": "default"},
        },

        # Monthly churn analytics - 1st of month at 10am
        "send-churn-analytics-report": {
            "task": "scheduled_reports.generate_churn_analytics_report",
            "schedule": crontab(hour=10, minute=0, day_of_month=1),  # 1st day of month
            "options": {"queue": "default"},
        },
    },

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# Event handlers for monitoring
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f"Request: {self.request!r}")
    return {"status": "success", "message": "Celery is working!"}
