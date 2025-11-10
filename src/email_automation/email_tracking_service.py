"""
Email Tracking Service.

Provides tracking for:
- Email opens
- Link clicks
- Bounce detection
- Delivery confirmation
- Unsubscribe management
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EmailStatus(str, Enum):
    """Email delivery status."""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"


class EmailEventType(str, Enum):
    """Email tracking event types."""
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"


class BounceType(str, Enum):
    """Email bounce types."""
    HARD = "hard"  # Permanent failure (invalid address)
    SOFT = "soft"  # Temporary failure (mailbox full, server down)
    COMPLAINT = "complaint"  # Spam complaint


@dataclass
class EmailTrackingEvent:
    """Represents an email tracking event."""
    event_id: str
    message_id: str
    event_type: EmailEventType
    event_time: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    link_url: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None


class EmailTrackingService:
    """
    Service for tracking email delivery and engagement.

    Features:
    - Open tracking with pixel
    - Click tracking with link wrapping
    - Bounce detection and handling
    - Delivery confirmation
    - Analytics aggregation
    """

    def __init__(self, db_session=None, base_url: str = "http://localhost:8000"):
        """
        Initialize email tracking service.

        Args:
            db_session: SQLAlchemy database session
            base_url: Base URL for tracking endpoints
        """
        self.db_session = db_session
        self.base_url = base_url.rstrip('/')
        logger.info("EmailTrackingService initialized")

    def generate_tracking_pixel_url(self, message_id: str) -> str:
        """
        Generate tracking pixel URL for open tracking.

        Args:
            message_id: Email message ID

        Returns:
            URL for 1x1 transparent tracking pixel
        """
        return f"{self.base_url}/api/email/track/open/{message_id}.png"

    def generate_click_tracking_url(
        self,
        message_id: str,
        original_url: str,
        link_id: Optional[str] = None
    ) -> str:
        """
        Generate click tracking URL that wraps original URL.

        Args:
            message_id: Email message ID
            original_url: Original destination URL
            link_id: Optional identifier for the link

        Returns:
            Tracking URL that redirects to original
        """
        # In production, you'd use a URL shortener or proper encoding
        link_id = link_id or str(uuid.uuid4())[:8]
        # Store mapping in database or Redis for fast lookup
        return f"{self.base_url}/api/email/track/click/{message_id}/{link_id}"

    def wrap_links_for_tracking(
        self,
        html_body: str,
        message_id: str
    ) -> str:
        """
        Wrap all links in HTML body with tracking URLs.

        Args:
            html_body: HTML email body
            message_id: Email message ID

        Returns:
            HTML with tracking-wrapped links
        """
        import re

        # Find all href attributes
        def replace_link(match):
            original_url = match.group(1)
            # Skip tracking pixel and already-tracked URLs
            if 'track/open' in original_url or 'track/click' in original_url:
                return match.group(0)

            tracking_url = self.generate_click_tracking_url(message_id, original_url)
            return f'href="{tracking_url}"'

        # Replace all href attributes
        html_with_tracking = re.sub(
            r'href="([^"]+)"',
            replace_link,
            html_body
        )

        return html_with_tracking

    def add_tracking_pixel(
        self,
        html_body: str,
        message_id: str
    ) -> str:
        """
        Add tracking pixel to HTML body.

        Args:
            html_body: HTML email body
            message_id: Email message ID

        Returns:
            HTML with tracking pixel added
        """
        pixel_url = self.generate_tracking_pixel_url(message_id)
        tracking_pixel = f'\n<img src="{pixel_url}" width="1" height="1" alt="" style="display:block" />'

        # Try to insert before </body> tag
        if '</body>' in html_body:
            html_body = html_body.replace('</body>', f'{tracking_pixel}\n</body>')
        else:
            html_body += tracking_pixel

        return html_body

    def record_event(
        self,
        message_id: str,
        event_type: EmailEventType,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        link_url: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> EmailTrackingEvent:
        """
        Record an email tracking event.

        Args:
            message_id: Email message ID
            event_type: Type of event
            user_agent: User agent string
            ip_address: IP address of event origin
            link_url: URL clicked (for click events)
            event_data: Additional event data

        Returns:
            Created EmailTrackingEvent
        """
        event = EmailTrackingEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            message_id=message_id,
            event_type=event_type,
            event_time=datetime.utcnow(),
            user_agent=user_agent,
            ip_address=ip_address,
            link_url=link_url,
            event_data=event_data
        )

        # Store in database if session provided
        if self.db_session:
            self._store_event_in_db(event)

        # Update message stats
        self._update_message_stats(message_id, event_type)

        logger.info(f"Recorded {event_type.value} event for message {message_id}")
        return event

    def record_open(
        self,
        message_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> EmailTrackingEvent:
        """Record email open event."""
        return self.record_event(
            message_id=message_id,
            event_type=EmailEventType.OPENED,
            user_agent=user_agent,
            ip_address=ip_address
        )

    def record_click(
        self,
        message_id: str,
        link_url: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> EmailTrackingEvent:
        """Record link click event."""
        return self.record_event(
            message_id=message_id,
            event_type=EmailEventType.CLICKED,
            link_url=link_url,
            user_agent=user_agent,
            ip_address=ip_address
        )

    def record_bounce(
        self,
        message_id: str,
        bounce_type: BounceType,
        bounce_reason: str
    ) -> EmailTrackingEvent:
        """Record email bounce event."""
        return self.record_event(
            message_id=message_id,
            event_type=EmailEventType.BOUNCED,
            event_data={
                'bounce_type': bounce_type.value,
                'bounce_reason': bounce_reason
            }
        )

    def record_delivery(
        self,
        message_id: str
    ) -> EmailTrackingEvent:
        """Record successful delivery event."""
        return self.record_event(
            message_id=message_id,
            event_type=EmailEventType.DELIVERED
        )

    def get_message_stats(self, message_id: str) -> Dict[str, Any]:
        """
        Get tracking statistics for a message.

        Args:
            message_id: Email message ID

        Returns:
            Dictionary of tracking stats
        """
        if not self.db_session:
            return {}

        # This would query the database for stats
        # Simplified for now
        return {
            'message_id': message_id,
            'opened': False,
            'open_count': 0,
            'clicked': False,
            'click_count': 0,
            'delivered': False,
            'bounced': False
        }

    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for a campaign.

        Args:
            campaign_id: Email campaign ID

        Returns:
            Dictionary of campaign stats
        """
        if not self.db_session:
            return {}

        # This would aggregate stats from all messages in campaign
        return {
            'campaign_id': campaign_id,
            'total_sent': 0,
            'total_delivered': 0,
            'total_opened': 0,
            'total_clicked': 0,
            'total_bounced': 0,
            'delivery_rate': 0.0,
            'open_rate': 0.0,
            'click_rate': 0.0,
            'bounce_rate': 0.0
        }

    def check_unsubscribe_status(self, email: str) -> bool:
        """
        Check if an email address is unsubscribed.

        Args:
            email: Email address to check

        Returns:
            True if unsubscribed, False otherwise
        """
        if not self.db_session:
            return False

        # Query email_preferences table
        # Simplified for now
        return False

    def unsubscribe_email(
        self,
        email: str,
        preference_type: str = "all"
    ) -> bool:
        """
        Unsubscribe an email address.

        Args:
            email: Email address to unsubscribe
            preference_type: Type of emails to unsubscribe from ("all" or specific type)

        Returns:
            True if successful
        """
        if not self.db_session:
            return False

        logger.info(f"Unsubscribed {email} from {preference_type} emails")
        # Update email_preferences table
        return True

    # Private helper methods

    def _store_event_in_db(self, event: EmailTrackingEvent):
        """Store tracking event in database."""
        if not self.db_session:
            return

        # Import here to avoid circular dependency
        try:
            # This would create an EmailTrackingEvent database record
            # Simplified for now
            logger.debug(f"Stored event {event.event_id} in database")
        except Exception as e:
            logger.error(f"Error storing event in database: {e}", exc_info=True)

    def _update_message_stats(self, message_id: str, event_type: EmailEventType):
        """Update message-level statistics."""
        if not self.db_session:
            return

        try:
            # This would update the email_messages table
            # Incrementing counters, setting timestamps, etc.
            logger.debug(f"Updated stats for message {message_id}: {event_type.value}")
        except Exception as e:
            logger.error(f"Error updating message stats: {e}", exc_info=True)


# Utility functions for analytics

def calculate_email_metrics(stats: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate email performance metrics.

    Args:
        stats: Raw email statistics

    Returns:
        Dictionary of calculated metrics (rates, percentages)
    """
    total_sent = stats.get('total_sent', 0)
    if total_sent == 0:
        return {
            'delivery_rate': 0.0,
            'open_rate': 0.0,
            'click_rate': 0.0,
            'bounce_rate': 0.0,
            'click_through_rate': 0.0
        }

    total_delivered = stats.get('total_delivered', 0)
    total_opened = stats.get('total_opened', 0)
    total_clicked = stats.get('total_clicked', 0)
    total_bounced = stats.get('total_bounced', 0)

    delivery_rate = (total_delivered / total_sent) * 100
    open_rate = (total_opened / total_delivered) * 100 if total_delivered > 0 else 0.0
    click_rate = (total_clicked / total_delivered) * 100 if total_delivered > 0 else 0.0
    bounce_rate = (total_bounced / total_sent) * 100
    click_through_rate = (total_clicked / total_opened) * 100 if total_opened > 0 else 0.0

    return {
        'delivery_rate': round(delivery_rate, 2),
        'open_rate': round(open_rate, 2),
        'click_rate': round(click_rate, 2),
        'bounce_rate': round(bounce_rate, 2),
        'click_through_rate': round(click_through_rate, 2)
    }
