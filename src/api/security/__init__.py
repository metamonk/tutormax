"""
Security module for TutorMax API.

Provides comprehensive security features including:
- Rate limiting
- CSRF protection
- XSS prevention
- Input sanitization
- Security headers
- Secret management
- Data encryption (AES-256)
- Data anonymization
- Privacy compliance (FERPA, COPPA, GDPR)
"""

from .rate_limiter import rate_limiter, RateLimiter, RateLimitConfig
from .security_headers import SecurityHeadersMiddleware
from .csrf import csrf_protect, CSRFProtect, generate_csrf_token
from .input_sanitizer import (
    sanitize_input,
    sanitize_html,
    sanitize_string,
    sanitize_dict,
    sanitize_list,
    sanitize_filename,
    validate_no_sql_injection,
    validate_email,
    validate_url,
)
from .secret_manager import (
    SecretManager,
    get_secret_manager,
    secret_manager,
    validate_secret_key,
    generate_secure_secret,
    setup_secure_logging,
    SecretRedactionFilter,
)
from .encryption import (
    EncryptionService,
    AnonymizationService,
    DataPrivacyHelper,
    encryption_service,
    anonymization_service,
    privacy_helper,
)

__all__ = [
    # Rate limiting
    'rate_limiter',
    'RateLimiter',
    'RateLimitConfig',
    # Security headers
    'SecurityHeadersMiddleware',
    # CSRF protection
    'csrf_protect',
    'CSRFProtect',
    'generate_csrf_token',
    # Input sanitization
    'sanitize_input',
    'sanitize_html',
    'sanitize_string',
    'sanitize_dict',
    'sanitize_list',
    'sanitize_filename',
    'validate_no_sql_injection',
    'validate_email',
    'validate_url',
    # Secret management
    'SecretManager',
    'get_secret_manager',
    'secret_manager',
    'validate_secret_key',
    'generate_secure_secret',
    'setup_secure_logging',
    'SecretRedactionFilter',
    # Data encryption & privacy
    'EncryptionService',
    'AnonymizationService',
    'DataPrivacyHelper',
    'encryption_service',
    'anonymization_service',
    'privacy_helper',
]
