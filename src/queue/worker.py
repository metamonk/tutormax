"""
Queue worker framework for processing messages.
"""
import logging
import signal
import sys
import time
from typing import Callable, Dict, Any, Optional, List
import traceback

from .client import RedisClient, get_redis_client
from .consumer import MessageConsumer
from .channels import QueueChannels
from .config import redis_config

logger = logging.getLogger(__name__)


class QueueWorker:
    """
    Worker framework for processing queued messages.

    Features:
    - Automatic message consumption and acknowledgment
    - Graceful shutdown handling
    - Error handling and retry logic
    - Processing callbacks for different channels
    - Stats tracking
    """

    def __init__(
        self,
        channels: List[str],
        redis_client: Optional[RedisClient] = None,
        consumer_group: str = "tutormax-workers",
        batch_size: int = None
    ):
        """
        Initialize queue worker.

        Args:
            channels: List of channels to process
            redis_client: Redis client (defaults to global instance)
            consumer_group: Consumer group name
            batch_size: Number of messages to process per batch
        """
        self.channels = channels
        self.redis_client = redis_client or get_redis_client()
        self.consumer = MessageConsumer(self.redis_client, consumer_group)
        self.batch_size = batch_size or redis_config.worker_batch_size

        # Processing callbacks
        self.handlers: Dict[str, Callable] = {}

        # Worker state
        self.is_running = False
        self.should_stop = False

        # Stats
        self.stats = {
            "messages_processed": 0,
            "messages_succeeded": 0,
            "messages_failed": 0,
            "batches_processed": 0,
            "errors": 0,
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def register_handler(
        self,
        channel: str,
        handler: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Register a message handler for a specific channel.

        Args:
            channel: Queue channel name
            handler: Callback function that takes message data and returns success bool

        Example:
            def process_tutor(data: dict) -> bool:
                # Process tutor data
                return True

            worker.register_handler(QueueChannels.TUTORS, process_tutor)
        """
        self.handlers[channel] = handler
        logger.info(f"Registered handler for channel: {channel}")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True

    def process_message(
        self,
        message: Dict[str, Any],
        channel: str
    ) -> bool:
        """
        Process a single message using registered handler.

        Args:
            message: Message dictionary with data
            channel: Channel the message came from

        Returns:
            True if processing succeeded, False otherwise
        """
        handler = self.handlers.get(channel)

        if not handler:
            logger.warning(f"No handler registered for channel: {channel}")
            return False

        try:
            # Extract data payload
            data = message.get("data", {})
            message_id = message.get("id", "unknown")

            logger.debug(f"Processing message {message_id} from {channel}")

            # Call handler
            success = handler(data)

            if success:
                self.stats["messages_succeeded"] += 1
                logger.debug(f"Successfully processed message {message_id}")
            else:
                self.stats["messages_failed"] += 1
                logger.warning(f"Handler returned False for message {message_id}")

            return success

        except Exception as e:
            self.stats["messages_failed"] += 1
            self.stats["errors"] += 1
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())
            return False

    def process_batch(self, channel: str) -> int:
        """
        Process a batch of messages from a channel.

        Args:
            channel: Channel to process

        Returns:
            Number of messages processed
        """
        try:
            # Consume messages
            messages = self.consumer.consume(
                channel,
                count=self.batch_size,
                block_ms=redis_config.worker_poll_interval_ms
            )

            if not messages:
                return 0

            processed = 0

            for message in messages:
                # Process message
                success = self.process_message(message, channel)

                # Acknowledge or retry
                message_id = message.get("_redis_id")

                if success:
                    self.consumer.acknowledge(channel, message_id)
                    processed += 1
                else:
                    # Retry failed message
                    self.consumer.retry_message(
                        channel,
                        message,
                        max_retries=redis_config.max_retries
                    )
                    # Still acknowledge to remove from pending
                    self.consumer.acknowledge(channel, message_id)

            self.stats["messages_processed"] += processed
            return processed

        except Exception as e:
            logger.error(f"Error processing batch from {channel}: {e}")
            self.stats["errors"] += 1
            return 0

    def run(self) -> None:
        """
        Start the worker and process messages continuously.

        Runs until interrupted by signal or should_stop is set.
        """
        logger.info(f"Starting worker for channels: {self.channels}")
        logger.info(f"Batch size: {self.batch_size}")

        # Ensure consumer groups exist
        for channel in self.channels:
            self.consumer.create_consumer_group(channel)

        self.is_running = True
        self.should_stop = False

        try:
            while not self.should_stop:
                batch_total = 0

                # Process each channel
                for channel in self.channels:
                    processed = self.process_batch(channel)
                    batch_total += processed

                if batch_total > 0:
                    self.stats["batches_processed"] += 1
                    logger.info(f"Processed batch: {batch_total} messages")

                # Short sleep to prevent tight loop if no messages
                if batch_total == 0:
                    time.sleep(redis_config.worker_poll_interval_ms / 1000)

        except KeyboardInterrupt:
            logger.info("Worker interrupted by user")

        except Exception as e:
            logger.error(f"Worker error: {e}")
            logger.error(traceback.format_exc())

        finally:
            self.is_running = False
            self._cleanup()

    def run_once(self) -> int:
        """
        Process one batch from each channel and return.

        Useful for testing or cron-based processing.

        Returns:
            Total number of messages processed
        """
        total_processed = 0

        # Ensure consumer groups exist
        for channel in self.channels:
            self.consumer.create_consumer_group(channel)

        # Process each channel once
        for channel in self.channels:
            processed = self.process_batch(channel)
            total_processed += processed

        return total_processed

    def _cleanup(self) -> None:
        """Cleanup worker resources."""
        logger.info("Cleaning up worker resources...")
        logger.info(f"Final stats: {self.get_stats()}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics.

        Returns:
            Dictionary of worker stats
        """
        return {
            **self.stats,
            "consumer_stats": self.consumer.get_stats(),
            "is_running": self.is_running,
        }

    def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info("Stopping worker...")
        self.should_stop = True
