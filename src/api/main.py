"""
FastAPI application for TutorMax data ingestion.

Provides REST API endpoints to receive tutor, session, and feedback data
from the synthetic data generation engine and queues them for processing.
"""

import logging
from datetime import datetime
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    TutorProfile,
    SessionData,
    FeedbackData,
    HealthCheckResponse,
    IngestionResponse,
    BatchIngestionResponse,
)
from .redis_service import redis_service, get_redis_service, RedisService
from .cache_service import cache_service, get_cache_service
from .performance_middleware import PerformanceMiddleware, RateLimitMiddleware, configure_compression
from .metrics_exporter import setup_metrics
from .prediction_router import router as prediction_router
from .websocket_router import router as websocket_router
from .tutor_portal_router import router as tutor_portal_router
from .tutor_profile_router import router as tutor_profile_router
from .worker_monitoring_router import router as worker_monitoring_router
from .feedback_auth_router import router as feedback_auth_router
from .intervention_router import router as intervention_router
from .audit_router import router as audit_router
from .audit_middleware import AuditLoggingMiddleware
from .data_retention_router import router as data_retention_router
from .uptime_router import router as uptime_router
from .sla_dashboard_router import router as sla_dashboard_router
from .performance_dashboard_router import router as performance_dashboard_router
from .alerting_router import router as alerting_router
from .analytics_router import router as analytics_router
from .performance_router import router as performance_router
from .gamification_router import router as gamification_router
from .tutor_goals_router import router as tutor_goals_router
from .training_resources_router import router as training_resources_router
from .reports_router import router as reports_router
from .email_tracking_router import router as email_tracking_router
from .email_campaigns_router import router as email_campaigns_router
from .auth import (
    auth_router,
    register_router,
    reset_password_router,
    verify_router,
    users_router,
    admin_router,
    google_oauth_router,
    microsoft_oauth_router,
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for Redis connection and Sentry.
    """
    # Startup
    logger.info("Starting TutorMax Data Ingestion API...")

    # Initialize Sentry for error tracking
    if settings.sentry_enabled:
        try:
            from src.api.sentry_config import init_sentry
            init_sentry(
                dsn=settings.sentry_dsn,
                environment=settings.sentry_environment,
                release=settings.app_version,
                traces_sample_rate=settings.sentry_traces_sample_rate,
                profiles_sample_rate=settings.sentry_profiles_sample_rate,
            )
            logger.info("Sentry initialized for error tracking")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry: {e}")

    # Connect to Redis
    try:
        await redis_service.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        logger.warning("API will start but Redis-dependent features will fail")

    # Connect cache service (uses same Redis instance)
    try:
        await cache_service.connect()
        logger.info("Cache service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize cache service: {e}")
        logger.warning("API will start but caching will be disabled")

    yield

    # Shutdown
    logger.info("Shutting down TutorMax Data Ingestion API...")
    await redis_service.disconnect()
    logger.info("Redis connection closed")

    await cache_service.disconnect()
    logger.info("Cache service disconnected")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for receiving and queuing tutor performance data",
    lifespan=lifespan,
)

# Set up Prometheus metrics
setup_metrics(app)

# Add performance middleware (should be first for accurate timing)
app.add_middleware(
    PerformanceMiddleware,
    enable_timing=True,
    enable_cache_headers=True,
    log_slow_requests=True,
    slow_request_threshold_ms=200
)

# Add rate limiting middleware
if settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_api_read_requests,
        burst_size=20
    )

# Add gzip compression
configure_compression(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add audit logging middleware
# Set log_all_requests=True for verbose logging during development
app.add_middleware(AuditLoggingMiddleware, log_all_requests=False)

# Include routers

# Authentication routers (FastAPI-Users)
app.include_router(
    auth_router,
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    register_router,
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    reset_password_router,
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    verify_router,
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
)
app.include_router(
    admin_router.router,
    prefix="/api",
    tags=["admin"],
)

# OAuth/SSO routers
app.include_router(
    google_oauth_router,
    prefix="/auth/google",
    tags=["auth", "oauth"],
)
app.include_router(
    microsoft_oauth_router,
    prefix="/auth/microsoft",
    tags=["auth", "oauth"],
)

# Application routers
app.include_router(prediction_router)
app.include_router(websocket_router)
app.include_router(tutor_portal_router)
app.include_router(tutor_profile_router)
app.include_router(worker_monitoring_router)
app.include_router(feedback_auth_router)
app.include_router(intervention_router)
app.include_router(audit_router)
app.include_router(data_retention_router)
app.include_router(uptime_router)
app.include_router(sla_dashboard_router)
app.include_router(performance_dashboard_router)
app.include_router(alerting_router)
app.include_router(analytics_router)
app.include_router(performance_router)
app.include_router(gamification_router)
app.include_router(tutor_goals_router)
app.include_router(training_resources_router)
app.include_router(reports_router)
app.include_router(email_tracking_router)
app.include_router(email_campaigns_router)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
        },
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check(
    redis: RedisService = Depends(get_redis_service)
) -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns application status and Redis connection state.
    """
    redis_connected = await redis.is_connected()

    return HealthCheckResponse(
        status="healthy" if redis_connected else "degraded",
        timestamp=datetime.now().isoformat(),
        redis_connected=redis_connected,
        version=settings.app_version,
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "tutors": f"{settings.api_prefix}/tutors",
            "sessions": f"{settings.api_prefix}/sessions",
            "feedback": f"{settings.api_prefix}/feedback",
            "predictions": f"{settings.api_prefix}/predictions",
        },
    }


# Tutor endpoints
@app.post(
    f"{settings.api_prefix}/tutors",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tutors"],
)
async def ingest_tutor(
    tutor: TutorProfile,
    redis: RedisService = Depends(get_redis_service),
) -> IngestionResponse:
    """
    Ingest a single tutor profile.

    Validates the tutor data and queues it for processing.
    """
    # Queue the tutor data
    queued = await redis.queue_tutor(tutor.model_dump())

    if not queued:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to queue tutor data - Redis unavailable",
        )

    logger.info(f"Tutor profile ingested: {tutor.tutor_id}")

    return IngestionResponse(
        success=True,
        message="Tutor profile received and queued for processing",
        id=tutor.tutor_id,
        queued=True,
        timestamp=datetime.now().isoformat(),
    )


@app.post(
    f"{settings.api_prefix}/tutors/batch",
    response_model=BatchIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tutors"],
)
async def ingest_tutors_batch(
    tutors: List[TutorProfile],
    redis: RedisService = Depends(get_redis_service),
) -> BatchIngestionResponse:
    """
    Ingest multiple tutor profiles in batch.

    Validates and queues all tutor profiles. Returns count of successfully queued items.
    """
    if not tutors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty batch - no tutors provided",
        )

    successful = 0
    errors = []

    for tutor in tutors:
        try:
            queued = await redis.queue_tutor(tutor.model_dump())
            if queued:
                successful += 1
            else:
                errors.append(f"Failed to queue tutor {tutor.tutor_id}")
        except Exception as e:
            errors.append(f"Error processing tutor {tutor.tutor_id}: {str(e)}")

    logger.info(f"Batch ingestion: {successful}/{len(tutors)} tutors queued")

    return BatchIngestionResponse(
        success=successful > 0,
        message=f"Batch ingestion completed: {successful}/{len(tutors)} tutors queued",
        count=successful,
        queued=successful > 0,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )


# Session endpoints
@app.post(
    f"{settings.api_prefix}/sessions",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"],
)
async def ingest_session(
    session: SessionData,
    redis: RedisService = Depends(get_redis_service),
) -> IngestionResponse:
    """
    Ingest a single session record.

    Validates the session data and queues it for processing.
    """
    # Queue the session data
    queued = await redis.queue_session(session.model_dump())

    if not queued:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to queue session data - Redis unavailable",
        )

    logger.info(f"Session ingested: {session.session_id}")

    return IngestionResponse(
        success=True,
        message="Session data received and queued for processing",
        id=session.session_id,
        queued=True,
        timestamp=datetime.now().isoformat(),
    )


@app.post(
    f"{settings.api_prefix}/sessions/batch",
    response_model=BatchIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"],
)
async def ingest_sessions_batch(
    sessions: List[SessionData],
    redis: RedisService = Depends(get_redis_service),
) -> BatchIngestionResponse:
    """
    Ingest multiple session records in batch.

    Validates and queues all sessions. Returns count of successfully queued items.
    """
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty batch - no sessions provided",
        )

    successful = 0
    errors = []

    for session in sessions:
        try:
            queued = await redis.queue_session(session.model_dump())
            if queued:
                successful += 1
            else:
                errors.append(f"Failed to queue session {session.session_id}")
        except Exception as e:
            errors.append(f"Error processing session {session.session_id}: {str(e)}")

    logger.info(f"Batch ingestion: {successful}/{len(sessions)} sessions queued")

    return BatchIngestionResponse(
        success=successful > 0,
        message=f"Batch ingestion completed: {successful}/{len(sessions)} sessions queued",
        count=successful,
        queued=successful > 0,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )


# Feedback endpoints
@app.post(
    f"{settings.api_prefix}/feedback",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Feedback"],
)
async def ingest_feedback(
    feedback: FeedbackData,
    redis: RedisService = Depends(get_redis_service),
) -> IngestionResponse:
    """
    Ingest a single student feedback record.

    Validates the feedback data and queues it for processing.
    """
    # Queue the feedback data
    queued = await redis.queue_feedback(feedback.model_dump())

    if not queued:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to queue feedback data - Redis unavailable",
        )

    logger.info(f"Feedback ingested: {feedback.feedback_id}")

    return IngestionResponse(
        success=True,
        message="Feedback data received and queued for processing",
        id=feedback.feedback_id,
        queued=True,
        timestamp=datetime.now().isoformat(),
    )


@app.post(
    f"{settings.api_prefix}/feedback/batch",
    response_model=BatchIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Feedback"],
)
async def ingest_feedback_batch(
    feedbacks: List[FeedbackData],
    redis: RedisService = Depends(get_redis_service),
) -> BatchIngestionResponse:
    """
    Ingest multiple feedback records in batch.

    Validates and queues all feedback. Returns count of successfully queued items.
    """
    if not feedbacks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty batch - no feedback provided",
        )

    successful = 0
    errors = []

    for feedback in feedbacks:
        try:
            queued = await redis.queue_feedback(feedback.model_dump())
            if queued:
                successful += 1
            else:
                errors.append(f"Failed to queue feedback {feedback.feedback_id}")
        except Exception as e:
            errors.append(f"Error processing feedback {feedback.feedback_id}: {str(e)}")

    logger.info(f"Batch ingestion: {successful}/{len(feedbacks)} feedbacks queued")

    return BatchIngestionResponse(
        success=successful > 0,
        message=f"Batch ingestion completed: {successful}/{len(feedbacks)} feedbacks queued",
        count=successful,
        queued=successful > 0,
        timestamp=datetime.now().isoformat(),
        errors=errors,
    )


# Queue stats endpoint (useful for monitoring)
@app.get(
    f"{settings.api_prefix}/queue/stats",
    tags=["Monitoring"],
)
async def get_queue_stats(
    redis: RedisService = Depends(get_redis_service),
):
    """
    Get current queue statistics.

    Returns the number of items in each queue.
    """
    stats = await redis.get_queue_stats()

    return {
        "timestamp": datetime.now().isoformat(),
        "queues": stats,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
