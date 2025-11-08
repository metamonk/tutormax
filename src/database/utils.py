"""
Database utility functions for TutorMax.
Provides helpers for common database operations.
"""

from typing import List, Optional, Type, TypeVar, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import (
    Tutor,
    Student,
    Session,
    StudentFeedback,
    TutorPerformanceMetric,
    ChurnPrediction,
    Intervention,
    TutorEvent,
    TutorStatus,
    RiskLevel,
    MetricWindow,
)

T = TypeVar('T')


# Tutor queries


async def get_tutor_by_id(
    db: AsyncSession,
    tutor_id: str,
    with_relations: bool = False
) -> Optional[Tutor]:
    """
    Get a tutor by ID.

    Args:
        db: Database session
        tutor_id: Tutor ID
        with_relations: Load related sessions, feedback, etc.

    Returns:
        Tutor or None if not found
    """
    query = select(Tutor).where(Tutor.tutor_id == tutor_id)

    if with_relations:
        query = query.options(
            selectinload(Tutor.sessions),
            selectinload(Tutor.feedback),
            selectinload(Tutor.performance_metrics),
            selectinload(Tutor.churn_predictions),
        )

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_active_tutors(db: AsyncSession) -> List[Tutor]:
    """Get all active tutors."""
    result = await db.execute(
        select(Tutor).where(Tutor.status == TutorStatus.ACTIVE)
    )
    return list(result.scalars().all())


async def get_tutors_by_risk_level(
    db: AsyncSession,
    risk_level: RiskLevel,
    limit: Optional[int] = None
) -> List[Tutor]:
    """
    Get tutors with a specific churn risk level.

    Args:
        db: Database session
        risk_level: Risk level to filter by
        limit: Maximum number of tutors to return

    Returns:
        List of tutors
    """
    # Subquery to get latest churn prediction per tutor
    latest_predictions = (
        select(
            ChurnPrediction.tutor_id,
            func.max(ChurnPrediction.prediction_date).label('latest_date')
        )
        .group_by(ChurnPrediction.tutor_id)
        .subquery()
    )

    query = (
        select(Tutor)
        .join(ChurnPrediction, Tutor.tutor_id == ChurnPrediction.tutor_id)
        .join(
            latest_predictions,
            and_(
                ChurnPrediction.tutor_id == latest_predictions.c.tutor_id,
                ChurnPrediction.prediction_date == latest_predictions.c.latest_date
            )
        )
        .where(ChurnPrediction.risk_level == risk_level)
        .order_by(ChurnPrediction.churn_score.desc())
    )

    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


# Session queries


async def get_tutor_sessions(
    db: AsyncSession,
    tutor_id: str,
    days_back: Optional[int] = None,
    include_feedback: bool = False
) -> List[Session]:
    """
    Get sessions for a tutor.

    Args:
        db: Database session
        tutor_id: Tutor ID
        days_back: Only include sessions from last N days
        include_feedback: Load feedback with sessions

    Returns:
        List of sessions
    """
    query = select(Session).where(Session.tutor_id == tutor_id)

    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.where(Session.scheduled_start >= cutoff_date)

    if include_feedback:
        query = query.options(selectinload(Session.feedback))

    query = query.order_by(Session.scheduled_start.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_first_sessions(
    db: AsyncSession,
    tutor_id: str,
    days_back: Optional[int] = None
) -> List[Session]:
    """Get first sessions (session_number = 1) for a tutor."""
    query = (
        select(Session)
        .where(
            and_(
                Session.tutor_id == tutor_id,
                Session.session_number == 1
            )
        )
    )

    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.where(Session.scheduled_start >= cutoff_date)

    result = await db.execute(query)
    return list(result.scalars().all())


# Performance metrics queries


async def get_latest_performance_metrics(
    db: AsyncSession,
    tutor_id: str,
    window: Optional[MetricWindow] = None
) -> Optional[TutorPerformanceMetric]:
    """
    Get the most recent performance metrics for a tutor.

    Args:
        db: Database session
        tutor_id: Tutor ID
        window: Specific time window (e.g., 30day)

    Returns:
        Latest performance metric or None
    """
    query = (
        select(TutorPerformanceMetric)
        .where(TutorPerformanceMetric.tutor_id == tutor_id)
    )

    if window:
        query = query.where(TutorPerformanceMetric.window == window)

    query = query.order_by(TutorPerformanceMetric.calculation_date.desc()).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_all_performance_metrics(
    db: AsyncSession,
    tutor_id: str,
    window: Optional[MetricWindow] = None
) -> List[TutorPerformanceMetric]:
    """Get all performance metrics for a tutor, optionally filtered by window."""
    query = (
        select(TutorPerformanceMetric)
        .where(TutorPerformanceMetric.tutor_id == tutor_id)
    )

    if window:
        query = query.where(TutorPerformanceMetric.window == window)

    query = query.order_by(TutorPerformanceMetric.calculation_date.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


# Churn prediction queries


async def get_latest_churn_prediction(
    db: AsyncSession,
    tutor_id: str
) -> Optional[ChurnPrediction]:
    """Get the most recent churn prediction for a tutor."""
    result = await db.execute(
        select(ChurnPrediction)
        .where(ChurnPrediction.tutor_id == tutor_id)
        .order_by(ChurnPrediction.prediction_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_high_risk_tutors(
    db: AsyncSession,
    min_score: int = 51,
    limit: Optional[int] = None
) -> List[tuple[Tutor, ChurnPrediction]]:
    """
    Get tutors with high churn risk scores.

    Args:
        db: Database session
        min_score: Minimum churn score (default 51 = high risk)
        limit: Maximum number to return

    Returns:
        List of (Tutor, ChurnPrediction) tuples
    """
    # Subquery for latest predictions
    latest_predictions = (
        select(
            ChurnPrediction.tutor_id,
            func.max(ChurnPrediction.prediction_date).label('latest_date')
        )
        .group_by(ChurnPrediction.tutor_id)
        .subquery()
    )

    query = (
        select(Tutor, ChurnPrediction)
        .join(ChurnPrediction, Tutor.tutor_id == ChurnPrediction.tutor_id)
        .join(
            latest_predictions,
            and_(
                ChurnPrediction.tutor_id == latest_predictions.c.tutor_id,
                ChurnPrediction.prediction_date == latest_predictions.c.latest_date
            )
        )
        .where(ChurnPrediction.churn_score >= min_score)
        .order_by(ChurnPrediction.churn_score.desc())
    )

    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    return list(result.all())


# Intervention queries


async def get_pending_interventions(
    db: AsyncSession,
    tutor_id: Optional[str] = None,
    assigned_to: Optional[str] = None
) -> List[Intervention]:
    """
    Get pending interventions.

    Args:
        db: Database session
        tutor_id: Filter by tutor
        assigned_to: Filter by assignee

    Returns:
        List of pending interventions
    """
    from src.database.models import InterventionStatus

    query = select(Intervention).where(
        Intervention.status == InterventionStatus.PENDING
    )

    if tutor_id:
        query = query.where(Intervention.tutor_id == tutor_id)

    if assigned_to:
        query = query.where(Intervention.assigned_to == assigned_to)

    query = query.order_by(Intervention.recommended_date.asc())

    result = await db.execute(query)
    return list(result.scalars().all())


# Event queries


async def get_tutor_events(
    db: AsyncSession,
    tutor_id: str,
    event_type: Optional[str] = None,
    days_back: Optional[int] = None
) -> List[TutorEvent]:
    """
    Get events for a tutor.

    Args:
        db: Database session
        tutor_id: Tutor ID
        event_type: Filter by event type
        days_back: Only include events from last N days

    Returns:
        List of events
    """
    query = select(TutorEvent).where(TutorEvent.tutor_id == tutor_id)

    if event_type:
        query = query.where(TutorEvent.event_type == event_type)

    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.where(TutorEvent.event_timestamp >= cutoff_date)

    query = query.order_by(TutorEvent.event_timestamp.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


# Statistics and aggregations


async def get_tutor_statistics(
    db: AsyncSession,
    tutor_id: str,
    days_back: int = 30
) -> dict:
    """
    Get aggregated statistics for a tutor.

    Args:
        db: Database session
        tutor_id: Tutor ID
        days_back: Number of days to look back

    Returns:
        Dictionary of statistics
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    # Count sessions
    session_count = await db.execute(
        select(func.count(Session.session_id))
        .where(
            and_(
                Session.tutor_id == tutor_id,
                Session.scheduled_start >= cutoff_date
            )
        )
    )

    # Average rating
    avg_rating = await db.execute(
        select(func.avg(StudentFeedback.overall_rating))
        .join(Session, StudentFeedback.session_id == Session.session_id)
        .where(
            and_(
                Session.tutor_id == tutor_id,
                Session.scheduled_start >= cutoff_date
            )
        )
    )

    # No-show count
    no_show_count = await db.execute(
        select(func.count(Session.session_id))
        .where(
            and_(
                Session.tutor_id == tutor_id,
                Session.scheduled_start >= cutoff_date,
                Session.no_show == True
            )
        )
    )

    # Reschedule count
    reschedule_count = await db.execute(
        select(func.count(Session.session_id))
        .where(
            and_(
                Session.tutor_id == tutor_id,
                Session.scheduled_start >= cutoff_date,
                Session.tutor_initiated_reschedule == True
            )
        )
    )

    return {
        "tutor_id": tutor_id,
        "days_back": days_back,
        "total_sessions": session_count.scalar() or 0,
        "average_rating": round(avg_rating.scalar() or 0, 2),
        "no_shows": no_show_count.scalar() or 0,
        "reschedules": reschedule_count.scalar() or 0,
    }
