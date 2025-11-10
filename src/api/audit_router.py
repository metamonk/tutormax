"""
Audit log API endpoints for searching, filtering, and compliance reporting.

Provides:
- Search and filter audit logs
- Export audit logs to CSV/JSON
- Compliance reports (user activity, data access, failed logins)
- Admin-only access with RBAC
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import csv
import io
import json

from ..database.database import get_async_session
from src.database.models import User, UserRole, AuditLog
from .auth.rbac import require_admin
from .audit_service import AuditService


router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


# Response models
class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    log_id: str
    user_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_method: Optional[str]
    request_path: Optional[str]
    status_code: Optional[int]
    success: bool
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogSearchResponse(BaseModel):
    """Paginated audit log search response."""
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class AuditStatistics(BaseModel):
    """Audit log statistics."""
    total_logs: int
    total_actions: Dict[str, int]
    total_users: int
    failed_logins: int
    successful_logins: int
    data_modifications: int
    data_access: int


class UserActivityReport(BaseModel):
    """User activity report."""
    user_id: int
    email: Optional[str]
    full_name: Optional[str]
    total_actions: int
    last_login: Optional[datetime]
    recent_activity: List[AuditLogResponse]


class FailedLoginReport(BaseModel):
    """Failed login attempts report."""
    total_failures: int
    unique_ips: int
    unique_emails: int
    recent_failures: List[AuditLogResponse]
    top_ips: List[Dict[str, Any]]


class DataAccessReport(BaseModel):
    """Data access report for a resource."""
    resource_type: str
    resource_id: str
    total_accesses: int
    unique_users: int
    access_history: List[AuditLogResponse]


# Endpoints

@router.get("/logs", response_model=AuditLogSearchResponse, dependencies=[Depends(require_admin)])
async def search_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    search_query: Optional[str] = Query(None, description="Text search in logs"),
    limit: int = Query(100, ge=1, le=1000, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    session: AsyncSession = Depends(get_async_session),
) -> AuditLogSearchResponse:
    """
    Search audit logs with various filters.

    Requires admin role. Supports pagination and complex filtering.
    """
    logs, total = await AuditService.search_logs(
        session=session,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
        start_date=start_date,
        end_date=end_date,
        ip_address=ip_address,
        search_query=search_query,
        limit=limit,
        offset=offset,
    )

    return AuditLogSearchResponse(
        logs=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(logs)) < total,
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse, dependencies=[Depends(require_admin)])
async def get_audit_log(
    log_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> AuditLogResponse:
    """
    Get a specific audit log entry by ID.

    Requires admin role.
    """
    from sqlalchemy import select

    result = await session.execute(
        select(AuditLog).where(AuditLog.log_id == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log {log_id} not found",
        )

    return AuditLogResponse.model_validate(log)


@router.get("/logs/export/csv", dependencies=[Depends(require_admin)])
async def export_audit_logs_csv(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10000, ge=1, le=100000),
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Export audit logs to CSV format.

    Requires admin role. Limited to 100,000 records per export.
    """
    logs, _ = await AuditService.search_logs(
        session=session,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=0,
    )

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "log_id",
        "timestamp",
        "user_id",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "request_method",
        "request_path",
        "status_code",
        "success",
        "error_message",
    ])

    # Write data
    for log in logs:
        writer.writerow([
            log.log_id,
            log.timestamp.isoformat(),
            log.user_id,
            log.action,
            log.resource_type or "",
            log.resource_id or "",
            log.ip_address or "",
            log.request_method or "",
            log.request_path or "",
            log.status_code or "",
            log.success,
            log.error_message or "",
        ])

    # Return as streaming response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )


@router.get("/logs/export/json", dependencies=[Depends(require_admin)])
async def export_audit_logs_json(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10000, ge=1, le=100000),
    session: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Export audit logs to JSON format.

    Requires admin role. Limited to 100,000 records per export.
    """
    logs, _ = await AuditService.search_logs(
        session=session,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=0,
    )

    # Convert to JSON-serializable format
    logs_data = [
        {
            "log_id": log.log_id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "request_method": log.request_method,
            "request_path": log.request_path,
            "status_code": log.status_code,
            "success": log.success,
            "error_message": log.error_message,
            "metadata": log.audit_metadata,
        }
        for log in logs
    ]

    return StreamingResponse(
        iter([json.dumps(logs_data, indent=2)]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        },
    )


@router.get("/statistics", response_model=AuditStatistics, dependencies=[Depends(require_admin)])
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    session: AsyncSession = Depends(get_async_session),
) -> AuditStatistics:
    """
    Get audit log statistics.

    Requires admin role. Returns counts by action type and summary metrics.
    """
    from sqlalchemy import select, func, distinct

    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Get action statistics
    action_stats = await AuditService.get_action_statistics(
        session=session,
        start_date=start_date,
        end_date=end_date,
    )

    # Get total logs count
    total_query = select(func.count()).select_from(AuditLog).where(
        AuditLog.timestamp.between(start_date, end_date)
    )
    total_result = await session.execute(total_query)
    total_logs = total_result.scalar()

    # Get unique users count
    users_query = select(func.count(distinct(AuditLog.user_id))).select_from(AuditLog).where(
        AuditLog.timestamp.between(start_date, end_date)
    )
    users_result = await session.execute(users_query)
    total_users = users_result.scalar()

    # Calculate specific metrics
    failed_logins = action_stats.get(AuditService.ACTION_LOGIN_FAILED, 0)
    successful_logins = action_stats.get(AuditService.ACTION_LOGIN, 0)

    # Count data modifications
    data_modifications = (
        action_stats.get(AuditService.ACTION_CREATE, 0) +
        action_stats.get(AuditService.ACTION_UPDATE, 0) +
        action_stats.get(AuditService.ACTION_DELETE, 0)
    )

    # Count data access
    data_access = (
        action_stats.get(AuditService.ACTION_VIEW, 0) +
        action_stats.get(AuditService.ACTION_LIST, 0) +
        action_stats.get(AuditService.ACTION_SEARCH, 0) +
        action_stats.get(AuditService.ACTION_EXPORT, 0)
    )

    return AuditStatistics(
        total_logs=total_logs,
        total_actions=action_stats,
        total_users=total_users,
        failed_logins=failed_logins,
        successful_logins=successful_logins,
        data_modifications=data_modifications,
        data_access=data_access,
    )


@router.get("/reports/user-activity/{user_id}", response_model=UserActivityReport, dependencies=[Depends(require_admin)])
async def get_user_activity_report(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    session: AsyncSession = Depends(get_async_session),
) -> UserActivityReport:
    """
    Get activity report for a specific user.

    Requires admin role. Shows user's recent activity and statistics.
    """
    from sqlalchemy import select

    # Get user info
    user_result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Get user activity
    activity = await AuditService.get_user_activity(
        session=session,
        user_id=user_id,
        days=days,
    )

    # Find last login
    last_login = None
    for log in activity:
        if log.action == AuditService.ACTION_LOGIN:
            last_login = log.timestamp
            break

    return UserActivityReport(
        user_id=user_id,
        email=user.email,
        full_name=user.full_name,
        total_actions=len(activity),
        last_login=last_login,
        recent_activity=[AuditLogResponse.model_validate(log) for log in activity[:50]],
    )


@router.get("/reports/failed-logins", response_model=FailedLoginReport, dependencies=[Depends(require_admin)])
async def get_failed_logins_report(
    hours: int = Query(24, ge=1, le=720, description="Number of hours to look back"),
    session: AsyncSession = Depends(get_async_session),
) -> FailedLoginReport:
    """
    Get report of failed login attempts.

    Requires admin role. Useful for security monitoring and detecting attacks.
    """
    from sqlalchemy import select, func

    failed_logins = await AuditService.get_failed_logins(
        session=session,
        hours=hours,
    )

    # Count unique IPs and emails
    unique_ips = set(log.ip_address for log in failed_logins if log.ip_address)
    unique_emails = set(
        log.audit_metadata.get("email")
        for log in failed_logins
        if log.audit_metadata and "email" in log.audit_metadata
    )

    # Count failures by IP
    ip_counts: Dict[str, int] = {}
    for log in failed_logins:
        if log.ip_address:
            ip_counts[log.ip_address] = ip_counts.get(log.ip_address, 0) + 1

    # Get top IPs
    top_ips = [
        {"ip_address": ip, "count": count}
        for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    return FailedLoginReport(
        total_failures=len(failed_logins),
        unique_ips=len(unique_ips),
        unique_emails=len(unique_emails),
        recent_failures=[AuditLogResponse.model_validate(log) for log in failed_logins[:100]],
        top_ips=top_ips,
    )


@router.get("/reports/data-access/{resource_type}/{resource_id}", response_model=DataAccessReport, dependencies=[Depends(require_admin)])
async def get_data_access_report(
    resource_type: str,
    resource_id: str,
    days: int = Query(90, ge=1, le=365, description="Number of days of history"),
    session: AsyncSession = Depends(get_async_session),
) -> DataAccessReport:
    """
    Get access history for a specific resource.

    Requires admin role. Shows who accessed what data and when.
    """
    from sqlalchemy import select, func

    access_history = await AuditService.get_resource_access_history(
        session=session,
        resource_type=resource_type,
        resource_id=resource_id,
        days=days,
    )

    # Count unique users
    unique_users = set(log.user_id for log in access_history if log.user_id)

    return DataAccessReport(
        resource_type=resource_type,
        resource_id=resource_id,
        total_accesses=len(access_history),
        unique_users=len(unique_users),
        access_history=[AuditLogResponse.model_validate(log) for log in access_history],
    )


@router.delete("/cleanup", dependencies=[Depends(require_admin)])
async def cleanup_old_audit_logs(
    retention_days: int = Query(365, ge=30, le=3650, description="Days to retain logs"),
    confirm: bool = Query(False, description="Confirm deletion"),
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Delete audit logs older than retention period.

    Requires admin role and confirmation. Use carefully!
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must set confirm=true to delete audit logs",
        )

    deleted_count = await AuditService.cleanup_old_logs(
        session=session,
        retention_days=retention_days,
    )

    return {
        "success": True,
        "deleted_count": deleted_count,
        "retention_days": retention_days,
        "timestamp": datetime.utcnow().isoformat(),
    }
