"""
Pydantic schemas for feedback authentication endpoints.

Defines request and response models for student feedback token-based authentication.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


class FeedbackTokenRequest(BaseModel):
    """Request to generate a feedback token for a session."""

    session_id: str = Field(..., description="Session ID")
    student_id: str = Field(..., description="Student ID")
    student_email: Optional[EmailStr] = Field(None, description="Student email address")
    send_email: bool = Field(True, description="Whether to send email with token link")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "SES-001",
                "student_id": "STU-001",
                "student_email": "student@example.com",
                "send_email": True
            }
        }


class FeedbackTokenResponse(BaseModel):
    """Response with generated feedback token."""

    success: bool
    token: str = Field(..., description="Generated feedback token")
    feedback_url: str = Field(..., description="Complete URL for feedback submission")
    expires_at: str = Field(..., description="Token expiration timestamp (ISO format)")
    session_id: str
    student_id: str
    email_sent: bool = Field(False, description="Whether email was sent")
    parent_notification_sent: bool = Field(False, description="Whether parent was notified (for under-13)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "token": "abc123xyz789...",
                "feedback_url": "http://localhost:8000/feedback/submit?token=abc123xyz789...",
                "expires_at": "2024-11-15T12:00:00Z",
                "session_id": "SES-001",
                "student_id": "STU-001",
                "email_sent": True,
                "parent_notification_sent": False
            }
        }


class ValidateTokenRequest(BaseModel):
    """Request to validate a feedback token."""

    token: str = Field(..., description="Feedback token to validate")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123xyz789..."
            }
        }


class ValidateTokenResponse(BaseModel):
    """Response for token validation."""

    valid: bool = Field(..., description="Whether token is valid")
    session_id: Optional[str] = None
    student_id: Optional[str] = None
    tutor_id: Optional[str] = None
    tutor_name: Optional[str] = None
    session_date: Optional[str] = None
    subject: Optional[str] = None
    is_under_13: Optional[bool] = None
    requires_parent_consent: Optional[bool] = None
    expires_at: Optional[str] = None
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "session_id": "SES-001",
                "student_id": "STU-001",
                "tutor_id": "TUT-001",
                "is_under_13": False,
                "requires_parent_consent": False,
                "expires_at": "2024-11-15T12:00:00Z",
                "message": "Token is valid"
            }
        }


class StudentFeedbackSubmission(BaseModel):
    """Student feedback submission via token."""

    token: str = Field(..., description="Feedback token")

    # Core ratings (1-5 scale)
    overall_rating: int = Field(..., ge=1, le=5, description="Overall session rating (1-5)")
    subject_knowledge_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    patience_rating: Optional[int] = Field(None, ge=1, le=5)
    engagement_rating: Optional[int] = Field(None, ge=1, le=5)
    helpfulness_rating: Optional[int] = Field(None, ge=1, le=5)

    # Additional feedback
    would_recommend: Optional[bool] = None
    improvement_areas: Optional[List[str]] = Field(None, max_items=10)
    free_text_feedback: Optional[str] = Field(None, max_length=2000)

    # COPPA compliance for under-13
    parent_consent_given: bool = Field(False, description="Parent consent for under-13 students")
    parent_signature: Optional[str] = Field(None, description="Parent name/signature")

    @validator('improvement_areas')
    def validate_improvement_areas(cls, v):
        """Validate improvement areas list."""
        if v is not None:
            valid_areas = [
                "subject_knowledge",
                "communication",
                "patience",
                "engagement",
                "punctuality",
                "technical_skills",
                "other"
            ]
            for area in v:
                if area not in valid_areas:
                    raise ValueError(f"Invalid improvement area: {area}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123xyz789...",
                "overall_rating": 5,
                "subject_knowledge_rating": 5,
                "communication_rating": 5,
                "patience_rating": 4,
                "engagement_rating": 5,
                "helpfulness_rating": 5,
                "would_recommend": True,
                "improvement_areas": ["punctuality"],
                "free_text_feedback": "Great tutor! Very helpful and patient.",
                "parent_consent_given": False,
                "parent_signature": None
            }
        }


class FeedbackSubmissionResponse(BaseModel):
    """Response after feedback submission."""

    success: bool
    feedback_id: str = Field(..., description="ID of created feedback record")
    session_id: str
    message: str
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "feedback_id": "FB-001",
                "session_id": "SES-001",
                "message": "Feedback submitted successfully",
                "timestamp": "2024-11-08T12:00:00Z"
            }
        }


class ParentConsentRequest(BaseModel):
    """Request for parent consent (COPPA compliance)."""

    student_id: str = Field(..., description="Student ID")
    parent_email: EmailStr = Field(..., description="Parent email address")
    parent_name: str = Field(..., max_length=200, description="Parent full name")
    consent_given: bool = Field(..., description="Whether parent gives consent")

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "STU-001",
                "parent_email": "parent@example.com",
                "parent_name": "Jane Doe",
                "consent_given": True
            }
        }


class ParentConsentResponse(BaseModel):
    """Response for parent consent submission."""

    success: bool
    student_id: str
    consent_recorded: bool
    message: str
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "student_id": "STU-001",
                "consent_recorded": True,
                "message": "Parent consent recorded successfully",
                "timestamp": "2024-11-08T12:00:00Z"
            }
        }
