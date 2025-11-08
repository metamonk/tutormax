"""
Integration tests for validation module with Redis queue system.

These tests verify the complete flow from Redis consumer to validation
to enrichment queue publishing.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.pipeline.validation.validation_worker import ValidationWorker
from src.queue.client import RedisClient


class TestValidationWorkerIntegration:
    """Integration tests for validation worker."""

    def test_worker_initialization(self):
        """Test that worker initializes correctly."""
        worker = ValidationWorker()

        assert worker is not None
        assert worker.validation_engine is not None
        assert worker.consumer is not None
        assert worker.publisher is not None

    def test_queue_mappings(self):
        """Test that queue mappings are correct."""
        mappings = ValidationWorker.QUEUE_MAPPINGS

        assert "tutormax:tutors" in mappings
        assert "tutormax:sessions" in mappings
        assert "tutormax:feedback" in mappings

        # Check tutor mapping
        tutor_mapping = mappings["tutormax:tutors"]
        assert tutor_mapping["data_type"] == "tutor"
        assert tutor_mapping["enrichment_queue"] == "tutormax:tutors:enrichment"

        # Check session mapping
        session_mapping = mappings["tutormax:sessions"]
        assert session_mapping["data_type"] == "session"
        assert session_mapping["enrichment_queue"] == "tutormax:sessions:enrichment"

        # Check feedback mapping
        feedback_mapping = mappings["tutormax:feedback"]
        assert feedback_mapping["data_type"] == "feedback"
        assert feedback_mapping["enrichment_queue"] == "tutormax:feedback:enrichment"

    @patch('src.pipeline.validation.validation_worker.MessageConsumer')
    @patch('src.pipeline.validation.validation_worker.MessagePublisher')
    def test_valid_message_flow(self, mock_publisher, mock_consumer):
        """Test that valid messages flow to enrichment queue."""
        # Setup
        worker = ValidationWorker()

        valid_tutor = {
            "tutor_id": "tutor_00001",
            "name": "Test",
            "email": "test@example.com",
            "age": 28,
            "location": "NY",
            "education_level": "Master's",
            "subjects": ["Mathematics"],
            "subject_type": "STEM",
            "onboarding_date": "2024-01-15T10:00:00",
            "tenure_days": 120,
            "behavioral_archetype": "high_performer",
            "baseline_sessions_per_week": 20,
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-05-14T10:00:00"
        }

        message = {
            "_redis_id": "test-id",
            "data": valid_tutor,
            "metadata": {}
        }

        # Mock consumer to return our message
        mock_consumer_instance = Mock()
        mock_consumer_instance.consume.return_value = [message]
        mock_consumer_instance.acknowledge.return_value = True
        worker.consumer = mock_consumer_instance

        # Mock publisher
        mock_publisher_instance = Mock()
        worker.publisher = mock_publisher_instance

        # Process message
        worker._process_channel("tutormax:tutors")

        # Verify message was published to enrichment queue
        mock_publisher_instance.publish.assert_called_once()
        call_args = mock_publisher_instance.publish.call_args
        assert call_args[0][0] == "tutormax:tutors:enrichment"
        assert call_args[0][1] == valid_tutor

        # Verify message was acknowledged
        mock_consumer_instance.acknowledge.assert_called_once_with(
            "tutormax:tutors",
            "test-id"
        )

    @patch('src.pipeline.validation.validation_worker.MessageConsumer')
    @patch('src.pipeline.validation.validation_worker.MessagePublisher')
    def test_invalid_message_flow(self, mock_publisher, mock_consumer):
        """Test that invalid messages flow to dead letter queue."""
        # Setup
        worker = ValidationWorker()

        invalid_tutor = {
            "tutor_id": "tutor_00001",
            "name": "Test",
            "email": "invalid-email",  # Invalid email
            "age": 100,  # Invalid age
            "location": "NY",
            "education_level": "Master's",
            "subjects": ["Mathematics"],
            "subject_type": "STEM",
            "onboarding_date": "2024-01-15T10:00:00",
            "tenure_days": 120,
            "behavioral_archetype": "high_performer",
            "baseline_sessions_per_week": 20,
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-05-14T10:00:00"
        }

        message = {
            "_redis_id": "test-id",
            "data": invalid_tutor,
            "metadata": {}
        }

        # Mock consumer
        mock_consumer_instance = Mock()
        mock_consumer_instance.consume.return_value = [message]
        mock_consumer_instance.acknowledge.return_value = True
        worker.consumer = mock_consumer_instance

        # Mock publisher
        mock_publisher_instance = Mock()
        worker.publisher = mock_publisher_instance

        # Process message
        worker._process_channel("tutormax:tutors")

        # Verify message was published to dead letter queue
        mock_publisher_instance.publish.assert_called_once()
        call_args = mock_publisher_instance.publish.call_args
        assert call_args[0][0] == "tutormax:dead_letter"
        assert call_args[0][1] == invalid_tutor

        # Verify metadata contains validation errors
        metadata = call_args[1]["metadata"]
        assert "validation_errors" in metadata
        assert metadata["validation_errors"]["valid"] is False
        assert len(metadata["validation_errors"]["errors"]) > 0

    def test_worker_statistics(self):
        """Test that worker tracks statistics correctly."""
        worker = ValidationWorker()

        # Initial stats
        stats = worker.get_stats()
        assert stats["messages_processed"] == 0
        assert stats["messages_valid"] == 0
        assert stats["messages_invalid"] == 0

    def test_validation_engine_stats(self):
        """Test that validation engine statistics are accessible."""
        worker = ValidationWorker()

        stats = worker.get_stats()
        assert "validation_engine" in stats
        assert "total_validated" in stats["validation_engine"]
        assert "by_type" in stats["validation_engine"]


class TestEndToEndValidation:
    """End-to-end validation tests."""

    def test_tutor_validation_end_to_end(self):
        """Test complete tutor validation flow."""
        from src.pipeline.validation import ValidationEngine

        engine = ValidationEngine()

        # Valid tutor
        valid_tutor = {
            "tutor_id": "tutor_00001",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "age": 28,
            "location": "New York",
            "education_level": "Master's Degree",
            "subjects": ["Mathematics", "Physics"],
            "subject_type": "STEM",
            "onboarding_date": "2024-01-15T10:00:00",
            "tenure_days": 120,
            "behavioral_archetype": "high_performer",
            "baseline_sessions_per_week": 20,
            "status": "active",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-05-14T10:00:00"
        }

        result = engine.validate_tutor(valid_tutor)
        assert result.valid is True

        # Invalid tutor
        invalid_tutor = valid_tutor.copy()
        invalid_tutor["age"] = 100

        result = engine.validate_tutor(invalid_tutor)
        assert result.valid is False

    def test_session_validation_end_to_end(self):
        """Test complete session validation flow."""
        from src.pipeline.validation import ValidationEngine

        engine = ValidationEngine()

        # Valid session
        valid_session = {
            "session_id": "session-001",
            "tutor_id": "tutor_00001",
            "student_id": "student_001",
            "session_number": 1,
            "is_first_session": True,
            "scheduled_start": "2024-05-14T15:00:00",
            "actual_start": "2024-05-14T15:00:00",
            "duration_minutes": 60,
            "subject": "Mathematics",
            "session_type": "1-on-1",
            "tutor_initiated_reschedule": False,
            "no_show": False,
            "late_start_minutes": 0,
            "engagement_score": 0.9,
            "learning_objectives_met": True,
            "technical_issues": False,
            "created_at": "2024-05-14T15:00:00",
            "updated_at": "2024-05-14T16:00:00"
        }

        result = engine.validate_session(valid_session)
        assert result.valid is True

    def test_feedback_validation_end_to_end(self):
        """Test complete feedback validation flow."""
        from src.pipeline.validation import ValidationEngine

        engine = ValidationEngine()

        # Valid feedback
        valid_feedback = {
            "feedback_id": "feedback-001",
            "session_id": "session-001",
            "student_id": "student_001",
            "tutor_id": "tutor_00001",
            "overall_rating": 5,
            "is_first_session": True,
            "subject_knowledge_rating": 5,
            "communication_rating": 5,
            "patience_rating": 5,
            "engagement_rating": 5,
            "helpfulness_rating": 5,
            "free_text_feedback": "Excellent!",
            "submitted_at": "2024-05-14T18:00:00",
            "created_at": "2024-05-14T18:00:00",
            "would_recommend": True,
            "improvement_areas": []
        }

        result = engine.validate_feedback(valid_feedback)
        assert result.valid is True

    def test_mixed_validation_batch(self):
        """Test validating a batch of mixed data types."""
        from src.pipeline.validation import ValidationEngine

        engine = ValidationEngine()

        # Create various valid data
        tutor = {
            "tutor_id": "tutor_001",
            "name": "Test",
            "email": "test@example.com",
            "age": 30,
            "location": "NYC",
            "education_level": "PhD",
            "subjects": ["Physics"],
            "subject_type": "STEM",
            "onboarding_date": "2024-01-01T00:00:00",
            "tenure_days": 100,
            "behavioral_archetype": "steady",
            "baseline_sessions_per_week": 15,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }

        session = {
            "session_id": "s1",
            "tutor_id": "tutor_001",
            "student_id": "student_001",
            "session_number": 1,
            "is_first_session": True,
            "scheduled_start": "2024-05-14T15:00:00",
            "actual_start": "2024-05-14T15:00:00",
            "duration_minutes": 60,
            "subject": "Physics",
            "session_type": "1-on-1",
            "tutor_initiated_reschedule": False,
            "no_show": False,
            "late_start_minutes": 0,
            "engagement_score": 0.95,
            "learning_objectives_met": True,
            "technical_issues": False,
            "created_at": "2024-05-14T15:00:00",
            "updated_at": "2024-05-14T16:00:00"
        }

        feedback = {
            "feedback_id": "f1",
            "session_id": "s1",
            "student_id": "student_001",
            "tutor_id": "tutor_001",
            "overall_rating": 5,
            "is_first_session": True,
            "subject_knowledge_rating": 5,
            "communication_rating": 5,
            "patience_rating": 5,
            "engagement_rating": 5,
            "helpfulness_rating": 5,
            "free_text_feedback": "Great!",
            "submitted_at": "2024-05-14T18:00:00",
            "created_at": "2024-05-14T18:00:00",
            "would_recommend": True,
            "improvement_areas": []
        }

        # Validate all
        tutor_result = engine.validate_tutor(tutor)
        session_result = engine.validate_session(session)
        feedback_result = engine.validate_feedback(feedback)

        assert tutor_result.valid is True
        assert session_result.valid is True
        assert feedback_result.valid is True

        # Check statistics
        stats = engine.get_stats()
        assert stats["total_validated"] == 3
        assert stats["valid_count"] == 3
        assert stats["invalid_count"] == 0
