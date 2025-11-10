"""
Tutor Goals API endpoints.

Provides goal setting, tracking, and recommendation features for tutors.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from pydantic import BaseModel

from .config import settings
from ..database.database import get_async_session
from src.database.models import (
    Tutor,
    TutorPerformanceMetric,
    MetricWindow,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=f"{settings.api_prefix}/tutor-goals", tags=["Tutor Goals"])


# In-memory storage for goals (in production, this should be in the database)
# Structure: {tutor_id: [goal_dict, ...]}
GOALS_STORE = {}


class GoalType(str):
    """Types of tutor goals."""
    RATING_IMPROVEMENT = "rating_improvement"
    SESSION_VOLUME = "session_volume"
    ON_TIME_PERCENTAGE = "on_time_percentage"
    FIRST_SESSION_SUCCESS = "first_session_success"
    STUDENT_RETENTION = "student_retention"
    ENGAGEMENT_SCORE = "engagement_score"
    CUSTOM = "custom"


class GoalStatus(str):
    """Goal completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    EXPIRED = "expired"


class GoalCreate(BaseModel):
    """Request to create a new goal."""
    goal_type: str
    target_value: float
    target_date: str
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None


class GoalUpdate(BaseModel):
    """Request to update a goal."""
    target_value: Optional[float] = None
    target_date: Optional[str] = None
    status: Optional[str] = None


class GoalResponse(BaseModel):
    """Tutor goal response."""
    goal_id: str
    goal_type: str
    title: str
    description: str
    target_value: float
    current_value: float
    progress_percentage: float
    target_date: str
    status: str
    created_date: str


class GoalsListResponse(BaseModel):
    """Response containing all tutor goals."""
    success: bool
    tutor_id: str
    goals: List[GoalResponse]
    active_goals: int
    achieved_goals: int
    recommended_goals: List[dict]
    timestamp: str


def get_goal_details(goal_type: str) -> tuple:
    """Get title and description for a goal type."""
    goal_info = {
        GoalType.RATING_IMPROVEMENT: (
            "Improve Average Rating",
            "Increase your average student rating to build stronger relationships"
        ),
        GoalType.SESSION_VOLUME: (
            "Increase Session Volume",
            "Complete more tutoring sessions to help more students"
        ),
        GoalType.ON_TIME_PERCENTAGE: (
            "Improve Punctuality",
            "Increase your on-time arrival percentage for sessions"
        ),
        GoalType.FIRST_SESSION_SUCCESS: (
            "First Session Excellence",
            "Improve success rate with new students in their first session"
        ),
        GoalType.STUDENT_RETENTION: (
            "Boost Student Retention",
            "Increase the percentage of students who continue working with you"
        ),
        GoalType.ENGAGEMENT_SCORE: (
            "Enhance Student Engagement",
            "Improve your average student engagement score"
        ),
        GoalType.CUSTOM: (
            "Custom Goal",
            "Personal development goal"
        )
    }
    return goal_info.get(goal_type, ("Custom Goal", "Personal development goal"))


async def calculate_current_value(
    tutor_id: str,
    goal_type: str,
    db: AsyncSession
) -> float:
    """Calculate current value for a goal based on latest metrics."""
    # Get latest metrics
    result = await db.execute(
        select(TutorPerformanceMetric)
        .where(
            TutorPerformanceMetric.tutor_id == tutor_id,
            TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY
        )
        .order_by(desc(TutorPerformanceMetric.calculation_date))
        .limit(1)
    )
    metric = result.scalar_one_or_none()

    if not metric:
        return 0.0

    # Map goal types to metrics
    if goal_type == GoalType.RATING_IMPROVEMENT:
        return metric.avg_rating or 0.0
    elif goal_type == GoalType.SESSION_VOLUME:
        return float(metric.sessions_completed or 0)
    elif goal_type == GoalType.ON_TIME_PERCENTAGE:
        # Calculate from reschedule rate (inverse)
        return (1.0 - (metric.reschedule_rate or 0.0)) * 100
    elif goal_type == GoalType.FIRST_SESSION_SUCCESS:
        return (metric.first_session_success_rate or 0.0) * 100
    elif goal_type == GoalType.STUDENT_RETENTION:
        # Placeholder - would need separate calculation
        return 75.0
    elif goal_type == GoalType.ENGAGEMENT_SCORE:
        return metric.engagement_score or 0.0
    else:
        return 0.0


def determine_goal_status(
    current_value: float,
    target_value: float,
    target_date: datetime
) -> str:
    """Determine goal status based on progress and timeline."""
    if datetime.now() > target_date:
        if current_value >= target_value:
            return GoalStatus.ACHIEVED
        else:
            return GoalStatus.EXPIRED
    elif current_value >= target_value:
        return GoalStatus.ACHIEVED
    elif current_value > 0:
        return GoalStatus.IN_PROGRESS
    else:
        return GoalStatus.NOT_STARTED


@router.get("/{tutor_id}", response_model=GoalsListResponse)
async def get_tutor_goals(
    tutor_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get all goals for a specific tutor.

    Returns active goals, achieved goals, and recommended goals
    based on performance metrics.

    Args:
        tutor_id: The tutor's unique identifier
        db: Database session

    Returns:
        List of goals with progress tracking and recommendations
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

        # Get tutor's goals from store
        tutor_goals = GOALS_STORE.get(tutor_id, [])

        # Update current values and status for all goals
        goals_responses = []
        for goal in tutor_goals:
            current_value = await calculate_current_value(tutor_id, goal["goal_type"], db)
            target_date = datetime.fromisoformat(goal["target_date"])
            status = determine_goal_status(current_value, goal["target_value"], target_date)

            # Update status in store
            goal["status"] = status

            progress_percentage = min((current_value / goal["target_value"]) * 100, 100.0)

            goals_responses.append(GoalResponse(
                goal_id=goal["goal_id"],
                goal_type=goal["goal_type"],
                title=goal["title"],
                description=goal["description"],
                target_value=goal["target_value"],
                current_value=current_value,
                progress_percentage=progress_percentage,
                target_date=goal["target_date"],
                status=status,
                created_date=goal["created_date"]
            ))

        # Get latest metrics for recommendations
        metrics_result = await db.execute(
            select(TutorPerformanceMetric)
            .where(
                TutorPerformanceMetric.tutor_id == tutor_id,
                TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY
            )
            .order_by(desc(TutorPerformanceMetric.calculation_date))
            .limit(1)
        )
        latest_metric = metrics_result.scalar_one_or_none()

        # Generate recommended goals based on performance
        recommended_goals = []
        if latest_metric:
            # Recommend rating improvement if below 4.5
            if latest_metric.avg_rating and latest_metric.avg_rating < 4.5:
                recommended_goals.append({
                    "goal_type": GoalType.RATING_IMPROVEMENT,
                    "title": "Improve Average Rating",
                    "description": "Increase your rating to 4.5 or higher",
                    "suggested_target": 4.5,
                    "current_value": latest_metric.avg_rating,
                    "priority": "high"
                })

            # Recommend session volume if below average
            if latest_metric.sessions_completed and latest_metric.sessions_completed < 20:
                recommended_goals.append({
                    "goal_type": GoalType.SESSION_VOLUME,
                    "title": "Increase Session Volume",
                    "description": "Complete 30 sessions this month",
                    "suggested_target": 30,
                    "current_value": latest_metric.sessions_completed,
                    "priority": "medium"
                })

            # Recommend first session success if below 80%
            if latest_metric.first_session_success_rate and latest_metric.first_session_success_rate < 0.8:
                recommended_goals.append({
                    "goal_type": GoalType.FIRST_SESSION_SUCCESS,
                    "title": "First Session Excellence",
                    "description": "Achieve 85% success rate with new students",
                    "suggested_target": 85.0,
                    "current_value": latest_metric.first_session_success_rate * 100,
                    "priority": "high"
                })

            # Recommend engagement improvement if below 8.0
            if latest_metric.engagement_score and latest_metric.engagement_score < 8.0:
                recommended_goals.append({
                    "goal_type": GoalType.ENGAGEMENT_SCORE,
                    "title": "Enhance Student Engagement",
                    "description": "Achieve 8.5 average engagement score",
                    "suggested_target": 8.5,
                    "current_value": latest_metric.engagement_score,
                    "priority": "medium"
                })

        # Count active and achieved goals
        active_goals = sum(1 for g in goals_responses if g.status in [GoalStatus.NOT_STARTED, GoalStatus.IN_PROGRESS])
        achieved_goals = sum(1 for g in goals_responses if g.status == GoalStatus.ACHIEVED)

        return GoalsListResponse(
            success=True,
            tutor_id=tutor_id,
            goals=goals_responses,
            active_goals=active_goals,
            achieved_goals=achieved_goals,
            recommended_goals=recommended_goals,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get goals for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tutor goals"
        )


@router.post("/{tutor_id}", response_model=GoalResponse)
async def create_tutor_goal(
    tutor_id: str,
    goal: GoalCreate = Body(...),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new goal for a tutor.

    Args:
        tutor_id: The tutor's unique identifier
        goal: Goal creation data
        db: Database session

    Returns:
        Created goal with initial progress
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

        # Get or create goal title/description
        if goal.goal_type == GoalType.CUSTOM:
            title = goal.custom_title or "Custom Goal"
            description = goal.custom_description or "Personal development goal"
        else:
            title, description = get_goal_details(goal.goal_type)

        # Calculate current value
        current_value = await calculate_current_value(tutor_id, goal.goal_type, db)

        # Create goal
        goal_id = str(uuid4())
        created_date = datetime.now()
        target_date = datetime.fromisoformat(goal.target_date)

        new_goal = {
            "goal_id": goal_id,
            "goal_type": goal.goal_type,
            "title": title,
            "description": description,
            "target_value": goal.target_value,
            "target_date": goal.target_date,
            "status": determine_goal_status(current_value, goal.target_value, target_date),
            "created_date": created_date.isoformat()
        }

        # Store goal
        if tutor_id not in GOALS_STORE:
            GOALS_STORE[tutor_id] = []
        GOALS_STORE[tutor_id].append(new_goal)

        progress_percentage = min((current_value / goal.target_value) * 100, 100.0)

        return GoalResponse(
            goal_id=goal_id,
            goal_type=goal.goal_type,
            title=title,
            description=description,
            target_value=goal.target_value,
            current_value=current_value,
            progress_percentage=progress_percentage,
            target_date=goal.target_date,
            status=new_goal["status"],
            created_date=new_goal["created_date"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create goal for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tutor goal"
        )


@router.delete("/{tutor_id}/{goal_id}")
async def delete_tutor_goal(
    tutor_id: str,
    goal_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete a goal for a tutor.

    Args:
        tutor_id: The tutor's unique identifier
        goal_id: The goal's unique identifier
        db: Database session

    Returns:
        Success status
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

        # Find and remove goal
        if tutor_id in GOALS_STORE:
            goals = GOALS_STORE[tutor_id]
            initial_length = len(goals)
            GOALS_STORE[tutor_id] = [g for g in goals if g["goal_id"] != goal_id]

            if len(GOALS_STORE[tutor_id]) == initial_length:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Goal {goal_id} not found"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal {goal_id} not found"
            )

        return {
            "success": True,
            "message": "Goal deleted successfully",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete goal {goal_id} for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tutor goal"
        )
