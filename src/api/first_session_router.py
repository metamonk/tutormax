"""
FastAPI router for first session success prediction API.

Provides endpoints for:
- Real-time prediction for single sessions
- Batch prediction for upcoming sessions
- Prediction history and analytics
- Model performance metrics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import logging
import uuid

from ..database.database import get_async_session
from ..database.models import (
    FirstSessionPrediction,
    Session,
    Tutor,
    Student,
    StudentFeedback,
    ModelPerformanceLog
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/first-session", tags=["first-session-prediction"])


# Pydantic models
class SessionPredictionRequest(BaseModel):
    """Request model for single session prediction."""
    session_id: str = Field(..., description="Session ID")


class SessionPredictionResponse(BaseModel):
    """Response model for session prediction."""
    prediction_id: str
    session_id: str
    tutor_id: str
    tutor_name: str
    student_id: str
    scheduled_start: str
    subject: str
    risk_probability: float = Field(..., ge=0, le=1, description="Probability of poor session (0-1)")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH, CRITICAL")
    should_send_alert: bool = Field(..., description="Whether alert should be sent")
    top_risk_factors: Optional[Dict[str, Any]] = Field(default=None, description="Top contributing risk factors")
    prediction_date: str
    model_version: str


class UpcomingSessionsRequest(BaseModel):
    """Request model for batch prediction."""
    lookahead_hours: int = Field(default=24, ge=1, le=168, description="Hours to look ahead (1-168)")


class PredictionHistoryResponse(BaseModel):
    """Response model for prediction history."""
    prediction_id: str
    session_id: str
    tutor_id: str
    risk_score: int
    risk_level: str
    prediction_date: str
    alert_sent: bool
    actual_rating: Optional[int]
    prediction_correct: Optional[bool]


class ModelPerformanceResponse(BaseModel):
    """Response model for model performance metrics."""
    model_type: str
    model_version: str
    evaluation_date: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    sample_size: int
    time_window_days: int


@router.post("/predict", response_model=SessionPredictionResponse)
async def predict_session(
    request: SessionPredictionRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Predict first session success for a single session.

    This endpoint makes a real-time prediction for an upcoming first session.
    If the risk is high, it triggers an alert to the tutor.

    Args:
        request: Session prediction request
        db: Database session

    Returns:
        Prediction results with risk assessment
    """
    # This would normally trigger a Celery task
    # For now, return a placeholder
    raise HTTPException(
        status_code=501,
        detail="Prediction endpoint requires trained model deployment. Use /predict-upcoming for batch processing."
    )


@router.get("/predict-upcoming", response_model=List[SessionPredictionResponse])
async def predict_upcoming_sessions(
    lookahead_hours: int = Query(default=24, ge=1, le=168, description="Hours to look ahead"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Predict all upcoming first sessions within timeframe.

    This endpoint identifies all scheduled first sessions in the next N hours
    and generates risk predictions for each.

    Args:
        lookahead_hours: Number of hours to look ahead (default: 24)
        db: Database session

    Returns:
        List of predictions for upcoming first sessions
    """
    logger.info(f"Predicting upcoming first sessions (next {lookahead_hours}h)")

    # Calculate time window
    now = datetime.now()
    cutoff = now + timedelta(hours=lookahead_hours)

    # Query upcoming first sessions
    query = (
        select(Session, Tutor, Student)
        .join(Tutor, Session.tutor_id == Tutor.tutor_id)
        .join(Student, Session.student_id == Student.student_id)
        .where(
            and_(
                Session.session_number == 1,
                Session.scheduled_start >= now,
                Session.scheduled_start <= cutoff
            )
        )
    )

    result = await db.execute(query)
    upcoming_sessions = result.all()

    logger.info(f"Found {len(upcoming_sessions)} upcoming first sessions")

    # For now, return placeholder data
    # In production, this would trigger Celery tasks for each session
    predictions = []

    for session, tutor, student in upcoming_sessions:
        # Placeholder prediction
        prediction = SessionPredictionResponse(
            prediction_id=f"pred_{uuid.uuid4().hex[:12]}",
            session_id=session.session_id,
            tutor_id=session.tutor_id,
            tutor_name=tutor.name,
            student_id=session.student_id,
            scheduled_start=session.scheduled_start.isoformat(),
            subject=session.subject,
            risk_probability=0.5,  # Placeholder
            risk_score=50,  # Placeholder
            risk_level="MEDIUM",  # Placeholder
            should_send_alert=False,  # Placeholder
            top_risk_factors=None,
            prediction_date=now.isoformat(),
            model_version="1.0.0"
        )
        predictions.append(prediction)

    return predictions


@router.get("/history/{tutor_id}", response_model=List[PredictionHistoryResponse])
async def get_prediction_history(
    tutor_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get prediction history for a tutor.

    Args:
        tutor_id: Tutor ID
        days: Number of days to look back (default: 30)
        db: Database session

    Returns:
        List of historical predictions
    """
    # Calculate time window
    cutoff = datetime.now() - timedelta(days=days)

    # Query predictions
    query = (
        select(FirstSessionPrediction)
        .where(
            and_(
                FirstSessionPrediction.tutor_id == tutor_id,
                FirstSessionPrediction.prediction_date >= cutoff
            )
        )
        .order_by(FirstSessionPrediction.prediction_date.desc())
    )

    result = await db.execute(query)
    predictions = result.scalars().all()

    # Convert to response models
    return [
        PredictionHistoryResponse(
            prediction_id=pred.prediction_id,
            session_id=pred.session_id,
            tutor_id=pred.tutor_id,
            risk_score=pred.risk_score,
            risk_level=pred.risk_level.value,
            prediction_date=pred.prediction_date.isoformat(),
            alert_sent=pred.alert_sent,
            actual_rating=pred.actual_rating,
            prediction_correct=pred.prediction_correct
        )
        for pred in predictions
    ]


@router.get("/analytics/model-performance", response_model=List[ModelPerformanceResponse])
async def get_model_performance(
    model_type: str = Query(default="first_session", description="Model type"),
    days: int = Query(default=90, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get model performance metrics over time.

    Args:
        model_type: Model type (default: first_session)
        days: Number of days to look back (default: 90)
        db: Database session

    Returns:
        List of performance metrics
    """
    # Calculate time window
    cutoff = datetime.now() - timedelta(days=days)

    # Query performance logs
    query = (
        select(ModelPerformanceLog)
        .where(
            and_(
                ModelPerformanceLog.model_type == model_type,
                ModelPerformanceLog.evaluation_date >= cutoff
            )
        )
        .order_by(ModelPerformanceLog.evaluation_date.desc())
    )

    result = await db.execute(query)
    logs = result.scalars().all()

    # Convert to response models
    return [
        ModelPerformanceResponse(
            model_type=log.model_type,
            model_version=log.model_version,
            evaluation_date=log.evaluation_date.isoformat(),
            accuracy=log.accuracy,
            precision=log.precision,
            recall=log.recall,
            f1_score=log.f1_score,
            auc_roc=log.auc_roc,
            sample_size=log.sample_size,
            time_window_days=log.time_window_days
        )
        for log in logs
    ]


@router.get("/analytics/summary")
async def get_prediction_analytics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get summary analytics for first session predictions.

    Args:
        days: Number of days to analyze (default: 30)
        db: Database session

    Returns:
        Summary statistics
    """
    # Calculate time window
    cutoff = datetime.now() - timedelta(days=days)

    # Total predictions
    total_query = select(func.count()).select_from(FirstSessionPrediction).where(
        FirstSessionPrediction.prediction_date >= cutoff
    )
    total_result = await db.execute(total_query)
    total_predictions = total_result.scalar()

    # High risk count
    high_risk_query = select(func.count()).select_from(FirstSessionPrediction).where(
        and_(
            FirstSessionPrediction.prediction_date >= cutoff,
            FirstSessionPrediction.risk_level.in_(['HIGH', 'CRITICAL'])
        )
    )
    high_risk_result = await db.execute(high_risk_query)
    high_risk_count = high_risk_result.scalar()

    # Alerts sent
    alerts_query = select(func.count()).select_from(FirstSessionPrediction).where(
        and_(
            FirstSessionPrediction.prediction_date >= cutoff,
            FirstSessionPrediction.alert_sent == True
        )
    )
    alerts_result = await db.execute(alerts_query)
    alerts_sent = alerts_result.scalar()

    # Accuracy (for completed sessions)
    accuracy_query = select(func.count()).select_from(FirstSessionPrediction).where(
        and_(
            FirstSessionPrediction.prediction_date >= cutoff,
            FirstSessionPrediction.prediction_correct == True,
            FirstSessionPrediction.actual_rating.isnot(None)
        )
    )
    accuracy_result = await db.execute(accuracy_query)
    correct_predictions = accuracy_result.scalar()

    total_evaluated_query = select(func.count()).select_from(FirstSessionPrediction).where(
        and_(
            FirstSessionPrediction.prediction_date >= cutoff,
            FirstSessionPrediction.actual_rating.isnot(None)
        )
    )
    total_evaluated_result = await db.execute(total_evaluated_query)
    total_evaluated = total_evaluated_result.scalar()

    accuracy = (correct_predictions / total_evaluated * 100) if total_evaluated > 0 else 0

    return {
        "time_window_days": days,
        "total_predictions": total_predictions or 0,
        "high_risk_count": high_risk_count or 0,
        "high_risk_percentage": (high_risk_count / total_predictions * 100) if total_predictions else 0,
        "alerts_sent": alerts_sent or 0,
        "alert_rate": (alerts_sent / total_predictions * 100) if total_predictions else 0,
        "predictions_evaluated": total_evaluated or 0,
        "prediction_accuracy": round(accuracy, 2)
    }
