"""
Performance optimization middleware for FastAPI.

Implements:
- Gzip compression for responses
- Response caching headers
- Request timing and logging
- Rate limiting per endpoint
"""

import time
import logging
from typing import Dict, Callable
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.datastructures import Headers


logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response performance optimization and monitoring.
    """

    def __init__(
        self,
        app,
        enable_timing: bool = True,
        enable_cache_headers: bool = True,
        log_slow_requests: bool = True,
        slow_request_threshold_ms: int = 200
    ):
        """
        Initialize performance middleware.

        Args:
            app: FastAPI application
            enable_timing: Add timing headers to responses
            enable_cache_headers: Add appropriate cache control headers
            log_slow_requests: Log requests that exceed threshold
            slow_request_threshold_ms: Threshold for slow request logging
        """
        super().__init__(app)
        self.enable_timing = enable_timing
        self.enable_cache_headers = enable_cache_headers
        self.log_slow_requests = log_slow_requests
        self.slow_request_threshold_ms = slow_request_threshold_ms

        # Performance statistics
        self.stats = {
            "total_requests": 0,
            "slow_requests": 0,
            "total_time_ms": 0,
            "p50_time_ms": 0,
            "p95_time_ms": 0,
            "p99_time_ms": 0,
            "request_times": []  # Store recent request times for percentile calculation
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add performance optimizations.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with performance headers
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000

        # Update statistics
        self._update_stats(duration_ms)

        # Add timing header
        if self.enable_timing:
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "")

        # Add cache control headers
        if self.enable_cache_headers:
            response = self._add_cache_headers(request, response)

        # Log slow requests
        if self.log_slow_requests and duration_ms > self.slow_request_threshold_ms:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms"
            )

        # Add performance stats header (for monitoring)
        response.headers["X-Server-Timing"] = (
            f"total;dur={duration_ms:.2f}"
        )

        return response

    def _add_cache_headers(self, request: Request, response: Response) -> Response:
        """
        Add appropriate cache control headers based on endpoint.

        Args:
            request: Request object
            response: Response object

        Returns:
            Response with cache headers
        """
        path = request.url.path

        # Static assets - long cache
        if any(path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.woff2']):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return response

        # API endpoints - different strategies
        if path.startswith("/api/"):
            # Read endpoints - short cache
            if request.method == "GET":
                if "/dashboard" in path:
                    # Dashboard data - 5 min cache
                    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
                elif "/predictions" in path:
                    # Predictions - 1 hour cache
                    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=300"
                elif "/metrics" in path:
                    # Metrics - 15 min cache
                    response.headers["Cache-Control"] = "public, max-age=900, stale-while-revalidate=60"
                else:
                    # Other GET endpoints - 1 min cache
                    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"

            # Write endpoints - no cache
            elif request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
                response.headers["Pragma"] = "no-cache"

        # Health check - no cache
        elif path in ["/health", "/healthz"]:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"

        return response

    def _update_stats(self, duration_ms: float) -> None:
        """
        Update performance statistics.

        Args:
            duration_ms: Request duration in milliseconds
        """
        self.stats["total_requests"] += 1
        self.stats["total_time_ms"] += duration_ms

        # Track request times for percentile calculation (keep last 1000)
        self.stats["request_times"].append(duration_ms)
        if len(self.stats["request_times"]) > 1000:
            self.stats["request_times"].pop(0)

        # Count slow requests
        if duration_ms > self.slow_request_threshold_ms:
            self.stats["slow_requests"] += 1

        # Calculate percentiles
        if len(self.stats["request_times"]) > 10:
            sorted_times = sorted(self.stats["request_times"])
            n = len(sorted_times)
            self.stats["p50_time_ms"] = sorted_times[int(n * 0.50)]
            self.stats["p95_time_ms"] = sorted_times[int(n * 0.95)]
            self.stats["p99_time_ms"] = sorted_times[int(n * 0.99)]

    def get_stats(self) -> Dict:
        """
        Get performance statistics.

        Returns:
            Performance statistics dictionary
        """
        avg_time = (
            self.stats["total_time_ms"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0
            else 0
        )

        return {
            "total_requests": self.stats["total_requests"],
            "slow_requests": self.stats["slow_requests"],
            "slow_request_rate": (
                self.stats["slow_requests"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0
                else 0
            ),
            "avg_time_ms": round(avg_time, 2),
            "p50_time_ms": round(self.stats["p50_time_ms"], 2),
            "p95_time_ms": round(self.stats["p95_time_ms"], 2),
            "p99_time_ms": round(self.stats["p99_time_ms"], 2),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.

    For production, use Redis-based rate limiting (e.g., slowapi with Redis backend).
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        burst_size: int = 20
    ):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute per IP
            burst_size: Max burst requests
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.request_counts: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check rate limits and process request.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response or 429 Too Many Requests
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        if not self._check_rate_limit(client_ip):
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self._get_remaining_requests(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client has exceeded rate limit.

        Args:
            client_ip: Client IP address

        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        minute_ago = now - 60

        # Initialize client request history
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []

        # Clean up old requests
        self.request_counts[client_ip] = [
            timestamp for timestamp in self.request_counts[client_ip]
            if timestamp > minute_ago
        ]

        # Check limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            return False

        # Record request
        self.request_counts[client_ip].append(now)
        return True

    def _get_remaining_requests(self, client_ip: str) -> int:
        """
        Get remaining requests for client.

        Args:
            client_ip: Client IP address

        Returns:
            Number of remaining requests
        """
        if client_ip not in self.request_counts:
            return self.requests_per_minute

        now = time.time()
        minute_ago = now - 60

        recent_requests = sum(
            1 for timestamp in self.request_counts[client_ip]
            if timestamp > minute_ago
        )

        return max(0, self.requests_per_minute - recent_requests)


# Compression configuration
def configure_compression(app):
    """
    Configure gzip compression for FastAPI app.

    Args:
        app: FastAPI application
    """
    # Add GZip middleware for responses > 1KB
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,  # Only compress responses > 1KB
        compresslevel=6  # Balance between speed and compression ratio
    )
    logger.info("Gzip compression enabled (min size: 1KB, level: 6)")
