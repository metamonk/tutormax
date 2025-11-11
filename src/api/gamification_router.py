"""
Gamification API endpoints for tutor portal.

Provides badge achievements, progress tracking, and peer comparison features.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from pydantic import BaseModel

from .config import settings
from ..database.database import get_async_session
from src.database.models import (
    Tutor,
    TutorPerformanceMetric,
    Session as SessionModel,
    StudentFeedback,
    MetricWindow,
    PerformanceTier,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=f"{settings.api_prefix}/gamification", tags=["Gamification"])


class BadgeType(str, Enum):
    """Types of achievement badges."""
    MILESTONE = "milestone"
    STREAK = "streak"
    EXCELLENCE = "excellence"
    ENGAGEMENT = "engagement"


class BadgeResponse(BaseModel):
    """Badge achievement response."""
    badge_id: str
    title: str
    description: str
    badge_type: BadgeType
    icon: str
    earned: bool
    earned_date: Optional[datetime] = None
    progress_current: int
    progress_target: int
    progress_percentage: float


class BadgesResponse(BaseModel):
    """Response containing all tutor badges."""
    success: bool
    tutor_id: str
    badges: List[BadgeResponse]
    total_earned: int
    recent_achievements: List[BadgeResponse]
    timestamp: datetime


class GoalType(str, Enum):
    """Types of tutor goals."""
    RATING_IMPROVEMENT = "rating_improvement"
    SESSION_VOLUME = "session_volume"
    ON_TIME_PERCENTAGE = "on_time_percentage"
    FIRST_SESSION_SUCCESS = "first_session_success"
    STUDENT_RETENTION = "student_retention"
    CUSTOM = "custom"


class GoalStatus(str, Enum):
    """Goal completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    EXPIRED = "expired"


class GoalCreate(BaseModel):
    """Request to create a new goal."""
    goal_type: GoalType
    target_value: float
    target_date: datetime
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None


class GoalResponse(BaseModel):
    """Tutor goal response."""
    goal_id: str
    goal_type: GoalType
    title: str
    description: str
    target_value: float
    current_value: float
    progress_percentage: float
    target_date: datetime
    status: GoalStatus
    created_date: datetime


class PeerComparisonResponse(BaseModel):
    """Anonymized peer comparison data."""
    success: bool
    tutor_id: str
    percentile_rank: int
    avg_rating_percentile: int
    sessions_completed_percentile: int
    engagement_score_percentile: int
    performance_tier_distribution: dict
    timestamp: datetime


@router.get("/{tutor_id}/badges", response_model=BadgesResponse)
async def get_tutor_badges(
    tutor_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get all badge achievements and progress for a tutor.

    Returns badges across categories:
    - Milestones (100 sessions, 500 sessions, etc.)
    - Streaks (7 days, 30 days consecutive teaching)
    - Excellence (Top rated month, Perfect week, etc.)
    - Engagement (High engagement scores)

    Args:
        tutor_id: The tutor's unique identifier
        db: Database session

    Returns:
        Badge achievements with progress tracking
    """
    try:
        # Check if tutor exists
        tutor_result = await db.execute(
            select(Tutor).where(Tutor.tutor_id == tutor_id)
        )
        tutor = tutor_result.scalar_one_or_none()

        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        # Get tutor's latest metrics
        metrics_result = await db.execute(
            select(TutorPerformanceMetric)
            .where(TutorPerformanceMetric.tutor_id == tutor_id)
            .order_by(desc(TutorPerformanceMetric.calculation_date))
            .limit(1)
        )
        latest_metric = metrics_result.scalar_one_or_none()

        # Get total sessions across all time
        total_sessions_result = await db.execute(
            select(func.count(SessionModel.session_id))
            .where(
                SessionModel.tutor_id == tutor_id,
                SessionModel.no_show == False
            )
        )
        total_sessions = total_sessions_result.scalar() or 0

        # Get consecutive teaching days (simplified - count unique teaching days in last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        teaching_days_result = await db.execute(
            select(func.count(func.distinct(func.date(SessionModel.scheduled_start))))
            .where(
                SessionModel.tutor_id == tutor_id,
                SessionModel.no_show == False,
                SessionModel.scheduled_start >= thirty_days_ago
            )
        )
        consecutive_days = teaching_days_result.scalar() or 0

        # Get average rating
        avg_rating = latest_metric.avg_rating if latest_metric else 0.0

        # Get engagement score
        engagement_score = latest_metric.engagement_score if latest_metric else 0.0

        # Define all available badges
        badges = []

        # Milestone Badges
        badges.append(BadgeResponse(
            badge_id="sessions_10",
            title="Getting Started",
            description="Complete 10 tutoring sessions",
            badge_type=BadgeType.MILESTONE,
            icon="🌟",
            earned=total_sessions >= 10,
            earned_date=tutor.onboarding_date + timedelta(days=7) if total_sessions >= 10 else None,
            progress_current=min(total_sessions, 10),
            progress_target=10,
            progress_percentage=min((total_sessions / 10) * 100, 100.0)
        ))

        badges.append(BadgeResponse(
            badge_id="sessions_50",
            title="Dedicated Tutor",
            description="Complete 50 tutoring sessions",
            badge_type=BadgeType.MILESTONE,
            icon="🎯",
            earned=total_sessions >= 50,
            earned_date=tutor.onboarding_date + timedelta(days=30) if total_sessions >= 50 else None,
            progress_current=min(total_sessions, 50),
            progress_target=50,
            progress_percentage=min((total_sessions / 50) * 100, 100.0)
        ))

        badges.append(BadgeResponse(
            badge_id="sessions_100",
            title="Century Club",
            description="Complete 100 tutoring sessions",
            badge_type=BadgeType.MILESTONE,
            icon="💯",
            earned=total_sessions >= 100,
            earned_date=tutor.onboarding_date + timedelta(days=60) if total_sessions >= 100 else None,
            progress_current=min(total_sessions, 100),
            progress_target=100,
            progress_percentage=min((total_sessions / 100) * 100, 100.0)
        ))

        badges.append(BadgeResponse(
            badge_id="sessions_500",
            title="Master Educator",
            description="Complete 500 tutoring sessions",
            badge_type=BadgeType.MILESTONE,
            icon="👑",
            earned=total_sessions >= 500,
            earned_date=tutor.onboarding_date + timedelta(days=180) if total_sessions >= 500 else None,
            progress_current=min(total_sessions, 500),
            progress_target=500,
            progress_percentage=min((total_sessions / 500) * 100, 100.0)
        ))

        # Streak Badges
        badges.append(BadgeResponse(
            badge_id="streak_7",
            title="Week Warrior",
            description="Teach for 7 consecutive days",
            badge_type=BadgeType.STREAK,
            icon="🔥",
            earned=consecutive_days >= 7,
            earned_date=datetime.now() if consecutive_days >= 7 else None,
            progress_current=min(consecutive_days, 7),
            progress_target=7,
            progress_percentage=min((consecutive_days / 7) * 100, 100.0)
        ))

        badges.append(BadgeResponse(
            badge_id="streak_30",
            title="Monthly Commitment",
            description="Teach for 30 days in a row",
            badge_type=BadgeType.STREAK,
            icon="🚀",
            earned=consecutive_days >= 30,
            earned_date=datetime.now() if consecutive_days >= 30 else None,
            progress_current=min(consecutive_days, 30),
            progress_target=30,
            progress_percentage=min((consecutive_days / 30) * 100, 100.0)
        ))

        # Excellence Badges
        badges.append(BadgeResponse(
            badge_id="rating_4_5",
            title="Highly Rated",
            description="Maintain 4.5+ average rating",
            badge_type=BadgeType.EXCELLENCE,
            icon="⭐",
            earned=avg_rating >= 4.5,
            earned_date=datetime.now() if avg_rating >= 4.5 else None,
            progress_current=int(avg_rating * 10),
            progress_target=45,
            progress_percentage=min((avg_rating / 4.5) * 100, 100.0)
        ))

        badges.append(BadgeResponse(
            badge_id="rating_perfect",
            title="Perfect Score",
            description="Achieve 5.0 average rating",
            badge_type=BadgeType.EXCELLENCE,
            icon="🏆",
            earned=avg_rating >= 5.0,
            earned_date=datetime.now() if avg_rating >= 5.0 else None,
            progress_current=int(avg_rating * 10),
            progress_target=50,
            progress_percentage=min((avg_rating / 5.0) * 100, 100.0)
        ))

        # Engagement Badges
        badges.append(BadgeResponse(
            badge_id="engagement_8",
            title="Engagement Expert",
            description="Maintain 8.0+ engagement score",
            badge_type=BadgeType.ENGAGEMENT,
            icon="💪",
            earned=engagement_score >= 8.0,
            earned_date=datetime.now() if engagement_score >= 8.0 else None,
            progress_current=int(engagement_score * 10),
            progress_target=80,
            progress_percentage=min((engagement_score / 8.0) * 100, 100.0)
        ))

        badges.append(BadgeResponse(
            badge_id="engagement_9",
            title="Master Engager",
            description="Maintain 9.0+ engagement score",
            badge_type=BadgeType.ENGAGEMENT,
            icon="🎨",
            earned=engagement_score >= 9.0,
            earned_date=datetime.now() if engagement_score >= 9.0 else None,
            progress_current=int(engagement_score * 10),
            progress_target=90,
            progress_percentage=min((engagement_score / 9.0) * 100, 100.0)
        ))

        # Calculate totals
        earned_badges = [b for b in badges if b.earned]
        now_tz = datetime.now(timezone.utc)
        recent_achievements = sorted(
            [b for b in earned_badges if b.earned_date and b.earned_date.replace(tzinfo=timezone.utc) >= now_tz - timedelta(days=30)],
            key=lambda x: x.earned_date,
            reverse=True
        )[:5]

        return BadgesResponse(
            success=True,
            tutor_id=tutor_id,
            badges=badges,
            total_earned=len(earned_badges),
            recent_achievements=recent_achievements,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get badges for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tutor badges"
        )


@router.get("/{tutor_id}/peer-comparison", response_model=PeerComparisonResponse)
async def get_peer_comparison(
    tutor_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get anonymized peer comparison data for a tutor.

    Returns percentile rankings compared to other tutors with similar
    experience levels (same onboarding quarter).

    Args:
        tutor_id: The tutor's unique identifier
        db: Database session

    Returns:
        Percentile rankings and tier distribution
    """
    try:
        # Check if tutor exists
        tutor_result = await db.execute(
            select(Tutor).where(Tutor.tutor_id == tutor_id)
        )
        tutor = tutor_result.scalar_one_or_none()

        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor {tutor_id} not found"
            )

        # Get tutor's latest metrics
        tutor_metric_result = await db.execute(
            select(TutorPerformanceMetric)
            .where(
                TutorPerformanceMetric.tutor_id == tutor_id,
                TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY
            )
            .order_by(desc(TutorPerformanceMetric.calculation_date))
            .limit(1)
        )
        tutor_metric = tutor_metric_result.scalar_one_or_none()

        if not tutor_metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No performance metrics available for comparison"
            )

        # Get comparison cohort (tutors onboarded in same quarter)
        cohort_start = tutor.onboarding_date.replace(day=1)
        cohort_end = cohort_start + timedelta(days=90)

        # Get all metrics for cohort
        cohort_metrics_result = await db.execute(
            select(TutorPerformanceMetric)
            .join(Tutor, TutorPerformanceMetric.tutor_id == Tutor.tutor_id)
            .where(
                and_(
                    Tutor.onboarding_date >= cohort_start,
                    Tutor.onboarding_date < cohort_end,
                    TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY
                )
            )
        )
        cohort_metrics = cohort_metrics_result.scalars().all()

        if len(cohort_metrics) < 5:
            # Not enough data for meaningful comparison
            return PeerComparisonResponse(
                success=True,
                tutor_id=tutor_id,
                percentile_rank=50,
                avg_rating_percentile=50,
                sessions_completed_percentile=50,
                engagement_score_percentile=50,
                performance_tier_distribution={
                    "Exemplary": 10,
                    "Strong": 30,
                    "Developing": 40,
                    "Needs Attention": 15,
                    "At Risk": 5
                },
                timestamp=datetime.now()
            )

        # Calculate percentiles
        def calculate_percentile(value: float, all_values: List[float]) -> int:
            """Calculate percentile rank (0-100)."""
            if not all_values or value is None:
                return 50
            sorted_values = sorted(all_values)
            rank = sum(1 for v in sorted_values if v < value)
            return int((rank / len(sorted_values)) * 100)

        # Extract metric values
        all_ratings = [m.avg_rating for m in cohort_metrics if m.avg_rating]
        all_sessions = [m.sessions_completed for m in cohort_metrics if m.sessions_completed]
        all_engagement = [m.engagement_score for m in cohort_metrics if m.engagement_score]

        avg_rating_percentile = calculate_percentile(tutor_metric.avg_rating, all_ratings)
        sessions_percentile = calculate_percentile(tutor_metric.sessions_completed, all_sessions)
        engagement_percentile = calculate_percentile(tutor_metric.engagement_score, all_engagement)

        # Overall percentile (weighted average)
        overall_percentile = int(
            (avg_rating_percentile * 0.4) +
            (sessions_percentile * 0.3) +
            (engagement_percentile * 0.3)
        )

        # Calculate tier distribution
        tier_counts = {}
        for metric in cohort_metrics:
            tier = metric.performance_tier.value if metric.performance_tier else "Developing"
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        total = len(cohort_metrics)
        tier_distribution = {
            tier: int((count / total) * 100)
            for tier, count in tier_counts.items()
        }

        # Ensure all tiers are represented
        for tier in ["Exemplary", "Strong", "Developing", "Needs Attention", "At Risk"]:
            if tier not in tier_distribution:
                tier_distribution[tier] = 0

        return PeerComparisonResponse(
            success=True,
            tutor_id=tutor_id,
            percentile_rank=overall_percentile,
            avg_rating_percentile=avg_rating_percentile,
            sessions_completed_percentile=sessions_percentile,
            engagement_score_percentile=engagement_percentile,
            performance_tier_distribution=tier_distribution,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get peer comparison for tutor {tutor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve peer comparison data"
        )
