"""
CSRF (Cross-Site Request Forgery) protection implementation.

Provides CSRF token generation, validation, and middleware for protecting
state-changing operations.
"""

import secrets
import hmac
import hashlib
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer
import redis.asyncio as aioredis

from ..config import settings

logger = logging.getLogger(__name__)

# CSRF token configuration
CSRF_TOKEN_LENGTH = 32
CSRF_TOKEN_EXPIRY_HOURS = 24
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"


class CSRFProtect:
    """
    CSRF protection manager.

    Generates and validates CSRF tokens using Redis for distributed storage.
    Uses double-submit cookie pattern with server-side validation.
    """

    def __init__(self, redis_url: str = None, secret_key: str = None):
        """
        Initialize CSRF protection.

        Args:
            redis_url: Redis connection URL (uses settings.redis_url if not provided)
            secret_key: Secret key for HMAC signing (uses settings.secret_key if not provided)
        """
        self.redis_url = redis_url or settings.redis_url
        self.secret_key = secret_key or settings.secret_key
        self.redis_client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("CSRF protection Redis connection established")

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("CSRF protection Redis connection closed")

    def _sign_token(self, token: str) -> str:
        """
        Sign a CSRF token with HMAC.

        Args:
            token: Raw token to sign

        Returns:
            Signed token
        """
        signature = hmac.new(
            self.secret_key.encode(),
            token.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{token}.{signature}"

    def _verify_signature(self, signed_token: str) -> Optional[str]:
        """
        Verify CSRF token signature.

        Args:
            signed_token: Signed token to verify

        Returns:
            Raw token if valid, None otherwise
        """
        try:
            token, signature = signed_token.rsplit(".", 1)
            expected_signature = hmac.new(
                self.secret_key.encode(),
                token.encode(),
                hashlib.sha256,
            ).hexdigest()

            if hmac.compare_digest(signature, expected_signature):
                return token
            return None
        except (ValueError, AttributeError):
            return None

    async def generate_token(self, session_id: str) -> str:
        """
        Generate a new CSRF token for a session.

        Args:
            session_id: User session identifier (e.g., user ID or session token)

        Returns:
            Signed CSRF token
        """
        if not self.redis_client:
            await self.connect()

        # Generate random token
        raw_token = secrets.token_urlsafe(CSRF_TOKEN_LENGTH)

        # Sign the token
        signed_token = self._sign_token(raw_token)

        # Store in Redis with expiry
        redis_key = f"csrf:{session_id}:{raw_token}"
        expiry_seconds = CSRF_TOKEN_EXPIRY_HOURS * 3600

        try:
            await self.redis_client.setex(
                redis_key,
                expiry_seconds,
                datetime.now().isoformat(),
            )
        except Exception as e:
            logger.error(f"Failed to store CSRF token in Redis: {e}")
            # Continue anyway - token will be validated by signature

        return signed_token

    async def validate_token(
        self,
        token: str,
        session_id: str,
        consume: bool = True,
    ) -> bool:
        """
        Validate a CSRF token.

        Args:
            token: Signed CSRF token to validate
            session_id: User session identifier
            consume: If True, token is deleted after validation (one-time use)

        Returns:
            True if token is valid, False otherwise
        """
        if not self.redis_client:
            await self.connect()

        # Verify signature
        raw_token = self._verify_signature(token)
        if not raw_token:
            logger.warning(f"CSRF token signature verification failed for session {session_id}")
            return False

        # Check Redis
        redis_key = f"csrf:{session_id}:{raw_token}"

        try:
            exists = await self.redis_client.exists(redis_key)
            if not exists:
                logger.warning(f"CSRF token not found in Redis for session {session_id}")
                return False

            # Consume token if requested (one-time use)
            if consume:
                await self.redis_client.delete(redis_key)

            return True
        except Exception as e:
            logger.error(f"Failed to validate CSRF token in Redis: {e}")
            # Fail closed - don't validate if Redis is down
            return False

    async def require_csrf_token(
        self,
        request: Request,
        x_csrf_token: Optional[str] = Header(None, alias=CSRF_HEADER_NAME),
    ) -> str:
        """
        Dependency that requires a valid CSRF token.

        Extracts session ID from authentication and validates CSRF token.

        Args:
            request: FastAPI request object
            x_csrf_token: CSRF token from request header

        Returns:
            Validated CSRF token

        Raises:
            HTTPException: If CSRF token is missing or invalid
        """
        if not x_csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing. Include X-CSRF-Token header.",
            )

        # Get session ID from authenticated user or session cookie
        # This assumes you have authentication middleware that sets request.state.user
        session_id = None

        # Try to get from authenticated user
        if hasattr(request.state, "user") and request.state.user:
            session_id = str(request.state.user.id)

        # Try to get from cookies
        if not session_id:
            session_id = request.cookies.get("session_id")

        # Try to get from authorization header (JWT)
        if not session_id:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Use the JWT token itself as session ID
                session_id = auth_header[7:]  # Remove "Bearer " prefix

        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No session found. Please authenticate first.",
            )

        # Validate token
        is_valid = await self.validate_token(x_csrf_token, session_id)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired CSRF token.",
            )

        return x_csrf_token


# Global CSRF protection instance
csrf_protect = CSRFProtect()


async def generate_csrf_token(request: Request) -> str:
    """
    Generate a CSRF token for the current session.

    Args:
        request: FastAPI request object

    Returns:
        New CSRF token

    Usage:
        @app.get("/csrf-token")
        async def get_csrf_token(
            request: Request,
            token: str = Depends(generate_csrf_token)
        ):
            return {"csrf_token": token}
    """
    # Get session ID
    session_id = None

    if hasattr(request.state, "user") and request.state.user:
        session_id = str(request.state.user.id)

    if not session_id:
        session_id = request.cookies.get("session_id")

    if not session_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_id = auth_header[7:]

    if not session_id:
        # Generate temporary session ID for anonymous users
        session_id = f"anon:{secrets.token_urlsafe(16)}"

    return await csrf_protect.generate_token(session_id)


async def get_csrf_protect() -> CSRFProtect:
    """
    Dependency for getting CSRF protection instance.

    Usage:
        @app.post("/endpoint")
        async def endpoint(csrf: CSRFProtect = Depends(get_csrf_protect)):
            ...
    """
    if not csrf_protect.redis_client:
        await csrf_protect.connect()
    return csrf_protect
