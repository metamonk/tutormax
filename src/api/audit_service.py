"""
Audit logging service for security and compliance tracking.

This service provides comprehensive audit logging for:
- Authentication events (login, logout, failed attempts)
- Data access (viewing sensitive data)
- Data modifications (CRUD operations)
- Administrative actions

All sensitive operations are logged asynchronously to minimize performance impact.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
import uuid

from src.database.models import AuditLog, User


class AuditService:
    """Service for managing audit logs."""

    # Action constants
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_LOGIN_FAILED = "login_failed"
    ACTION_PASSWORD_RESET = "password_reset"
    ACTION_PASSWORD_CHANGE = "password_change"
    ACTION_REGISTER = "register"
    ACTION_VERIFY_EMAIL = "verify_email"

    # Data access actions
    ACTION_VIEW = "view"
    ACTION_LIST = "list"
    ACTION_EXPORT = "export"
    ACTION_SEARCH = "search"

    # Data modification actions
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_BULK_UPDATE = "bulk_update"
    ACTION_BULK_DELETE = "bulk_delete"

    # Administrative actions
    ACTION_ROLE_CHANGE = "role_change"
    ACTION_USER_ENABLE = "user_enable"
    ACTION_USER_DISABLE = "user_disable"
    ACTION_INTERVENTION_CREATE = "intervention_create"
    ACTION_INTERVENTION_UPDATE = "intervention_update"

    # Resource types
    RESOURCE_USER = "user"
    RESOURCE_TUTOR = "tutor"
    RESOURCE_STUDENT = "student"
    RESOURCE_SESSION = "session"
    RESOURCE_FEEDBACK = "feedback"
    RESOURCE_PERFORMANCE_METRIC = "performance_metric"
    RESOURCE_CHURN_PREDICTION = "churn_prediction"
    RESOURCE_INTERVENTION = "intervention"
    RESOURCE_NOTIFICATION = "notification"
    RESOURCE_MANAGER_NOTE = "manager_note"

    @staticmethod
    async def log(
        session: AsyncSession,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        status_code: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            session: Database session
            action: Type of action performed
            user_id: ID of user performing action (if authenticated)
            resource_type: Type of resource affected (e.g., "tutor", "session")
            resource_id: ID of specific resource affected
            ip_address: IP address of client
            user_agent: User agent string
            request_method: HTTP method (GET, POST, etc.)
            request_path: Request path/endpoint
            status_code: HTTP status code
            success: Whether action succeeded
            error_message: Error message if failed
            metadata: Additional context data

        Returns:
            Created AuditLog instance
        """
        log_entry = AuditLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            status_code=status_code,
            success=success,
            error_message=error_message,
            audit_metadata=metadata,
            timestamp=datetime.utcnow(),
        )

        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)

        return log_entry

    @staticmethod
    async def log_authentication(
        session: AsyncSession,
        action: str,
        user_id: Optional[int],
        email: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log authentication-related events.

        Args:
            session: Database session
            action: Authentication action (login, logout, login_failed, etc.)
            user_id: User ID if known
            email: Email address used for authentication
            ip_address: Client IP address
            user_agent: User agent string
            success: Whether authentication succeeded
            error_message: Error message if failed
            metadata: Additional context

        Returns:
            Created AuditLog instance
        """
        meta = metadata or {}
        meta["email"] = email

        return await AuditService.log(
            session=session,
            action=action,
            user_id=user_id,
            resource_type=AuditService.RESOURCE_USER,
            resource_id=str(user_id) if user_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="POST",
            request_path="/auth/jwt/login" if action == AuditService.ACTION_LOGIN else "/auth",
            status_code=200 if success else 401,
            success=success,
            error_message=error_message,
            metadata=meta,
        )

    @staticmethod
    async def log_data_access(
        session: AsyncSession,
        user_id: int,
        resource_type: str,
        resource_id: Optional[str],
        action: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log data access events (viewing/listing/searching data).

        Args:
            session: Database session
            user_id: User accessing data
            resource_type: Type of resource accessed
            resource_id: ID of specific resource (None for list operations)
            action: Access action (view, list, search, export)
            ip_address: Client IP address
            user_agent: User agent string
            request_path: Request path
            metadata: Additional context (e.g., search filters)

        Returns:
            Created AuditLog instance
        """
        return await AuditService.log(
            session=session,
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="GET",
            request_path=request_path,
            status_code=200,
            success=True,
            metadata=metadata,
        )

    @staticmethod
    async def log_data_modification(
        session: AsyncSession,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_method: str,
        request_path: str,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log data modification events (create, update, delete).

        Args:
            session: Database session
            user_id: User modifying data
            action: Modification action (create, update, delete)
            resource_type: Type of resource modified
            resource_id: ID of specific resource
            ip_address: Client IP address
            user_agent: User agent string
            request_method: HTTP method (POST, PUT, DELETE)
            request_path: Request path
            success: Whether modification succeeded
            error_message: Error message if failed
            metadata: Additional context (e.g., changed fields)

        Returns:
            Created AuditLog instance
        """
        return await AuditService.log(
            session=session,
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            status_code=200 if success else 500,
            success=success,
            error_message=error_message,
            metadata=metadata,
        )

    @staticmethod
    async def search_logs(
        session: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        success: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[AuditLog], int]:
        """
        Search audit logs with filters.

        Args:
            session: Database session
            user_id: Filter by user ID
            action: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by specific resource ID
            success: Filter by success status
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            ip_address: Filter by IP address
            search_query: Text search in error messages and metadata
            limit: Maximum results to return
            offset: Number of results to skip (for pagination)

        Returns:
            Tuple of (logs list, total count)
        """
        # Build filters
        filters = []

        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)

        if action:
            filters.append(AuditLog.action == action)

        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)

        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)

        if success is not None:
            filters.append(AuditLog.success == success)

        if start_date:
            filters.append(AuditLog.timestamp >= start_date)

        if end_date:
            filters.append(AuditLog.timestamp <= end_date)

        if ip_address:
            filters.append(AuditLog.ip_address == ip_address)

        if search_query:
            # Search in error_message or request_path
            search_filter = or_(
                AuditLog.error_message.ilike(f"%{search_query}%"),
                AuditLog.request_path.ilike(f"%{search_query}%"),
            )
            filters.append(search_filter)

        # Get total count
        count_query = select(func.count()).select_from(AuditLog)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await session.execute(count_query)
        total = count_result.scalar()

        # Get logs
        query = (
            select(AuditLog)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )

        if filters:
            query = query.where(and_(*filters))

        result = await session.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    @staticmethod
    async def get_user_activity(
        session: AsyncSession,
        user_id: int,
        days: int = 30,
    ) -> List[AuditLog]:
        """
        Get recent activity for a specific user.

        Args:
            session: Database session
            user_id: User ID
            days: Number of days of history to return

        Returns:
            List of audit logs
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= start_date,
                )
            )
            .order_by(desc(AuditLog.timestamp))
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_failed_logins(
        session: AsyncSession,
        hours: int = 24,
        ip_address: Optional[str] = None,
    ) -> List[AuditLog]:
        """
        Get failed login attempts.

        Args:
            session: Database session
            hours: Number of hours to look back
            ip_address: Filter by specific IP address

        Returns:
            List of failed login audit logs
        """
        start_date = datetime.utcnow() - timedelta(hours=hours)

        filters = [
            AuditLog.action == AuditService.ACTION_LOGIN_FAILED,
            AuditLog.timestamp >= start_date,
        ]

        if ip_address:
            filters.append(AuditLog.ip_address == ip_address)

        query = (
            select(AuditLog)
            .where(and_(*filters))
            .order_by(desc(AuditLog.timestamp))
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def cleanup_old_logs(
        session: AsyncSession,
        retention_days: int = 365,
    ) -> int:
        """
        Delete audit logs older than retention period.

        Args:
            session: Database session
            retention_days: Number of days to retain logs

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Get count before deletion
        count_query = select(func.count()).select_from(AuditLog).where(
            AuditLog.timestamp < cutoff_date
        )
        count_result = await session.execute(count_query)
        count = count_result.scalar()

        # Delete old logs
        delete_query = select(AuditLog).where(AuditLog.timestamp < cutoff_date)
        result = await session.execute(delete_query)
        logs_to_delete = result.scalars().all()

        for log in logs_to_delete:
            await session.delete(log)

        await session.commit()

        return count

    @staticmethod
    async def get_resource_access_history(
        session: AsyncSession,
        resource_type: str,
        resource_id: str,
        days: int = 90,
    ) -> List[AuditLog]:
        """
        Get access history for a specific resource.

        Args:
            session: Database session
            resource_type: Type of resource
            resource_id: Resource ID
            days: Number of days of history

        Returns:
            List of audit logs for the resource
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id,
                    AuditLog.timestamp >= start_date,
                )
            )
            .order_by(desc(AuditLog.timestamp))
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_action_statistics(
        session: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get statistics on action counts.

        Args:
            session: Database session
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            Dictionary mapping action names to counts
        """
        filters = []

        if start_date:
            filters.append(AuditLog.timestamp >= start_date)

        if end_date:
            filters.append(AuditLog.timestamp <= end_date)

        query = select(AuditLog.action, func.count(AuditLog.log_id))

        if filters:
            query = query.where(and_(*filters))

        query = query.group_by(AuditLog.action)

        result = await session.execute(query)
        stats = {action: count for action, count in result.all()}

        return stats


# Convenience function for easier imports
async def log_audit_event(
    session: AsyncSession,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Convenience function to log audit events.

    This is a wrapper around AuditService.log() for easier imports.

    Args:
        session: Database session
        user_id: ID of user performing the action
        action: Action being performed
        resource_type: Type of resource being acted upon
        resource_id: Optional ID of specific resource
        details: Optional additional details
        ip_address: Optional IP address
        user_agent: Optional user agent string
    """
    audit_service = AuditService()
    await audit_service.log(
        session=session,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
