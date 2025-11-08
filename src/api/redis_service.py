"""
Redis service for message queuing.

Handles Redis connection and message queue operations for the data ingestion pipeline.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import redis.asyncio as redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis service for queuing incoming data for downstream processing.

    Supports async operations for non-blocking I/O in FastAPI.
    """

    # Queue names for different data types
    TUTOR_QUEUE = "tutormax:queue:tutors"
    SESSION_QUEUE = "tutormax:queue:sessions"
    FEEDBACK_QUEUE = "tutormax:queue:feedbacks"

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis service.

        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379/0)
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Establish connection to Redis.

        Should be called during application startup.
        """
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info(f"Successfully connected to Redis at {self.redis_url}")
        except RedisError as e:
            self._connected = False
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """
        Close Redis connection.

        Should be called during application shutdown.
        """
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    async def is_connected(self) -> bool:
        """
        Check if Redis is connected and responsive.

        Returns:
            True if connected and responsive, False otherwise
        """
        if not self._connected or not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except RedisError:
            self._connected = False
            return False

    async def queue_tutor(self, tutor_data: Dict[str, Any]) -> bool:
        """
        Queue tutor profile data for processing.

        Args:
            tutor_data: Tutor profile dictionary

        Returns:
            True if successfully queued, False otherwise
        """
        return await self._enqueue(self.TUTOR_QUEUE, tutor_data)

    async def queue_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Queue session data for processing.

        Args:
            session_data: Session data dictionary

        Returns:
            True if successfully queued, False otherwise
        """
        return await self._enqueue(self.SESSION_QUEUE, session_data)

    async def queue_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """
        Queue feedback data for processing.

        Args:
            feedback_data: Feedback data dictionary

        Returns:
            True if successfully queued, False otherwise
        """
        return await self._enqueue(self.FEEDBACK_QUEUE, feedback_data)

    async def _enqueue(self, queue_name: str, data: Dict[str, Any]) -> bool:
        """
        Enqueue data to specified Redis queue.

        Uses Redis LPUSH to add to the left side of the list (queue).
        Processors will use RPOP to dequeue from the right side (FIFO).

        Args:
            queue_name: Name of the Redis queue
            data: Data dictionary to enqueue

        Returns:
            True if successfully queued, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            # Add metadata
            message = {
                "data": data,
                "queued_at": datetime.now().isoformat(),
                "queue": queue_name,
            }

            # Serialize to JSON
            message_json = json.dumps(message)

            # Push to queue (LPUSH adds to left, RPOP removes from right = FIFO)
            await self.redis_client.lpush(queue_name, message_json)

            logger.debug(f"Successfully queued message to {queue_name}")
            return True

        except RedisError as e:
            logger.error(f"Failed to queue message to {queue_name}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize message for {queue_name}: {e}")
            return False

    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get the current length of a queue.

        Args:
            queue_name: Name of the Redis queue

        Returns:
            Queue length, or -1 on error
        """
        if not self.redis_client:
            return -1

        try:
            length = await self.redis_client.llen(queue_name)
            return length
        except RedisError as e:
            logger.error(f"Failed to get queue length for {queue_name}: {e}")
            return -1

    async def get_queue_stats(self) -> Dict[str, int]:
        """
        Get statistics for all queues.

        Returns:
            Dictionary mapping queue names to their lengths
        """
        return {
            "tutors": await self.get_queue_length(self.TUTOR_QUEUE),
            "sessions": await self.get_queue_length(self.SESSION_QUEUE),
            "feedbacks": await self.get_queue_length(self.FEEDBACK_QUEUE),
        }


# Global Redis service instance
redis_service = RedisService()


async def get_redis_service() -> RedisService:
    """
    Dependency injection function for FastAPI.

    Returns:
        RedisService instance
    """
    return redis_service
