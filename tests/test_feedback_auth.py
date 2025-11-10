"""
Unit tests for feedback authentication system.

Tests token generation, validation, COPPA compliance, and feedback submission.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from src.api.feedback_token_utils import FeedbackTokenManager, generate_feedback_url
from src.api.feedback_auth_schemas import (
    FeedbackTokenRequest,
    ValidateTokenRequest,
    StudentFeedbackSubmission
)


class TestFeedbackTokenManager:
    """Test suite for FeedbackTokenManager."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis service."""
        redis = Mock()
        redis.redis_client = AsyncMock()
        return redis

    @pytest.fixture
    def token_manager(self, mock_redis):
        """Create FeedbackTokenManager instance with mock Redis."""
        return FeedbackTokenManager(mock_redis)

    def test_generate_token(self):
        """Test token generation produces unique secure tokens."""
        token1 = FeedbackTokenManager.generate_token()
        token2 = FeedbackTokenManager.generate_token()

        # Tokens should be non-empty strings
        assert isinstance(token1, str)
        assert len(token1) > 0

        # Tokens should be unique
        assert token1 != token2

        # Tokens should be URL-safe (no special characters)
        assert all(c.isalnum() or c in '-_' for c in token1)

    def test_hash_token(self):
        """Test token hashing produces consistent SHA-256 hash."""
        token = "test_token_123"
        hash1 = FeedbackTokenManager.hash_token(token)
        hash2 = FeedbackTokenManager.hash_token(token)

        # Hash should be consistent
        assert hash1 == hash2

        # Hash should be hex string
        assert all(c in '0123456789abcdef' for c in hash1)

        # SHA-256 produces 64 character hex string
        assert len(hash1) == 64

    @pytest.mark.asyncio
    async def test_create_feedback_token(self, token_manager, mock_redis):
        """Test feedback token creation with metadata."""
        # Configure mock
        mock_redis.redis_client.setex = AsyncMock()

        # Create token
        token = await token_manager.create_feedback_token(
            session_id="SES-001",
            student_id="STU-001",
            tutor_id="TUT-001",
            student_email="student@example.com",
            is_under_13=False
        )

        # Verify token created
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify Redis was called
        mock_redis.redis_client.setex.assert_called_once()

        # Verify token data structure
        call_args = mock_redis.redis_client.setex.call_args
        redis_key = call_args[0][0]
        ttl = call_args[0][1]
        token_json = call_args[0][2]

        assert redis_key.startswith("tutormax:feedback_token:")
        assert ttl == 7 * 24 * 60 * 60  # 7 days in seconds

        token_data = json.loads(token_json)
        assert token_data["session_id"] == "SES-001"
        assert token_data["student_id"] == "STU-001"
        assert token_data["tutor_id"] == "TUT-001"
        assert token_data["is_under_13"] is False
        assert token_data["uses"] == 0
        assert token_data["max_uses"] == 1

    @pytest.mark.asyncio
    async def test_create_token_with_parent_email(self, token_manager, mock_redis):
        """Test token creation for under-13 student includes parent email."""
        mock_redis.redis_client.setex = AsyncMock()

        token = await token_manager.create_feedback_token(
            session_id="SES-001",
            student_id="STU-001",
            tutor_id="TUT-001",
            parent_email="parent@example.com",
            is_under_13=True
        )

        # Verify token data includes parent email
        call_args = mock_redis.redis_client.setex.call_args
        token_json = call_args[0][2]
        token_data = json.loads(token_json)

        assert token_data["parent_email"] == "parent@example.com"
        assert token_data["is_under_13"] is True

    @pytest.mark.asyncio
    async def test_validate_valid_token(self, token_manager, mock_redis):
        """Test validation of valid token returns metadata."""
        # Mock token data
        token_data = {
            "session_id": "SES-001",
            "student_id": "STU-001",
            "tutor_id": "TUT-001",
            "uses": 0,
            "max_uses": 1,
            "feedback_submitted": False
        }
        mock_redis.redis_client.get = AsyncMock(return_value=json.dumps(token_data))

        # Validate token
        result = await token_manager.validate_token("test_token")

        # Should return token data
        assert result is not None
        assert result["session_id"] == "SES-001"
        assert result["student_id"] == "STU-001"

    @pytest.mark.asyncio
    async def test_validate_expired_token(self, token_manager, mock_redis):
        """Test validation of expired token returns None."""
        # Mock expired token (not found in Redis)
        mock_redis.redis_client.get = AsyncMock(return_value=None)

        # Validate token
        result = await token_manager.validate_token("expired_token")

        # Should return None
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_used_token(self, token_manager, mock_redis):
        """Test validation of already-used token returns None."""
        # Mock used token
        token_data = {
            "session_id": "SES-001",
            "uses": 1,
            "max_uses": 1,
            "feedback_submitted": True
        }
        mock_redis.redis_client.get = AsyncMock(return_value=json.dumps(token_data))

        # Validate token
        result = await token_manager.validate_token("used_token")

        # Should return None (already used)
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_token_used(self, token_manager, mock_redis):
        """Test marking token as used updates metadata."""
        # Mock initial token data
        token_data = {
            "session_id": "SES-001",
            "uses": 0,
            "max_uses": 1,
            "feedback_submitted": False
        }
        mock_redis.redis_client.get = AsyncMock(return_value=json.dumps(token_data))
        mock_redis.redis_client.ttl = AsyncMock(return_value=3600)  # 1 hour remaining
        mock_redis.redis_client.setex = AsyncMock()

        # Mark as used
        result = await token_manager.mark_token_used("test_token", "FB-001")

        # Should succeed
        assert result is True

        # Verify Redis was updated
        mock_redis.redis_client.setex.assert_called_once()

        # Verify updated data
        call_args = mock_redis.redis_client.setex.call_args
        updated_json = call_args[0][2]
        updated_data = json.loads(updated_json)

        assert updated_data["uses"] == 1
        assert updated_data["feedback_submitted"] is True
        assert updated_data["feedback_id"] == "FB-001"
        assert "used_at" in updated_data

    @pytest.mark.asyncio
    async def test_revoke_token(self, token_manager, mock_redis):
        """Test token revocation deletes from Redis."""
        mock_redis.redis_client.delete = AsyncMock()

        # Revoke token
        result = await token_manager.revoke_token("test_token")

        # Should succeed
        assert result is True

        # Verify Redis delete was called
        mock_redis.redis_client.delete.assert_called_once_with(
            "tutormax:feedback_token:test_token"
        )


class TestFeedbackURLGeneration:
    """Test feedback URL generation."""

    def test_generate_feedback_url(self):
        """Test URL generation with token."""
        token = "abc123xyz"
        url = generate_feedback_url(token)

        # URL should contain token
        assert token in url
        assert "token=" in url

        # URL should be properly formatted
        assert url.startswith("http")

    def test_generate_feedback_url_custom_base(self):
        """Test URL generation with custom base URL."""
        token = "abc123xyz"
        base_url = "https://tutormax.com"
        url = generate_feedback_url(token, base_url)

        # URL should use custom base
        assert url.startswith(base_url)
        assert token in url


class TestFeedbackSchemas:
    """Test Pydantic schemas validation."""

    def test_feedback_token_request_validation(self):
        """Test FeedbackTokenRequest schema validation."""
        # Valid request
        request = FeedbackTokenRequest(
            session_id="SES-001",
            student_id="STU-001",
            student_email="student@example.com",
            send_email=True
        )

        assert request.session_id == "SES-001"
        assert request.student_id == "STU-001"
        assert request.send_email is True

    def test_student_feedback_submission_validation(self):
        """Test StudentFeedbackSubmission schema validation."""
        # Valid submission
        submission = StudentFeedbackSubmission(
            token="abc123",
            overall_rating=5,
            subject_knowledge_rating=5,
            communication_rating=4,
            would_recommend=True,
            improvement_areas=["punctuality"],
            free_text_feedback="Great tutor!",
            parent_consent_given=False
        )

        assert submission.overall_rating == 5
        assert submission.would_recommend is True

    def test_feedback_submission_rating_validation(self):
        """Test rating must be between 1 and 5."""
        # Invalid rating (too high)
        with pytest.raises(ValueError):
            StudentFeedbackSubmission(
                token="abc123",
                overall_rating=6,  # Invalid
                parent_consent_given=False
            )

        # Invalid rating (too low)
        with pytest.raises(ValueError):
            StudentFeedbackSubmission(
                token="abc123",
                overall_rating=0,  # Invalid
                parent_consent_given=False
            )

    def test_feedback_submission_improvement_areas_validation(self):
        """Test improvement areas must be from valid list."""
        # Valid areas
        submission = StudentFeedbackSubmission(
            token="abc123",
            overall_rating=5,
            improvement_areas=["communication", "punctuality"],
            parent_consent_given=False
        )
        assert len(submission.improvement_areas) == 2

        # Invalid area
        with pytest.raises(ValueError):
            StudentFeedbackSubmission(
                token="abc123",
                overall_rating=5,
                improvement_areas=["invalid_area"],
                parent_consent_given=False
            )


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
