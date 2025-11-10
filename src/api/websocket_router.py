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
        latest_metrics_query = (
            select(TutorPerformanceMetric)
            .where(TutorPerformanceMetric.window == "30day")
            .order_by(TutorPerformanceMetric.calculation_date.desc())
        )
        metrics_result = await db.execute(latest_metrics_query)
        metrics = metrics_result.scalars().all()

        # Calculate performance distribution
        performance_distribution = {
            "Needs Support": 0,
            "Developing": 0,
            "Strong": 0,
            "Exemplary": 0,
        }

        total_rating = 0
        total_engagement = 0
        active_tutors = len(metrics)

        for metric in metrics:
            performance_distribution[metric.performance_tier] += 1
            total_rating += metric.avg_rating
            total_engagement += metric.engagement_score

        avg_rating = total_rating / active_tutors if active_tutors > 0 else 0
        avg_engagement_score = total_engagement / active_tutors if active_tutors > 0 else 0

        # Get session counts (would need to aggregate from sessions table)
        # For now, return mock data
        total_sessions_7day = sum(m.sessions_completed for m in metrics if m.window == "7day")
        total_sessions_30day = sum(m.sessions_completed for m in metrics)

        # Mock alert counts (would come from alerts table)
        alerts_count = {
            "critical": performance_distribution["Needs Support"],
            "warning": performance_distribution["Developing"],
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
                "Needs Support": 0,
                "Developing": 0,
                "Strong": 0,
                "Exemplary": 0,
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
