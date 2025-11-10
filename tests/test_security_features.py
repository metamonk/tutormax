"""
Tests for security hardening features (Task 14.4).

Tests cover:
- Rate limiting
- CSRF protection
- XSS prevention
- SQL injection prevention
- Input sanitization
- Secret management
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime

# Import security modules
from src.api.security.rate_limiter import RateLimiter, RateLimitConfig
from src.api.security.csrf import CSRFProtect
from src.api.security.input_sanitizer import (
    sanitize_html,
    sanitize_string,
    validate_no_sql_injection,
    sanitize_filename,
    validate_email,
    validate_url,
)
from src.api.security.secret_manager import (
    SecretManager,
    validate_secret_key,
    generate_secure_secret,
)


class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.fixture
    async def limiter(self):
        """Create rate limiter instance."""
        limiter = RateLimiter(redis_url="redis://localhost:6379/15")  # Use test DB
        await limiter.connect()
        yield limiter
        await limiter.disconnect()

    @pytest.mark.asyncio
    async def test_rate_limit_basic(self, limiter):
        """Test basic rate limiting."""
        key = "test:basic"
        max_requests = 3
        window = 10

        # First 3 requests should pass
        for i in range(max_requests):
            is_limited, count, _ = await limiter.is_rate_limited(key, max_requests, window)
            assert not is_limited
            assert count == i + 1

        # 4th request should be limited
        is_limited, count, retry_after = await limiter.is_rate_limited(key, max_requests, window)
        assert is_limited
        assert count >= max_requests
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_rate_limit_sliding_window(self, limiter):
        """Test sliding window algorithm."""
        key = "test:sliding"
        max_requests = 2
        window = 2  # 2 seconds

        # First request
        is_limited, _, _ = await limiter.is_rate_limited(key, max_requests, window)
        assert not is_limited

        # Second request
        is_limited, _, _ = await limiter.is_rate_limited(key, max_requests, window)
        assert not is_limited

        # Third request (should be limited)
        is_limited, _, retry_after = await limiter.is_rate_limited(key, max_requests, window)
        assert is_limited
        assert retry_after <= window

        # Wait for window to pass
        time.sleep(window + 0.5)

        # Should be able to make requests again
        is_limited, _, _ = await limiter.is_rate_limited(key, max_requests, window)
        assert not is_limited

    @pytest.mark.asyncio
    async def test_rate_limit_different_keys(self, limiter):
        """Test that different keys are tracked separately."""
        max_requests = 2
        window = 10

        # Use up limit for key1
        for _ in range(max_requests):
            is_limited, _, _ = await limiter.is_rate_limited("key1", max_requests, window)
            assert not is_limited

        # key1 should be limited
        is_limited, _, _ = await limiter.is_rate_limited("key1", max_requests, window)
        assert is_limited

        # key2 should still work
        is_limited, _, _ = await limiter.is_rate_limited("key2", max_requests, window)
        assert not is_limited


class TestCSRFProtection:
    """Test CSRF protection functionality."""

    @pytest.fixture
    async def csrf(self):
        """Create CSRF protection instance."""
        csrf = CSRFProtect(
            redis_url="redis://localhost:6379/15",
            secret_key="test-secret-key-for-csrf-testing-only"
        )
        await csrf.connect()
        yield csrf
        await csrf.disconnect()

    @pytest.mark.asyncio
    async def test_generate_token(self, csrf):
        """Test CSRF token generation."""
        session_id = "test-session-123"
        token = await csrf.generate_token(session_id)

        assert token is not None
        assert "." in token  # Should have token.signature format
        assert len(token) > 32

    @pytest.mark.asyncio
    async def test_validate_token(self, csrf):
        """Test CSRF token validation."""
        session_id = "test-session-456"
        token = await csrf.generate_token(session_id)

        # Valid token should pass
        is_valid = await csrf.validate_token(token, session_id, consume=False)
        assert is_valid

        # Invalid token should fail
        is_valid = await csrf.validate_token("invalid-token", session_id, consume=False)
        assert not is_valid

        # Wrong session should fail
        is_valid = await csrf.validate_token(token, "wrong-session", consume=False)
        assert not is_valid

    @pytest.mark.asyncio
    async def test_token_consumption(self, csrf):
        """Test one-time token consumption."""
        session_id = "test-session-789"
        token = await csrf.generate_token(session_id)

        # First validation with consume=True
        is_valid = await csrf.validate_token(token, session_id, consume=True)
        assert is_valid

        # Second validation should fail (token consumed)
        is_valid = await csrf.validate_token(token, session_id, consume=False)
        assert not is_valid


class TestInputSanitization:
    """Test input sanitization functionality."""

    def test_sanitize_html_basic(self):
        """Test basic HTML sanitization."""
        dangerous = "<script>alert('XSS')</script>"
        safe = sanitize_html(dangerous)

        assert "<script>" not in safe
        assert "&lt;script&gt;" in safe

    def test_sanitize_html_with_formatting(self):
        """Test HTML sanitization with allowed formatting."""
        text = "<b>Bold</b> and <script>alert('XSS')</script>"
        safe = sanitize_html(text, allow_basic_formatting=True)

        assert "<b>Bold</b>" in safe  # Allowed
        assert "<script>" not in safe  # Removed

    def test_sanitize_string_comprehensive(self):
        """Test comprehensive string sanitization."""
        dangerous = "<script>alert('XSS')</script>Normal text"
        safe = sanitize_string(dangerous, max_length=100, check_sql_injection=True)

        assert "alert" not in safe or "&lt;" in safe
        assert len(safe) <= 100

    def test_sanitize_string_truncation(self):
        """Test string truncation."""
        long_text = "a" * 1000
        safe = sanitize_string(long_text, max_length=100)

        assert len(safe) == 100

    def test_validate_no_sql_injection_safe(self):
        """Test SQL injection detection with safe input."""
        safe_inputs = [
            "john.doe@example.com",
            "Normal user input",
            "User with numbers 123",
        ]

        for text in safe_inputs:
            is_safe = validate_no_sql_injection(text, raise_on_suspicious=False)
            assert is_safe

    def test_validate_no_sql_injection_dangerous(self):
        """Test SQL injection detection with dangerous input."""
        dangerous_inputs = [
            "1' OR '1'='1",
            "admin'--",
            "'; DROP TABLE users--",
            "1 UNION SELECT * FROM users",
        ]

        for text in dangerous_inputs:
            is_safe = validate_no_sql_injection(text, raise_on_suspicious=False)
            assert not is_safe

    def test_validate_no_sql_injection_raises(self):
        """Test SQL injection validation raises on suspicious input."""
        dangerous = "1' OR '1'='1"

        with pytest.raises(ValueError, match="dangerous SQL patterns"):
            validate_no_sql_injection(dangerous, raise_on_suspicious=True)

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        dangerous_names = [
            "../../../etc/passwd",
            "file<script>.txt",
            "file/with/path.txt",
            "file\\with\\backslash.txt",
        ]

        for name in dangerous_names:
            safe = sanitize_filename(name)
            assert ".." not in safe
            assert "/" not in safe
            assert "\\" not in safe
            assert "<" not in safe

    def test_validate_email(self):
        """Test email validation."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "test+tag@domain.org",
        ]

        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user@domain",
        ]

        for email in valid_emails:
            assert validate_email(email)

        for email in invalid_emails:
            assert not validate_email(email)

    def test_validate_url(self):
        """Test URL validation."""
        valid_urls = [
            "https://example.com",
            "http://example.com/path",
            "https://sub.domain.com:8080/path?query=value",
        ]

        invalid_urls = [
            "javascript:alert('XSS')",
            "not a url",
            "ftp://example.com",  # FTP not in default allowed schemes
        ]

        for url in valid_urls:
            assert validate_url(url)

        for url in invalid_urls:
            assert not validate_url(url, allowed_schemes=['http', 'https'])


class TestSecretManagement:
    """Test secret management functionality."""

    def test_redact_secrets_in_text(self):
        """Test secret redaction in text."""
        manager = SecretManager()

        text = "API key is api_key=sk-abc123 and password=secret123"
        redacted = manager.redact_secrets(text)

        assert "sk-abc123" not in redacted
        assert "secret123" not in redacted
        assert "REDACTED" in redacted

    def test_redact_dict(self):
        """Test secret redaction in dictionaries."""
        manager = SecretManager()

        data = {
            "username": "john",
            "password": "secret123",
            "api_key": "sk-abc123",
            "public_data": "visible",
        }

        redacted = manager.redact_dict(data)

        assert redacted["username"] == "john"
        assert redacted["public_data"] == "visible"
        assert redacted["password"] == "***REDACTED***"
        assert redacted["api_key"] == "***REDACTED***"

    def test_validate_secret_key_strong(self):
        """Test validation of strong secret keys."""
        strong_secrets = [
            "a" * 32 + "b" * 16,  # 32+ chars, good entropy
            generate_secure_secret(32),
            "x8f2k9m3n4p5q6r7s8t9u0v1w2y3z4a5b6c7d8e9",
        ]

        for secret in strong_secrets:
            assert validate_secret_key(secret)

    def test_validate_secret_key_weak(self):
        """Test validation rejects weak secret keys."""
        weak_secrets = [
            "short",
            "your-secret-key",
            "password123",
            "change-this-secret",
            "a" * 32,  # Long but low entropy
        ]

        for secret in weak_secrets:
            assert not validate_secret_key(secret)

    def test_generate_secure_secret(self):
        """Test secure secret generation."""
        secret = generate_secure_secret(32)

        assert len(secret) >= 32
        assert validate_secret_key(secret)

    def test_load_secret(self):
        """Test secret loading with validation."""
        manager = SecretManager()

        # Mock environment variable
        with patch.dict('os.environ', {'TEST_SECRET': 'a' * 40}):
            secret = manager.load_secret(
                'TEST_SECRET',
                required=True,
                min_length=32
            )

            assert secret == 'a' * 40
            assert 'TEST_SECRET' in manager.secret_metadata

    def test_load_secret_required_missing(self):
        """Test that loading required missing secret raises error."""
        manager = SecretManager()

        with pytest.raises(ValueError, match="Required secret"):
            manager.load_secret('NONEXISTENT_SECRET', required=True)

    def test_load_secret_too_short(self):
        """Test that short secrets are rejected."""
        manager = SecretManager()

        with patch.dict('os.environ', {'SHORT_SECRET': 'abc'}):
            with pytest.raises(ValueError, match="too short"):
                manager.load_secret('SHORT_SECRET', min_length=32)


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_sql_injection_with_sanitization(self):
        """Test that SQL injection attempts are caught by sanitization."""
        from src.api.security import sanitize_input

        malicious_inputs = [
            {"name": "admin'--", "email": "test@example.com"},
            {"search": "'; DROP TABLE users--"},
        ]

        for data in malicious_inputs:
            with pytest.raises(ValueError):
                sanitize_input(data, check_sql_injection=True)

    def test_xss_with_multiple_vectors(self):
        """Test XSS prevention with various attack vectors."""
        from src.api.security import sanitize_string

        xss_vectors = [
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        ]

        for vector in xss_vectors:
            safe = sanitize_string(vector, allow_html=False)
            assert "alert" not in safe or "&lt;" in safe
            assert "javascript:" not in safe or "&lt;" in safe

    def test_combined_security_pipeline(self):
        """Test full security pipeline for user input."""
        from src.api.security import sanitize_input, validate_no_sql_injection

        # Simulate user input through full pipeline
        user_input = {
            "comment": "<script>alert('XSS')</script>Hello",
            "rating": 5,
        }

        # Step 1: Sanitize
        sanitized = sanitize_input(user_input, check_sql_injection=True)

        # Step 2: Verify no dangerous content
        assert "<script>" not in str(sanitized)

        # Step 3: Verify structure preserved
        assert sanitized["rating"] == 5


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
