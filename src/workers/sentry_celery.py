"""
Sentry Integration for Celery Workers

Initializes Sentry for Celery workers to track:
- Task errors and exceptions
- Task performance
- Worker health
"""

import logging
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from src.api.config import settings

logger = logging.getLogger(__name__)


def init_sentry_for_celery():
    """
    Initialize Sentry for Celery workers.

    This should be called when the Celery worker starts,
    typically in the worker initialization.
    """
    if not settings.sentry_enabled:
        logger.info("Sentry is disabled")
        return

    sentry_dsn = settings.sentry_dsn

    if not sentry_dsn or sentry_dsn == "your_sentry_dsn_here":
        logger.warning(
            "Sentry DSN not configured. Error tracking disabled for Celery. "
            "Set SENTRY_DSN environment variable to enable Sentry."
        )
        return

    try:
        logger.info(f"Initializing Sentry for Celery workers (env: {settings.sentry_environment})")

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=settings.sentry_environment,
            release=settings.app_version,

            # Integrations for Celery
            integrations=[
                CeleryIntegration(
                    monitor_beat_tasks=True,  # Monitor beat scheduled tasks
                    exclude_beat_tasks=[],  # Don't exclude any tasks
                ),
                RedisIntegration(),
                SqlalchemyIntegration(),
            ],

            # Performance monitoring
            traces_sample_rate=settings.sentry_traces_sample_rate,
            profiles_sample_rate=settings.sentry_profiles_sample_rate,

            # Error tracking
            attach_stacktrace=True,
            max_breadcrumbs=50,

            # Debug mode (only for development)
            debug=settings.sentry_environment == 'development',
        )

        # Set global tags
        sentry_sdk.set_tag("app_name", "TutorMax Celery Worker")
        sentry_sdk.set_tag("app_version", settings.app_version)
        sentry_sdk.set_tag("component", "celery_worker")

        logger.info("Sentry initialized successfully for Celery")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry for Celery: {e}", exc_info=True)


# Initialize Sentry when this module is imported by Celery workers
# This ensures Sentry is ready before any tasks are executed
init_sentry_for_celery()
