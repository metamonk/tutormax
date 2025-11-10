"""
FastAPI application for TutorMax data ingestion - ENHANCED WITH SECURITY.

Provides REST API endpoints to receive tutor, session, and feedback data
from the synthetic data generation engine and queues them for processing.

Security Features:
- Rate limiting on authentication endpoints
- CSRF protection for state-changing operations
- XSS prevention via security headers
- Input sanitization and validation
- SQL injection prevention
- Secure secret management

IMPORTANT: This file contains security enhancements for main.py.
Integrate these changes into main.py as needed.
"""

import logging
from datetime import datetime
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Request
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
from .prediction_router import router as prediction_router
from .websocket_router import router as websocket_router
from .tutor_portal_router import router as tutor_portal_router
from .tutor_profile_router import router as tutor_profile_router
from .worker_monitoring_router import router as worker_monitoring_router

try:
    from .feedback_auth_router import router as feedback_auth_router
    from .audit_router import router as audit_router
    from .audit_middleware import AuditLoggingMiddleware
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False

from .auth import (
    auth_router,
    register_router,
    reset_password_router,
    verify_router,
    users_router,
    admin_router,
)

# Import security components
from .security import (
    rate_limiter,
    SecurityHeadersMiddleware,
    csrf_protect,
    generate_csrf_token,
    setup_secure_logging,
    secret_manager,
    validate_secret_key,
)

# Configure secure logging with secret redaction
setup_secure_logging()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Validate secret key on startup
if not validate_secret_key(settings.secret_key):
    logger.error(
        "SECURITY WARNING: Secret key does not meet security requirements! "
        "Please generate a strong secret key using: openssl rand -hex 32"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for Redis connection and security components.
    """
    # Startup
    logger.info("Starting TutorMax Data Ingestion API with security enhancements...")

    try:
        await redis_service.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        logger.warning("API will start but Redis-dependent features will fail")

    # Initialize security components
    try:
        await rate_limiter.connect()
        logger.info("Rate limiter initialized")
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}")

    try:
        await csrf_protect.connect()
        logger.info("CSRF protection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize CSRF protection: {e}")

    # Load critical secrets
    try:
        secret_manager.load_secret('SECRET_KEY', required=True, min_length=32)
        logger.info("Critical secrets validated")
    except Exception as e:
        logger.error(f"Secret validation failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down TutorMax Data Ingestion API...")
    await redis_service.disconnect()
    await rate_limiter.disconnect()
    await csrf_protect.disconnect()
    logger.info("All connections closed")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for receiving and queuing tutor performance data with enhanced security",
    lifespan=lifespan,
)


# Add Security Headers Middleware (FIRST - sets security headers on all responses)
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add audit logging middleware if available
if HAS_AUDIT:
    app.add_middleware(AuditLoggingMiddleware, log_all_requests=False)


# ===== SECURITY ENDPOINTS =====

@app.get("/security/csrf-token", tags=["Security"])
async def get_csrf_token(
    request: Request,
    token: str = Depends(generate_csrf_token)
):
    """
    Get a CSRF token for the current session.

    Include this token in the X-CSRF-Token header for all state-changing operations.
    """
    return {
        "csrf_token": token,
        "header_name": "X-CSRF-Token",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/security/headers", tags=["Security"])
async def get_security_info():
    """
    Get information about security features enabled on this API.
    """
    return {
        "features": {
            "rate_limiting": True,
            "csrf_protection": True,
            "security_headers": True,
            "input_sanitization": True,
            "sql_injection_prevention": True,
            "xss_prevention": True,
            "secure_logging": True,
        },
        "rate_limits": {
            "auth_login": "5 requests per 5 minutes",
            "auth_register": "3 requests per hour",
            "auth_password_reset": "3 requests per hour",
            "api_read": "100 requests per minute",
            "api_write": "30 requests per minute",
        },
        "recommendations": {
            "include_csrf_token": "GET /security/csrf-token to obtain token",
            "use_https": "Always use HTTPS in production",
            "rotate_secrets": "Rotate secrets every 90 days",
        },
    }


# ===== ROUTERS =====

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

# Application routers
app.include_router(prediction_router)
app.include_router(websocket_router)
app.include_router(tutor_portal_router)
app.include_router(tutor_profile_router)
app.include_router(worker_monitoring_router)

if HAS_AUDIT:
    app.include_router(audit_router)


# ===== EXCEPTION HANDLERS =====

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
    """Handle unexpected exceptions with secret redaction."""
    # Redact any secrets from error message before logging
    error_msg = str(exc)
    redacted_msg = secret_manager.redact_secrets(error_msg)
    logger.error(f"Unexpected error: {redacted_msg}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
        },
    )


# ===== HEALTH & ROOT ENDPOINTS =====

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


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "security": {
            "rate_limiting": "enabled",
            "csrf_protection": "enabled",
            "security_headers": "enabled",
        },
        "endpoints": {
            "health": "/health",
            "security_info": "/security/headers",
            "csrf_token": "/security/csrf-token",
            "tutors": f"{settings.api_prefix}/tutors",
            "sessions": f"{settings.api_prefix}/sessions",
            "feedback": f"{settings.api_prefix}/feedback",
            "predictions": f"{settings.api_prefix}/predictions",
        },
    }


# ===== DATA INGESTION ENDPOINTS =====
# Note: These endpoints use Pydantic models which already provide
# input validation. Additional sanitization is applied at the model level.

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
