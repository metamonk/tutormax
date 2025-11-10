"""
Utilities for feedback token generation and validation.

Implements session-specific feedback tokens for student feedback submission
with COPPA compliance and security measures.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import logging

from .config import settings

logger = logging.getLogger(__name__)


class FeedbackTokenManager:
    """
    Manager for feedback token generation, validation, and storage.

    Uses Redis for token storage with automatic expiration.
    Implements secure token generation and validation for student feedback.
    """

    # Token configuration
    TOKEN_LENGTH = 32  # 32 bytes = 256 bits of randomness
    TOKEN_EXPIRY_DAYS = 7  # Default expiration: 7 days after session
    MAX_USES = 1  # One-time use tokens

    # Redis key prefix for feedback tokens
    TOKEN_PREFIX = "tutormax:feedback_token:"

    def __init__(self, redis_service):
        """
        Initialize feedback token manager.

        Args:
            redis_service: RedisService instance for token storage
        """
        self.redis = redis_service

    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure random token.

        Returns:
            URL-safe token string (43 characters)
        """
        return secrets.token_urlsafe(FeedbackTokenManager.TOKEN_LENGTH)

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token for storage (defense in depth).

        Args:
            token: Raw token string

        Returns:
            SHA-256 hex digest of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def create_feedback_token(
        self,
        session_id: str,
        student_id: str,
        tutor_id: str,
        student_email: Optional[str] = None,
        parent_email: Optional[str] = None,
        is_under_13: bool = False,
        expiry_days: Optional[int] = None,
        max_uses: Optional[int] = None
    ) -> str:
        """
        Create a new feedback token for a session.

        Args:
            session_id: Session ID the feedback is for
            student_id: Student ID
            tutor_id: Tutor ID
            student_email: Student's email (optional)
            parent_email: Parent's email for under-13 students
            is_under_13: Whether student is under 13 (COPPA)
            expiry_days: Custom expiration in days (default: TOKEN_EXPIRY_DAYS)
            max_uses: Maximum number of uses (default: MAX_USES)

        Returns:
            Generated token string

        Raises:
            Exception: If Redis storage fails
        """
        # Generate token
        token = self.generate_token()

        # Calculate expiry
        expiry_days = expiry_days or self.TOKEN_EXPIRY_DAYS
        expiry_seconds = expiry_days * 24 * 60 * 60

        # Prepare token metadata
        token_data = {
            "session_id": session_id,
            "student_id": student_id,
            "tutor_id": tutor_id,
            "student_email": student_email,
            "parent_email": parent_email,
            "is_under_13": is_under_13,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=expiry_days)).isoformat(),
            "max_uses": max_uses or self.MAX_USES,
            "uses": 0,
            "used_at": None,
            "feedback_submitted": False
        }

        # Store in Redis with expiration
        redis_key = f"{self.TOKEN_PREFIX}{token}"

        try:
            if not self.redis.redis_client:
                raise Exception("Redis client not initialized")

            # Serialize token data
            token_json = json.dumps(token_data)

            # Store with expiration
            await self.redis.redis_client.setex(
                redis_key,
                expiry_seconds,
                token_json
            )

            logger.info(f"Created feedback token for session {session_id}, student {student_id}")
            return token

        except Exception as e:
            logger.error(f"Failed to create feedback token: {e}")
            raise

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a feedback token and return its metadata.

        Args:
            token: Token string to validate

        Returns:
            Token metadata if valid, None if invalid or expired
        """
        redis_key = f"{self.TOKEN_PREFIX}{token}"

        try:
            if not self.redis.redis_client:
                logger.error("Redis client not initialized")
                return None

            # Retrieve token data
            token_json = await self.redis.redis_client.get(redis_key)

            if not token_json:
                logger.warning(f"Token not found or expired")
                return None

            # Parse token data
            token_data = json.loads(token_json)

            # Check if token has been used up
            if token_data.get("uses", 0) >= token_data.get("max_uses", 1):
                logger.warning(f"Token already used maximum times")
                return None

            # Check if feedback already submitted
            if token_data.get("feedback_submitted", False):
                logger.warning(f"Feedback already submitted with this token")
                return None

            return token_data

        except Exception as e:
            logger.error(f"Failed to validate token: {e}")
            return None

    async def mark_token_used(
        self,
        token: str,
        feedback_id: Optional[str] = None
    ) -> bool:
        """
        Mark a token as used and optionally link to submitted feedback.

        Args:
            token: Token string
            feedback_id: ID of submitted feedback (optional)

        Returns:
            True if successfully marked, False otherwise
        """
        redis_key = f"{self.TOKEN_PREFIX}{token}"

        try:
            if not self.redis.redis_client:
                return False

            # Retrieve current token data
            token_json = await self.redis.redis_client.get(redis_key)

            if not token_json:
                return False

            # Parse and update token data
            token_data = json.loads(token_json)
            token_data["uses"] = token_data.get("uses", 0) + 1
            token_data["used_at"] = datetime.utcnow().isoformat()
            token_data["feedback_submitted"] = True

            if feedback_id:
                token_data["feedback_id"] = feedback_id

            # Get remaining TTL
            ttl = await self.redis.redis_client.ttl(redis_key)

            if ttl > 0:
                # Update token data with same TTL
                updated_json = json.dumps(token_data)
                await self.redis.redis_client.setex(
                    redis_key,
                    ttl,
                    updated_json
                )

                logger.info(f"Marked token as used (session: {token_data.get('session_id')})")
                return True
            else:
                # Token expired during validation
                return False

        except Exception as e:
            logger.error(f"Failed to mark token as used: {e}")
            return False

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a token before expiration.

        Args:
            token: Token string to revoke

        Returns:
            True if successfully revoked, False otherwise
        """
        redis_key = f"{self.TOKEN_PREFIX}{token}"

        try:
            if not self.redis.redis_client:
                return False

            await self.redis.redis_client.delete(redis_key)
            logger.info(f"Revoked feedback token")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    async def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token without validating it.

        Useful for administrative purposes.

        Args:
            token: Token string

        Returns:
            Token metadata if exists, None otherwise
        """
        redis_key = f"{self.TOKEN_PREFIX}{token}"

        try:
            if not self.redis.redis_client:
                return None

            token_json = await self.redis.redis_client.get(redis_key)

            if not token_json:
                return None

            return json.loads(token_json)

        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None


def generate_feedback_url(token: str, base_url: Optional[str] = None) -> str:
    """
    Generate a complete feedback URL with token.

    Args:
        token: Feedback token
        base_url: Base URL for the application (default: from settings)

    Returns:
        Complete URL for student feedback submission
    """
    base = base_url or settings.oauth_redirect_base_url or "http://localhost:8000"
    return f"{base}/feedback/submit?token={token}"
