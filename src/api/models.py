"""
Pydantic models for API request validation.

Models match the data structures from the synthetic data generation engine.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class TutorProfile(BaseModel):
    """Tutor profile data model."""

    tutor_id: str = Field(..., description="Unique tutor identifier")
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    age: int = Field(..., ge=18, le=100)
    location: str = Field(..., min_length=1, max_length=255)
    education_level: str = Field(..., min_length=1, max_length=100)
    subjects: List[str] = Field(..., min_length=1, max_length=10)
    subject_type: str = Field(..., description="Primary subject category: STEM, Language, or TestPrep")
    onboarding_date: str = Field(..., description="ISO format datetime")
    tenure_days: int = Field(..., ge=0)
    behavioral_archetype: str = Field(..., description="Tutor behavioral archetype")
    baseline_sessions_per_week: int = Field(..., ge=0, le=50)
    status: str = Field(default="active")
    created_at: str = Field(..., description="ISO format datetime")
    updated_at: str = Field(..., description="ISO format datetime")

    @field_validator('behavioral_archetype')
    @classmethod
    def validate_archetype(cls, v: str) -> str:
        valid_archetypes = ['high_performer', 'at_risk', 'new_tutor', 'steady', 'churner']
        if v not in valid_archetypes:
            raise ValueError(f'behavioral_archetype must be one of {valid_archetypes}')
        return v

    @field_validator('subject_type')
    @classmethod
    def validate_subject_type(cls, v: str) -> str:
        valid_types = ['STEM', 'Language', 'TestPrep']
        if v not in valid_types:
            raise ValueError(f'subject_type must be one of {valid_types}')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ['active', 'inactive', 'suspended']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
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
                "updated_at": "2024-05-14T10:00:00"
            }
        }
    }


class SessionData(BaseModel):
    """Session data model."""

    session_id: str = Field(..., description="Unique session identifier")
    tutor_id: str = Field(..., description="Reference to tutor")
    student_id: str = Field(..., description="Reference to student")
    session_number: int = Field(..., ge=1)
    is_first_session: bool
    scheduled_start: str = Field(..., description="ISO format datetime")
    actual_start: Optional[str] = Field(None, description="ISO format datetime, null if no-show")
    duration_minutes: int = Field(..., ge=0, le=300)
    subject: str = Field(..., min_length=1, max_length=100)
    session_type: str = Field(default="1-on-1")
    tutor_initiated_reschedule: bool
    no_show: bool
    late_start_minutes: int = Field(..., ge=0, le=60)
    engagement_score: float = Field(..., ge=0.0, le=1.0)
    learning_objectives_met: bool
    technical_issues: bool
    created_at: str = Field(..., description="ISO format datetime")
    updated_at: str = Field(..., description="ISO format datetime")

    @field_validator('session_type')
    @classmethod
    def validate_session_type(cls, v: str) -> str:
        valid_types = ['1-on-1', 'group', 'workshop']
        if v not in valid_types:
            raise ValueError(f'session_type must be one of {valid_types}')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
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
                "updated_at": "2024-05-14T16:05:00"
            }
        }
    }


class FeedbackData(BaseModel):
    """Student feedback data model."""

    feedback_id: str = Field(..., description="Unique feedback identifier")
    session_id: str = Field(..., description="Reference to session")
    student_id: str = Field(..., description="Reference to student")
    tutor_id: str = Field(..., description="Reference to tutor")
    overall_rating: int = Field(..., ge=1, le=5)
    is_first_session: bool
    subject_knowledge_rating: int = Field(..., ge=1, le=5)
    communication_rating: int = Field(..., ge=1, le=5)
    patience_rating: int = Field(..., ge=1, le=5)
    engagement_rating: int = Field(..., ge=1, le=5)
    helpfulness_rating: int = Field(..., ge=1, le=5)
    free_text_feedback: str = Field(default="", max_length=5000)
    submitted_at: str = Field(..., description="ISO format datetime")
    created_at: str = Field(..., description="ISO format datetime")

    # First session specific fields (optional)
    would_recommend: Optional[bool] = None
    improvement_areas: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
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
                "would_recommend": None,
                "improvement_areas": None
            }
        }
    }


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    redis_connected: bool
    version: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2024-05-14T10:00:00",
                "redis_connected": True,
                "version": "0.1.0"
            }
        }
    }


class IngestionResponse(BaseModel):
    """Standard response for data ingestion endpoints."""

    success: bool
    message: str
    id: str
    queued: bool
    timestamp: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Tutor profile received and queued for processing",
                "id": "tutor_00001",
                "queued": True,
                "timestamp": "2024-05-14T10:00:00"
            }
        }
    }


class BatchIngestionResponse(BaseModel):
    """Response for batch ingestion endpoints."""

    success: bool
    message: str
    count: int
    queued: bool
    timestamp: str
    errors: List[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Batch ingestion completed",
                "count": 150,
                "queued": True,
                "timestamp": "2024-05-14T10:00:00",
                "errors": []
            }
        }
    }
