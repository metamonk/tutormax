"""
Message publisher for pushing messages to Redis queues.
"""
import logging
from typing import Any, Dict, Optional
import redis

from .client import RedisClient
from .channels import QueueChannels
from .serializer import MessageSerializer
from .config import redis_config

logger = logging.getLogger(__name__)


class MessagePublisher:
    """
    Publishes messages to Redis streams for queue processing.

    Uses Redis Streams (XADD) for reliable message queuing with:
    - Message persistence
    - Consumer groups
    - Automatic TTL management
    - Retry support
    """

    def __init__(self, redis_client: RedisClient):
        """
        Initialize message publisher.

        Args:
            redis_client: Redis client instance
        """
        self.redis_client = redis_client
        self.serializer = MessageSerializer()

    def publish(
        self,
        channel: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None
    ) -> str:
        """
        Publish message to a queue channel.

        Args:
            channel: Queue channel name (e.g., QueueChannels.TUTORS)
            data: Message data payload
            metadata: Optional metadata (e.g., source, priority)
            ttl_seconds: Time-to-live in seconds (defaults to config)

        Returns:
            Message ID assigned by Redis

        Raises:
            redis.RedisError: If publishing fails
        """
        try:
            # Serialize message
            message_json = self.serializer.serialize(channel, data, metadata)

            # Get Redis client
            client = self.redis_client.get_client()

            # Add to Redis stream
            message_id = client.xadd(
                channel,
                {"message": message_json},
                maxlen=redis_config.queue_maxlen,
                approximate=True  # Allow approximate trimming for performance
            )

            # Set TTL on the stream key if this is the first message
            ttl = ttl_seconds or redis_config.message_ttl_seconds
            if ttl > 0:
                client.expire(channel, ttl)

            logger.debug(f"Published message to {channel}: {message_id}")
            return message_id

        except redis.RedisError as e:
            logger.error(f"Failed to publish message to {channel}: {e}")
            raise

    def publish_batch(
        self,
        channel: str,
        messages: list[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> list[str]:
        """
        Publish multiple messages in a batch for efficiency.

        Args:
            channel: Queue channel name
            messages: List of message data payloads
            metadata: Optional metadata applied to all messages

        Returns:
            List of message IDs
        """
        message_ids = []

        try:
            client = self.redis_client.get_client()

            with self.redis_client.pipeline() as pipe:
                for data in messages:
                    message_json = self.serializer.serialize(channel, data, metadata)
                    pipe.xadd(
                        channel,
                        {"message": message_json},
                        maxlen=redis_config.queue_maxlen,
                        approximate=True
                    )

                results = pipe.execute()
                message_ids = [msg_id for msg_id in results if msg_id]

            logger.info(f"Published {len(message_ids)} messages to {channel}")
            return message_ids

        except redis.RedisError as e:
            logger.error(f"Failed to publish batch to {channel}: {e}")
            raise

    def publish_tutor_data(self, tutor_data: Dict[str, Any]) -> str:
        """Convenience method to publish tutor data."""
        return self.publish(QueueChannels.TUTORS, tutor_data)

    def publish_session_data(self, session_data: Dict[str, Any]) -> str:
        """Convenience method to publish session data."""
        return self.publish(QueueChannels.SESSIONS, session_data)

    def publish_feedback_data(self, feedback_data: Dict[str, Any]) -> str:
        """Convenience method to publish feedback data."""
        return self.publish(QueueChannels.FEEDBACK, feedback_data)

    def get_stream_length(self, channel: str) -> int:
        """
        Get number of messages in a stream.

        Args:
            channel: Queue channel name

        Returns:
            Number of messages in stream
        """
        try:
            client = self.redis_client.get_client()
            return client.xlen(channel)
        except redis.RedisError as e:
            logger.error(f"Failed to get stream length for {channel}: {e}")
            return 0

    def get_stream_info(self, channel: str) -> Dict[str, Any]:
        """
        Get detailed information about a stream.

        Args:
            channel: Queue channel name

        Returns:
            Stream info dictionary
        """
        try:
            client = self.redis_client.get_client()
            info = client.xinfo_stream(channel)
            return {
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "groups": info.get("groups", 0),
            }
        except redis.RedisError as e:
            logger.error(f"Failed to get stream info for {channel}: {e}")
            return {}
