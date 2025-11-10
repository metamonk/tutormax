"""
Training Resources API endpoints.

Provides access to training materials, videos, articles, and best practices.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from .config import settings
from ..database.database import get_async_session
from src.database.models import Tutor, TutorPerformanceMetric, MetricWindow
from sqlalchemy import desc

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=f"{settings.api_prefix}/training-resources", tags=["Training Resources"])


# In-memory storage for resource progress (in production, use database)
PROGRESS_STORE = {}  # {tutor_id: {resource_id: {completed: bool, completion_date: str}}}


class ResourceType(str):
    """Types of training resources."""
    VIDEO = "video"
    ARTICLE = "article"
    BEST_PRACTICE = "best_practice"
    INTERACTIVE = "interactive"
    QUIZ = "quiz"


class ResourceCategory(str):
    """Categories of training content."""
    STUDENT_ENGAGEMENT = "student_engagement"
    TIME_MANAGEMENT = "time_management"
    FIRST_SESSION = "first_session"
    COMMUNICATION = "communication"
    SUBJECT_MASTERY = "subject_mastery"
    TECHNOLOGY = "technology"
    STUDENT_SUPPORT = "student_support"
    PERFORMANCE = "performance"
    GENERAL = "general"


class ResourceResponse(BaseModel):
    """Training resource response."""
    resource_id: str
    title: str
    description: str
    resource_type: str
    category: str
    duration_minutes: int
    difficulty_level: str
    is_recommended: bool
    completed: bool
    completion_date: Optional[str] = None
    thumbnail_url: Optional[str] = None
    content_url: str
    tags: List[str]


class ResourcesListResponse(BaseModel):
    """Response containing training resources."""
    success: bool
    resources: List[ResourceResponse]
    total: int
    completed_count: int
    recommended_count: int
    timestamp: str


class ResourceProgressUpdate(BaseModel):
    """Update progress for a resource."""
    completed: bool


# Sample training resources
TRAINING_RESOURCES = [
    {
        "resource_id": "res_001",
        "title": "Mastering Student Engagement",
        "description": "Learn proven techniques to keep students motivated and actively participating in sessions",
        "resource_type": ResourceType.VIDEO,
        "category": ResourceCategory.STUDENT_ENGAGEMENT,
        "duration_minutes": 45,
        "difficulty_level": "intermediate",
        "content_url": "https://training.tutormax.example/videos/student-engagement",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/engagement.jpg",
        "tags": ["engagement", "motivation", "interaction", "best-practices"]
    },
    {
        "resource_id": "res_002",
        "title": "First Session Excellence",
        "description": "Create outstanding first impressions and build strong rapport with new students",
        "resource_type": ResourceType.VIDEO,
        "category": ResourceCategory.FIRST_SESSION,
        "duration_minutes": 30,
        "difficulty_level": "beginner",
        "content_url": "https://training.tutormax.example/videos/first-session",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/first-session.jpg",
        "tags": ["first-session", "rapport", "introduction", "onboarding"]
    },
    {
        "resource_id": "res_003",
        "title": "Time Management for Tutors",
        "description": "Optimize your schedule and reduce reschedules with effective time management",
        "resource_type": ResourceType.ARTICLE,
        "category": ResourceCategory.TIME_MANAGEMENT,
        "duration_minutes": 15,
        "difficulty_level": "beginner",
        "content_url": "https://training.tutormax.example/articles/time-management",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/time-mgmt.jpg",
        "tags": ["scheduling", "organization", "productivity", "planning"]
    },
    {
        "resource_id": "res_004",
        "title": "Effective Communication Strategies",
        "description": "Improve how you explain complex concepts and provide constructive feedback",
        "resource_type": ResourceType.VIDEO,
        "category": ResourceCategory.COMMUNICATION,
        "duration_minutes": 40,
        "difficulty_level": "intermediate",
        "content_url": "https://training.tutormax.example/videos/communication",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/communication.jpg",
        "tags": ["communication", "feedback", "explanation", "clarity"]
    },
    {
        "resource_id": "res_005",
        "title": "Goal-Oriented Tutoring",
        "description": "Strategies for setting and achieving learning objectives in every session",
        "resource_type": ResourceType.VIDEO,
        "category": ResourceCategory.PERFORMANCE,
        "duration_minutes": 35,
        "difficulty_level": "intermediate",
        "content_url": "https://training.tutormax.example/videos/goal-oriented",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/goals.jpg",
        "tags": ["goals", "objectives", "planning", "outcomes"]
    },
    {
        "resource_id": "res_006",
        "title": "Technology Tools Masterclass",
        "description": "Master the virtual whiteboard, screen sharing, and collaboration tools",
        "resource_type": ResourceType.INTERACTIVE,
        "category": ResourceCategory.TECHNOLOGY,
        "duration_minutes": 60,
        "difficulty_level": "beginner",
        "content_url": "https://training.tutormax.example/interactive/tech-tools",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/tech.jpg",
        "tags": ["technology", "tools", "whiteboard", "screen-sharing"]
    },
    {
        "resource_id": "res_007",
        "title": "Supporting Struggling Students",
        "description": "Approaches for helping students who are behind or facing challenges",
        "resource_type": ResourceType.ARTICLE,
        "category": ResourceCategory.STUDENT_SUPPORT,
        "duration_minutes": 20,
        "difficulty_level": "advanced",
        "content_url": "https://training.tutormax.example/articles/struggling-students",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/support.jpg",
        "tags": ["support", "challenges", "empathy", "strategies"]
    },
    {
        "resource_id": "res_008",
        "title": "Math Tutoring Best Practices",
        "description": "Subject-specific strategies for effective math tutoring",
        "resource_type": ResourceType.VIDEO,
        "category": ResourceCategory.SUBJECT_MASTERY,
        "duration_minutes": 50,
        "difficulty_level": "intermediate",
        "content_url": "https://training.tutormax.example/videos/math-practices",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/math.jpg",
        "tags": ["math", "subject-specific", "problem-solving", "techniques"]
    },
    {
        "resource_id": "res_009",
        "title": "Building Student Confidence",
        "description": "Techniques to help students overcome anxiety and build self-efficacy",
        "resource_type": ResourceType.ARTICLE,
        "category": ResourceCategory.STUDENT_SUPPORT,
        "duration_minutes": 12,
        "difficulty_level": "beginner",
        "content_url": "https://training.tutormax.example/articles/confidence-building",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/confidence.jpg",
        "tags": ["confidence", "anxiety", "encouragement", "mindset"]
    },
    {
        "resource_id": "res_010",
        "title": "Advanced Engagement Techniques",
        "description": "Take your engagement skills to the next level with advanced strategies",
        "resource_type": ResourceType.VIDEO,
        "category": ResourceCategory.STUDENT_ENGAGEMENT,
        "duration_minutes": 55,
        "difficulty_level": "advanced",
        "content_url": "https://training.tutormax.example/videos/advanced-engagement",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/advanced-engagement.jpg",
        "tags": ["engagement", "advanced", "techniques", "mastery"]
    },
    {
        "resource_id": "res_011",
        "title": "Understanding Learning Styles",
        "description": "Adapt your teaching approach to different learning styles and preferences",
        "resource_type": ResourceType.ARTICLE,
        "category": ResourceCategory.GENERAL,
        "duration_minutes": 18,
        "difficulty_level": "beginner",
        "content_url": "https://training.tutormax.example/articles/learning-styles",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/learning-styles.jpg",
        "tags": ["learning-styles", "adaptation", "personalization", "teaching"]
    },
    {
        "resource_id": "res_012",
        "title": "Performance Metrics Quiz",
        "description": "Test your knowledge of tutor performance metrics and improvement strategies",
        "resource_type": ResourceType.QUIZ,
        "category": ResourceCategory.PERFORMANCE,
        "duration_minutes": 10,
        "difficulty_level": "intermediate",
        "content_url": "https://training.tutormax.example/quiz/performance-metrics",
        "thumbnail_url": "https://training.tutormax.example/thumbnails/quiz.jpg",
        "tags": ["quiz", "assessment", "metrics", "performance"]
    },
]


def get_recommended_resources(
    tutor_metric: Optional[TutorPerformanceMetric]
) -> List[str]:
    """
    Determine recommended resources based on tutor performance.

    Returns list of resource IDs.
    """
    if not tutor_metric:
        # New tutor - recommend beginner resources
        return ["res_002", "res_006", "res_011"]

    recommended = []

    # Recommend based on performance gaps
    if tutor_metric.avg_rating and tutor_metric.avg_rating < 4.0:
        recommended.extend(["res_001", "res_004"])  # Engagement and Communication

    if tutor_metric.first_session_success_rate and tutor_metric.first_session_success_rate < 0.8:
        recommended.append("res_002")  # First Session Excellence

    if tutor_metric.reschedule_rate and tutor_metric.reschedule_rate > 0.15:
        recommended.append("res_003")  # Time Management

    if tutor_metric.engagement_score and tutor_metric.engagement_score < 7.0:
        recommended.extend(["res_001", "res_010"])  # Engagement resources

    if tutor_metric.learning_objectives_met_pct and tutor_metric.learning_objectives_met_pct < 0.8:
        recommended.append("res_005")  # Goal-Oriented Tutoring

    # Always recommend support resources for struggling students
    recommended.append("res_007")

    # Remove duplicates while preserving order
    seen = set()
    unique_recommended = []
    for resource_id in recommended:
        if resource_id not in seen:
            seen.add(resource_id)
            unique_recommended.append(resource_id)

    return unique_recommended[:5]  # Limit to top 5


@router.get("/", response_model=ResourcesListResponse)
async def get_training_resources(
    tutor_id: Optional[str] = Query(None, description="Tutor ID for personalized recommendations"),
    category: Optional[str] = Query(None, description="Filter by category"),
    resource_type: Optional[str] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get all training resources with optional filters.

    Returns resources with personalized recommendations based on
    tutor performance metrics.

    Args:
        tutor_id: Optional tutor ID for personalized recommendations
        category: Optional category filter
        resource_type: Optional type filter
        search: Optional search query
        db: Database session

    Returns:
        List of training resources with completion status
    """
    try:
        # Get recommended resources if tutor_id provided
        recommended_ids = []
        if tutor_id:
            # Check if tutor exists
            result = await db.execute(
                select(Tutor).where(Tutor.tutor_id == tutor_id)
            )
            tutor = result.scalar_one_or_none()

            if tutor:
                # Get latest metrics
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
                recommended_ids = get_recommended_resources(latest_metric)

        # Filter resources
        resources = TRAINING_RESOURCES.copy()

        if category:
            resources = [r for r in resources if r["category"] == category]

        if resource_type:
            resources = [r for r in resources if r["resource_type"] == resource_type]

        if search:
            search_lower = search.lower()
            resources = [
                r for r in resources
                if search_lower in r["title"].lower() or
                   search_lower in r["description"].lower() or
                   any(search_lower in tag for tag in r["tags"])
            ]

        # Get progress data for tutor
        tutor_progress = PROGRESS_STORE.get(tutor_id, {}) if tutor_id else {}

        # Build responses
        resource_responses = []
        for resource in resources:
            progress = tutor_progress.get(resource["resource_id"], {})
            is_recommended = resource["resource_id"] in recommended_ids

            resource_responses.append(ResourceResponse(
                resource_id=resource["resource_id"],
                title=resource["title"],
                description=resource["description"],
                resource_type=resource["resource_type"],
                category=resource["category"],
                duration_minutes=resource["duration_minutes"],
                difficulty_level=resource["difficulty_level"],
                is_recommended=is_recommended,
                completed=progress.get("completed", False),
                completion_date=progress.get("completion_date"),
                thumbnail_url=resource.get("thumbnail_url"),
                content_url=resource["content_url"],
                tags=resource["tags"]
            ))

        # Sort: recommended first, then uncompleted, then by title
        resource_responses.sort(
            key=lambda x: (
                not x.is_recommended,
                x.completed,
                x.title
            )
        )

        completed_count = sum(1 for r in resource_responses if r.completed)
        recommended_count = sum(1 for r in resource_responses if r.is_recommended)

        return ResourcesListResponse(
            success=True,
            resources=resource_responses,
            total=len(resource_responses),
            completed_count=completed_count,
            recommended_count=recommended_count,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Failed to get training resources: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve training resources"
        )


@router.post("/{tutor_id}/{resource_id}/progress")
async def update_resource_progress(
    tutor_id: str,
    resource_id: str,
    progress: ResourceProgressUpdate = Body(...),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update completion progress for a training resource.

    Args:
        tutor_id: The tutor's unique identifier
        resource_id: The resource's unique identifier
        progress: Progress update data
        db: Database session

    Returns:
        Success status with updated progress
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

        # Check if resource exists
        resource = next((r for r in TRAINING_RESOURCES if r["resource_id"] == resource_id), None)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource {resource_id} not found"
            )

        # Update progress
        if tutor_id not in PROGRESS_STORE:
            PROGRESS_STORE[tutor_id] = {}

        PROGRESS_STORE[tutor_id][resource_id] = {
            "completed": progress.completed,
            "completion_date": datetime.now().isoformat() if progress.completed else None
        }

        return {
            "success": True,
            "tutor_id": tutor_id,
            "resource_id": resource_id,
            "completed": progress.completed,
            "completion_date": PROGRESS_STORE[tutor_id][resource_id]["completion_date"],
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update progress for tutor {tutor_id}, resource {resource_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resource progress"
        )
