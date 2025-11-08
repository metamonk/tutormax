"""
Message consumer for reading messages from Redis queues.
"""
import logging
from typing import Any, Dict, List, Optional, Callable
import redis
import time

from .client import RedisClient
from .channels import QueueChannels
from .serializer import MessageSerializer
from .config import redis_config

logger = logging.getLogger(__name__)


class MessageConsumer:
    """
    Consumes messages from Redis streams using consumer groups.

    Provides:
    - Consumer group management
    - Message acknowledgment
    - Automatic retry of failed messages
    - Dead letter queue for permanently failed messages
    """

    def __init__(
        self,
        redis_client: RedisClient,
        consumer_group: str = "tutormax-workers",
        consumer_name: Optional[str] = None
    ):
        """
        Initialize message consumer.

        Args:
            redis_client: Redis client instance
            consumer_group: Consumer group name
            consumer_name: Unique consumer name (defaults to hostname-pid)
        """
        self.redis_client = redis_client
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"consumer-{time.time_ns()}"
        self.serializer = MessageSerializer()

        # Track processing stats
        self.stats = {
            "messages_processed": 0,
            "messages_failed": 0,
            "messages_acknowledged": 0,
        }

    def create_consumer_group(
        self,
        channel: str,
        start_id: str = "0"
    ) -> bool:
        """
        Create consumer group for a channel if it doesn't exist.

        Args:
            channel: Queue channel name
            start_id: Starting message ID ('0' for all, '$' for new only)

        Returns:
            True if group was created, False if it already existed
        """
        try:
            client = self.redis_client.get_client()
            client.xgroup_create(channel, self.consumer_group, start_id, mkstream=True)
            logger.info(f"Created consumer group '{self.consumer_group}' for {channel}")
            return True

        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{self.consumer_group}' already exists for {channel}")
                return False
            raise

    def consume(
        self,
        channel: str,
        count: int = 1,
        block_ms: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Consume messages from a channel.

        Args:
            channel: Queue channel name
            count: Maximum number of messages to read
            block_ms: Block for up to this many milliseconds (None = don't block)

        Returns:
            List of deserialized messages with metadata
        """
        try:
            client = self.redis_client.get_client()

            # Ensure consumer group exists
            self.create_consumer_group(channel)

            # Read messages from stream
            messages = client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {channel: ">"},  # '>' means only new messages
                count=count,
                block=block_ms
            )

            if not messages:
                return []

            # Parse messages
            parsed_messages = []
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    try:
                        message_json = message_data.get("message", "{}")
                        parsed_msg = self.serializer.deserialize(message_json)
                        parsed_msg["_redis_id"] = message_id
                        parsed_msg["_stream"] = stream_name
                        parsed_messages.append(parsed_msg)

                    except ValueError as e:
                        logger.error(f"Failed to deserialize message {message_id}: {e}")
                        # Acknowledge bad message to remove it from pending
                        self.acknowledge(channel, message_id)
                        self.stats["messages_failed"] += 1

            self.stats["messages_processed"] += len(parsed_messages)
            return parsed_messages

        except redis.RedisError as e:
            logger.error(f"Failed to consume from {channel}: {e}")
            raise

    def acknowledge(self, channel: str, message_id: str) -> bool:
        """
        Acknowledge successful processing of a message.

        Args:
            channel: Queue channel name
            message_id: Redis message ID

        Returns:
            True if acknowledged successfully
        """
        try:
            client = self.redis_client.get_client()
            result = client.xack(channel, self.consumer_group, message_id)

            if result:
                self.stats["messages_acknowledged"] += 1
                logger.debug(f"Acknowledged message {message_id} from {channel}")

            return bool(result)

        except redis.RedisError as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")
            return False

    def retry_message(
        self,
        channel: str,
        message: Dict[str, Any],
        max_retries: int = 3
    ) -> bool:
        """
        Retry a failed message or send to dead letter queue.

        Args:
            channel: Original queue channel
            message: Message dictionary
            max_retries: Maximum retry attempts

        Returns:
            True if retried, False if sent to dead letter queue
        """
        try:
            client = self.redis_client.get_client()

            # Get current retry count
            metadata = message.get("metadata", {})
            retry_count = metadata.get("retry_count", 0) + 1

            if retry_count <= max_retries:
                # Add to retry channel
                retry_channel = QueueChannels.get_retry_channel(channel)
                metadata["retry_count"] = retry_count
                metadata["original_channel"] = channel

                retry_message_json = self.serializer.serialize(
                    retry_channel,
                    message.get("data", {}),
                    metadata
                )

                client.xadd(retry_channel, {"message": retry_message_json})
                logger.info(f"Retrying message (attempt {retry_count}/{max_retries})")
                return True

            else:
                # Send to dead letter queue
                metadata["retry_count"] = retry_count
                metadata["original_channel"] = channel
                metadata["reason"] = "Max retries exceeded"

                dlq_message_json = self.serializer.serialize(
                    QueueChannels.DEAD_LETTER,
                    message.get("data", {}),
                    metadata
                )

                client.xadd(QueueChannels.DEAD_LETTER, {"message": dlq_message_json})
                logger.warning(f"Message sent to dead letter queue after {retry_count} attempts")
                return False

        except redis.RedisError as e:
            logger.error(f"Failed to retry message: {e}")
            return False

    def get_pending_messages(
        self,
        channel: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get pending messages that haven't been acknowledged.

        Args:
            channel: Queue channel name
            count: Maximum number of pending messages to retrieve

        Returns:
            List of pending message info
        """
        try:
            client = self.redis_client.get_client()

            # Get pending message info
            pending = client.xpending_range(
                channel,
                self.consumer_group,
                "-",
                "+",
                count
            )

            return [
                {
                    "message_id": p["message_id"],
                    "consumer": p["consumer"],
                    "time_since_delivered": p["time_since_delivered"],
                    "times_delivered": p["times_delivered"],
                }
                for p in pending
            ]

        except redis.RedisError as e:
            logger.error(f"Failed to get pending messages: {e}")
            return []

    def claim_pending_messages(
        self,
        channel: str,
        min_idle_time_ms: int = 60000,  # 1 minute
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Claim pending messages that have been idle too long (dead consumer recovery).

        Args:
            channel: Queue channel name
            min_idle_time_ms: Minimum idle time in milliseconds
            count: Maximum messages to claim

        Returns:
            List of claimed messages
        """
        try:
            client = self.redis_client.get_client()

            # Get pending messages
            pending = client.xpending_range(
                channel,
                self.consumer_group,
                "-",
                "+",
                count
            )

            if not pending:
                return []

            # Claim idle messages
            message_ids = [p["message_id"] for p in pending]
            claimed = client.xclaim(
                channel,
                self.consumer_group,
                self.consumer_name,
                min_idle_time_ms,
                message_ids
            )

            # Parse claimed messages
            claimed_messages = []
            for message_id, message_data in claimed:
                try:
                    message_json = message_data.get("message", "{}")
                    parsed_msg = self.serializer.deserialize(message_json)
                    parsed_msg["_redis_id"] = message_id
                    parsed_msg["_stream"] = channel
                    claimed_messages.append(parsed_msg)
                except ValueError as e:
                    logger.error(f"Failed to deserialize claimed message {message_id}: {e}")

            logger.info(f"Claimed {len(claimed_messages)} pending messages from {channel}")
            return claimed_messages

        except redis.RedisError as e:
            logger.error(f"Failed to claim pending messages: {e}")
            return []

    def get_stats(self) -> Dict[str, int]:
        """Get consumer statistics."""
        return self.stats.copy()
