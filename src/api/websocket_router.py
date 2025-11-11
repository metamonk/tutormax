"""
WebSocket Router for Real-Time Dashboard

Provides WebSocket endpoints for real-time updates to the operations dashboard.
"""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database.connection import get_session
from src.database.models import TutorPerformanceMetric, Tutor
from .websocket_service import ConnectionManager, get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    manager: ConnectionManager = Depends(get_connection_manager),
):
    """
    WebSocket endpoint for operations dashboard.

    Provides real-time updates for:
    - Tutor performance metrics
    - Critical alerts
    - Intervention tasks
    - Performance analytics
    """
    await manager.connect(websocket)

    try:
        # Send initial analytics on connection
        async with get_session() as db:
            initial_analytics = await _get_analytics(db)
            await manager.send_personal(websocket, "analytics_update", initial_analytics)

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for messages from client (ping/pong, commands, etc.)
                data = await websocket.receive_text()
                logger.debug(f"Received message from client: {data}")

                # Handle client requests if needed
                # For now, just acknowledge
                if data == "ping":
                    await manager.send_personal(websocket, "analytics_update", {"pong": True})

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        await manager.disconnect(websocket)


async def _get_analytics(db: AsyncSession) -> dict:
    """
    Get current performance analytics for the dashboard.

    Args:
        db: Database session

    Returns:
        Dictionary with analytics data
    """
    try:
        # Count total tutors
        total_tutors_query = select(func.count()).select_from(Tutor)
        total_tutors_result = await db.execute(total_tutors_query)
        total_tutors = total_tutors_result.scalar() or 0

        # Get latest metrics for active tutors (30-day window)
        # Note: MetricWindow enum uses uppercase with underscore (e.g., THIRTY_DAY)
        # Get the most recent metric for each tutor
        from src.database.models import MetricWindow
        from sqlalchemy import distinct, and_

        # Get all 30-day metrics, we'll deduplicate in Python
        latest_metrics_query = (
            select(TutorPerformanceMetric)
            .where(TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY)
            .order_by(TutorPerformanceMetric.tutor_id, TutorPerformanceMetric.calculation_date.desc())
        )
        all_metrics_result = await db.execute(latest_metrics_query)
        all_metrics = all_metrics_result.scalars().all()

        # Deduplicate: Keep only the latest metric for each tutor
        seen_tutors = set()
        metrics = []
        for metric in all_metrics:
            if metric.tutor_id not in seen_tutors:
                metrics.append(metric)
                seen_tutors.add(metric.tutor_id)

        # Calculate performance distribution
        # Note: PerformanceTier enum values match database exactly
        performance_distribution = {
            "Exemplary": 0,
            "Strong": 0,
            "Developing": 0,
            "Needs Attention": 0,
            "At Risk": 0,
        }

        total_rating = 0
        total_engagement = 0

        # Count unique tutors and aggregate metrics
        # Note: We only use 30-day metrics for tier distribution and averages
        active_tutors = len(metrics)

        for metric in metrics:
            # Convert enum value to string for dictionary key
            tier_key = metric.performance_tier.value if hasattr(metric.performance_tier, 'value') else str(metric.performance_tier)
            if tier_key in performance_distribution:
                performance_distribution[tier_key] += 1
            # Aggregate ratings and engagement (only from 30-day window)
            total_rating += (metric.avg_rating or 0)
            total_engagement += (metric.engagement_score or 0)

        avg_rating = total_rating / active_tutors if active_tutors > 0 else 0
        avg_engagement_score = total_engagement / active_tutors if active_tutors > 0 else 0

        # Get session counts from metrics
        # Query 7-day metrics separately
        seven_day_query = (
            select(TutorPerformanceMetric)
            .where(TutorPerformanceMetric.window == MetricWindow.SEVEN_DAY)
        )
        seven_day_result = await db.execute(seven_day_query)
        seven_day_metrics = seven_day_result.scalars().all()

        total_sessions_7day = sum(m.sessions_completed for m in seven_day_metrics)
        total_sessions_30day = sum(m.sessions_completed for m in metrics)

        # Mock alert counts (would come from alerts table)
        alerts_count = {
            "critical": performance_distribution.get("At Risk", 0) + performance_distribution.get("Needs Attention", 0),
            "warning": performance_distribution.get("Developing", 0),
            "info": 0,
        }

        return {
            "total_tutors": total_tutors,
            "active_tutors": active_tutors,
            "performance_distribution": performance_distribution,
            "avg_rating": round(avg_rating, 2),
            "avg_engagement_score": round(avg_engagement_score, 2),
            "total_sessions_7day": total_sessions_7day,
            "total_sessions_30day": total_sessions_30day,
            "alerts_count": alerts_count,
        }

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return {
            "total_tutors": 0,
            "active_tutors": 0,
            "performance_distribution": {
                "Exemplary": 0,
                "Strong": 0,
                "Developing": 0,
                "Needs Attention": 0,
                "At Risk": 0,
            },
            "avg_rating": 0,
            "avg_engagement_score": 0,
            "total_sessions_7day": 0,
            "total_sessions_30day": 0,
            "alerts_count": {"critical": 0, "warning": 0, "info": 0},
        }


@router.get("/ws/status")
async def websocket_status(manager: ConnectionManager = Depends(get_connection_manager)):
    """
    Get WebSocket connection status.
    """
    return {
        "active_connections": manager.get_connection_count(),
        "status": "operational",
    }
