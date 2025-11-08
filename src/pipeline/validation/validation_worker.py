"""
Validation worker for processing messages from Redis queues.

Consumes messages from Redis, validates data, and publishes to
enrichment queues or dead letter queue based on validation results.
"""

import logging
import time
import signal
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime

from ...queue.client import RedisClient
from ...queue.consumer import MessageConsumer
from ...queue.publisher import MessagePublisher
from ...queue.channels import QueueChannels
from ...queue.config import redis_config
from .validation_engine import ValidationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationWorker:
    """
    Worker that validates messages from Redis queues.

    Processes messages in batches:
    1. Consume from Redis queue
    2. Validate data
    3. Publish valid data to enrichment queue
    4. Send invalid data to dead letter queue
    5. Acknowledge processed messages
    """

    # Queue mappings
    QUEUE_MAPPINGS = {
        QueueChannels.TUTORS: {
            "data_type": "tutor",
            "enrichment_queue": "tutormax:tutors:enrichment"
        },
        QueueChannels.SESSIONS: {
            "data_type": "session",
            "enrichment_queue": "tutormax:sessions:enrichment"
        },
        QueueChannels.FEEDBACK: {
            "data_type": "feedback",
            "enrichment_queue": "tutormax:feedback:enrichment"
        },
    }

    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        consumer_group: str = "validation-workers",
        batch_size: int = 10,
        poll_interval_ms: int = 1000
    ):
        """
        Initialize validation worker.

        Args:
            redis_client: Redis client instance (creates new if None)
            consumer_group: Consumer group name
            batch_size: Number of messages to process per batch
            poll_interval_ms: Polling interval in milliseconds
        """
        self.redis_client = redis_client or RedisClient()
        self.consumer_group = consumer_group
        self.batch_size = batch_size
        self.poll_interval_ms = poll_interval_ms

        # Initialize components
        self.consumer = MessageConsumer(
            self.redis_client,
            consumer_group=consumer_group
        )
        self.publisher = MessagePublisher(self.redis_client)
        self.validation_engine = ValidationEngine()

        # Worker state
        self.running = False
        self.stats = {
            "messages_processed": 0,
            "messages_valid": 0,
            "messages_invalid": 0,
            "batches_processed": 0,
            "start_time": None,
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False

    def start(self, channels: Optional[List[str]] = None):
        """
        Start the validation worker.

        Args:
            channels: List of channels to process (processes all if None)
        """
        if channels is None:
            channels = [ch.value for ch in [
                QueueChannels.TUTORS,
                QueueChannels.SESSIONS,
                QueueChannels.FEEDBACK
            ]]

        logger.info(f"Starting validation worker")
        logger.info(f"Consumer group: {self.consumer_group}")
        logger.info(f"Channels: {channels}")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Poll interval: {self.poll_interval_ms}ms")

        self.running = True
        self.stats["start_time"] = datetime.now()

        # Create consumer groups for all channels
        for channel in channels:
            try:
                self.consumer.create_consumer_group(channel, start_id="0")
            except Exception as e:
                logger.error(f"Failed to create consumer group for {channel}: {e}")

        # Main processing loop
        try:
            while self.running:
                processed_any = False

                for channel in channels:
                    processed = self._process_channel(channel)
                    if processed > 0:
                        processed_any = True

                # Sleep if no messages were processed
                if not processed_any:
                    time.sleep(self.poll_interval_ms / 1000.0)

                # Log stats periodically
                if self.stats["batches_processed"] % 10 == 0:
                    self._log_stats()

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)

        finally:
            self._shutdown()

    def _process_channel(self, channel: str) -> int:
        """
        Process messages from a single channel.

        Args:
            channel: Channel name

        Returns:
            Number of messages processed
        """
        try:
            # Consume messages
            messages = self.consumer.consume(
                channel,
                count=self.batch_size,
                block_ms=None  # Non-blocking
            )

            if not messages:
                return 0

            logger.info(f"Processing {len(messages)} messages from {channel}")

            # Process batch
            for message in messages:
                self._process_message(channel, message)

            self.stats["batches_processed"] += 1

            return len(messages)

        except Exception as e:
            logger.error(f"Error processing channel {channel}: {e}", exc_info=True)
            return 0

    def _process_message(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Process a single message.

        Args:
            channel: Source channel
            message: Message data
        """
        message_id = message.get("_redis_id")
        data = message.get("data", {})

        try:
            # Get queue mapping
            if channel not in self.QUEUE_MAPPINGS:
                logger.error(f"Unknown channel: {channel}")
                self.consumer.acknowledge(channel, message_id)
                return

            mapping = self.QUEUE_MAPPINGS[channel]
            data_type = mapping["data_type"]
            enrichment_queue = mapping["enrichment_queue"]

            # Validate data
            validation_result = self.validation_engine.validate(data, data_type)

            self.stats["messages_processed"] += 1

            if validation_result.valid:
                # Publish to enrichment queue
                self._publish_valid_data(
                    enrichment_queue,
                    data,
                    message.get("metadata", {}),
                    validation_result
                )
                self.stats["messages_valid"] += 1

                logger.debug(
                    f"Valid {data_type}: {data.get(data_type + '_id', 'unknown')}"
                )

            else:
                # Send to dead letter queue
                self._publish_invalid_data(
                    channel,
                    data,
                    message.get("metadata", {}),
                    validation_result
                )
                self.stats["messages_invalid"] += 1

                logger.warning(
                    f"Invalid {data_type}: {validation_result.errors[0].message if validation_result.errors else 'unknown error'}"
                )

            # Acknowledge message
            self.consumer.acknowledge(channel, message_id)

        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}", exc_info=True)

            # Try to retry or send to DLQ
            try:
                self.consumer.retry_message(channel, message, max_retries=3)
                self.consumer.acknowledge(channel, message_id)
            except Exception as retry_error:
                logger.error(f"Failed to retry message: {retry_error}")

    def _publish_valid_data(
        self,
        enrichment_queue: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any],
        validation_result
    ) -> None:
        """
        Publish valid data to enrichment queue.

        Args:
            enrichment_queue: Enrichment queue name
            data: Validated data
            metadata: Message metadata
            validation_result: Validation result
        """
        # Enrich metadata
        enriched_metadata = metadata.copy()
        enriched_metadata["validated_at"] = datetime.now().isoformat()
        enriched_metadata["validation_warnings"] = len(validation_result.warnings)

        # Add validation metadata
        if validation_result.metadata:
            enriched_metadata["validation_metadata"] = validation_result.metadata

        # Publish to enrichment queue
        self.publisher.publish(
            enrichment_queue,
            data,
            metadata=enriched_metadata
        )

    def _publish_invalid_data(
        self,
        source_channel: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any],
        validation_result
    ) -> None:
        """
        Publish invalid data to dead letter queue.

        Args:
            source_channel: Source channel name
            data: Invalid data
            metadata: Message metadata
            validation_result: Validation result with errors
        """
        # Enrich metadata with validation errors
        dlq_metadata = metadata.copy()
        dlq_metadata["validation_failed_at"] = datetime.now().isoformat()
        dlq_metadata["source_channel"] = source_channel
        dlq_metadata["validation_errors"] = validation_result.to_dict()

        # Publish to dead letter queue
        self.publisher.publish(
            QueueChannels.DEAD_LETTER,
            data,
            metadata=dlq_metadata
        )

    def _log_stats(self) -> None:
        """Log current statistics."""
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
            rate = self.stats["messages_processed"] / uptime if uptime > 0 else 0

            logger.info(
                f"Stats: processed={self.stats['messages_processed']}, "
                f"valid={self.stats['messages_valid']}, "
                f"invalid={self.stats['messages_invalid']}, "
                f"batches={self.stats['batches_processed']}, "
                f"rate={rate:.2f} msg/s"
            )

            # Log validation engine stats
            validation_stats = self.validation_engine.get_stats()
            logger.info(f"Validation stats: {validation_stats}")

    def _shutdown(self) -> None:
        """Shutdown worker gracefully."""
        logger.info("Shutting down validation worker...")

        # Log final stats
        self._log_stats()

        logger.info("Validation worker stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        stats = self.stats.copy()
        stats["validation_engine"] = self.validation_engine.get_stats()
        return stats


def main():
    """Main entry point for validation worker."""
    logger.info("Starting TutorMax Validation Worker")

    # Create worker
    worker = ValidationWorker(
        batch_size=redis_config.worker_batch_size,
        poll_interval_ms=redis_config.worker_poll_interval_ms
    )

    # Start processing
    worker.start()


if __name__ == "__main__":
    main()
