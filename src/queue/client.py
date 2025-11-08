"""
Redis client with connection pooling and error handling.
"""
import redis
from redis.connection import ConnectionPool
from typing import Optional
import logging
from contextlib import contextmanager

from .config import redis_config, get_redis_url

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling and error handling.

    Provides:
    - Connection pooling for efficient resource usage
    - Automatic reconnection on failure
    - Graceful shutdown handling
    - Health checks
    """

    def __init__(self, url: Optional[str] = None):
        """
        Initialize Redis client with connection pool.

        Args:
            url: Redis connection URL (defaults to config)
        """
        self.url = url or get_redis_url()
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self._is_connected = False

    def connect(self) -> None:
        """Establish Redis connection with pooling."""
        try:
            self.pool = ConnectionPool.from_url(
                self.url,
                max_connections=redis_config.max_connections,
                socket_timeout=redis_config.socket_timeout,
                socket_connect_timeout=redis_config.socket_connect_timeout,
                retry_on_timeout=redis_config.retry_on_timeout,
                decode_responses=True,  # Automatically decode byte responses to strings
            )

            self.client = redis.Redis(connection_pool=self.pool)

            # Test connection
            self.client.ping()
            self._is_connected = True
            logger.info(f"Redis client connected to {redis_config.host}:{redis_config.port}")

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def disconnect(self) -> None:
        """Close Redis connection and cleanup pool."""
        if self.client:
            try:
                self.client.close()
                logger.info("Redis client disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting Redis client: {e}")
            finally:
                self._is_connected = False
                self.client = None

        if self.pool:
            try:
                self.pool.disconnect()
                self.pool = None
            except Exception as e:
                logger.error(f"Error disconnecting connection pool: {e}")

    def is_connected(self) -> bool:
        """Check if client is connected to Redis."""
        if not self._is_connected or not self.client:
            return False

        try:
            self.client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            self._is_connected = False
            return False

    def health_check(self) -> dict:
        """
        Perform health check on Redis connection.

        Returns:
            Dictionary with health status and info
        """
        try:
            if not self.is_connected():
                return {
                    "status": "unhealthy",
                    "error": "Not connected to Redis"
                }

            # Get Redis info
            info = self.client.info()

            return {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def get_client(self) -> redis.Redis:
        """
        Get Redis client instance.

        Returns:
            Redis client

        Raises:
            RuntimeError: If not connected
        """
        if not self.is_connected():
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self.client

    @contextmanager
    def pipeline(self):
        """
        Context manager for Redis pipeline operations.

        Example:
            with redis_client.pipeline() as pipe:
                pipe.set('key1', 'value1')
                pipe.set('key2', 'value2')
                pipe.execute()
        """
        client = self.get_client()
        pipe = client.pipeline()
        try:
            yield pipe
        finally:
            pipe.reset()


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Get global Redis client instance (singleton pattern).

    Returns:
        RedisClient instance
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = RedisClient()
        _redis_client.connect()

    return _redis_client


def shutdown_redis_client() -> None:
    """Shutdown global Redis client."""
    global _redis_client

    if _redis_client is not None:
        _redis_client.disconnect()
        _redis_client = None
