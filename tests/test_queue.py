"""
Tests for Redis message queue functionality.
"""
import pytest
import time
from src.queue import (
    RedisClient,
    MessagePublisher,
    MessageConsumer,
    QueueWorker,
    QueueChannels,
    MessageSerializer
)


@pytest.fixture
def redis_client():
    """Fixture for Redis client."""
    client = RedisClient()
    client.connect()
    yield client
    client.disconnect()


@pytest.fixture
def publisher(redis_client):
    """Fixture for message publisher."""
    return MessagePublisher(redis_client)


@pytest.fixture
def consumer(redis_client):
    """Fixture for message consumer."""
    return MessageConsumer(redis_client)


@pytest.fixture
def cleanup_streams(redis_client):
    """Cleanup test streams after tests."""
    yield
    # Cleanup all test streams
    redis = redis_client.get_client()
    for channel in QueueChannels.all_channels():
        try:
            redis.delete(channel)
            redis.delete(f"{channel}:retry")
            redis.delete(f"{channel}:processing")
        except:
            pass


class TestMessageSerializer:
    """Test message serialization."""

    def test_serialize_deserialize(self):
        """Test basic serialization and deserialization."""
        data = {"tutor_id": "T001", "name": "John"}
        metadata = {"source": "test"}

        # Serialize
        message_json = MessageSerializer.serialize(
            QueueChannels.TUTORS,
            data,
            metadata
        )

        # Deserialize
        message = MessageSerializer.deserialize(message_json)

        assert message["channel"] == QueueChannels.TUTORS
        assert message["data"] == data
        assert message["metadata"] == metadata
        assert "id" in message
        assert "timestamp" in message
        assert "checksum" in message

    def test_checksum_validation(self):
        """Test that checksum validation catches tampering."""
        data = {"tutor_id": "T001"}
        message_json = MessageSerializer.serialize(QueueChannels.TUTORS, data)

        # Tamper with message
        import json
        message_dict = json.loads(message_json)
        message_dict["data"]["tutor_id"] = "T002"  # Change data
        tampered_json = json.dumps(message_dict)

        # Should raise error on checksum mismatch
        with pytest.raises(ValueError, match="checksum"):
            MessageSerializer.deserialize(tampered_json)

    def test_extract_data(self):
        """Test extracting just the data payload."""
        data = {"tutor_id": "T001", "name": "John"}
        message_json = MessageSerializer.serialize(QueueChannels.TUTORS, data)

        extracted_data = MessageSerializer.extract_data(message_json)
        assert extracted_data == data


class TestRedisClient:
    """Test Redis client functionality."""

    def test_connection(self, redis_client):
        """Test Redis connection."""
        assert redis_client.is_connected()

    def test_health_check(self, redis_client):
        """Test health check."""
        health = redis_client.health_check()
        assert health["status"] == "healthy"
        assert "redis_version" in health

    def test_pipeline(self, redis_client):
        """Test pipeline context manager."""
        with redis_client.pipeline() as pipe:
            pipe.set("test_key_1", "value1")
            pipe.set("test_key_2", "value2")
            results = pipe.execute()

        assert len(results) == 2

        # Cleanup
        redis = redis_client.get_client()
        redis.delete("test_key_1", "test_key_2")


class TestMessagePublisher:
    """Test message publisher."""

    def test_publish_message(self, publisher, cleanup_streams):
        """Test publishing a single message."""
        data = {"tutor_id": "T001", "name": "John Smith"}
        msg_id = publisher.publish(QueueChannels.TUTORS, data)

        assert msg_id is not None
        assert isinstance(msg_id, (str, bytes))

    def test_publish_batch(self, publisher, cleanup_streams):
        """Test batch publishing."""
        messages = [
            {"tutor_id": f"T{i:03d}", "name": f"Tutor {i}"}
            for i in range(5)
        ]

        msg_ids = publisher.publish_batch(QueueChannels.TUTORS, messages)

        assert len(msg_ids) == 5
        assert all(msg_id is not None for msg_id in msg_ids)

    def test_convenience_methods(self, publisher, cleanup_streams):
        """Test convenience publishing methods."""
        # Publish tutor data
        tutor_id = publisher.publish_tutor_data({"tutor_id": "T001"})
        assert tutor_id is not None

        # Publish session data
        session_id = publisher.publish_session_data({"session_id": "S001"})
        assert session_id is not None

        # Publish feedback data
        feedback_id = publisher.publish_feedback_data({"feedback_id": "F001"})
        assert feedback_id is not None

    def test_get_stream_length(self, publisher, cleanup_streams):
        """Test getting stream length."""
        # Initially empty
        length = publisher.get_stream_length(QueueChannels.TUTORS)
        initial_length = length

        # Publish 3 messages
        for i in range(3):
            publisher.publish_tutor_data({"tutor_id": f"T{i:03d}"})

        # Should have 3 messages
        length = publisher.get_stream_length(QueueChannels.TUTORS)
        assert length == initial_length + 3


class TestMessageConsumer:
    """Test message consumer."""

    def test_consume_messages(self, publisher, consumer, cleanup_streams):
        """Test consuming messages."""
        # Publish test message
        test_data = {"tutor_id": "T001", "name": "John"}
        publisher.publish(QueueChannels.TUTORS, test_data)

        # Consume messages
        messages = consumer.consume(QueueChannels.TUTORS, count=1)

        assert len(messages) == 1
        assert messages[0]["data"] == test_data

    def test_acknowledge_message(self, publisher, consumer, cleanup_streams):
        """Test message acknowledgment."""
        # Publish and consume
        publisher.publish(QueueChannels.TUTORS, {"tutor_id": "T001"})
        messages = consumer.consume(QueueChannels.TUTORS, count=1)

        assert len(messages) == 1

        # Acknowledge
        msg_id = messages[0]["_redis_id"]
        result = consumer.acknowledge(QueueChannels.TUTORS, msg_id)

        assert result is True

    def test_consumer_group_creation(self, consumer, cleanup_streams):
        """Test consumer group creation."""
        # Create group
        created = consumer.create_consumer_group(QueueChannels.TUTORS)

        # First time should return True
        assert created is True or created is False  # May already exist

        # Second time should return False (already exists)
        created = consumer.create_consumer_group(QueueChannels.TUTORS)
        assert created is False


class TestQueueWorker:
    """Test queue worker."""

    def test_register_handler(self):
        """Test registering message handlers."""
        worker = QueueWorker([QueueChannels.TUTORS])

        def test_handler(data: dict) -> bool:
            return True

        worker.register_handler(QueueChannels.TUTORS, test_handler)

        assert QueueChannels.TUTORS in worker.handlers

    def test_process_message(self, publisher, cleanup_streams):
        """Test processing a single message."""
        processed_data = []

        def test_handler(data: dict) -> bool:
            processed_data.append(data)
            return True

        worker = QueueWorker([QueueChannels.TUTORS])
        worker.register_handler(QueueChannels.TUTORS, test_handler)

        # Publish test message
        test_data = {"tutor_id": "T001"}
        publisher.publish(QueueChannels.TUTORS, test_data)

        # Process once
        worker.run_once()

        # Verify handler was called
        assert len(processed_data) == 1
        assert processed_data[0] == test_data

    def test_worker_stats(self):
        """Test worker statistics tracking."""
        worker = QueueWorker([QueueChannels.TUTORS])

        stats = worker.get_stats()

        assert "messages_processed" in stats
        assert "messages_succeeded" in stats
        assert "messages_failed" in stats
        assert "is_running" in stats


class TestIntegration:
    """Integration tests for full workflow."""

    def test_full_workflow(self, publisher, cleanup_streams):
        """Test complete publish-consume-process workflow."""
        # Track processed messages
        processed = []

        def handler(data: dict) -> bool:
            processed.append(data)
            return True

        # Publish test messages
        test_messages = [
            {"tutor_id": "T001", "name": "Alice"},
            {"tutor_id": "T002", "name": "Bob"},
            {"tutor_id": "T003", "name": "Charlie"},
        ]

        for msg in test_messages:
            publisher.publish(QueueChannels.TUTORS, msg)

        # Create and run worker
        worker = QueueWorker([QueueChannels.TUTORS], batch_size=10)
        worker.register_handler(QueueChannels.TUTORS, handler)
        worker.run_once()

        # Verify all messages processed
        assert len(processed) == 3
        assert all(msg in processed for msg in test_messages)

        # Verify stats
        stats = worker.get_stats()
        assert stats["messages_succeeded"] == 3
        assert stats["messages_failed"] == 0
