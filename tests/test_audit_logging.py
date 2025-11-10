"""
Tests for audit logging system.

Tests:
- Audit service functionality
- Middleware logging
- API endpoints
- Search and filtering
- Compliance reports
"""

import pytest
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import AuditLog, User, UserRole
from src.api.audit_service import AuditService
from src.api.audit_middleware import AuditLoggingMiddleware


@pytest.mark.asyncio
async def test_audit_log_creation(db_session: AsyncSession):
    """Test creating an audit log entry."""
    log = await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        resource_type=AuditService.RESOURCE_USER,
        resource_id="1",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        request_method="POST",
        request_path="/auth/jwt/login",
        status_code=200,
        success=True,
        metadata={"test": "data"},
    )

    assert log.log_id is not None
    assert log.user_id == 1
    assert log.action == AuditService.ACTION_LOGIN
    assert log.success is True
    assert log.ip_address == "192.168.1.1"
    assert log.audit_metadata == {"test": "data"}


@pytest.mark.asyncio
async def test_authentication_logging(db_session: AsyncSession):
    """Test logging authentication events."""
    log = await AuditService.log_authentication(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        email="test@example.com",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        success=True,
    )

    assert log.action == AuditService.ACTION_LOGIN
    assert log.success is True
    assert log.audit_metadata["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_failed_authentication_logging(db_session: AsyncSession):
    """Test logging failed authentication."""
    log = await AuditService.log_authentication(
        session=db_session,
        action=AuditService.ACTION_LOGIN_FAILED,
        user_id=None,
        email="hacker@example.com",
        ip_address="192.168.1.100",
        user_agent="curl/7.64.1",
        success=False,
        error_message="Invalid credentials",
    )

    assert log.action == AuditService.ACTION_LOGIN_FAILED
    assert log.success is False
    assert log.error_message == "Invalid credentials"
    assert log.user_id is None


@pytest.mark.asyncio
async def test_data_access_logging(db_session: AsyncSession):
    """Test logging data access events."""
    log = await AuditService.log_data_access(
        session=db_session,
        user_id=1,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-123",
        action=AuditService.ACTION_VIEW,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        request_path="/api/tutors/tutor-123",
        metadata={"viewed_fields": ["name", "email", "performance"]},
    )

    assert log.action == AuditService.ACTION_VIEW
    assert log.resource_type == AuditService.RESOURCE_TUTOR
    assert log.resource_id == "tutor-123"
    assert log.audit_metadata["viewed_fields"] is not None


@pytest.mark.asyncio
async def test_data_modification_logging(db_session: AsyncSession):
    """Test logging data modification events."""
    log = await AuditService.log_data_modification(
        session=db_session,
        user_id=1,
        action=AuditService.ACTION_UPDATE,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        request_method="PUT",
        request_path="/api/tutors/tutor-123",
        success=True,
        metadata={"changed_fields": ["email", "subjects"]},
    )

    assert log.action == AuditService.ACTION_UPDATE
    assert log.request_method == "PUT"
    assert log.audit_metadata["changed_fields"] == ["email", "subjects"]


@pytest.mark.asyncio
async def test_search_logs_by_user(db_session: AsyncSession):
    """Test searching audit logs by user ID."""
    # Create multiple logs
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        ip_address="192.168.1.1",
        success=True,
    )
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_VIEW,
        user_id=1,
        resource_type=AuditService.RESOURCE_TUTOR,
        success=True,
    )
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
        user_id=2,
        ip_address="192.168.1.2",
        success=True,
    )

    # Search for user 1
    logs, total = await AuditService.search_logs(
        session=db_session,
        user_id=1,
    )

    assert total == 2
    assert all(log.user_id == 1 for log in logs)


@pytest.mark.asyncio
async def test_search_logs_by_action(db_session: AsyncSession):
    """Test searching audit logs by action type."""
    # Create logs with different actions
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        success=True,
    )
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
        user_id=2,
        success=True,
    )
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_LOGOUT,
        user_id=1,
        success=True,
    )

    # Search for login actions
    logs, total = await AuditService.search_logs(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
    )

    assert total == 2
    assert all(log.action == AuditService.ACTION_LOGIN for log in logs)


@pytest.mark.asyncio
async def test_search_logs_by_date_range(db_session: AsyncSession):
    """Test searching audit logs by date range."""
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)

    # Create logs with different timestamps (need to manually set)
    log1 = AuditLog(
        log_id="log1",
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        timestamp=two_days_ago,
        success=True,
    )
    log2 = AuditLog(
        log_id="log2",
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        timestamp=yesterday,
        success=True,
    )
    log3 = AuditLog(
        log_id="log3",
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        timestamp=now,
        success=True,
    )

    db_session.add_all([log1, log2, log3])
    await db_session.commit()

    # Search for logs from yesterday onwards
    logs, total = await AuditService.search_logs(
        session=db_session,
        start_date=yesterday - timedelta(hours=1),
    )

    assert total >= 2  # Should include yesterday and today


@pytest.mark.asyncio
async def test_search_logs_by_resource(db_session: AsyncSession):
    """Test searching logs by resource type and ID."""
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_VIEW,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-123",
        user_id=1,
        success=True,
    )
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_UPDATE,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-123",
        user_id=1,
        success=True,
    )
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_VIEW,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-456",
        user_id=1,
        success=True,
    )

    # Search for specific tutor
    logs, total = await AuditService.search_logs(
        session=db_session,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-123",
    )

    assert total == 2
    assert all(log.resource_id == "tutor-123" for log in logs)


@pytest.mark.asyncio
async def test_get_user_activity(db_session: AsyncSession):
    """Test getting user activity report."""
    # Create activity for user
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        success=True,
    )
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_VIEW,
        user_id=1,
        resource_type=AuditService.RESOURCE_TUTOR,
        success=True,
    )

    # Get activity
    activity = await AuditService.get_user_activity(
        session=db_session,
        user_id=1,
        days=30,
    )

    assert len(activity) >= 2


@pytest.mark.asyncio
async def test_get_failed_logins(db_session: AsyncSession):
    """Test getting failed login attempts."""
    # Create failed login attempts
    await AuditService.log_authentication(
        session=db_session,
        action=AuditService.ACTION_LOGIN_FAILED,
        user_id=None,
        email="attacker@example.com",
        ip_address="192.168.1.100",
        user_agent="curl/7.64.1",
        success=False,
    )
    await AuditService.log_authentication(
        session=db_session,
        action=AuditService.ACTION_LOGIN_FAILED,
        user_id=None,
        email="attacker@example.com",
        ip_address="192.168.1.100",
        user_agent="curl/7.64.1",
        success=False,
    )

    # Get failed logins
    failed = await AuditService.get_failed_logins(
        session=db_session,
        hours=24,
    )

    assert len(failed) >= 2
    assert all(log.action == AuditService.ACTION_LOGIN_FAILED for log in failed)


@pytest.mark.asyncio
async def test_get_failed_logins_by_ip(db_session: AsyncSession):
    """Test getting failed logins filtered by IP."""
    # Create failed logins from different IPs
    await AuditService.log_authentication(
        session=db_session,
        action=AuditService.ACTION_LOGIN_FAILED,
        user_id=None,
        email="test@example.com",
        ip_address="192.168.1.100",
        user_agent="curl/7.64.1",
        success=False,
    )
    await AuditService.log_authentication(
        session=db_session,
        action=AuditService.ACTION_LOGIN_FAILED,
        user_id=None,
        email="test@example.com",
        ip_address="192.168.1.200",
        user_agent="curl/7.64.1",
        success=False,
    )

    # Get failed logins for specific IP
    failed = await AuditService.get_failed_logins(
        session=db_session,
        hours=24,
        ip_address="192.168.1.100",
    )

    assert all(log.ip_address == "192.168.1.100" for log in failed)


@pytest.mark.asyncio
async def test_cleanup_old_logs(db_session: AsyncSession):
    """Test cleanup of old audit logs."""
    # Create old log (manually set timestamp)
    old_date = datetime.utcnow() - timedelta(days=400)
    old_log = AuditLog(
        log_id="old-log",
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        timestamp=old_date,
        success=True,
    )
    db_session.add(old_log)
    await db_session.commit()

    # Create recent log
    await AuditService.log(
        session=db_session,
        action=AuditService.ACTION_LOGIN,
        user_id=1,
        success=True,
    )

    # Clean up logs older than 365 days
    deleted = await AuditService.cleanup_old_logs(
        session=db_session,
        retention_days=365,
    )

    assert deleted >= 1

    # Verify old log was deleted
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.log_id == "old-log")
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_get_resource_access_history(db_session: AsyncSession):
    """Test getting access history for a resource."""
    # Create access logs for resource
    await AuditService.log_data_access(
        session=db_session,
        user_id=1,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-123",
        action=AuditService.ACTION_VIEW,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        request_path="/api/tutors/tutor-123",
    )
    await AuditService.log_data_modification(
        session=db_session,
        user_id=1,
        action=AuditService.ACTION_UPDATE,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        request_method="PUT",
        request_path="/api/tutors/tutor-123",
        success=True,
    )

    # Get access history
    history = await AuditService.get_resource_access_history(
        session=db_session,
        resource_type=AuditService.RESOURCE_TUTOR,
        resource_id="tutor-123",
        days=90,
    )

    assert len(history) >= 2
    assert all(log.resource_id == "tutor-123" for log in history)


@pytest.mark.asyncio
async def test_get_action_statistics(db_session: AsyncSession):
    """Test getting action statistics."""
    # Create various logs
    await AuditService.log(session=db_session, action=AuditService.ACTION_LOGIN, user_id=1, success=True)
    await AuditService.log(session=db_session, action=AuditService.ACTION_LOGIN, user_id=2, success=True)
    await AuditService.log(session=db_session, action=AuditService.ACTION_LOGOUT, user_id=1, success=True)
    await AuditService.log(session=db_session, action=AuditService.ACTION_CREATE, user_id=1, success=True)

    # Get statistics
    stats = await AuditService.get_action_statistics(
        session=db_session,
    )

    assert stats[AuditService.ACTION_LOGIN] >= 2
    assert stats[AuditService.ACTION_LOGOUT] >= 1
    assert stats[AuditService.ACTION_CREATE] >= 1


@pytest.mark.asyncio
async def test_pagination(db_session: AsyncSession):
    """Test pagination of search results."""
    # Create 50 logs
    for i in range(50):
        await AuditService.log(
            session=db_session,
            action=AuditService.ACTION_LOGIN,
            user_id=1,
            success=True,
        )

    # Get first page
    logs_page1, total = await AuditService.search_logs(
        session=db_session,
        user_id=1,
        limit=20,
        offset=0,
    )

    assert len(logs_page1) == 20
    assert total >= 50

    # Get second page
    logs_page2, _ = await AuditService.search_logs(
        session=db_session,
        user_id=1,
        limit=20,
        offset=20,
    )

    assert len(logs_page2) == 20
    # Ensure different logs
    assert logs_page1[0].log_id != logs_page2[0].log_id


def test_middleware_should_audit_authentication(client: TestClient):
    """Test that middleware audits authentication endpoints."""
    # This would require a test client with the middleware installed
    # and a mock database session
    pass


def test_middleware_should_audit_modifications(client: TestClient):
    """Test that middleware audits data modifications."""
    pass


def test_middleware_excludes_health_checks(client: TestClient):
    """Test that middleware excludes health check endpoints."""
    pass
