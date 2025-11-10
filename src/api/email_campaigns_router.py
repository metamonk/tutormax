"""
FastAPI router for email campaign management.

Provides endpoints for:
- Creating scheduled campaigns
- Managing campaign recipients
- Viewing campaign stats
- Campaign scheduling and execution
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from src.database.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email/campaigns", tags=["email-campaigns"])


# Pydantic models for request/response
class CampaignCreate(BaseModel):
    """Schema for creating a new campaign."""
    name: str
    template_type: str
    subject: str
    scheduled_at: Optional[datetime] = None
    recipient_type: str  # 'tutors', 'managers', 'students'
    recipient_ids: Optional[List[str]] = None  # Specific recipients, or None for all
    ab_variant: Optional[str] = None


class CampaignResponse(BaseModel):
    """Schema for campaign response."""
    campaign_id: str
    name: str
    template_type: str
    subject: str
    status: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    recipient_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    created_at: datetime


class CampaignStatsResponse(BaseModel):
    """Schema for campaign statistics."""
    campaign_id: str
    name: str
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    bounce_rate: float


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new email campaign.

    Args:
        campaign: Campaign creation data
        db: Database session

    Returns:
        Created campaign details
    """
    try:
        # In production, this would create an EmailCampaign record
        # For now, return mock response

        campaign_id = f"camp_{datetime.utcnow().timestamp():.0f}"

        logger.info(f"Created campaign {campaign_id}: {campaign.name}")

        return CampaignResponse(
            campaign_id=campaign_id,
            name=campaign.name,
            template_type=campaign.template_type,
            subject=campaign.subject,
            status="scheduled" if campaign.scheduled_at else "draft",
            scheduled_at=campaign.scheduled_at,
            sent_at=None,
            recipient_count=len(campaign.recipient_ids) if campaign.recipient_ids else 0,
            delivered_count=0,
            opened_count=0,
            clicked_count=0,
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error creating campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List email campaigns with optional filtering.

    Args:
        status: Filter by status (scheduled, sending, completed, failed)
        limit: Maximum number of campaigns to return
        offset: Offset for pagination
        db: Database session

    Returns:
        List of campaigns
    """
    try:
        # In production, query EmailCampaign table
        # For now, return empty list

        logger.info(f"Listing campaigns with status={status}, limit={limit}, offset={offset}")

        return []

    except Exception as e:
        logger.error(f"Error listing campaigns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details for a specific campaign.

    Args:
        campaign_id: Campaign ID
        db: Database session

    Returns:
        Campaign details
    """
    try:
        # In production, query EmailCampaign table
        # For now, return mock data

        logger.info(f"Getting campaign {campaign_id}")

        # Mock response - replace with actual database query
        raise HTTPException(status_code=404, detail="Campaign not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def get_campaign_stats(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for a specific campaign.

    Args:
        campaign_id: Campaign ID
        db: Database session

    Returns:
        Campaign statistics including delivery and engagement metrics
    """
    try:
        # In production, aggregate stats from email_messages and email_tracking_events
        # For now, return mock data

        logger.info(f"Getting stats for campaign {campaign_id}")

        # Mock stats - replace with actual aggregation query
        return CampaignStatsResponse(
            campaign_id=campaign_id,
            name="Mock Campaign",
            total_sent=100,
            total_delivered=95,
            total_opened=68,
            total_clicked=32,
            total_bounced=5,
            delivery_rate=95.0,
            open_rate=71.6,  # 68/95 * 100
            click_rate=33.7,  # 32/95 * 100
            bounce_rate=5.0
        )

    except Exception as e:
        logger.error(f"Error getting campaign stats for {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/send")
async def send_campaign_now(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a campaign immediately (override scheduled time).

    Args:
        campaign_id: Campaign ID
        db: Database session

    Returns:
        Success confirmation
    """
    try:
        # In production:
        # 1. Get campaign from database
        # 2. Update status to 'sending'
        # 3. Trigger Celery task to process campaign
        # 4. Return confirmation

        logger.info(f"Triggering immediate send for campaign {campaign_id}")

        return {
            "success": True,
            "message": f"Campaign {campaign_id} queued for sending",
            "campaign_id": campaign_id
        }

    except Exception as e:
        logger.error(f"Error sending campaign {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a campaign (only if not sent).

    Args:
        campaign_id: Campaign ID
        db: Database session

    Returns:
        Success confirmation
    """
    try:
        # In production:
        # 1. Check campaign status
        # 2. Only allow deletion of draft/scheduled campaigns
        # 3. Delete campaign and related records

        logger.info(f"Deleting campaign {campaign_id}")

        return {
            "success": True,
            "message": f"Campaign {campaign_id} deleted"
        }

    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/overview")
async def get_email_analytics_overview(
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Get email analytics overview for dashboard.

    Args:
        days: Number of days to analyze
        db: Database session

    Returns:
        Analytics overview with key metrics
    """
    try:
        # In production, aggregate metrics from email_messages and email_tracking_events
        # For now, return mock data for the dashboard

        logger.info(f"Getting email analytics overview for last {days} days")

        return {
            "success": True,
            "period_days": days,
            "metrics": {
                "total_sent": 15420,
                "total_delivered": 14648,
                "total_opened": 10253,
                "total_clicked": 4108,
                "total_bounced": 772,
                "delivery_rate": 95.0,
                "open_rate": 70.0,
                "click_rate": 28.1,
                "bounce_rate": 5.0
            },
            "by_template_type": [
                {
                    "template_type": "feedback_reminder",
                    "total_sent": 4800,
                    "open_rate": 72.5,
                    "click_rate": 45.2
                },
                {
                    "template_type": "first_session_checkin",
                    "total_sent": 1200,
                    "open_rate": 85.3,
                    "click_rate": 52.8
                },
                {
                    "template_type": "rescheduling_alert",
                    "total_sent": 380,
                    "open_rate": 91.2,
                    "click_rate": 38.4
                },
                {
                    "template_type": "performance_report",
                    "total_sent": 2400,
                    "open_rate": 78.6,
                    "click_rate": 35.7
                },
                {
                    "template_type": "manager_digest",
                    "total_sent": 120,
                    "open_rate": 95.8,
                    "click_rate": 68.3
                }
            ],
            "trends": {
                "sent_by_day": [520, 505, 530, 498, 515, 525, 510],
                "opened_by_day": [364, 354, 371, 349, 361, 368, 357],
                "clicked_by_day": [146, 142, 149, 140, 145, 147, 143]
            }
        }

    except Exception as e:
        logger.error(f"Error getting email analytics overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
