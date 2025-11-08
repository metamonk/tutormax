"""
Enrichment worker for processing validated messages from Redis.

Consumes validated messages, enriches them with derived fields,
and persists enriched data to PostgreSQL database.
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
from .enrichment_engine import EnrichmentEngine
from .db_persister import DatabasePersister

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnrichmentWorker:
    """
    Worker that enriches validated data and persists to database.

    Processing flow:
    1. Consume from enrichment queues
    2. Enrich data with derived fields
    3. Persist to PostgreSQL database
    4. Handle failures with retry/DLQ
    5. Acknowledge processed messages
    """

    # Queue mappings for enrichment queues
    QUEUE_MAPPINGS = {
        "tutormax:tutors:enrichment": {
            "data_type": "tutor",
            "id_field": "tutor_id"
        },
        "tutormax:sessions:enrichment": {
            "data_type": "session",
            "id_field": "session_id"
        },
        "tutormax:feedback:enrichment": {
            "data_type": "feedback",
            "id_field": "feedback_id"
        },
    }

    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        consumer_group: str = "enrichment-workers",
        batch_size: int = 10,
        poll_interval_ms: int = 1000
    ):
        """
        Initialize enrichment worker.

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
        self.enrichment_engine = EnrichmentEngine()
        self.db_persister = DatabasePersister()

        # Worker state
        self.running = False
        self.stats = {
            "messages_processed": 0,
            "messages_enriched": 0,
            "messages_persisted": 0,
            "messages_failed": 0,
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

    def start(self, queues: Optional[List[str]] = None):
        """
        Start the enrichment worker.

        Args:
            queues: List of enrichment queues to process (processes all if None)
        """
        if queues is None:
            queues = list(self.QUEUE_MAPPINGS.keys())

        logger.info(f"Starting enrichment worker")
        logger.info(f"Consumer group: {self.consumer_group}")
        logger.info(f"Queues: {queues}")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Poll interval: {self.poll_interval_ms}ms")

        self.running = True
        self.stats["start_time"] = datetime.now()

        # Create consumer groups for all queues
        for queue in queues:
            try:
                self.consumer.create_consumer_group(queue, start_id="0")
            except Exception as e:
                logger.warning(f"Consumer group may already exist for {queue}: {e}")

        # Main processing loop
        try:
            while self.running:
                processed_any = False

                for queue in queues:
                    processed = self._process_queue(queue)
                    if processed > 0:
                        processed_any = True

                # Sleep if no messages were processed
                if not processed_any:
                    time.sleep(self.poll_interval_ms / 1000.0)

                # Log stats periodically
                if self.stats["batches_processed"] % 10 == 0 and self.stats["batches_processed"] > 0:
                    self._log_stats()

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)

        finally:
            self._shutdown()

    def _process_queue(self, queue: str) -> int:
        """
        Process messages from a single enrichment queue.

        Args:
            queue: Queue name

        Returns:
            Number of messages processed
        """
        try:
            # Consume messages
            messages = self.consumer.consume(
                queue,
                count=self.batch_size,
                block_ms=None  # Non-blocking
            )

            if not messages:
                return 0

            logger.info(f"Processing {len(messages)} messages from {queue}")

            # Process batch
            batch_items = []
            message_ids = []

            for message in messages:
                result = self._process_message(queue, message)
                if result:
                    batch_items.append(result)
                    message_ids.append(message.get("_redis_id"))

            # Persist batch to database
            if batch_items:
                mapping = self.QUEUE_MAPPINGS.get(queue, {})
                data_type = mapping.get("data_type")

                import asyncio
                persistence_results = asyncio.run(
                    self.db_persister.persist_batch(batch_items, data_type)
                )

                self.stats["messages_persisted"] += persistence_results["success"]
                self.stats["messages_failed"] += persistence_results["failed"]

            # Acknowledge all messages
            for message_id in message_ids:
                try:
                    self.consumer.acknowledge(queue, message_id)
                except Exception as e:
                    logger.error(f"Failed to acknowledge message {message_id}: {e}")

            self.stats["batches_processed"] += 1

            return len(messages)

        except Exception as e:
            logger.error(f"Error processing queue {queue}: {e}", exc_info=True)
            return 0

    def _process_message(
        self, queue: str, message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single message.

        Args:
            queue: Source queue
            message: Message data

        Returns:
            Enriched data ready for persistence, or None if failed
        """
        message_id = message.get("_redis_id")
        data = message.get("data", {})

        try:
            # Get queue mapping
            if queue not in self.QUEUE_MAPPINGS:
                logger.error(f"Unknown queue: {queue}")
                return None

            mapping = self.QUEUE_MAPPINGS[queue]
            data_type = mapping["data_type"]
            id_field = mapping["id_field"]

            # Enrich data
            enrichment_result = self.enrichment_engine.enrich(data, data_type)

            self.stats["messages_processed"] += 1

            if enrichment_result.success:
                self.stats["messages_enriched"] += 1

                logger.debug(
                    f"Enriched {data_type}: {data.get(id_field, 'unknown')} "
                    f"with {len(enrichment_result.derived_fields)} derived fields"
                )

                # Return enriched data for batch persistence
                return self._prepare_for_persistence(
                    enrichment_result.data, data_type
                )

            else:
                # Send to dead letter queue
                self._publish_failed_enrichment(
                    queue,
                    data,
                    message.get("metadata", {}),
                    enrichment_result.errors
                )

                logger.warning(
                    f"Enrichment failed for {data_type}: {enrichment_result.errors}"
                )

                return None

        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}", exc_info=True)
            self.stats["messages_failed"] += 1
            return None

    def _prepare_for_persistence(
        self, data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """
        Prepare enriched data for database persistence.

        Filters out fields that don't belong in the database model.

        Args:
            data: Enriched data
            data_type: Type of data

        Returns:
            Data ready for database insertion
        """
        # Define allowed fields for each model
        ALLOWED_FIELDS = {
            "tutor": {
                "tutor_id", "name", "email", "onboarding_date", "status",
                "subjects", "education_level", "location",
                "baseline_sessions_per_week", "behavioral_archetype",
                "created_at", "updated_at"
            },
            "session": {
                "session_id", "tutor_id", "student_id", "session_number",
                "scheduled_start", "actual_start", "duration_minutes",
                "subject", "session_type", "tutor_initiated_reschedule",
                "no_show", "late_start_minutes", "engagement_score",
                "learning_objectives_met", "technical_issues",
                "created_at", "updated_at"
            },
            "feedback": {
                "feedback_id", "session_id", "student_id", "tutor_id",
                "overall_rating", "is_first_session",
                "subject_knowledge_rating", "communication_rating",
                "patience_rating", "engagement_rating", "helpfulness_rating",
                "would_recommend", "improvement_areas", "free_text_feedback",
                "submitted_at", "created_at"
            }
        }

        allowed = ALLOWED_FIELDS.get(data_type, set())
        return {k: v for k, v in data.items() if k in allowed}

    def _publish_failed_enrichment(
        self,
        source_queue: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any],
        errors: List[str]
    ) -> None:
        """
        Publish failed enrichment to dead letter queue.

        Args:
            source_queue: Source queue name
            data: Original data
            metadata: Message metadata
            errors: List of enrichment errors
        """
        # Enrich metadata with enrichment errors
        dlq_metadata = metadata.copy()
        dlq_metadata["enrichment_failed_at"] = datetime.now().isoformat()
        dlq_metadata["source_queue"] = source_queue
        dlq_metadata["enrichment_errors"] = errors

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
                f"enriched={self.stats['messages_enriched']}, "
                f"persisted={self.stats['messages_persisted']}, "
                f"failed={self.stats['messages_failed']}, "
                f"batches={self.stats['batches_processed']}, "
                f"rate={rate:.2f} msg/s"
            )

            # Log enrichment engine stats
            enrichment_stats = self.enrichment_engine.get_stats()
            logger.info(f"Enrichment stats: {enrichment_stats}")

            # Log database persister stats
            db_stats = self.db_persister.get_stats()
            logger.info(f"Database stats: {db_stats}")

    def _shutdown(self) -> None:
        """Shutdown worker gracefully."""
        logger.info("Shutting down enrichment worker...")

        # Log final stats
        self._log_stats()

        logger.info("Enrichment worker stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        stats = self.stats.copy()
        stats["enrichment_engine"] = self.enrichment_engine.get_stats()
        stats["database_persister"] = self.db_persister.get_stats()
        return stats


def main():
    """Main entry point for enrichment worker."""
    logger.info("Starting TutorMax Enrichment Worker")

    # Create worker
    worker = EnrichmentWorker(
        batch_size=redis_config.worker_batch_size,
        poll_interval_ms=redis_config.worker_poll_interval_ms
    )

    # Start processing
    worker.start()


if __name__ == "__main__":
    main()
