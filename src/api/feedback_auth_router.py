"""
FastAPI router for student feedback authentication.

Implements token-based authentication for student feedback submission
with COPPA compliance for under-13 students.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from .feedback_auth_schemas import (
    FeedbackTokenRequest,
    FeedbackTokenResponse,
    ValidateTokenRequest,
    ValidateTokenResponse,
    StudentFeedbackSubmission,
    FeedbackSubmissionResponse,
    ParentConsentRequest,
    ParentConsentResponse
)
from .feedback_token_utils import FeedbackTokenManager, generate_feedback_url
from .email_service import get_email_service_from_settings
from .redis_service import get_redis_service, RedisService
from ..database.database import get_async_session
from src.database.models import Student, Session, StudentFeedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["Student Feedback"])


def get_token_manager(redis: RedisService = Depends(get_redis_service)) -> FeedbackTokenManager:
    """Dependency to get feedback token manager."""
    return FeedbackTokenManager(redis)


@router.post("/request-token", response_model=FeedbackTokenResponse)
async def request_feedback_token(
    request: FeedbackTokenRequest,
    token_manager: FeedbackTokenManager = Depends(get_token_manager),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Generate a feedback token for a session and optionally send email.

    This endpoint is typically called by the system after a session completes.
    Generates a unique token linked to the session and student, and optionally
    sends an email invitation with the feedback link.

    For students under 13, a notification is sent to the parent email instead.
    """
    try:
        # Verify session exists
        session_result = await db.execute(
            select(Session).where(Session.session_id == request.session_id)
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )

        # Verify student exists and get COPPA info
        student_result = await db.execute(
            select(Student).where(Student.student_id == request.student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {request.student_id} not found"
            )

        # Check if feedback already exists for this session
        existing_feedback = await db.execute(
            select(StudentFeedback).where(StudentFeedback.session_id == request.session_id)
        )
        if existing_feedback.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback already submitted for this session"
            )

        # Determine email recipients based on COPPA status
        student_email = request.student_email
        parent_email = student.parent_email if student.is_under_13 else None
        is_under_13 = student.is_under_13

        # Create feedback token
        token = await token_manager.create_feedback_token(
            session_id=request.session_id,
            student_id=request.student_id,
            tutor_id=session.tutor_id,
            student_email=student_email,
            parent_email=parent_email,
            is_under_13=is_under_13
        )

        # Generate feedback URL
        feedback_url = generate_feedback_url(token)

        # Get token info for expiration
        token_info = await token_manager.get_token_info(token)
        expires_at = token_info.get("expires_at") if token_info else None

        # Send email if requested
        email_sent = False
        parent_notification_sent = False

        if request.send_email:
            email_service = get_email_service_from_settings()

            if email_service:
                # Format session date
                session_date = session.scheduled_start.strftime("%B %d, %Y at %I:%M %p")

                if is_under_13 and parent_email:
                    # Send to parent for COPPA compliance
                    parent_notification_sent = email_service.send_parent_notification(
                        parent_email=parent_email,
                        parent_name="Parent/Guardian",  # Could be enhanced with actual parent name
                        student_name=student.name,
                        tutor_name=session.tutor.name,
                        session_date=session_date,
                        feedback_url=feedback_url
                    )
                elif student_email:
                    # Send to student (13+)
                    email_sent = email_service.send_feedback_invitation(
                        student_email=student_email,
                        student_name=student.name,
                        tutor_name=session.tutor.name,
                        session_date=session_date,
                        feedback_url=feedback_url,
                        expires_at=expires_at or "7 days"
                    )
            else:
                logger.warning("Email service not configured - skipping email")

        return FeedbackTokenResponse(
            success=True,
            token=token,
            feedback_url=feedback_url,
            expires_at=expires_at or datetime.utcnow().isoformat(),
            session_id=request.session_id,
            student_id=request.student_id,
            email_sent=email_sent,
            parent_notification_sent=parent_notification_sent
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating feedback token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate feedback token"
        )


@router.post("/validate-token", response_model=ValidateTokenResponse)
async def validate_feedback_token(
    request: ValidateTokenRequest,
    token_manager: FeedbackTokenManager = Depends(get_token_manager),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Validate a feedback token and return session information.

    Used by the frontend to verify a token before displaying the feedback form.
    Returns information about COPPA requirements if student is under 13.
    """
    try:
        # Validate token
        token_data = await token_manager.validate_token(request.token)

        if not token_data:
            return ValidateTokenResponse(
                valid=False,
                message="Token is invalid or expired"
            )

        # Check if student requires parent consent
        is_under_13 = token_data.get("is_under_13", False)
        requires_parent_consent = is_under_13

        # Get student to verify consent status
        if is_under_13:
            student_result = await db.execute(
                select(Student).where(Student.student_id == token_data.get("student_id"))
            )
            student = student_result.scalar_one_or_none()

            if student and not student.parent_consent_given:
                requires_parent_consent = True

        # Get session info for display
        session_result = await db.execute(
            select(Session).where(Session.session_id == token_data.get("session_id"))
        )
        session = session_result.scalar_one_or_none()

        tutor_name = None
        session_date = None
        subject = None

        if session:
            if session.tutor:
                tutor_name = session.tutor.name
            session_date = session.scheduled_start.isoformat() if session.scheduled_start else None
            subject = session.subject

        return ValidateTokenResponse(
            valid=True,
            session_id=token_data.get("session_id"),
            student_id=token_data.get("student_id"),
            tutor_id=token_data.get("tutor_id"),
            tutor_name=tutor_name,
            session_date=session_date,
            subject=subject,
            is_under_13=is_under_13,
            requires_parent_consent=requires_parent_consent,
            expires_at=token_data.get("expires_at"),
            message="Token is valid"
        )

    except Exception as e:
        logger.error(f"Error validating token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate token"
        )


@router.post("/submit", response_model=FeedbackSubmissionResponse)
async def submit_feedback(
    submission: StudentFeedbackSubmission,
    request: Request,
    token_manager: FeedbackTokenManager = Depends(get_token_manager),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Submit student feedback using a token.

    Validates the token, checks COPPA compliance for under-13 students,
    and creates the feedback record in the database.
    """
    try:
        # Validate token
        token_data = await token_manager.validate_token(submission.token)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        session_id = token_data.get("session_id")
        student_id = token_data.get("student_id")
        is_under_13 = token_data.get("is_under_13", False)

        # COPPA compliance check
        if is_under_13:
            student_result = await db.execute(
                select(Student).where(Student.student_id == student_id)
            )
            student = student_result.scalar_one_or_none()

            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )

            # Check if parent consent is required
            if not student.parent_consent_given and not submission.parent_consent_given:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Parent consent required for students under 13"
                )

            # Update parent consent if provided
            if submission.parent_consent_given and not student.parent_consent_given:
                student.parent_consent_given = True
                student.parent_consent_date = datetime.utcnow()
                student.parent_consent_ip = request.client.host if request.client else None
                await db.commit()

        # Check if feedback already exists
        existing_feedback = await db.execute(
            select(StudentFeedback).where(StudentFeedback.session_id == session_id)
        )
        if existing_feedback.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback already submitted for this session"
            )

        # Get session to verify it exists and get tutor_id
        session_result = await db.execute(
            select(Session).where(Session.session_id == session_id)
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Create feedback record
        feedback_id = f"FB-{secrets.token_hex(8)}"
        feedback = StudentFeedback(
            feedback_id=feedback_id,
            session_id=session_id,
            student_id=student_id,
            tutor_id=session.tutor_id,
            overall_rating=submission.overall_rating,
            is_first_session=session.session_number == 1,
            subject_knowledge_rating=submission.subject_knowledge_rating,
            communication_rating=submission.communication_rating,
            patience_rating=submission.patience_rating,
            engagement_rating=submission.engagement_rating,
            helpfulness_rating=submission.helpfulness_rating,
            would_recommend=submission.would_recommend,
            improvement_areas=submission.improvement_areas,
            free_text_feedback=submission.free_text_feedback,
            submitted_at=datetime.utcnow()
        )

        db.add(feedback)
        await db.commit()

        # Mark token as used
        await token_manager.mark_token_used(submission.token, feedback_id)

        logger.info(f"Feedback submitted: {feedback_id} for session {session_id}")

        return FeedbackSubmissionResponse(
            success=True,
            feedback_id=feedback_id,
            session_id=session_id,
            message="Feedback submitted successfully",
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.post("/parent-consent", response_model=ParentConsentResponse)
async def record_parent_consent(
    consent_request: ParentConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Record parent consent for a student (COPPA compliance).

    This endpoint allows parents to provide or revoke consent for their
    under-13 child to provide feedback.
    """
    try:
        # Get student
        student_result = await db.execute(
            select(Student).where(Student.student_id == consent_request.student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )

        # Verify student is under 13
        if not student.is_under_13:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent consent not required for students 13 and over"
            )

        # Update consent information
        student.parent_email = consent_request.parent_email
        student.parent_consent_given = consent_request.consent_given
        student.parent_consent_date = datetime.utcnow()
        student.parent_consent_ip = request.client.host if request.client else None

        await db.commit()

        logger.info(
            f"Parent consent recorded for student {consent_request.student_id}: "
            f"{consent_request.consent_given}"
        )

        return ParentConsentResponse(
            success=True,
            student_id=consent_request.student_id,
            consent_recorded=True,
            message="Parent consent recorded successfully",
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording parent consent: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record parent consent"
        )


@router.get("/token-info/{token}")
async def get_token_info(
    token: str,
    token_manager: FeedbackTokenManager = Depends(get_token_manager)
):
    """
    Get information about a feedback token (for debugging/admin).

    Note: This endpoint should be protected with authentication in production.
    """
    token_info = await token_manager.get_token_info(token)

    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )

    return token_info
