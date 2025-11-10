"""
Sentry Configuration for Error Tracking and Performance Monitoring

Configures Sentry SDK for:
- Error tracking and reporting
- Performance monitoring (APM)
- Request/response tracking
- Custom context and tags
- Release tracking
"""

import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from typing import Optional

from src.api.config import settings

logger = logging.getLogger(__name__)


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
) -> None:
    """
    Initialize Sentry SDK with FastAPI and Celery integrations.

    Args:
        dsn: Sentry DSN (defaults to SENTRY_DSN env var)
        environment: Environment name (production, staging, development)
        release: Release version (e.g., git commit SHA)
        traces_sample_rate: % of transactions to send (0.0-1.0)
        profiles_sample_rate: % of profiles to send (0.0-1.0)
    """
    # Get DSN from parameters or environment
    sentry_dsn = dsn or getattr(settings, 'sentry_dsn', None)

    if not sentry_dsn or sentry_dsn == "your_sentry_dsn_here":
        logger.warning(
            "Sentry DSN not configured. Error tracking disabled. "
            "Set SENTRY_DSN environment variable to enable Sentry."
        )
        return

    # Determine environment
    env = environment or getattr(settings, 'environment', 'development')

    # Determine release (git commit SHA or version)
    release_version = release or getattr(settings, 'app_version', None)

    logger.info(f"Initializing Sentry for environment: {env}")

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=env,
            release=release_version,

            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",  # Group transactions by endpoint
                ),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(
                    monitor_beat_tasks=True,  # Monitor Celery beat tasks
                    exclude_beat_tasks=[],  # Tasks to exclude from monitoring
                ),
                AsyncioIntegration(),
            ],

            # Performance Monitoring
            traces_sample_rate=traces_sample_rate,

            # Profiling (requires Sentry profiling feature)
            profiles_sample_rate=profiles_sample_rate,

            # Error Sampling
            # send_default_pii=False,  # Don't send PII (important for GDPR/FERPA/COPPA)

            # Request data
            max_breadcrumbs=50,  # Number of breadcrumbs to keep
            attach_stacktrace=True,  # Attach stack traces to messages

            # Event processors
            before_send=before_send_event,
            before_breadcrumb=before_breadcrumb,

            # Debug mode (only for development)
            debug=env == 'development',
        )

        logger.info("Sentry initialized successfully")

        # Set global tags
        sentry_sdk.set_tag("app_name", settings.app_name)
        sentry_sdk.set_tag("app_version", settings.app_version)

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)


def before_send_event(event: dict, hint: dict) -> Optional[dict]:
    """
    Process events before sending to Sentry.

    Use this to:
    - Filter out sensitive data (PII)
    - Modify or enrich events
    - Drop certain events

    Args:
        event: Sentry event dictionary
        hint: Additional context about the event

    Returns:
        Modified event or None to drop the event
    """
    # Remove PII from request data
    if 'request' in event:
        request = event['request']

        # Remove sensitive headers
        if 'headers' in request:
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                if header in request['headers']:
                    request['headers'][header] = '[Filtered]'

        # Remove sensitive query params
        if 'query_string' in request:
            sensitive_params = ['token', 'api_key', 'password']
            # This is a simple example - you may need more sophisticated filtering
            for param in sensitive_params:
                if param in request.get('query_string', ''):
                    request['query_string'] = '[Filtered]'

    # Remove PII from user context
    if 'user' in event:
        # Keep only non-PII user data
        user = event['user']
        allowed_fields = {'id', 'username', 'role'}
        event['user'] = {k: v for k, v in user.items() if k in allowed_fields}

    # Add custom context
    sentry_sdk.set_context("app_info", {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": getattr(settings, 'environment', 'unknown'),
    })

    return event


def before_breadcrumb(crumb: dict, hint: dict) -> Optional[dict]:
    """
    Process breadcrumbs before adding to event.

    Args:
        crumb: Breadcrumb dictionary
        hint: Additional context

    Returns:
        Modified breadcrumb or None to drop it
    """
    # Filter out noisy breadcrumbs
    if crumb.get('category') == 'httplib' and crumb.get('data', {}).get('url', '').endswith('/health'):
        # Drop health check breadcrumbs to reduce noise
        return None

    return crumb


def capture_exception(
    error: Exception,
    level: str = "error",
    extra: Optional[dict] = None,
    tags: Optional[dict] = None,
) -> Optional[str]:
    """
    Capture an exception and send to Sentry.

    Args:
        error: Exception to capture
        level: Severity level (fatal, error, warning, info, debug)
        extra: Additional context data
        tags: Custom tags for filtering

    Returns:
        Event ID or None if not sent
    """
    with sentry_sdk.push_scope() as scope:
        # Set level
        scope.level = level

        # Add extra context
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        # Add tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        # Capture exception
        event_id = sentry_sdk.capture_exception(error)

        if event_id:
            logger.info(f"Exception captured by Sentry: {event_id}")

        return event_id


def capture_message(
    message: str,
    level: str = "info",
    extra: Optional[dict] = None,
    tags: Optional[dict] = None,
) -> Optional[str]:
    """
    Capture a message and send to Sentry.

    Args:
        message: Message to capture
        level: Severity level (fatal, error, warning, info, debug)
        extra: Additional context data
        tags: Custom tags for filtering

    Returns:
        Event ID or None if not sent
    """
    with sentry_sdk.push_scope() as scope:
        # Set level
        scope.level = level

        # Add extra context
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)

        # Add tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        # Capture message
        event_id = sentry_sdk.capture_message(message, level)

        return event_id


def set_user_context(
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
) -> None:
    """
    Set user context for Sentry events.

    Note: Be careful with PII. Only include non-sensitive identifiers.

    Args:
        user_id: User ID (non-PII)
        username: Username (if not PII)
        email: Email (only if compliant with privacy regulations)
        role: User role
    """
    sentry_sdk.set_user({
        "id": user_id,
        "username": username,
        "email": email,
        "role": role,
    })


def clear_user_context() -> None:
    """Clear user context from Sentry scope."""
    sentry_sdk.set_user(None)


def set_custom_context(name: str, data: dict) -> None:
    """
    Set custom context for Sentry events.

    Args:
        name: Context name
        data: Context data dictionary
    """
    sentry_sdk.set_context(name, data)


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: Optional[dict] = None,
) -> None:
    """
    Add a breadcrumb to the current scope.

    Breadcrumbs provide a trail of events leading up to an error.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "api", "db", "auth")
        level: Severity level
        data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )


def start_transaction(
    name: str,
    op: str = "http.server",
    description: Optional[str] = None,
) -> sentry_sdk.tracing.Transaction:
    """
    Start a performance monitoring transaction.

    Args:
        name: Transaction name (e.g., endpoint name)
        op: Operation type (e.g., "http.server", "db.query", "task")
        description: Optional description

    Returns:
        Transaction object
    """
    transaction = sentry_sdk.start_transaction(
        name=name,
        op=op,
    )

    if description:
        transaction.description = description

    return transaction


def start_span(
    op: str,
    description: Optional[str] = None,
) -> sentry_sdk.tracing.Span:
    """
    Start a performance monitoring span within a transaction.

    Args:
        op: Operation type (e.g., "db.query", "http.client", "cache.get")
        description: Span description

    Returns:
        Span object
    """
    span = sentry_sdk.start_span(op=op)

    if description:
        span.description = description

    return span
