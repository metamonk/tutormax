"""
Redis configuration for TutorMax message queue.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class RedisConfig(BaseSettings):
    """Redis connection and queue configuration."""

    # Connection settings
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    # Connection pool settings
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    # Retry settings
    retry_on_timeout: bool = True
    max_retries: int = 3
    retry_backoff_ms: int = 100

    # Message settings
    message_ttl_seconds: int = 86400  # 24 hours
    max_message_size_bytes: int = 1048576  # 1 MB

    # Worker settings
    worker_batch_size: int = 10
    worker_poll_interval_ms: int = 100
    worker_max_processing_time_seconds: int = 300  # 5 minutes

    # Queue settings
    queue_maxlen: int = 100000  # Maximum queue length

    class Config:
        env_prefix = "REDIS_"
        env_file = ".env"
        case_sensitive = False


# Global config instance
redis_config = RedisConfig()


def get_redis_url() -> str:
    """Get Redis connection URL."""
    if redis_config.password:
        return f"redis://:{redis_config.password}@{redis_config.host}:{redis_config.port}/{redis_config.db}"
    return f"redis://{redis_config.host}:{redis_config.port}/{redis_config.db}"
