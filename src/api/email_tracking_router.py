"""
FastAPI router for email tracking endpoints.

Provides endpoints for:
- Open tracking (tracking pixel)
- Click tracking (link redirects)
- Unsubscribe management
- Email metrics and analytics
"""

import logging
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import io

from src.database.database import get_db
from src.email_automation.email_tracking_service import (
    EmailTrackingService,
    EmailEventType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email/track", tags=["email-tracking"])


# 1x1 transparent PNG pixel for open tracking
TRANSPARENT_PIXEL = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
    0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
    0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
    0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
])


@router.get("/open/{message_id}.png")
async def track_email_open(
    message_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Track email open via 1x1 transparent tracking pixel.

    Args:
        message_id: Unique email message ID
        request: FastAPI request object for accessing headers
        db: Database session

    Returns:
        1x1 transparent PNG image
    """
    try:
        # Get tracking service
        tracking_service = EmailTrackingService(db_session=db)

        # Extract user agent and IP
        user_agent = request.headers.get("user-agent")
        # Get real IP from X-Forwarded-For header if behind proxy
        ip_address = request.headers.get("x-forwarded-for")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None

        # Record open event
        tracking_service.record_open(
            message_id=message_id,
            user_agent=user_agent,
            ip_address=ip_address
        )

        logger.info(f"Recorded email open for message {message_id}")

    except Exception as e:
        # Don't fail the pixel - just log the error
        logger.error(f"Error tracking email open for {message_id}: {e}", exc_info=True)

    # Always return the tracking pixel
    return StreamingResponse(
        io.BytesIO(TRANSPARENT_PIXEL),
        media_type="image/png",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.get("/click/{message_id}/{link_id}")
async def track_email_click(
    message_id: str,
    link_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Track email link click and redirect to original URL.

    Args:
        message_id: Unique email message ID
        link_id: Unique link identifier
        request: FastAPI request object
        db: Database session

    Returns:
        Redirect to original URL
    """
    try:
        # Get tracking service
        tracking_service = EmailTrackingService(db_session=db)

        # Extract user agent and IP
        user_agent = request.headers.get("user-agent")
        ip_address = request.headers.get("x-forwarded-for")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None

        # Look up original URL from database or Redis
        # For now, use a placeholder - in production you'd query:
        # SELECT original_url FROM email_click_tracking WHERE message_id = ? AND link_id = ?
        original_url = f"https://tutormax.com/redirect-placeholder/{message_id}/{link_id}"

        # Record click event
        tracking_service.record_click(
            message_id=message_id,
            link_url=original_url,
            user_agent=user_agent,
            ip_address=ip_address
        )

        logger.info(f"Recorded email click for message {message_id}, link {link_id}")

        # Redirect to original URL
        return RedirectResponse(url=original_url, status_code=302)

    except Exception as e:
        logger.error(f"Error tracking email click for {message_id}/{link_id}: {e}", exc_info=True)
        # Redirect to home page on error
        return RedirectResponse(url="https://tutormax.com", status_code=302)


@router.post("/unsubscribe")
async def unsubscribe_email(
    email: str,
    preference_type: str = "all",
    db: AsyncSession = Depends(get_db)
):
    """
    Unsubscribe an email address from emails.

    Args:
        email: Email address to unsubscribe
        preference_type: Type of emails to unsubscribe from ("all" or specific type)
        db: Database session

    Returns:
        Success confirmation
    """
    try:
        tracking_service = EmailTrackingService(db_session=db)

        # Unsubscribe the email
        success = tracking_service.unsubscribe_email(
            email=email,
            preference_type=preference_type
        )

        if success:
            logger.info(f"Unsubscribed {email} from {preference_type} emails")
            return {
                "success": True,
                "message": f"Successfully unsubscribed {email} from {preference_type} emails"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to unsubscribe")

    except Exception as e:
        logger.error(f"Error unsubscribing {email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{message_id}")
async def get_email_status(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get tracking status for a specific email message.

    Args:
        message_id: Unique email message ID
        db: Database session

    Returns:
        Email tracking statistics
    """
    try:
        tracking_service = EmailTrackingService(db_session=db)

        # Get message stats
        stats = tracking_service.get_message_stats(message_id)

        return {
            "success": True,
            "message_id": message_id,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting email status for {message_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaign/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated statistics for an email campaign.

    Args:
        campaign_id: Email campaign ID
        db: Database session

    Returns:
        Campaign statistics including delivery, open, and click rates
    """
    try:
        tracking_service = EmailTrackingService(db_session=db)

        # Get campaign stats
        stats = tracking_service.get_campaign_stats(campaign_id)

        return {
            "success": True,
            "campaign_id": campaign_id,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting campaign stats for {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
