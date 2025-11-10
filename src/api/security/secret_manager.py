"""
Secret management utilities for secure handling of sensitive configuration.

Provides:
- Secret redaction in logs
- Secret rotation support
- Secure secret loading from environment
- Secret validation
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Manages application secrets with security best practices.

    Features:
    - Automatic redaction in logs
    - Secret rotation tracking
    - Validation and format checking
    - Secure environment variable loading
    """

    # Patterns to identify secrets in logs
    SECRET_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)', 'password'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)', 'api_key'),
        (r'secret[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)', 'secret_key'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)', 'token'),
        (r'bearer\s+([a-zA-Z0-9\-_\.]+)', 'bearer_token'),
        (r'(sk-[a-zA-Z0-9]{32,})', 'openai_key'),  # OpenAI API keys
        (r'(xox[baprs]-[a-zA-Z0-9-]+)', 'slack_token'),  # Slack tokens
        (r'(ghp_[a-zA-Z0-9]{36})', 'github_token'),  # GitHub tokens
        (r'(AKIA[0-9A-Z]{16})', 'aws_access_key'),  # AWS access keys
    ]

    # Secrets that should never be logged
    SENSITIVE_KEYS = {
        'password',
        'secret_key',
        'api_key',
        'token',
        'access_token',
        'refresh_token',
        'private_key',
        'client_secret',
        'database_password',
        'postgres_password',
        'redis_password',
        'jwt_secret',
    }

    def __init__(self):
        """Initialize secret manager."""
        self.secrets: Dict[str, str] = {}
        self.secret_metadata: Dict[str, Dict[str, Any]] = {}
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), name)
            for pattern, name in self.SECRET_PATTERNS
        ]

    def redact_secrets(self, text: str) -> str:
        """
        Redact secrets from text (for safe logging).

        Args:
            text: Text that may contain secrets

        Returns:
            Text with secrets redacted
        """
        if not isinstance(text, str):
            return text

        redacted = text
        for pattern, secret_type in self._compiled_patterns:
            redacted = pattern.sub(f'{secret_type}=***REDACTED***', redacted)

        return redacted

    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact secrets from dictionary (for safe logging).

        Args:
            data: Dictionary that may contain secrets

        Returns:
            Dictionary with secrets redacted
        """
        if not isinstance(data, dict):
            return data

        redacted = {}
        for key, value in data.items():
            key_lower = key.lower().replace('-', '_')

            if any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYS):
                redacted[key] = '***REDACTED***'
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, str):
                redacted[key] = self.redact_secrets(value)
            else:
                redacted[key] = value

        return redacted

    def load_secret(
        self,
        key: str,
        default: Optional[str] = None,
        required: bool = False,
        min_length: Optional[int] = None,
        validate_func: Optional[callable] = None,
    ) -> Optional[str]:
        """
        Load a secret from environment variables with validation.

        Args:
            key: Environment variable name
            default: Default value if not found
            required: If True, raises ValueError if secret not found
            min_length: Minimum required length for the secret
            validate_func: Optional validation function

        Returns:
            Secret value

        Raises:
            ValueError: If required secret is missing or validation fails
        """
        value = os.getenv(key, default)

        if required and not value:
            raise ValueError(f"Required secret '{key}' not found in environment")

        if value:
            # Validate minimum length
            if min_length and len(value) < min_length:
                raise ValueError(
                    f"Secret '{key}' is too short. "
                    f"Minimum length: {min_length}, got: {len(value)}"
                )

            # Custom validation
            if validate_func and not validate_func(value):
                raise ValueError(f"Secret '{key}' failed custom validation")

            # Store secret metadata
            self.secret_metadata[key] = {
                'loaded_at': datetime.now(),
                'length': len(value),
                'source': 'environment',
            }

            # Store secret (in memory only, never log)
            self.secrets[key] = value

            # Log that secret was loaded (but not the value)
            logger.info(f"Secret '{key}' loaded successfully (length: {len(value)})")

        return value

    def rotate_secret(self, key: str, new_value: str) -> None:
        """
        Rotate a secret (update to new value).

        Args:
            key: Secret key to rotate
            new_value: New secret value
        """
        old_metadata = self.secret_metadata.get(key, {})

        self.secrets[key] = new_value
        self.secret_metadata[key] = {
            'loaded_at': datetime.now(),
            'length': len(new_value),
            'source': 'rotation',
            'previous_rotation': old_metadata.get('loaded_at'),
        }

        logger.info(f"Secret '{key}' rotated successfully")

    def get_secret(self, key: str) -> Optional[str]:
        """
        Get a secret value.

        Args:
            key: Secret key

        Returns:
            Secret value or None if not found
        """
        return self.secrets.get(key)

    def validate_secret_age(self, key: str, max_age_days: int = 90) -> bool:
        """
        Check if a secret is older than max_age_days.

        Args:
            key: Secret key
            max_age_days: Maximum age in days

        Returns:
            True if secret should be rotated, False otherwise
        """
        metadata = self.secret_metadata.get(key)
        if not metadata:
            return False

        loaded_at = metadata.get('loaded_at')
        if not loaded_at:
            return False

        age = datetime.now() - loaded_at
        should_rotate = age > timedelta(days=max_age_days)

        if should_rotate:
            logger.warning(
                f"Secret '{key}' is {age.days} days old. "
                f"Consider rotating (max age: {max_age_days} days)"
            )

        return should_rotate

    def validate_all_secrets(self, max_age_days: int = 90) -> List[str]:
        """
        Check all secrets for rotation needs.

        Args:
            max_age_days: Maximum age in days

        Returns:
            List of secret keys that need rotation
        """
        needs_rotation = []
        for key in self.secrets.keys():
            if self.validate_secret_age(key, max_age_days):
                needs_rotation.append(key)

        return needs_rotation

    def clear_secrets(self) -> None:
        """Clear all secrets from memory."""
        self.secrets.clear()
        self.secret_metadata.clear()
        logger.info("All secrets cleared from memory")


# Global secret manager instance
secret_manager = SecretManager()


def get_secret_manager() -> SecretManager:
    """
    Get the global secret manager instance.

    Returns:
        SecretManager instance
    """
    return secret_manager


def redact_secrets_in_logs(func):
    """
    Decorator to automatically redact secrets from function logs.

    Usage:
        @redact_secrets_in_logs
        def process_data(api_key: str, data: dict):
            logger.info(f"Processing with key: {api_key}")  # Will be redacted
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Redact secrets in exception messages before re-raising
            error_msg = str(e)
            redacted_msg = secret_manager.redact_secrets(error_msg)
            logger.error(f"Error in {func.__name__}: {redacted_msg}")
            raise

    return wrapper


# Logging filter to redact secrets
class SecretRedactionFilter(logging.Filter):
    """
    Logging filter that redacts secrets from log messages.

    Usage:
        handler = logging.StreamHandler()
        handler.addFilter(SecretRedactionFilter())
        logger.addHandler(handler)
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to redact secrets.

        Args:
            record: Log record to filter

        Returns:
            True (always pass through, but modify the record)
        """
        # Redact secrets from the message
        if isinstance(record.msg, str):
            record.msg = secret_manager.redact_secrets(record.msg)

        # Redact secrets from arguments
        if record.args:
            if isinstance(record.args, dict):
                record.args = secret_manager.redact_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    secret_manager.redact_secrets(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True


def setup_secure_logging():
    """
    Setup logging with automatic secret redaction.

    Call this once at application startup.
    """
    # Add filter to all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(SecretRedactionFilter())

    logger.info("Secure logging with secret redaction enabled")


def validate_secret_key(secret: str) -> bool:
    """
    Validate that a secret key meets minimum security requirements.

    Args:
        secret: Secret key to validate

    Returns:
        True if secret is strong enough
    """
    # Minimum length
    if len(secret) < 32:
        logger.warning("Secret key is too short (minimum 32 characters)")
        return False

    # Check for default/weak values
    weak_secrets = [
        'change-this',
        'your-secret-key',
        'secret',
        'password',
        '12345',
        'admin',
    ]

    secret_lower = secret.lower()
    for weak in weak_secrets:
        if weak in secret_lower:
            logger.warning(f"Secret key contains weak pattern: {weak}")
            return False

    # Check entropy (character diversity)
    unique_chars = len(set(secret))
    if unique_chars < 16:
        logger.warning("Secret key lacks sufficient entropy")
        return False

    return True


def generate_secure_secret(length: int = 32) -> str:
    """
    Generate a cryptographically secure random secret.

    Args:
        length: Length of the secret (minimum 32)

    Returns:
        Secure random secret
    """
    import secrets

    if length < 32:
        length = 32

    return secrets.token_urlsafe(length)
