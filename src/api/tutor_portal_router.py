"""
Tutor Portal API endpoints.

Provides REST endpoints for tutors to view their own performance metrics,
session ratings, and recommended training modules.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from .config import settings
from ..database.database import get_async_session
from src.database.models import (
    Tutor,
    TutorPerformanceMetric,
    Session as SessionModel,
    StudentFeedback,
    Intervention,
    MetricWindow,
    InterventionType,
    InterventionStatus,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=f"{settings.api_prefix}/tutors", tags=["Tutor Portal"])


@router.get("/{tutor_id}/metrics")
async def get_tutor_metrics(
    tutor_id: str,
    window: Optional[str] = "30day",
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get performance metrics for a specific tutor.

    Returns the tutor's performance tier, ratings, and key metrics
    for the specified time window.

    Args:
        tutor_id: The tutor's unique identifier
        window: Time window (7day, 30day, 90day). Defaults to 30day.
        db: Database session

    Returns:
        Tutor performance metrics including tier, ratings, and KPIs
    """
    try:
        # Validate window parameter
        if window not in ["7day", "30day", "90day"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid window parameter. Must be one of: 7day, 30day, 90day"
            )

        # Check if tutor exists
        result = await db.execute(
            select(Tutor).where(Tutor.tutor_id == tutor_id)
        )
        tutor = result.scalar_one_or_none()

        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        # Get latest metrics for the specified window
        result = await db.execute(
            select(TutorPerformanceMetric)
            .where(
                TutorPerformanceMetric.tutor_id == tutor_id,
                TutorPerformanceMetric.window == MetricWindow(window)
            )
            .order_by(desc(TutorPerformanceMetric.calculation_date))
            .limit(1)
        )
        metric = result.scalar_one_or_none()

        if not metric:
            # Return default structure if no metrics calculated yet
            return {
                "success": True,
                "tutor_id": tutor_id,
                "tutor_name": tutor.name,
                "window": window,
                "message": "No metrics available yet. Complete more sessions to see your performance.",
                "metrics": None,
                "timestamp": datetime.now().isoformat()
            }

        return {
            "success": True,
            "tutor_id": tutor_id,
            "tutor_name": tutor.name,
            "window": window,
            "calculation_date": metric.calculation_date.isoformat(),
            "metrics": {
                "performance_tier": metric.performance_tier.value if metric.performance_tier else None,
                "sessions_completed": metric.sessions_completed,
                "avg_rating": round(metric.avg_rating, 2) if metric.avg_rating else None,
                "first_session_success_rate": round(metric.first_session_success_rate, 1) if metric.first_session_success_rate else None,
                "reschedule_rate": round(metric.reschedule_rate, 1) if metric.reschedule_rate else None,
                "no_show_count": metric.no_show_count,
                "engagement_score": round(metric.engagement_score, 2) if metric.engagement_score else None,
                "learning_objectives_met_pct": round(metric.learning_objectives_met_pct, 1) if metric.learning_objectives_met_pct else None,
                "response_time_avg_minutes": round(metric.response_time_avg_minutes, 1) if metric.response_time_avg_minutes else None,
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tutor metrics"
        )


@router.get("/{tutor_id}/sessions")
async def get_tutor_sessions(
    tutor_id: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get recent sessions with ratings for a specific tutor.

    Returns a list of the tutor's recent sessions along with student
    feedback and ratings.

    Args:
        tutor_id: The tutor's unique identifier
        limit: Maximum number of sessions to return (default: 20)
        offset: Number of sessions to skip (for pagination)
        db: Database session

    Returns:
        List of sessions with ratings and feedback
    """
    try:
        # Check if tutor exists
        result = await db.execute(
            select(Tutor).where(Tutor.tutor_id == tutor_id)
        )
        tutor = result.scalar_one_or_none()

        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        # Get sessions with feedback
        sessions_query = (
            select(SessionModel, StudentFeedback)
            .outerjoin(StudentFeedback, SessionModel.session_id == StudentFeedback.session_id)
            .where(SessionModel.tutor_id == tutor_id)
            .order_by(desc(SessionModel.scheduled_start))
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(sessions_query)
        results = result.all()

        # Get total count for pagination
        count_result = await db.execute(
            select(func.count()).select_from(SessionModel).where(SessionModel.tutor_id == tutor_id)
        )
        total_count = count_result.scalar()

        sessions = []
        for session, feedback in results:
            session_data = {
                "session_id": session.session_id,
                "student_id": session.student_id,
                "session_number": session.session_number,
                "scheduled_start": session.scheduled_start.isoformat(),
                "actual_start": session.actual_start.isoformat() if session.actual_start else None,
                "duration_minutes": session.duration_minutes,
                "subject": session.subject,
                "session_type": session.session_type.value,
                "engagement_score": round(session.engagement_score, 2) if session.engagement_score else None,
                "learning_objectives_met": session.learning_objectives_met,
                "no_show": session.no_show,
                "rating": None,
                "feedback_text": None,
            }

            if feedback:
                session_data.update({
                    "rating": feedback.overall_rating,
                    "feedback_text": feedback.feedback_text,
                    "would_recommend": feedback.would_recommend,
                })

            sessions.append(session_data)

        return {
            "success": True,
            "tutor_id": tutor_id,
            "sessions": sessions,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sessions for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tutor sessions"
        )


@router.get("/{tutor_id}/recommendations")
async def get_tutor_recommendations(
    tutor_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get recommended training modules and interventions for a specific tutor.

    Returns personalized recommendations based on the tutor's performance
    metrics and areas for improvement.

    Args:
        tutor_id: The tutor's unique identifier
        db: Database session

    Returns:
        Recommended training modules and growth areas
    """
    try:
        # Check if tutor exists
        result = await db.execute(
            select(Tutor).where(Tutor.tutor_id == tutor_id)
        )
        tutor = result.scalar_one_or_none()

        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        # Get latest performance metrics
        metric_result = await db.execute(
            select(TutorPerformanceMetric)
            .where(TutorPerformanceMetric.tutor_id == tutor_id)
            .order_by(desc(TutorPerformanceMetric.calculation_date))
            .limit(1)
        )
        metric = metric_result.scalar_one_or_none()

        # Get pending training interventions
        interventions_result = await db.execute(
            select(Intervention)
            .where(
                Intervention.tutor_id == tutor_id,
                Intervention.intervention_type == InterventionType.TRAINING_MODULE,
                Intervention.status.in_([InterventionStatus.PENDING, InterventionStatus.IN_PROGRESS])
            )
            .order_by(desc(Intervention.created_at))
        )
        interventions = interventions_result.scalars().all()

        # Build recommendations based on metrics
        recommendations = []
        growth_areas = []

        if metric:
            # Analyze metrics and suggest training
            if metric.avg_rating and metric.avg_rating < 4.0:
                recommendations.append({
                    "title": "Improving Student Satisfaction",
                    "description": "Learn strategies to enhance student engagement and satisfaction",
                    "priority": "high",
                    "category": "student_satisfaction",
                    "estimated_time": "45 minutes"
                })
                growth_areas.append("Student Satisfaction")

            if metric.first_session_success_rate and metric.first_session_success_rate < 0.8:
                recommendations.append({
                    "title": "First Session Excellence",
                    "description": "Master techniques for creating positive first impressions and building rapport",
                    "priority": "high",
                    "category": "first_session",
                    "estimated_time": "30 minutes"
                })
                growth_areas.append("First Session Success")

            if metric.reschedule_rate and metric.reschedule_rate > 0.15:
                recommendations.append({
                    "title": "Time Management & Scheduling",
                    "description": "Improve scheduling practices and reduce reschedules",
                    "priority": "medium",
                    "category": "scheduling",
                    "estimated_time": "30 minutes"
                })
                growth_areas.append("Time Management")

            if metric.engagement_score and metric.engagement_score < 7.0:
                recommendations.append({
                    "title": "Student Engagement Strategies",
                    "description": "Advanced techniques to keep students motivated and engaged",
                    "priority": "medium",
                    "category": "engagement",
                    "estimated_time": "60 minutes"
                })
                growth_areas.append("Student Engagement")

            if metric.learning_objectives_met_pct and metric.learning_objectives_met_pct < 0.8:
                recommendations.append({
                    "title": "Goal-Oriented Tutoring",
                    "description": "Strategies for effectively meeting learning objectives",
                    "priority": "high",
                    "category": "learning_objectives",
                    "estimated_time": "45 minutes"
                })
                growth_areas.append("Learning Objectives")

        # Add any existing training interventions
        for intervention in interventions:
            recommendations.append({
                "title": intervention.title,
                "description": intervention.description,
                "priority": "assigned",
                "category": "intervention",
                "status": intervention.status.value,
                "assigned_date": intervention.created_at.isoformat(),
                "due_date": intervention.due_date.isoformat() if intervention.due_date else None,
            })

        # If no specific recommendations, provide general growth suggestions
        if not recommendations:
            recommendations.append({
                "title": "Advanced Tutoring Techniques",
                "description": "Continue developing your skills with advanced tutoring strategies",
                "priority": "low",
                "category": "general",
                "estimated_time": "60 minutes"
            })

        return {
            "success": True,
            "tutor_id": tutor_id,
            "tutor_name": tutor.name,
            "performance_tier": metric.performance_tier.value if metric and metric.performance_tier else None,
            "recommendations": recommendations,
            "growth_areas": growth_areas,
            "message": "Keep up the great work!" if not growth_areas else "Focus on these areas to improve your performance",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tutor recommendations"
        )


@router.get("/{tutor_id}/profile")
async def get_tutor_profile(
    tutor_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get basic profile information for a tutor.

    Args:
        tutor_id: The tutor's unique identifier
        db: Database session

    Returns:
        Tutor profile information
    """
    try:
        result = await db.execute(
            select(Tutor).where(Tutor.tutor_id == tutor_id)
        )
        tutor = result.scalar_one_or_none()

        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        return {
            "success": True,
            "tutor_id": tutor.tutor_id,
            "name": tutor.name,
            "email": tutor.email,
            "onboarding_date": tutor.onboarding_date.isoformat(),
            "status": tutor.status.value,
            "subjects": tutor.subjects,
            "education_level": tutor.education_level,
            "location": tutor.location,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tutor profile"
        )


@router.get("/{tutor_id}/feedback")
async def get_tutor_feedback(
    tutor_id: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get student feedback for a specific tutor's sessions.

    Returns a list of feedback with ratings from students for this tutor's sessions.

    Args:
        tutor_id: The tutor's unique identifier
        limit: Maximum number of feedback entries to return (default: 20)
        offset: Number of entries to skip (for pagination)
        db: Database session

    Returns:
        List of feedback with ratings and session details
    """
    try:
        # Check if tutor exists
        result = await db.execute(
            select(Tutor).where(Tutor.tutor_id == tutor_id)
        )
        tutor = result.scalar_one_or_none()

        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        # Get feedback with session information
        feedback_query = (
            select(StudentFeedback, SessionModel)
            .join(SessionModel, StudentFeedback.session_id == SessionModel.session_id)
            .where(StudentFeedback.tutor_id == tutor_id)
            .order_by(desc(StudentFeedback.feedback_date))
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(feedback_query)
        results = result.all()

        # Get total count for pagination
        count_result = await db.execute(
            select(func.count()).select_from(StudentFeedback).where(StudentFeedback.tutor_id == tutor_id)
        )
        total_count = count_result.scalar()

        feedback_list = []
        for feedback, session in results:
            feedback_data = {
                "feedback_id": feedback.feedback_id,
                "session_id": feedback.session_id,
                "student_id": feedback.student_id,
                "session_date": session.scheduled_start.isoformat(),
                "rating": feedback.overall_rating,
                "feedback_text": feedback.feedback_text,
                "would_recommend": feedback.would_recommend,
                "subject": session.subject,
                "communication_rating": feedback.communication_rating,
                "knowledge_rating": feedback.knowledge_rating,
                "patience_rating": feedback.patience_rating,
                "preparedness_rating": feedback.preparedness_rating,
                "feedback_date": feedback.feedback_date.isoformat(),
            }
            feedback_list.append(feedback_data)

        return {
            "success": True,
            "tutor_id": tutor_id,
            "feedback": feedback_list,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feedback for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tutor feedback"
        )
