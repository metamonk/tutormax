"""
Audit logging middleware for FastAPI.

Automatically logs all requests to sensitive endpoints and tracks
authentication events, data access, and modifications.
"""

import time
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import async_session_maker
from .audit_service import AuditService

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log sensitive operations to audit log.

    Logs:
    - All authentication endpoints
    - All data modification operations (POST, PUT, PATCH, DELETE)
    - All sensitive data access (configurable paths)
    - All admin operations
    """

    # Paths that should always be audited
    SENSITIVE_PATHS = [
        "/api/tutors/",
        "/api/students/",
        "/api/sessions/",
        "/api/performance/",
        "/api/predictions/",
        "/api/interventions/",
        "/api/admin/",
        "/api/users/",
        "/api/manager-notes/",
        "/api/tutor-profiles/",
    ]

    # Authentication paths
    AUTH_PATHS = [
        "/auth/jwt/login",
        "/auth/jwt/logout",
        "/auth/register",
        "/auth/forgot-password",
        "/auth/reset-password",
        "/auth/request-verify-token",
        "/auth/verify",
    ]

    # Paths to exclude from audit logging (health checks, static files, etc.)
    EXCLUDED_PATHS = [
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
        "/static/",
    ]

    def __init__(self, app: ASGIApp, log_all_requests: bool = False):
        """
        Initialize audit logging middleware.

        Args:
            app: ASGI application
            log_all_requests: If True, log all requests (verbose). If False, only log sensitive operations.
        """
        super().__init__(app)
        self.log_all_requests = log_all_requests

    def _should_audit_request(self, request: Request) -> bool:
        """
        Determine if request should be audited.

        Args:
            request: FastAPI request

        Returns:
            True if request should be audited
        """
        path = request.url.path
        method = request.method

        # Check if path is excluded
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return False

        # Always audit authentication endpoints
        if any(path.startswith(auth_path) for auth_path in self.AUTH_PATHS):
            return True

        # Always audit data modifications (POST, PUT, PATCH, DELETE)
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True

        # Audit GET requests to sensitive paths
        if method == "GET":
            if any(path.startswith(sensitive) for sensitive in self.SENSITIVE_PATHS):
                return True

        # If log_all_requests is enabled, audit everything
        if self.log_all_requests:
            return True

        return False

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address from request.

        Handles X-Forwarded-For header for proxied requests.

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (if behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP in chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Get direct client IP
        if request.client:
            return request.client.host

        return None

    def _get_user_id(self, request: Request) -> Optional[int]:
        """
        Extract user ID from request state (set by FastAPI-Users).

        Args:
            request: FastAPI request

        Returns:
            User ID if authenticated, None otherwise
        """
        # FastAPI-Users stores user in request.state.user
        if hasattr(request.state, "user"):
            user = request.state.user
            if user and hasattr(user, "id"):
                return user.id

        return None

    def _determine_action(self, request: Request, response: Response) -> str:
        """
        Determine audit action based on request/response.

        Args:
            request: FastAPI request
            response: Response object

        Returns:
            Action string for audit log
        """
        path = request.url.path
        method = request.method

        # Authentication actions
        if "/auth/jwt/login" in path:
            return AuditService.ACTION_LOGIN if response.status_code == 200 else AuditService.ACTION_LOGIN_FAILED
        if "/auth/jwt/logout" in path:
            return AuditService.ACTION_LOGOUT
        if "/auth/register" in path:
            return AuditService.ACTION_REGISTER
        if "/auth/reset-password" in path or "/auth/forgot-password" in path:
            return AuditService.ACTION_PASSWORD_RESET
        if "/auth/verify" in path:
            return AuditService.ACTION_VERIFY_EMAIL

        # Data modification actions
        if method == "POST":
            return AuditService.ACTION_CREATE
        if method in ["PUT", "PATCH"]:
            return AuditService.ACTION_UPDATE
        if method == "DELETE":
            return AuditService.ACTION_DELETE

        # Data access actions
        if method == "GET":
            if "/export" in path:
                return AuditService.ACTION_EXPORT
            if "/search" in path:
                return AuditService.ACTION_SEARCH
            # Check if viewing single resource or listing
            # Simple heuristic: if path ends with ID-like pattern, it's a view
            path_parts = path.rstrip("/").split("/")
            last_part = path_parts[-1] if path_parts else ""
            if last_part and (last_part.isdigit() or len(last_part) > 20):
                return AuditService.ACTION_VIEW
            return AuditService.ACTION_LIST

        return "unknown"

    def _determine_resource_type(self, path: str) -> Optional[str]:
        """
        Determine resource type from request path.

        Args:
            path: Request path

        Returns:
            Resource type string
        """
        if "/tutors" in path:
            return AuditService.RESOURCE_TUTOR
        if "/students" in path:
            return AuditService.RESOURCE_STUDENT
        if "/sessions" in path:
            return AuditService.RESOURCE_SESSION
        if "/feedback" in path:
            return AuditService.RESOURCE_FEEDBACK
        if "/performance" in path:
            return AuditService.RESOURCE_PERFORMANCE_METRIC
        if "/predictions" in path:
            return AuditService.RESOURCE_CHURN_PREDICTION
        if "/interventions" in path:
            return AuditService.RESOURCE_INTERVENTION
        if "/users" in path:
            return AuditService.RESOURCE_USER
        if "/manager-notes" in path:
            return AuditService.RESOURCE_MANAGER_NOTE

        return None

    def _extract_resource_id(self, path: str) -> Optional[str]:
        """
        Extract resource ID from path if present.

        Args:
            path: Request path

        Returns:
            Resource ID if found, None otherwise
        """
        # Simple extraction: get last path segment if it looks like an ID
        path_parts = path.rstrip("/").split("/")
        if path_parts:
            last_part = path_parts[-1]
            # Check if it's an ID (numeric or long string)
            if last_part and (last_part.isdigit() or len(last_part) > 10):
                return last_part

        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log to audit trail if needed.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        start_time = time.time()

        # Check if we should audit this request
        should_audit = self._should_audit_request(request)

        # Process request
        response = await call_next(request)

        # Only audit if needed and response was generated
        if should_audit:
            try:
                # Extract request information
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("User-Agent")
                user_id = self._get_user_id(request)
                action = self._determine_action(request, response)
                resource_type = self._determine_resource_type(request.url.path)
                resource_id = self._extract_resource_id(request.url.path)

                # Create database session for audit logging
                async with async_session_maker() as session:
                    try:
                        await AuditService.log(
                            session=session,
                            action=action,
                            user_id=user_id,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            request_method=request.method,
                            request_path=request.url.path,
                            status_code=response.status_code,
                            success=200 <= response.status_code < 400,
                            error_message=None,
                            metadata={
                                "query_params": dict(request.query_params),
                                "duration_ms": int((time.time() - start_time) * 1000),
                            },
                        )
                    except Exception as log_error:
                        # Don't fail the request if audit logging fails
                        logger.error(f"Failed to write audit log: {log_error}", exc_info=True)

            except Exception as e:
                # Catch any unexpected errors to prevent middleware from breaking requests
                logger.error(f"Error in audit middleware: {e}", exc_info=True)

        return response
