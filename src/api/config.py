"""
Configuration settings for the TutorMax API.

Uses pydantic-settings for environment variable management.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be set in .env file or system environment.
    """

    # Application settings
    app_name: str = "TutorMax Data Ingestion API"
    app_version: str = "0.1.0"
    debug: bool = False

    # API settings
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",  # React default dev server
        "http://localhost:3001",  # Next.js dev server (alternative port)
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:8080",  # Alternative frontend port
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 10

    # Logging settings
    log_level: str = "INFO"

    # Rate limiting (sessions per day target)
    max_sessions_per_day: int = 3000

    # Authentication & JWT settings
    secret_key: str = "your-secret-key-change-in-production-use-openssl-rand"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OAuth Settings
    google_client_id: str = ""
    google_client_secret: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    custom_oauth_client_id: str = ""
    custom_oauth_client_secret: str = ""
    oauth_redirect_base_url: str = "http://localhost:8000"  # Base URL for OAuth callbacks

    # Password policy
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = False

    # Account security
    max_failed_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30

    # Security settings (Task 14.4 - Security Hardening)
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_auth_login_requests: int = 5
    rate_limit_auth_login_window: int = 300  # 5 minutes
    rate_limit_auth_register_requests: int = 3
    rate_limit_auth_register_window: int = 3600  # 1 hour
    rate_limit_api_read_requests: int = 100
    rate_limit_api_read_window: int = 60  # 1 minute
    rate_limit_api_write_requests: int = 30
    rate_limit_api_write_window: int = 60  # 1 minute

    # CSRF protection
    csrf_enabled: bool = True
    csrf_token_expiry_hours: int = 24

    # XSS prevention
    security_headers_enabled: bool = True
    csp_policy: str = ""  # Empty means use default from SecurityHeadersMiddleware
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year

    # Input sanitization
    input_sanitization_enabled: bool = True
    max_input_length: int = 10000

    # Secret management
    secret_rotation_days: int = 90

    # Data encryption & privacy (Task 14.6)
    encryption_enabled: bool = True
    encryption_key: str = ""  # Optional: Override derived key from secret_key
    anonymization_enabled: bool = True  # Anonymize data for analytics
    coppa_compliance_enabled: bool = True  # Enable COPPA protections for under-13 users

    # Data retention & compliance
    audit_log_retention_days: int = 2555  # 7 years for FERPA compliance
    pii_data_retention_days: int = 2555  # 7 years for educational records
    anonymize_after_days: int = 1095  # Anonymize after 3 years (inactive users)

    # Email settings (for feedback invitations)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = ""
    smtp_from_name: str = "TutorMax"

    # Database settings
    postgres_user: str = "tutormax"
    postgres_password: str = "tutormax_dev"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "tutormax"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Monitoring & Error Tracking (Task 19)
    sentry_dsn: str = ""  # Sentry DSN for error tracking
    sentry_environment: str = "development"  # Environment name (production, staging, development)
    sentry_traces_sample_rate: float = 0.1  # % of transactions to sample (0.0-1.0)
    sentry_profiles_sample_rate: float = 0.1  # % of profiles to sample (0.0-1.0)
    sentry_enabled: bool = True  # Enable/disable Sentry

    # Alerting Configuration (Task 19.6)
    alert_email: str = ""  # Email address for alerts (defaults to smtp_from_email)
    slack_webhook_url: str = ""  # Slack webhook URL for alerts
    alert_webhook_url: str = ""  # Generic webhook URL (e.g., PagerDuty Events API)
    pagerduty_routing_key: str = ""  # PagerDuty integration/routing key
    alert_dedup_window_minutes: int = 15  # Alert deduplication window

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
