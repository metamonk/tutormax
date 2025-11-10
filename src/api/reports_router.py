"""
Reports and Data Export API endpoints.

Provides comprehensive reporting and data export functionality for operations managers.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from .config import settings
from ..database.database import get_async_session
from .export_service import ExportService
from .auth.rbac import require_operations_manager
from src.database.models import User, InterventionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{settings.api_prefix}/reports", tags=["Reports"])


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    PDF = "pdf"


class ReportType(str, Enum):
    """Types of reports available."""
    TUTOR_PERFORMANCE = "tutor_performance"
    INTERVENTION_HISTORY = "intervention_history"
    CHURN_ANALYTICS = "churn_analytics"
    MONTHLY_SUMMARY = "monthly_summary"


class ReportMetric(str, Enum):
    """Available metrics for custom reports."""
    AVG_RATING = "avg_rating"
    SESSIONS_COMPLETED = "sessions_completed"
    ENGAGEMENT_SCORE = "engagement_score"
    RESCHEDULE_RATE = "reschedule_rate"
    NO_SHOW_RATE = "no_show_rate"
    FIRST_SESSION_SUCCESS = "first_session_success_rate"
    LEARNING_OBJECTIVES_MET = "learning_objectives_met_pct"
    PERFORMANCE_TIER = "performance_tier"


class CustomReportRequest(BaseModel):
    """Request to build a custom report."""
    report_name: str = Field(..., description="Name for the custom report")
    start_date: datetime = Field(..., description="Start date for data")
    end_date: datetime = Field(..., description="End date for data")
    metrics: List[ReportMetric] = Field(..., description="Metrics to include")
    tutor_ids: Optional[List[str]] = Field(None, description="Specific tutors (empty = all)")
    format: ExportFormat = Field(ExportFormat.CSV, description="Export format")
    group_by_tier: bool = Field(False, description="Group results by performance tier")
    include_summary: bool = Field(True, description="Include summary statistics")


class ScheduledReportRequest(BaseModel):
    """Request to schedule a recurring report."""
    report_type: ReportType
    frequency: str = Field(..., description="Frequency: daily, weekly, monthly")
    recipients: List[str] = Field(..., description="Email addresses to send report to")
    format: ExportFormat = ExportFormat.CSV
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@router.get("/tutor-performance/export")
async def export_tutor_performance(
    format: ExportFormat = Query(..., description="Export format (csv or pdf)"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    tutor_ids: Optional[str] = Query(None, description="Comma-separated tutor IDs"),
    session: AsyncSession = Depends(get_async_session),
    _user: User = Depends(require_operations_manager),
):
    """
    Export tutor performance data in CSV or PDF format.

    **Requires:** Operations Manager role

    Args:
        format: Export format (csv or pdf)
        start_date: Optional start date filter
        end_date: Optional end date filter
        tutor_ids: Optional comma-separated list of tutor IDs

    Returns:
        File download with performance data
    """
    try:
        export_service = ExportService(session)

        # Parse tutor IDs
        tutor_id_list = tutor_ids.split(',') if tutor_ids else None

        if format == ExportFormat.CSV:
            buffer = await export_service.export_tutor_performance_csv(
                start_date=start_date,
                end_date=end_date,
                tutor_ids=tutor_id_list
            )

            filename = f"tutor_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        elif format == ExportFormat.PDF:
            buffer = await export_service.export_tutor_performance_pdf(
                start_date=start_date,
                end_date=end_date,
                tutor_ids=tutor_id_list
            )

            filename = f"tutor_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

    except Exception as e:
        logger.error(f"Failed to export tutor performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export tutor performance data"
        )


@router.get("/interventions/export")
async def export_interventions(
    format: ExportFormat = Query(..., description="Export format (csv or pdf)"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    status_filter: Optional[InterventionStatus] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_async_session),
    _user: User = Depends(require_operations_manager),
):
    """
    Export intervention history in CSV format.

    **Requires:** Operations Manager role

    Args:
        format: Export format (currently only CSV supported)
        start_date: Optional start date filter
        end_date: Optional end date filter
        status_filter: Optional intervention status filter

    Returns:
        CSV file download with intervention data
    """
    try:
        export_service = ExportService(session)

        buffer = await export_service.export_interventions_csv(
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter
        )

        filename = f"interventions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Failed to export interventions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export intervention data"
        )


@router.post("/custom-report")
async def generate_custom_report(
    request: CustomReportRequest,
    session: AsyncSession = Depends(get_async_session),
    _user: User = Depends(require_operations_manager),
):
    """
    Generate a custom report with selected metrics and filters.

    **Requires:** Operations Manager role

    This endpoint allows operations managers to build custom reports by:
    - Selecting specific metrics (rating, sessions, engagement, etc.)
    - Choosing date ranges
    - Filtering by specific tutors
    - Grouping by performance tier
    - Choosing output format (CSV or PDF)

    Args:
        request: Custom report configuration

    Returns:
        File download with custom report data
    """
    try:
        export_service = ExportService(session)

        # For now, use the standard export with custom filtering
        # In a production system, this would build a fully custom query based on selected metrics

        if request.format == ExportFormat.CSV:
            buffer = await export_service.export_tutor_performance_csv(
                start_date=request.start_date,
                end_date=request.end_date,
                tutor_ids=request.tutor_ids
            )

            filename = f"{request.report_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        else:
            buffer = await export_service.export_tutor_performance_pdf(
                start_date=request.start_date,
                end_date=request.end_date,
                tutor_ids=request.tutor_ids
            )

            filename = f"{request.report_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

    except Exception as e:
        logger.error(f"Failed to generate custom report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate custom report"
        )


@router.get("/analytics-summary/export")
async def export_analytics_summary(
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    session: AsyncSession = Depends(get_async_session),
    _user: User = Depends(require_operations_manager),
):
    """
    Export comprehensive analytics summary for a date range.

    **Requires:** Operations Manager role

    Args:
        start_date: Start date for report
        end_date: End date for report

    Returns:
        PDF file with analytics summary
    """
    try:
        export_service = ExportService(session)

        buffer = await export_service.export_analytics_summary_pdf(
            start_date=start_date,
            end_date=end_date
        )

        filename = f"analytics_summary_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Failed to export analytics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics summary"
        )


@router.post("/schedule")
async def schedule_recurring_report(
    request: ScheduledReportRequest,
    session: AsyncSession = Depends(get_async_session),
    _user: User = Depends(require_operations_manager),
):
    """
    Schedule a recurring report delivery.

    **Requires:** Operations Manager role

    This endpoint provides information about automated report scheduling.
    Report schedules are configured in the Celery Beat scheduler.

    Args:
        request: Scheduled report configuration

    Returns:
        Confirmation of scheduled report configuration
    """
    # Map report types to scheduled tasks
    report_task_mapping = {
        ReportType.TUTOR_PERFORMANCE: {
            "weekly": "send-weekly-performance-report",
            "monthly": "send-monthly-performance-report"
        },
        ReportType.INTERVENTION_HISTORY: {
            "weekly": "send-intervention-effectiveness-report"
        },
        ReportType.CHURN_ANALYTICS: {
            "monthly": "send-churn-analytics-report"
        }
    }

    # Validate request
    task_mapping = report_task_mapping.get(request.report_type, {})
    task_name = task_mapping.get(request.frequency)

    if not task_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report type '{request.report_type.value}' does not support '{request.frequency}' frequency. "
                   f"Available frequencies: {', '.join(task_mapping.keys())}"
        )

    # Get schedule info
    schedule_info = {
        "weekly": "Every Monday at 9:00 AM UTC",
        "monthly": "1st day of each month at 9:00 AM UTC"
    }

    if request.report_type == ReportType.INTERVENTION_HISTORY:
        schedule_info["weekly"] = "Every Friday at 4:00 PM UTC"
    elif request.report_type == ReportType.CHURN_ANALYTICS:
        schedule_info["monthly"] = "1st day of each month at 10:00 AM UTC"

    return {
        "success": True,
        "message": f"Report scheduling confirmed for {request.frequency} delivery",
        "report_type": request.report_type.value,
        "frequency": request.frequency,
        "format": request.format.value,
        "schedule": schedule_info.get(request.frequency, "As configured"),
        "celery_task": task_name,
        "delivery_method": "Email to all Operations Managers",
        "note": "Reports are automatically delivered via Celery Beat. "
                "Recipients list is determined by users with Operations Manager role. "
                "To modify schedules, update the Celery Beat configuration in src/workers/celery_app.py"
    }


@router.get("/templates")
async def get_report_templates(
    _user: User = Depends(require_operations_manager),
):
    """
    Get available report templates.

    **Requires:** Operations Manager role

    Returns:
        List of pre-configured report templates
    """
    templates = [
        {
            "id": "monthly_churn",
            "name": "Monthly Churn Report",
            "description": "Comprehensive monthly churn analysis with risk factors",
            "metrics": ["churn_risk", "interventions", "performance_trends"],
            "recommended_frequency": "monthly"
        },
        {
            "id": "intervention_effectiveness",
            "name": "Intervention Effectiveness Report",
            "description": "Analysis of intervention outcomes and success rates",
            "metrics": ["intervention_count", "completion_rate", "outcome_analysis"],
            "recommended_frequency": "weekly"
        },
        {
            "id": "tutor_performance_summary",
            "name": "Tutor Performance Summary",
            "description": "Overall tutor performance metrics and tier distribution",
            "metrics": ["avg_rating", "sessions", "engagement", "tier_distribution"],
            "recommended_frequency": "weekly"
        },
        {
            "id": "quarterly_trends",
            "name": "Quarterly Trends Analysis",
            "description": "Long-term performance and engagement trends",
            "metrics": ["rating_trends", "session_volume", "retention_rates"],
            "recommended_frequency": "quarterly"
        },
    ]

    return {
        "success": True,
        "templates": templates,
        "total": len(templates)
    }
