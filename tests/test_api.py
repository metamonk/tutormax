"""
Tests for the FastAPI data ingestion endpoints.

Tests basic functionality of tutor, session, and feedback endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.api.main import app
from src.api.redis_service import redis_service


# Test client
client = TestClient(app)


# Mock Redis for tests
@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis service for all tests."""
    with patch.object(redis_service, 'is_connected', return_value=True):
        with patch.object(redis_service, 'queue_tutor', return_value=True):
            with patch.object(redis_service, 'queue_session', return_value=True):
                with patch.object(redis_service, 'queue_feedback', return_value=True):
                    with patch.object(redis_service, 'get_queue_stats', return_value={
                        'tutors': 10,
                        'sessions': 50,
                        'feedbacks': 40,
                    }):
                        yield


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test health check returns correct status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "redis_connected" in data
        assert "version" in data


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert "endpoints" in data


class TestTutorEndpoints:
    """Test tutor ingestion endpoints."""

    def test_ingest_tutor_valid(self):
        """Test ingesting a valid tutor profile."""
        tutor_data = {
            "tutor_id": "tutor_00001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 28,
            "location": "New York",
            "education_level": "Master's Degree",
            "subjects": ["Mathematics", "Algebra"],
            "subject_type": "STEM",
            "onboarding_date": "2024-01-15T10:00:00",
            "tenure_days": 120,
            "behavioral_archetype": "high_performer",
            "baseline_sessions_per_week": 20,
            "status": "active",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-05-14T10:00:00",
        }

        response = client.post("/api/tutors", json=tutor_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["id"] == "tutor_00001"
        assert data["queued"] is True

    def test_ingest_tutor_invalid_email(self):
        """Test ingesting tutor with invalid email."""
        tutor_data = {
            "tutor_id": "tutor_00001",
            "name": "John Doe",
            "email": "invalid-email",  # Invalid
            "age": 28,
            "location": "New York",
            "education_level": "Master's Degree",
            "subjects": ["Mathematics"],
            "subject_type": "STEM",
            "onboarding_date": "2024-01-15T10:00:00",
            "tenure_days": 120,
            "behavioral_archetype": "high_performer",
            "baseline_sessions_per_week": 20,
            "status": "active",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-05-14T10:00:00",
        }

        response = client.post("/api/tutors", json=tutor_data)
        assert response.status_code == 422  # Validation error

    def test_ingest_tutor_invalid_archetype(self):
        """Test ingesting tutor with invalid archetype."""
        tutor_data = {
            "tutor_id": "tutor_00001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 28,
            "location": "New York",
            "education_level": "Master's Degree",
            "subjects": ["Mathematics"],
            "subject_type": "STEM",
            "onboarding_date": "2024-01-15T10:00:00",
            "tenure_days": 120,
            "behavioral_archetype": "invalid_archetype",  # Invalid
            "baseline_sessions_per_week": 20,
            "status": "active",
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-05-14T10:00:00",
        }

        response = client.post("/api/tutors", json=tutor_data)
        assert response.status_code == 422  # Validation error


class TestSessionEndpoints:
    """Test session ingestion endpoints."""

    def test_ingest_session_valid(self):
        """Test ingesting a valid session."""
        session_data = {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "tutor_id": "tutor_00001",
            "student_id": "student_00042",
            "session_number": 3,
            "is_first_session": False,
            "scheduled_start": "2024-05-14T15:00:00",
            "actual_start": "2024-05-14T15:02:00",
            "duration_minutes": 60,
            "subject": "Algebra",
            "session_type": "1-on-1",
            "tutor_initiated_reschedule": False,
            "no_show": False,
            "late_start_minutes": 2,
            "engagement_score": 0.92,
            "learning_objectives_met": True,
            "technical_issues": False,
            "created_at": "2024-05-14T15:00:00",
            "updated_at": "2024-05-14T16:05:00",
        }

        response = client.post("/api/sessions", json=session_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["queued"] is True

    def test_ingest_session_invalid_engagement_score(self):
        """Test ingesting session with invalid engagement score."""
        session_data = {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "tutor_id": "tutor_00001",
            "student_id": "student_00042",
            "session_number": 3,
            "is_first_session": False,
            "scheduled_start": "2024-05-14T15:00:00",
            "actual_start": "2024-05-14T15:02:00",
            "duration_minutes": 60,
            "subject": "Algebra",
            "session_type": "1-on-1",
            "tutor_initiated_reschedule": False,
            "no_show": False,
            "late_start_minutes": 2,
            "engagement_score": 1.5,  # Invalid (>1.0)
            "learning_objectives_met": True,
            "technical_issues": False,
            "created_at": "2024-05-14T15:00:00",
            "updated_at": "2024-05-14T16:05:00",
        }

        response = client.post("/api/sessions", json=session_data)
        assert response.status_code == 422  # Validation error


class TestFeedbackEndpoints:
    """Test feedback ingestion endpoints."""

    def test_ingest_feedback_valid(self):
        """Test ingesting valid feedback."""
        feedback_data = {
            "feedback_id": "660e8400-e29b-41d4-a716-446655440000",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "student_id": "student_00042",
            "tutor_id": "tutor_00001",
            "overall_rating": 5,
            "is_first_session": False,
            "subject_knowledge_rating": 5,
            "communication_rating": 5,
            "patience_rating": 4,
            "engagement_rating": 5,
            "helpfulness_rating": 5,
            "free_text_feedback": "Great session, very helpful!",
            "submitted_at": "2024-05-14T18:30:00",
            "created_at": "2024-05-14T18:30:00",
        }

        response = client.post("/api/feedback", json=feedback_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["id"] == "660e8400-e29b-41d4-a716-446655440000"
        assert data["queued"] is True

    def test_ingest_feedback_invalid_rating(self):
        """Test ingesting feedback with invalid rating."""
        feedback_data = {
            "feedback_id": "660e8400-e29b-41d4-a716-446655440000",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "student_id": "student_00042",
            "tutor_id": "tutor_00001",
            "overall_rating": 6,  # Invalid (>5)
            "is_first_session": False,
            "subject_knowledge_rating": 5,
            "communication_rating": 5,
            "patience_rating": 4,
            "engagement_rating": 5,
            "helpfulness_rating": 5,
            "free_text_feedback": "Great session!",
            "submitted_at": "2024-05-14T18:30:00",
            "created_at": "2024-05-14T18:30:00",
        }

        response = client.post("/api/feedback", json=feedback_data)
        assert response.status_code == 422  # Validation error


class TestQueueStats:
    """Test queue statistics endpoint."""

    def test_queue_stats(self):
        """Test getting queue statistics."""
        response = client.get("/api/queue/stats")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "queues" in data
        assert "tutors" in data["queues"]
        assert "sessions" in data["queues"]
        assert "feedbacks" in data["queues"]
