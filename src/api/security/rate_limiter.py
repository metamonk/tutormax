"""
Rate limiting implementation using Redis for distributed rate limiting.

Provides configurable rate limits for different endpoint types with
proper 429 responses and retry-after headers.
"""

import logging
import time
from typing import Optional, Callable
from functools import wraps

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis

from ..config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-backed distributed rate limiter.

    Supports different rate limits for different endpoint types and
    provides proper HTTP 429 responses with retry-after headers.
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL (uses settings.redis_url if not provided)
        """
        self.redis_url = redis_url or settings.redis_url
        self.redis_client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections,
            )
            logger.info("Rate limiter Redis connection established")

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Rate limiter Redis connection closed")

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Check if a key is rate limited.

        Uses sliding window log algorithm for accurate rate limiting.

        Args:
            key: Unique identifier for the rate limit (e.g., "auth:login:192.168.1.1")
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_limited, current_count, retry_after_seconds)
        """
        if not self.redis_client:
            await self.connect()

        now = time.time()
        window_start = now - window_seconds

        # Redis key for this rate limit
        redis_key = f"ratelimit:{key}"

        try:
            # Use a pipeline for atomic operations
            pipe = self.redis_client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(redis_key, 0, window_start)

            # Count requests in current window
            pipe.zcard(redis_key)

            # Add current request
            pipe.zadd(redis_key, {str(now): now})

            # Set expiry on the key
            pipe.expire(redis_key, window_seconds)

            results = await pipe.execute()
            current_count = results[1]  # Count before adding current request

            # Check if rate limit exceeded
            if current_count >= max_requests:
                # Calculate retry-after time
                # Get oldest request in window
                oldest = await self.redis_client.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(window_start + window_seconds - oldest_time) + 1
                else:
                    retry_after = window_seconds

                return True, current_count, retry_after

            return False, current_count + 1, 0

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - don't block requests if Redis is down
            return False, 0, 0

    def limit(
        self,
        max_requests: int,
        window_seconds: int,
        key_func: Optional[Callable] = None,
    ):
        """
        Decorator for rate limiting endpoints.

        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
            key_func: Optional function to generate custom rate limit key
                     Receives the Request object and returns a string
                     Default: Uses client IP address

        Example:
            @app.post("/login")
            @rate_limiter.limit(max_requests=5, window_seconds=300)
            async def login(request: Request):
                ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request from args/kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if not request:
                    request = kwargs.get('request')

                if not request:
                    logger.warning("Rate limiter: No request object found")
                    return await func(*args, **kwargs)

                # Generate rate limit key
                if key_func:
                    key = key_func(request)
                else:
                    # Default: Use client IP and endpoint
                    client_ip = request.client.host if request.client else "unknown"
                    endpoint = request.url.path
                    key = f"{endpoint}:{client_ip}"

                # Check rate limit
                is_limited, count, retry_after = await self.is_rate_limited(
                    key, max_requests, window_seconds
                )

                if is_limited:
                    logger.warning(
                        f"Rate limit exceeded for {key}: {count}/{max_requests} "
                        f"requests in {window_seconds}s window"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Rate limit exceeded",
                            "message": f"Too many requests. Please try again in {retry_after} seconds.",
                            "retry_after": retry_after,
                            "limit": max_requests,
                            "window": window_seconds,
                        },
                        headers={"Retry-After": str(retry_after)},
                    )

                # Add rate limit headers to response
                response = await func(*args, **kwargs)

                # Add rate limit info headers if response supports it
                if hasattr(response, 'headers'):
                    response.headers["X-RateLimit-Limit"] = str(max_requests)
                    response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - count))
                    response.headers["X-RateLimit-Reset"] = str(int(time.time() + window_seconds))

                return response

            return wrapper
        return decorator


# Global rate limiter instance
rate_limiter = RateLimiter()


# Predefined rate limit configurations
class RateLimitConfig:
    """Predefined rate limit configurations for different endpoint types."""

    # Authentication endpoints - strict limits
    AUTH_LOGIN = {"max_requests": 5, "window_seconds": 300}  # 5 per 5 minutes
    AUTH_REGISTER = {"max_requests": 3, "window_seconds": 3600}  # 3 per hour
    AUTH_PASSWORD_RESET = {"max_requests": 3, "window_seconds": 3600}  # 3 per hour
    AUTH_VERIFY = {"max_requests": 10, "window_seconds": 3600}  # 10 per hour

    # API endpoints - moderate limits
    API_READ = {"max_requests": 100, "window_seconds": 60}  # 100 per minute
    API_WRITE = {"max_requests": 30, "window_seconds": 60}  # 30 per minute
    API_BATCH = {"max_requests": 10, "window_seconds": 60}  # 10 per minute

    # WebSocket - generous limits
    WEBSOCKET_CONNECT = {"max_requests": 5, "window_seconds": 60}  # 5 per minute
    WEBSOCKET_MESSAGE = {"max_requests": 60, "window_seconds": 60}  # 60 per minute


async def get_rate_limiter() -> RateLimiter:
    """
    Dependency for getting rate limiter instance.

    Usage:
        @app.post("/endpoint")
        async def endpoint(limiter: RateLimiter = Depends(get_rate_limiter)):
            ...
    """
    if not rate_limiter.redis_client:
        await rate_limiter.connect()
    return rate_limiter
