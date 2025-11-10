"""
Security headers middleware for XSS prevention and other security best practices.

Implements security headers following OWASP recommendations:
- Content Security Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Strict-Transport-Security (HSTS)
- Referrer-Policy
- Permissions-Policy
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Configurable security headers to prevent XSS, clickjacking,
    and other common web vulnerabilities.
    """

    def __init__(
        self,
        app: ASGIApp,
        csp_policy: str = None,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str = None,
    ):
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application
            csp_policy: Content Security Policy directive
            hsts_max_age: HSTS max-age in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
            frame_options: X-Frame-Options value (DENY, SAMEORIGIN, or ALLOW-FROM)
            content_type_options: X-Content-Type-Options value
            xss_protection: X-XSS-Protection value
            referrer_policy: Referrer-Policy value
            permissions_policy: Permissions-Policy value
        """
        super().__init__(app)

        # Content Security Policy
        # Default CSP that balances security and functionality
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # HSTS (HTTP Strict Transport Security)
        hsts_parts = [f"max-age={hsts_max_age}"]
        if hsts_include_subdomains:
            hsts_parts.append("includeSubDomains")
        if hsts_preload:
            hsts_parts.append("preload")
        self.hsts_header = "; ".join(hsts_parts)

        # Other headers
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy

        # Permissions Policy (formerly Feature Policy)
        self.permissions_policy = permissions_policy or (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint handler

        Returns:
            Response with security headers added
        """
        # Process request
        response = await call_next(request)

        # Add security headers
        response.headers["Content-Security-Policy"] = self.csp_policy
        response.headers["X-Content-Type-Options"] = self.content_type_options
        response.headers["X-Frame-Options"] = self.frame_options
        response.headers["X-XSS-Protection"] = self.xss_protection
        response.headers["Referrer-Policy"] = self.referrer_policy
        response.headers["Permissions-Policy"] = self.permissions_policy

        # Add HSTS only for HTTPS connections
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = self.hsts_header

        # Add additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        return response


def get_security_headers_middleware(
    csp_policy: str = None,
    strict_mode: bool = False,
) -> SecurityHeadersMiddleware:
    """
    Factory function to create security headers middleware.

    Args:
        csp_policy: Custom CSP policy (uses default if not provided)
        strict_mode: Enable strict security settings (may break functionality)

    Returns:
        Configured SecurityHeadersMiddleware instance
    """
    if strict_mode:
        # Strict CSP that may break some functionality
        csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "font-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )
        return SecurityHeadersMiddleware(
            app=None,  # Will be set by FastAPI
            csp_policy=csp_policy,
            hsts_max_age=63072000,  # 2 years
            hsts_include_subdomains=True,
            hsts_preload=True,
            frame_options="DENY",
            xss_protection="1; mode=block",
        )
    else:
        return SecurityHeadersMiddleware(
            app=None,  # Will be set by FastAPI
            csp_policy=csp_policy,
        )
