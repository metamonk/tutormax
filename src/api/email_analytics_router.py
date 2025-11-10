"""
Email Analytics Dashboard API Router.

Provides endpoints for:
- Campaign performance metrics
- Email delivery tracking
- Open rates and click-through rates
- A/B test results
- Unsubscribe management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc

from src.database.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email-analytics", tags=["Email Analytics"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class EmailCampaignStats(BaseModel):
    """Campaign statistics model."""
    campaign_id: str
    campaign_name: str
    campaign_type: str
    status: str
    total_recipients: int
    emails_sent: int
    emails_delivered: int
    emails_opened: int
    emails_clicked: int
    emails_bounced: int
    emails_failed: int
    unsubscribes: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    bounce_rate: float
    click_through_rate: float
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailMessageDetails(BaseModel):
    """Individual email message details."""
    message_id: str
    recipient_email: str
    recipient_id: Optional[str]
    recipient_type: Optional[str]
    subject: str
    template_type: str
    template_version: str
    ab_variant: Optional[str]
    status: str
    priority: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    first_clicked_at: Optional[datetime]
    bounce_type: Optional[str]
    failure_reason: Optional[str]
    open_count: int
    click_count: int

    class Config:
        from_attributes = True


class ABTestResults(BaseModel):
    """A/B test comparison results."""
    campaign_id: str
    variant_a_stats: dict
    variant_b_stats: dict
    winner: Optional[str] = None
    confidence_level: Optional[float] = None


class EmailPreferences(BaseModel):
    """User email preferences."""
    email: EmailStr
    unsubscribed_all: bool = False
    feedback_reminders: bool = True
    session_checkins: bool = True
    performance_reports: bool = True
    weekly_digests: bool = True
    monthly_summaries: bool = True
    marketing_emails: bool = True
    system_notifications: bool = True


class OverallEmailMetrics(BaseModel):
    """Overall email performance metrics."""
    period_days: int
    total_emails_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_failed: int
    avg_delivery_rate: float
    avg_open_rate: float
    avg_click_rate: float
    avg_bounce_rate: float
    total_unsubscribes: int


# ============================================================================
# CAMPAIGN ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/campaigns", response_model=List[EmailCampaignStats])
async def get_email_campaigns(
    status: Optional[str] = Query(None, description="Filter by status"),
    campaign_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of email campaigns with statistics.

    Args:
        status: Filter by campaign status (draft, scheduled, sending, completed, cancelled)
        campaign_type: Filter by campaign type
        limit: Maximum results to return
        offset: Results offset for pagination
        db: Database session

    Returns:
        List of email campaigns with statistics
    """
    try:
        # In production, would query email_campaigns table
        # Simplified mock data for now

        mock_campaigns = [
            EmailCampaignStats(
                campaign_id="camp_001",
                campaign_name="Weekly Tutor Digest - Week 45",
                campaign_type="weekly_digest",
                status="completed",
                total_recipients=150,
                emails_sent=150,
                emails_delivered=147,
                emails_opened=105,
                emails_clicked=62,
                emails_bounced=3,
                emails_failed=0,
                unsubscribes=1,
                delivery_rate=98.0,
                open_rate=71.4,
                click_rate=42.2,
                bounce_rate=2.0,
                click_through_rate=59.0,
                scheduled_at=datetime.utcnow() - timedelta(days=7),
                started_at=datetime.utcnow() - timedelta(days=7),
                completed_at=datetime.utcnow() - timedelta(days=7, hours=1)
            ),
            EmailCampaignStats(
                campaign_id="camp_002",
                campaign_name="Feedback Reminders - Batch 123",
                campaign_type="feedback_reminder",
                status="completed",
                total_recipients=85,
                emails_sent=85,
                emails_delivered=84,
                emails_opened=48,
                emails_clicked=32,
                emails_bounced=1,
                emails_failed=0,
                unsubscribes=0,
                delivery_rate=98.8,
                open_rate=57.1,
                click_rate=38.1,
                bounce_rate=1.2,
                click_through_rate=66.7,
                scheduled_at=datetime.utcnow() - timedelta(days=1),
                started_at=datetime.utcnow() - timedelta(days=1),
                completed_at=datetime.utcnow() - timedelta(hours=23)
            )
        ]

        return mock_campaigns[:limit]

    except Exception as e:
        logger.error(f"Error fetching campaigns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}", response_model=EmailCampaignStats)
async def get_campaign_details(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed statistics for a specific campaign.

    Args:
        campaign_id: Campaign ID
        db: Database session

    Returns:
        Campaign statistics
    """
    try:
        # In production, would query database
        # Mock response for now
        return EmailCampaignStats(
            campaign_id=campaign_id,
            campaign_name="Test Campaign",
            campaign_type="weekly_digest",
            status="completed",
            total_recipients=100,
            emails_sent=100,
            emails_delivered=98,
            emails_opened=70,
            emails_clicked=45,
            emails_bounced=2,
            emails_failed=0,
            unsubscribes=1,
            delivery_rate=98.0,
            open_rate=71.4,
            click_rate=45.9,
            bounce_rate=2.0,
            click_through_rate=64.3,
            scheduled_at=datetime.utcnow() - timedelta(days=1),
            completed_at=datetime.utcnow() - timedelta(hours=23)
        )

    except Exception as e:
        logger.error(f"Error fetching campaign {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}/messages", response_model=List[EmailMessageDetails])
async def get_campaign_messages(
    campaign_id: str,
    status: Optional[str] = Query(None, description="Filter by message status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get individual messages for a campaign.

    Args:
        campaign_id: Campaign ID
        status: Filter by message status
        limit: Maximum results
        offset: Results offset
        db: Database session

    Returns:
        List of email messages
    """
    try:
        # In production, would query email_messages table
        # Mock data for now
        return []

    except Exception as e:
        logger.error(f"Error fetching messages for campaign {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@router.get("/campaigns/{campaign_id}/ab-test", response_model=ABTestResults)
async def get_ab_test_results(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get A/B test results for a campaign.

    Args:
        campaign_id: Campaign ID
        db: Database session

    Returns:
        A/B test comparison results
    """
    try:
        # In production, would calculate from database
        # Mock data showing variant B performing better
        return ABTestResults(
            campaign_id=campaign_id,
            variant_a_stats={
                "emails_sent": 75,
                "emails_opened": 45,
                "emails_clicked": 28,
                "open_rate": 60.0,
                "click_rate": 37.3,
                "click_through_rate": 62.2
            },
            variant_b_stats={
                "emails_sent": 75,
                "emails_opened": 58,
                "emails_clicked": 39,
                "open_rate": 77.3,
                "click_rate": 52.0,
                "click_through_rate": 67.2
            },
            winner="B",
            confidence_level=0.95
        )

    except Exception as e:
        logger.error(f"Error fetching A/B test results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OVERALL METRICS ENDPOINTS
# ============================================================================

@router.get("/metrics/overall", response_model=OverallEmailMetrics)
async def get_overall_metrics(
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall email performance metrics for a period.

    Args:
        period_days: Number of days to analyze
        db: Database session

    Returns:
        Overall email metrics
    """
    try:
        # In production, would aggregate from database
        # Mock data showing healthy email performance
        return OverallEmailMetrics(
            period_days=period_days,
            total_emails_sent=2450,
            total_delivered=2401,
            total_opened=1681,
            total_clicked=1008,
            total_bounced=49,
            total_failed=5,
            avg_delivery_rate=98.0,
            avg_open_rate=70.0,
            avg_click_rate=42.0,
            avg_bounce_rate=2.0,
            total_unsubscribes=12
        )

    except Exception as e:
        logger.error(f"Error fetching overall metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/template/{template_type}", response_model=dict)
async def get_template_performance(
    template_type: str,
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance metrics for a specific template type.

    Args:
        template_type: Type of email template
        period_days: Number of days to analyze
        db: Database session

    Returns:
        Template performance metrics
    """
    try:
        # In production, would aggregate from database
        return {
            "template_type": template_type,
            "period_days": period_days,
            "total_sent": 450,
            "avg_open_rate": 68.5,
            "avg_click_rate": 41.2,
            "avg_delivery_rate": 98.5,
            "trend": "improving"
        }

    except Exception as e:
        logger.error(f"Error fetching template metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PREFERENCES & UNSUBSCRIBE ENDPOINTS
# ============================================================================

@router.get("/preferences/{email}", response_model=EmailPreferences)
async def get_email_preferences(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get email preferences for an address.

    Args:
        email: Email address
        db: Database session

    Returns:
        Email preferences
    """
    try:
        # In production, would query email_preferences table
        return EmailPreferences(
            email=email,
            unsubscribed_all=False,
            feedback_reminders=True,
            session_checkins=True,
            performance_reports=True,
            weekly_digests=True,
            monthly_summaries=True,
            marketing_emails=True,
            system_notifications=True
        )

    except Exception as e:
        logger.error(f"Error fetching preferences for {email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/{email}", response_model=EmailPreferences)
async def update_email_preferences(
    email: str,
    preferences: EmailPreferences,
    db: AsyncSession = Depends(get_db)
):
    """
    Update email preferences for an address.

    Args:
        email: Email address
        preferences: Updated preferences
        db: Database session

    Returns:
        Updated email preferences
    """
    try:
        # In production, would update email_preferences table
        logger.info(f"Updated email preferences for {email}")
        return preferences

    except Exception as e:
        logger.error(f"Error updating preferences for {email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe/{email}")
async def unsubscribe_email(
    email: str,
    preference_type: str = Query("all", description="Type to unsubscribe from"),
    db: AsyncSession = Depends(get_db)
):
    """
    Unsubscribe an email address.

    Args:
        email: Email address to unsubscribe
        preference_type: Type of emails to unsubscribe from
        db: Database session

    Returns:
        Success confirmation
    """
    try:
        # In production, would update email_preferences table
        logger.info(f"Unsubscribed {email} from {preference_type}")

        return {
            "success": True,
            "email": email,
            "unsubscribed_from": preference_type,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error unsubscribing {email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRACKING ENDPOINTS (Called by email clients)
# ============================================================================

@router.get("/track/open/{message_id}.png")
async def track_email_open(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Track email open event (1x1 transparent pixel).

    Args:
        message_id: Email message ID
        db: Database session

    Returns:
        1x1 transparent PNG
    """
    try:
        from fastapi.responses import Response

        # Record open event in database
        logger.info(f"Email opened: {message_id}")

        # In production, would call email_tracking_service.record_open()

        # Return 1x1 transparent PNG
        pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

        return Response(content=pixel, media_type="image/png")

    except Exception as e:
        logger.error(f"Error tracking open for {message_id}: {e}", exc_info=True)
        # Still return pixel even on error
        pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(content=pixel, media_type="image/png")


@router.get("/track/click/{message_id}/{link_id}")
async def track_email_click(
    message_id: str,
    link_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Track email click event and redirect to original URL.

    Args:
        message_id: Email message ID
        link_id: Link identifier
        db: Database session

    Returns:
        Redirect to original URL
    """
    try:
        from fastapi.responses import RedirectResponse

        # Record click event in database
        logger.info(f"Email link clicked: {message_id}/{link_id}")

        # In production:
        # 1. Record click with email_tracking_service.record_click()
        # 2. Look up original URL from database/Redis
        # 3. Redirect to original URL

        # For now, redirect to homepage
        return RedirectResponse(url="https://tutormax.com")

    except Exception as e:
        logger.error(f"Error tracking click for {message_id}/{link_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
