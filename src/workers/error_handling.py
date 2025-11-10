"""
Centralized error handling and retry logic for Celery workers.

This module provides:
- Custom exception classes for worker errors
- Retry decorators with backoff strategies
- Error logging and monitoring utilities
- Circuit breaker pattern for external services
"""

import logging
import functools
import time
from typing import Callable, Optional, Type, Tuple, Any
from celery import Task
from celery.exceptions import Reject, Retry, SoftTimeLimitExceeded
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exception Classes
# ============================================================================

class WorkerError(Exception):
    """Base exception for worker errors."""
    pass


class DatabaseConnectionError(WorkerError):
    """Database connection failed."""
    pass


class ModelLoadError(WorkerError):
    """ML model loading failed."""
    pass


class DataValidationError(WorkerError):
    """Data validation failed."""
    pass


class ExternalServiceError(WorkerError):
    """External service unavailable."""
    pass


class RetryableError(WorkerError):
    """Error that should trigger a retry."""
    pass


class NonRetryableError(WorkerError):
    """Error that should not trigger a retry."""
    pass


# ============================================================================
# Retry Strategies
# ============================================================================

def exponential_backoff(retry_count: int, base_delay: int = 60, max_delay: int = 3600) -> int:
    """
    Calculate exponential backoff delay.

    Args:
        retry_count: Current retry attempt number
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** retry_count), max_delay)
    # Add jitter (±20%)
    jitter = delay * 0.2
    import random
    return int(delay + random.uniform(-jitter, jitter))


def linear_backoff(retry_count: int, base_delay: int = 60, increment: int = 60) -> int:
    """
    Calculate linear backoff delay.

    Args:
        retry_count: Current retry attempt number
        base_delay: Base delay in seconds
        increment: Delay increment per retry

    Returns:
        Delay in seconds
    """
    return base_delay + (retry_count * increment)


# ============================================================================
# Custom Task Base Classes
# ============================================================================

class ResilientTask(Task):
    """
    Base task class with robust error handling and retry logic.

    Features:
    - Automatic retry with configurable backoff
    - Error logging with context
    - Soft time limit handling
    - Dead letter queue integration
    """

    autoretry_for = (
        DatabaseConnectionError,
        ExternalServiceError,
        RetryableError,
    )
    retry_kwargs = {
        'max_retries': 3,
        'countdown': 60,  # Will be overridden by backoff
    }
    retry_backoff = True
    retry_backoff_max = 3600  # 1 hour max
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Called when task fails after all retries.

        Args:
            exc: Exception that caused failure
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info object
        """
        logger.error(
            f"Task {self.name} [{task_id}] failed permanently",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
                "exception_type": type(exc).__name__,
                "traceback": einfo.traceback,
            }
        )

        # Send to monitoring/alerting system
        self._send_failure_alert(task_id, exc, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Called when task is retried.

        Args:
            exc: Exception that triggered retry
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info object
        """
        retry_count = self.request.retries
        logger.warning(
            f"Task {self.name} [{task_id}] retry {retry_count}/{self.max_retries}",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "retry_count": retry_count,
                "max_retries": self.max_retries,
                "exception": str(exc),
                "exception_type": type(exc).__name__,
            }
        )

    def on_success(self, retval, task_id, args, kwargs):
        """
        Called when task succeeds.

        Args:
            retval: Task return value
            task_id: Unique task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
        """
        logger.info(
            f"Task {self.name} [{task_id}] completed successfully",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "retries": self.request.retries,
            }
        )

    def _send_failure_alert(self, task_id: str, exc: Exception, einfo):
        """
        Send alert for permanent task failure.

        Override this method to integrate with your alerting system
        (e.g., PagerDuty, Sentry, email, etc.)

        Future enhancement: Integrate with alert_service.py to send alerts via:
        - Email (using email_service.py)
        - Slack/PagerDuty webhooks
        - SMS for critical failures

        Example integration:
            from src.api.alert_service import AlertService
            alert_service = AlertService()
            await alert_service.create_alert(
                alert_type="WORKER_FAILURE",
                severity="high",
                title=f"Worker task failed: {task_id}",
                description=str(exc)
            )
        """
        # Placeholder - implement when external alerting is configured
        pass


# ============================================================================
# Error Handling Decorators
# ============================================================================

def handle_database_errors(func: Callable) -> Callable:
    """
    Decorator to handle database connection errors.

    Converts database exceptions to DatabaseConnectionError for retry logic.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Check if it's a database-related error
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in [
                'connection', 'database', 'postgres', 'timeout', 'closed'
            ]):
                logger.error(f"Database error in {func.__name__}: {e}")
                raise DatabaseConnectionError(f"Database error: {e}") from e
            else:
                raise

    return wrapper


def handle_model_errors(func: Callable) -> Callable:
    """
    Decorator to handle ML model loading/inference errors.

    Converts model exceptions to ModelLoadError.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in [
                'model', 'pickle', 'xgboost', 'sklearn', 'prediction'
            ]):
                logger.error(f"Model error in {func.__name__}: {e}")
                raise ModelLoadError(f"Model error: {e}") from e
            else:
                raise

    return wrapper


def handle_soft_time_limit(func: Callable) -> Callable:
    """
    Decorator to gracefully handle soft time limit exceeded.

    Logs warning and allows cleanup before hard limit.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SoftTimeLimitExceeded:
            logger.warning(
                f"Task {func.__name__} exceeded soft time limit, cleaning up..."
            )
            # Perform cleanup here if needed
            raise  # Re-raise to trigger Celery's handling

    return wrapper


# ============================================================================
# Circuit Breaker Pattern
# ============================================================================

class CircuitBreaker:
    """
    Circuit breaker for external services.

    Prevents cascading failures by temporarily blocking calls to failing services.

    States:
    - CLOSED: Normal operation, calls allowed
    - OPEN: Too many failures, calls blocked
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function return value

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: attempting recovery (HALF_OPEN)")
            else:
                raise ExternalServiceError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _on_success(self):
        """Reset circuit breaker on success."""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker: recovered (CLOSED)")

    def _on_failure(self):
        """Handle failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"Circuit breaker: opened after {self.failure_count} failures"
            )


# ============================================================================
# Utility Functions
# ============================================================================

def log_task_error(
    task_name: str,
    task_id: str,
    error: Exception,
    context: Optional[dict] = None
):
    """
    Log task error with structured context.

    Args:
        task_name: Name of the task
        task_id: Unique task ID
        error: Exception that occurred
        context: Additional context dictionary
    """
    log_data = {
        "task_name": task_name,
        "task_id": task_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if context:
        log_data.update(context)

    logger.error(
        f"Task error: {task_name}",
        extra=log_data
    )


def should_retry(error: Exception) -> bool:
    """
    Determine if error should trigger a retry.

    Args:
        error: Exception to evaluate

    Returns:
        True if should retry, False otherwise
    """
    # Retryable errors
    if isinstance(error, (
        DatabaseConnectionError,
        ExternalServiceError,
        RetryableError,
        ConnectionError,
        TimeoutError,
    )):
        return True

    # Non-retryable errors
    if isinstance(error, (
        NonRetryableError,
        DataValidationError,
        ValueError,
        TypeError,
    )):
        return False

    # Check error message for retryable patterns
    error_str = str(error).lower()
    retryable_keywords = [
        'timeout', 'connection', 'network', 'unavailable', 'temporary'
    ]

    return any(keyword in error_str for keyword in retryable_keywords)
