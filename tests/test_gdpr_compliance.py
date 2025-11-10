"""
Test suite for GDPR compliance features.

Tests all GDPR data subject rights implementation:
- Right to Access (Article 15)
- Right to Erasure (Article 17)
- Right to Rectification (Article 16)
- Right to Data Portability (Article 20)
- Consent Management (Article 7)
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, Tutor, Student, UserRole
from src.api.compliance import gdpr_service, consent_manager, data_breach_notifier


@pytest.mark.asyncio
async def test_export_user_data(async_session: AsyncSession):
    """Test GDPR Article 15 - Right to Access."""
    # Create a test user
    user = User(
        id=999,
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        is_active=True,
        is_verified=True,
        roles=[UserRole.STUDENT]
    )
    async_session.add(user)
    await async_session.commit()

    # Export user data
    data = await gdpr_service.export_user_data(
        session=async_session,
        user_id=user.id,
        format="json"
    )

    # Verify export structure
    assert data["export_metadata"]["user_id"] == user.id
    assert data["account_information"]["email"] == user.email
    assert data["account_information"]["full_name"] == user.full_name
    assert "sessions" in data
    assert "feedback" in data
    assert "audit_logs" in data

    # Cleanup
    await async_session.delete(user)
    await async_session.commit()


@pytest.mark.asyncio
async def test_delete_user_data(async_session: AsyncSession):
    """Test GDPR Article 17 - Right to Erasure."""
    # Create a test user
    user = User(
        id=998,
        email="delete_test@example.com",
        hashed_password="hashed",
        full_name="Delete Test User",
        is_active=True,
        is_verified=True,
        roles=[UserRole.TUTOR]
    )
    async_session.add(user)
    await async_session.commit()

    user_id = user.id

    # Delete user data
    summary = await gdpr_service.delete_user_data(
        session=async_session,
        user_id=user_id,
        deletion_reason="Test deletion",
        retain_audit_logs=True
    )

    # Verify deletion
    assert summary["user_id"] == user_id
    assert "records_deleted" in summary
    assert summary["records_deleted"]["user_account"] == 1

    # Verify user is deleted
    from sqlalchemy import select
    result = await async_session.execute(select(User).where(User.id == user_id))
    deleted_user = result.scalar_one_or_none()
    assert deleted_user is None


@pytest.mark.asyncio
async def test_rectify_user_data(async_session: AsyncSession):
    """Test GDPR Article 16 - Right to Rectification."""
    # Create a test user
    user = User(
        id=997,
        email="rectify_test@example.com",
        hashed_password="hashed",
        full_name="Wrong Name",
        is_active=True,
        is_verified=True,
        roles=[UserRole.STUDENT]
    )
    async_session.add(user)
    await async_session.commit()

    # Rectify user data
    corrections = {
        "account": {
            "full_name": "Correct Name"
        }
    }

    summary = await gdpr_service.rectify_user_data(
        session=async_session,
        user_id=user.id,
        corrections=corrections,
        requesting_user_id=user.id
    )

    # Verify rectification
    assert "changes_applied" in summary
    assert "account.full_name" in summary["changes_applied"]
    assert summary["changes_applied"]["account.full_name"]["old"] == "Wrong Name"
    assert summary["changes_applied"]["account.full_name"]["new"] == "Correct Name"

    # Refresh user
    await async_session.refresh(user)
    assert user.full_name == "Correct Name"

    # Cleanup
    await async_session.delete(user)
    await async_session.commit()


@pytest.mark.asyncio
async def test_portable_data_json(async_session: AsyncSession):
    """Test GDPR Article 20 - Right to Data Portability (JSON format)."""
    # Create a test user
    user = User(
        id=996,
        email="portable_test@example.com",
        hashed_password="hashed",
        full_name="Portable Test User",
        is_active=True,
        is_verified=True,
        roles=[UserRole.TUTOR]
    )
    async_session.add(user)
    await async_session.commit()

    # Generate portable data
    data_bytes, mime_type = await gdpr_service.generate_portable_data(
        session=async_session,
        user_id=user.id,
        format="json"
    )

    # Verify format
    assert mime_type == "application/json"
    assert isinstance(data_bytes, bytes)
    assert len(data_bytes) > 0

    # Verify JSON is valid
    import json
    data = json.loads(data_bytes.decode('utf-8'))
    assert data["export_metadata"]["user_id"] == user.id

    # Cleanup
    await async_session.delete(user)
    await async_session.commit()


@pytest.mark.asyncio
async def test_portable_data_pdf(async_session: AsyncSession):
    """Test GDPR Article 20 - Right to Data Portability (PDF format)."""
    # Create a test user
    user = User(
        id=995,
        email="pdf_test@example.com",
        hashed_password="hashed",
        full_name="PDF Test User",
        is_active=True,
        is_verified=True,
        roles=[UserRole.STUDENT]
    )
    async_session.add(user)
    await async_session.commit()

    # Generate portable data
    data_bytes, mime_type = await gdpr_service.generate_portable_data(
        session=async_session,
        user_id=user.id,
        format="pdf"
    )

    # Verify format
    assert mime_type == "application/pdf"
    assert isinstance(data_bytes, bytes)
    assert len(data_bytes) > 0
    # PDF files start with %PDF
    assert data_bytes[:4] == b'%PDF'

    # Cleanup
    await async_session.delete(user)
    await async_session.commit()


@pytest.mark.asyncio
async def test_consent_management(async_session: AsyncSession):
    """Test GDPR Article 7 - Consent Management."""
    # Create a test user
    user = User(
        id=994,
        email="consent_test@example.com",
        hashed_password="hashed",
        full_name="Consent Test User",
        is_active=True,
        is_verified=True,
        roles=[UserRole.STUDENT]
    )
    async_session.add(user)
    await async_session.commit()

    # Grant consent
    await consent_manager.record_consent(
        session=async_session,
        user_id=user.id,
        purpose=consent_manager.PURPOSE_MARKETING,
        granted=True
    )

    # Check consent status
    status = await consent_manager.get_consent_status(
        session=async_session,
        user_id=user.id,
        purpose=consent_manager.PURPOSE_MARKETING
    )
    assert status is True

    # Withdraw consent
    await consent_manager.record_consent(
        session=async_session,
        user_id=user.id,
        purpose=consent_manager.PURPOSE_MARKETING,
        granted=False
    )

    # Check consent status again
    status = await consent_manager.get_consent_status(
        session=async_session,
        user_id=user.id,
        purpose=consent_manager.PURPOSE_MARKETING
    )
    assert status is False

    # Cleanup
    await async_session.delete(user)
    await async_session.commit()


@pytest.mark.asyncio
async def test_withdraw_all_consents(async_session: AsyncSession):
    """Test withdrawing all consents at once."""
    # Create a test user
    user = User(
        id=993,
        email="withdraw_all_test@example.com",
        hashed_password="hashed",
        full_name="Withdraw All Test User",
        is_active=True,
        is_verified=True,
        roles=[UserRole.TUTOR]
    )
    async_session.add(user)
    await async_session.commit()

    # Grant multiple consents
    purposes = [
        consent_manager.PURPOSE_MARKETING,
        consent_manager.PURPOSE_ANALYTICS,
        consent_manager.PURPOSE_PERSONALIZATION
    ]

    for purpose in purposes:
        await consent_manager.record_consent(
            session=async_session,
            user_id=user.id,
            purpose=purpose,
            granted=True
        )

    # Withdraw all consents
    count = await consent_manager.withdraw_all_consents(
        session=async_session,
        user_id=user.id
    )

    assert count == 3

    # Verify all consents are withdrawn
    for purpose in purposes:
        status = await consent_manager.get_consent_status(
            session=async_session,
            user_id=user.id,
            purpose=purpose
        )
        assert status is False

    # Cleanup
    await async_session.delete(user)
    await async_session.commit()


def test_breach_notification_requirements():
    """Test data breach notification requirement logic."""
    # Test authority notification
    assert data_breach_notifier.should_notify_authority(
        severity=data_breach_notifier.SEVERITY_CRITICAL,
        affected_count=10
    ) is True

    assert data_breach_notifier.should_notify_authority(
        severity=data_breach_notifier.SEVERITY_HIGH,
        affected_count=500
    ) is True

    assert data_breach_notifier.should_notify_authority(
        severity=data_breach_notifier.SEVERITY_MEDIUM,
        affected_count=150
    ) is True

    assert data_breach_notifier.should_notify_authority(
        severity=data_breach_notifier.SEVERITY_LOW,
        affected_count=5
    ) is False

    # Test user notification
    assert data_breach_notifier.should_notify_users(
        severity=data_breach_notifier.SEVERITY_CRITICAL,
        data_types=["email"]
    ) is True

    assert data_breach_notifier.should_notify_users(
        severity=data_breach_notifier.SEVERITY_HIGH,
        data_types=["password", "email"]
    ) is True

    assert data_breach_notifier.should_notify_users(
        severity=data_breach_notifier.SEVERITY_MEDIUM,
        data_types=["email"]
    ) is False


@pytest.mark.asyncio
async def test_breach_logging(async_session: AsyncSession):
    """Test data breach logging."""
    breach_id = await data_breach_notifier.log_breach(
        session=async_session,
        breach_description="Test breach for unit testing",
        affected_data_types=["email", "name"],
        affected_user_count=100,
        severity=data_breach_notifier.SEVERITY_MEDIUM,
        discovered_at=datetime.utcnow(),
        contained_at=datetime.utcnow(),
        root_cause="Test root cause",
        mitigation_steps=["Step 1", "Step 2"]
    )

    # Verify breach was logged
    assert breach_id is not None
    assert len(breach_id) > 0


@pytest.mark.asyncio
async def test_breach_notification_templates():
    """Test breach notification email templates."""
    # Critical breach template
    template = await data_breach_notifier.get_breach_notification_template(
        severity=data_breach_notifier.SEVERITY_CRITICAL,
        affected_data_types=["password", "email"]
    )

    assert "subject" in template
    assert "body" in template
    assert "URGENT" in template["subject"]
    assert "password" in template["body"] or "email" in template["body"]

    # High breach template
    template = await data_breach_notifier.get_breach_notification_template(
        severity=data_breach_notifier.SEVERITY_HIGH,
        affected_data_types=["email"]
    )

    assert "subject" in template
    assert "body" in template
