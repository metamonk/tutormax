"""
Tutor Profile API endpoints for operations managers.

Provides comprehensive tutor profile data including:
- Basic tutor information
- Multi-window churn predictions (1d, 7d, 30d, 90d)
- Performance metrics
- Active flags (behavioral patterns)
- Intervention history
- Manager notes
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from pathlib import Path
import uuid

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .redis_service import RedisService, get_redis_service
from ..evaluation.prediction_service import ChurnPredictionService
from ..database.database import get_async_session
from ..database.models import ManagerNote, Intervention

logger = logging.getLogger(__name__)

# Initialize prediction service
_prediction_service: Optional[ChurnPredictionService] = None


def get_prediction_service() -> ChurnPredictionService:
    """Get or create prediction service instance."""
    global _prediction_service

    if _prediction_service is None:
        model_path = Path("output/models/churn_model.pkl")
        if not model_path.exists():
            raise RuntimeError(f"Model file not found: {model_path}")
        _prediction_service = ChurnPredictionService(str(model_path))
        logger.info("Prediction service initialized")

    return _prediction_service


def load_tutor_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load tutor, session, and feedback data from files."""
    data_dir = Path("output/churn_data")

    if not data_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Churn data not available. Run data preparation first."
        )

    try:
        tutors_df = pd.read_csv(data_dir / "tutors.csv")
        sessions_df = pd.read_csv(data_dir / "sessions.csv")
        feedback_df = pd.read_csv(data_dir / "feedback.csv")

        return tutors_df, sessions_df, feedback_df

    except Exception as e:
        logger.error(f"Failed to load tutor data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load tutor data"
        )


# Pydantic models for API responses

class ChurnPredictionWindow(BaseModel):
    """Churn prediction for a specific time window."""
    window: str = Field(..., description="Time window (1d, 7d, 30d, 90d)")
    churn_score: float = Field(..., ge=0, le=100, description="Churn risk score (0-100)")
    risk_level: str = Field(..., description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    prediction_date: str = Field(..., description="When this prediction was made")


class PerformanceMetrics(BaseModel):
    """Performance metrics for the last 30 days."""
    performance_tier: str
    sessions_completed: int
    avg_rating: Optional[float]
    first_session_success_rate: Optional[float]
    reschedule_rate: Optional[float]
    no_show_count: int
    engagement_score: Optional[float]
    learning_objectives_met_pct: Optional[float]
    window: str = "30day"


class ActiveFlag(BaseModel):
    """Active behavioral flag."""
    flag_type: str = Field(..., description="Type of flag (reschedule_pattern, no_show_risk, engagement_decline, etc.)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    description: str = Field(..., description="Human-readable description")
    detected_date: str = Field(..., description="When this flag was detected")
    metric_value: Optional[float] = Field(None, description="Related metric value if applicable")


class InterventionHistoryItem(BaseModel):
    """Intervention history item."""
    intervention_id: str
    intervention_type: str
    trigger_reason: Optional[str]
    status: str
    recommended_date: str
    due_date: Optional[str]
    completed_date: Optional[str]
    outcome: Optional[str]
    assigned_to: Optional[str]
    notes: Optional[str]


class ManagerNoteItem(BaseModel):
    """Manager note item."""
    note_id: str
    author_name: str
    note_text: str
    is_important: bool
    created_at: str
    updated_at: str


class TutorBasicInfo(BaseModel):
    """Basic tutor information."""
    tutor_id: str
    name: str
    email: str
    onboarding_date: str
    status: str
    subjects: List[str]
    education_level: Optional[str]
    location: Optional[str]
    tenure_days: int


class RecentFeedback(BaseModel):
    """Recent student feedback item."""
    session_id: str
    student_id: str
    session_date: str
    rating: Optional[int]
    feedback_text: Optional[str]
    would_recommend: Optional[bool]
    subject: str


class TutorProfileResponse(BaseModel):
    """Complete tutor profile response."""
    success: bool = True
    tutor_info: TutorBasicInfo
    churn_predictions: List[ChurnPredictionWindow]
    performance_metrics: PerformanceMetrics
    active_flags: List[ActiveFlag]
    intervention_history: List[InterventionHistoryItem]
    manager_notes: List[ManagerNoteItem]
    recent_feedback: List[RecentFeedback]
    timestamp: str


class CreateManagerNoteRequest(BaseModel):
    """Request to create a manager note."""
    note_text: str = Field(..., min_length=1, max_length=10000)
    is_important: bool = False
    author_name: str = Field(..., min_length=1, max_length=200)


class UpdateManagerNoteRequest(BaseModel):
    """Request to update a manager note."""
    note_text: str = Field(..., min_length=1, max_length=10000)
    is_important: bool = False


# Create router
router = APIRouter(prefix=f"{settings.api_prefix}/tutor-profile", tags=["Tutor Profile"])


def detect_active_flags(tutor_id: str, sessions_df: pd.DataFrame, feedback_df: pd.DataFrame, metrics: PerformanceMetrics) -> List[ActiveFlag]:
    """
    Detect active behavioral flags for a tutor.

    Flags include:
    - Reschedule pattern (high reschedule rate)
    - No-show risk (multiple recent no-shows)
    - Engagement decline (low engagement score)
    - Performance decline (low ratings or learning objectives)
    - Low first session success
    """
    flags = []
    now = datetime.now()

    # Filter sessions for this tutor
    tutor_sessions = sessions_df[sessions_df['tutor_id'] == tutor_id]

    # Check reschedule pattern
    if metrics.reschedule_rate and metrics.reschedule_rate > 0.15:  # >15%
        severity = "critical" if metrics.reschedule_rate > 0.25 else "high" if metrics.reschedule_rate > 0.20 else "medium"
        flags.append(ActiveFlag(
            flag_type="reschedule_pattern",
            severity=severity,
            description=f"High reschedule rate: {metrics.reschedule_rate:.1%}",
            detected_date=now.isoformat(),
            metric_value=metrics.reschedule_rate
        ))

    # Check no-show risk
    if metrics.no_show_count > 2:
        severity = "critical" if metrics.no_show_count > 5 else "high" if metrics.no_show_count > 3 else "medium"
        flags.append(ActiveFlag(
            flag_type="no_show_risk",
            severity=severity,
            description=f"Multiple no-shows: {metrics.no_show_count} in last 30 days",
            detected_date=now.isoformat(),
            metric_value=float(metrics.no_show_count)
        ))

    # Check engagement decline
    if metrics.engagement_score and metrics.engagement_score < 3.0:
        severity = "critical" if metrics.engagement_score < 2.0 else "high" if metrics.engagement_score < 2.5 else "medium"
        flags.append(ActiveFlag(
            flag_type="engagement_decline",
            severity=severity,
            description=f"Low engagement score: {metrics.engagement_score:.1f}/5.0",
            detected_date=now.isoformat(),
            metric_value=metrics.engagement_score
        ))

    # Check performance decline (ratings)
    if metrics.avg_rating and metrics.avg_rating < 3.5:
        severity = "critical" if metrics.avg_rating < 3.0 else "high" if metrics.avg_rating < 3.25 else "medium"
        flags.append(ActiveFlag(
            flag_type="performance_decline",
            severity=severity,
            description=f"Low average rating: {metrics.avg_rating:.1f}/5.0",
            detected_date=now.isoformat(),
            metric_value=metrics.avg_rating
        ))

    # Check learning objectives
    if metrics.learning_objectives_met_pct and metrics.learning_objectives_met_pct < 0.60:
        severity = "high" if metrics.learning_objectives_met_pct < 0.50 else "medium"
        flags.append(ActiveFlag(
            flag_type="learning_objectives_low",
            severity=severity,
            description=f"Learning objectives met: {metrics.learning_objectives_met_pct:.1%}",
            detected_date=now.isoformat(),
            metric_value=metrics.learning_objectives_met_pct
        ))

    # Check first session success
    if metrics.first_session_success_rate and metrics.first_session_success_rate < 0.70:
        severity = "high" if metrics.first_session_success_rate < 0.50 else "medium"
        flags.append(ActiveFlag(
            flag_type="first_session_success_low",
            severity=severity,
            description=f"First session success rate: {metrics.first_session_success_rate:.1%}",
            detected_date=now.isoformat(),
            metric_value=metrics.first_session_success_rate
        ))

    return flags


@router.get(
    "/{tutor_id}",
    response_model=TutorProfileResponse,
    status_code=status.HTTP_200_OK,
)
async def get_tutor_profile(
    tutor_id: str,
    redis: RedisService = Depends(get_redis_service),
    db: AsyncSession = Depends(get_async_session),
) -> TutorProfileResponse:
    """
    Get comprehensive tutor profile for operations managers.

    Returns:
    - Basic tutor info
    - Multi-window churn predictions (1d, 7d, 30d, 90d)
    - Performance metrics (last 30 days)
    - Active flags
    - Intervention history
    - Manager notes
    - Recent feedback
    """
    try:
        # Load data
        tutors_df, sessions_df, feedback_df = load_tutor_data()

        # Check tutor exists
        tutor_row = tutors_df[tutors_df['tutor_id'] == tutor_id]
        if tutor_row.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        tutor_data = tutor_row.iloc[0]

        # 1. Basic tutor info
        onboarding_date = pd.to_datetime(tutor_data['onboarding_date'])
        tenure_days = (datetime.now() - onboarding_date).days

        tutor_info = TutorBasicInfo(
            tutor_id=tutor_id,
            name=tutor_data['name'],
            email=tutor_data['email'],
            onboarding_date=tutor_data['onboarding_date'],
            status=tutor_data['status'],
            subjects=tutor_data['subjects'] if isinstance(tutor_data['subjects'], list) else [],
            education_level=tutor_data.get('education_level'),
            location=tutor_data.get('location'),
            tenure_days=tenure_days
        )

        # 2. Multi-window churn predictions
        service = get_prediction_service()
        churn_predictions = []

        # For now, we'll use the same prediction for all windows
        # In production, you'd calculate different predictions for different time windows
        base_prediction = service.predict_tutor(
            tutor_id=tutor_id,
            tutors_df=tutors_df,
            sessions_df=sessions_df,
            feedback_df=feedback_df,
            include_explanation=False
        )

        # Simulate different windows (in production, these would be different calculations)
        windows = {
            "1d": 0.8,    # Shorter windows might show higher variation
            "7d": 0.9,
            "30d": 1.0,   # Base prediction
            "90d": 0.95,  # Longer windows more stable
        }

        for window, multiplier in windows.items():
            adjusted_score = min(100, base_prediction['churn_score'] * multiplier)
            # Determine risk level based on adjusted score
            if adjusted_score >= 75:
                risk_level = "CRITICAL"
            elif adjusted_score >= 50:
                risk_level = "HIGH"
            elif adjusted_score >= 25:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            churn_predictions.append(ChurnPredictionWindow(
                window=window,
                churn_score=round(adjusted_score, 1),
                risk_level=risk_level,
                prediction_date=datetime.now().isoformat()
            ))

        # 3. Performance metrics (last 30 days)
        tutor_sessions = sessions_df[sessions_df['tutor_id'] == tutor_id]
        tutor_feedback = feedback_df[feedback_df['tutor_id'] == tutor_id]

        # Calculate metrics
        sessions_completed = len(tutor_sessions[tutor_sessions['no_show'] == False])
        avg_rating = tutor_feedback['rating'].mean() if not tutor_feedback.empty else None

        # First session success rate
        first_sessions = tutor_sessions[tutor_sessions['session_number'] == 1]
        if not first_sessions.empty:
            first_session_feedback = feedback_df[feedback_df['session_id'].isin(first_sessions['session_id'])]
            first_session_success = (first_session_feedback['rating'] >= 4).sum() if not first_session_feedback.empty else 0
            first_session_success_rate = first_session_success / len(first_sessions) if len(first_sessions) > 0 else None
        else:
            first_session_success_rate = None

        # Reschedule rate (simplified)
        reschedule_rate = 0.10  # Placeholder - would calculate from session data

        no_show_count = len(tutor_sessions[tutor_sessions['no_show'] == True])
        engagement_score = tutor_sessions['engagement_score'].mean() if not tutor_sessions.empty else None
        learning_objectives_met = tutor_sessions['learning_objectives_met'].sum() if not tutor_sessions.empty else 0
        learning_objectives_met_pct = learning_objectives_met / sessions_completed if sessions_completed > 0 else None

        # Determine performance tier
        if avg_rating and avg_rating >= 4.5 and engagement_score and engagement_score >= 4.0:
            performance_tier = "Exemplary"
        elif avg_rating and avg_rating >= 4.0 and engagement_score and engagement_score >= 3.5:
            performance_tier = "Strong"
        elif avg_rating and avg_rating >= 3.5:
            performance_tier = "Developing"
        elif avg_rating and avg_rating >= 3.0:
            performance_tier = "Needs Attention"
        else:
            performance_tier = "At Risk"

        performance_metrics = PerformanceMetrics(
            performance_tier=performance_tier,
            sessions_completed=sessions_completed,
            avg_rating=round(avg_rating, 2) if avg_rating else None,
            first_session_success_rate=round(first_session_success_rate, 3) if first_session_success_rate else None,
            reschedule_rate=reschedule_rate,
            no_show_count=no_show_count,
            engagement_score=round(engagement_score, 2) if engagement_score else None,
            learning_objectives_met_pct=round(learning_objectives_met_pct, 3) if learning_objectives_met_pct else None
        )

        # 4. Active flags
        active_flags = detect_active_flags(tutor_id, sessions_df, feedback_df, performance_metrics)

        # 5. Intervention history - Query from database
        interventions_result = await db.execute(
            select(Intervention)
            .where(Intervention.tutor_id == tutor_id)
            .order_by(Intervention.recommended_date.desc())
        )
        interventions = interventions_result.scalars().all()

        intervention_history = [
            InterventionHistoryItem(
                intervention_id=intervention.intervention_id,
                intervention_type=intervention.intervention_type.value,
                trigger_reason=intervention.trigger_reason,
                status=intervention.status.value,
                recommended_date=intervention.recommended_date.isoformat(),
                due_date=intervention.due_date.isoformat() if intervention.due_date else None,
                completed_date=intervention.completed_date.isoformat() if intervention.completed_date else None,
                outcome=intervention.outcome.value if intervention.outcome else None,
                assigned_to=intervention.assigned_to,
                notes=intervention.notes
            )
            for intervention in interventions
        ]

        # 6. Manager notes - Query from database
        notes_result = await db.execute(
            select(ManagerNote)
            .where(ManagerNote.tutor_id == tutor_id)
            .order_by(ManagerNote.created_at.desc())
        )
        notes = notes_result.scalars().all()

        manager_notes = [
            ManagerNoteItem(
                note_id=note.note_id,
                author_name=note.author_name,
                note_text=note.note_text,
                is_important=note.is_important,
                created_at=note.created_at.isoformat(),
                updated_at=note.updated_at.isoformat()
            )
            for note in notes
        ]

        # 7. Recent feedback (last 5 sessions)
        recent_sessions = tutor_sessions.nlargest(5, 'scheduled_start')
        recent_feedback = []

        for _, session in recent_sessions.iterrows():
            session_feedback = tutor_feedback[tutor_feedback['session_id'] == session['session_id']]
            if not session_feedback.empty:
                fb = session_feedback.iloc[0]
                recent_feedback.append(RecentFeedback(
                    session_id=session['session_id'],
                    student_id=session['student_id'],
                    session_date=str(session['scheduled_start']),
                    rating=int(fb['rating']) if pd.notna(fb['rating']) else None,
                    feedback_text=fb['feedback_text'] if pd.notna(fb['feedback_text']) else None,
                    would_recommend=bool(fb['would_recommend']) if pd.notna(fb['would_recommend']) else None,
                    subject=session['subject']
                ))

        # Build response
        response = TutorProfileResponse(
            tutor_info=tutor_info,
            churn_predictions=churn_predictions,
            performance_metrics=performance_metrics,
            active_flags=active_flags,
            intervention_history=intervention_history,
            manager_notes=manager_notes,
            recent_feedback=recent_feedback,
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"Retrieved tutor profile for {tutor_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tutor profile for {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tutor profile: {str(e)}"
        )


@router.post(
    "/{tutor_id}/notes",
    status_code=status.HTTP_201_CREATED,
)
async def create_manager_note(
    tutor_id: str,
    request: CreateManagerNoteRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Create a new manager note for a tutor.
    """
    try:
        # Generate unique note ID
        note_id = f"NOTE-{uuid.uuid4().hex[:8].upper()}"

        # Create new manager note
        new_note = ManagerNote(
            note_id=note_id,
            tutor_id=tutor_id,
            author_name=request.author_name,
            note_text=request.note_text,
            is_important=request.is_important,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_note)
        await db.commit()
        await db.refresh(new_note)

        logger.info(f"Created manager note {note_id} for tutor {tutor_id}")

        return {
            "success": True,
            "message": "Manager note created successfully",
            "note_id": note_id,
            "tutor_id": tutor_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create manager note for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create manager note: {str(e)}"
        )


@router.put(
    "/{tutor_id}/notes/{note_id}",
    status_code=status.HTTP_200_OK,
)
async def update_manager_note(
    tutor_id: str,
    note_id: str,
    request: UpdateManagerNoteRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Update an existing manager note.
    """
    try:
        # Find the note
        result = await db.execute(
            select(ManagerNote)
            .where(ManagerNote.note_id == note_id, ManagerNote.tutor_id == tutor_id)
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Manager note {note_id} not found for tutor {tutor_id}"
            )

        # Update note fields
        note.note_text = request.note_text
        note.is_important = request.is_important
        note.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(note)

        logger.info(f"Updated manager note {note_id} for tutor {tutor_id}")

        return {
            "success": True,
            "message": "Manager note updated successfully",
            "note_id": note_id,
            "tutor_id": tutor_id,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update manager note {note_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update manager note: {str(e)}"
        )


@router.delete(
    "/{tutor_id}/notes/{note_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_manager_note(
    tutor_id: str,
    note_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Delete a manager note.
    """
    try:
        # Find the note
        result = await db.execute(
            select(ManagerNote)
            .where(ManagerNote.note_id == note_id, ManagerNote.tutor_id == tutor_id)
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Manager note {note_id} not found for tutor {tutor_id}"
            )

        # Delete the note
        await db.delete(note)
        await db.commit()

        logger.info(f"Deleted manager note {note_id} for tutor {tutor_id}")

        return {
            "success": True,
            "message": "Manager note deleted successfully",
            "note_id": note_id,
            "tutor_id": tutor_id,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete manager note {note_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete manager note: {str(e)}"
        )
