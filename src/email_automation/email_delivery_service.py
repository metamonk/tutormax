"""
Enhanced Email Delivery Service with Retry Logic.

Provides:
- SMTP delivery with retry logic
- Priority queue management
- Delivery tracking integration
- Template rendering integration
- Bounce handling
"""

import logging
import smtplib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
import time

from .email_template_engine import EmailTemplateEngine, EmailTemplateType
from .email_tracking_service import EmailTrackingService, EmailStatus

logger = logging.getLogger(__name__)


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EmailMessage:
    """Represents an email message to be sent."""
    message_id: str
    recipient_email: str
    recipient_id: Optional[str]
    recipient_type: Optional[str]
    subject: str
    html_body: str
    text_body: str
    template_type: str
    template_version: str
    priority: EmailPriority = EmailPriority.MEDIUM
    scheduled_at: Optional[datetime] = None
    campaign_id: Optional[str] = None
    ab_variant: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EnhancedEmailService:
    """
    Enhanced email service with retry logic and tracking.

    Features:
    - SMTP delivery with exponential backoff retry
    - Priority queue support
    - Automatic tracking pixel and link wrapping
    - Bounce detection and handling
    - Delivery confirmation
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_use_tls: bool = True,
        from_email: Optional[str] = None,
        from_name: str = "TutorMax",
        template_engine: Optional[EmailTemplateEngine] = None,
        tracking_service: Optional[EmailTrackingService] = None,
        max_retries: int = 3,
        retry_delay: int = 60,
        db_session=None
    ):
        """
        Initialize enhanced email service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            smtp_use_tls: Whether to use TLS
            from_email: Sender email address
            from_name: Sender display name
            template_engine: EmailTemplateEngine instance
            tracking_service: EmailTrackingService instance
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            db_session: Database session for persistence
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.from_email = from_email or smtp_user
        self.from_name = from_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.db_session = db_session

        # Initialize template engine
        self.template_engine = template_engine or EmailTemplateEngine()

        # Initialize tracking service
        self.tracking_service = tracking_service or EmailTrackingService(
            db_session=db_session
        )

        logger.info("EnhancedEmailService initialized")

    def send_email(
        self,
        email_message: EmailMessage,
        enable_tracking: bool = True,
        retry_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Send an email message with retry logic.

        Args:
            email_message: EmailMessage to send
            enable_tracking: Whether to add tracking pixel and wrap links
            retry_on_failure: Whether to retry on failure

        Returns:
            Dictionary with send result
        """
        result = {
            'message_id': email_message.message_id,
            'success': False,
            'status': EmailStatus.QUEUED.value,
            'attempts': 0,
            'error': None
        }

        # Prepare email body with tracking if enabled
        html_body = email_message.html_body
        if enable_tracking:
            html_body = self.tracking_service.add_tracking_pixel(
                html_body,
                email_message.message_id
            )
            html_body = self.tracking_service.wrap_links_for_tracking(
                html_body,
                email_message.message_id
            )

        # Retry loop
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                result['attempts'] = retry_count + 1
                result['status'] = EmailStatus.SENDING.value

                # Send via SMTP
                self._send_via_smtp(
                    to_email=email_message.recipient_email,
                    subject=email_message.subject,
                    html_body=html_body,
                    text_body=email_message.text_body
                )

                # Mark as sent
                result['success'] = True
                result['status'] = EmailStatus.SENT.value
                result['sent_at'] = datetime.utcnow()

                # Record sent event
                from .email_tracking_service import EmailEventType
                self.tracking_service.record_event(
                    message_id=email_message.message_id,
                    event_type=EmailEventType.SENT
                )

                logger.info(
                    f"Email sent successfully to {email_message.recipient_email} "
                    f"(message_id: {email_message.message_id})"
                )
                break

            except smtplib.SMTPRecipientsRefused as e:
                # Permanent failure - don't retry
                error_msg = f"Recipients refused: {e}"
                logger.error(error_msg)
                result['error'] = error_msg
                result['status'] = EmailStatus.BOUNCED.value

                # Record bounce
                self.tracking_service.record_bounce(
                    message_id=email_message.message_id,
                    bounce_type='hard',
                    bounce_reason=error_msg
                )
                break

            except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
                # Temporary failure - retry if enabled
                error_msg = f"SMTP error: {e}"
                logger.warning(
                    f"Failed to send email (attempt {retry_count + 1}/{self.max_retries + 1}): {error_msg}"
                )
                result['error'] = error_msg

                if not retry_on_failure or retry_count >= self.max_retries:
                    result['status'] = EmailStatus.FAILED.value
                    logger.error(f"Email send failed after {retry_count + 1} attempts")
                    break

                # Exponential backoff
                delay = self.retry_delay * (2 ** retry_count)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                retry_count += 1

            except Exception as e:
                # Unexpected error
                error_msg = f"Unexpected error: {e}"
                logger.error(error_msg, exc_info=True)
                result['error'] = error_msg
                result['status'] = EmailStatus.FAILED.value
                break

        # Update database if session provided
        if self.db_session:
            self._update_message_in_db(email_message, result)

        return result

    def send_templated_email(
        self,
        template_type: EmailTemplateType,
        recipient_email: str,
        context: Dict[str, Any],
        recipient_id: Optional[str] = None,
        recipient_type: Optional[str] = None,
        priority: EmailPriority = EmailPriority.MEDIUM,
        campaign_id: Optional[str] = None,
        ab_variant: Optional[str] = None,
        enable_tracking: bool = True
    ) -> Dict[str, Any]:
        """
        Render and send a templated email.

        Args:
            template_type: Type of email template
            recipient_email: Recipient email address
            context: Template context variables
            recipient_id: Recipient ID (tutor_id, student_id, etc.)
            recipient_type: Type of recipient (tutor, student, manager)
            priority: Email priority level
            campaign_id: Campaign ID if part of campaign
            ab_variant: A/B test variant
            enable_tracking: Whether to enable tracking

        Returns:
            Dictionary with send result
        """
        try:
            # Render template
            template = self.template_engine.render_template(
                template_type=template_type,
                context=context,
                ab_variant=ab_variant
            )

            # Create email message
            message = EmailMessage(
                message_id=f"msg_{uuid.uuid4().hex[:16]}",
                recipient_email=recipient_email,
                recipient_id=recipient_id,
                recipient_type=recipient_type,
                subject=template.subject,
                html_body=template.html_body,
                text_body=template.text_body,
                template_type=template_type.value,
                template_version=template.version,
                priority=priority,
                campaign_id=campaign_id,
                ab_variant=ab_variant,
                metadata={
                    'template_id': template.template_id,
                    'personalization_tokens': template.personalization_tokens
                }
            )

            # Send email
            return self.send_email(message, enable_tracking=enable_tracking)

        except Exception as e:
            logger.error(f"Error sending templated email: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'status': EmailStatus.FAILED.value
            }

    def send_batch_emails(
        self,
        messages: List[EmailMessage],
        enable_tracking: bool = True,
        respect_priority: bool = True
    ) -> Dict[str, Any]:
        """
        Send multiple emails in batch.

        Args:
            messages: List of EmailMessage objects
            enable_tracking: Whether to enable tracking
            respect_priority: Whether to send in priority order

        Returns:
            Dictionary with batch send results
        """
        # Sort by priority if requested
        if respect_priority:
            priority_order = {
                EmailPriority.CRITICAL: 0,
                EmailPriority.HIGH: 1,
                EmailPriority.MEDIUM: 2,
                EmailPriority.LOW: 3
            }
            messages = sorted(messages, key=lambda m: priority_order.get(m.priority, 2))

        results = {
            'total': len(messages),
            'successful': 0,
            'failed': 0,
            'results': []
        }

        for message in messages:
            result = self.send_email(message, enable_tracking=enable_tracking)
            results['results'].append(result)

            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1

        logger.info(
            f"Batch send complete: {results['successful']} successful, "
            f"{results['failed']} failed out of {results['total']}"
        )

        return results

    # Private methods

    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ):
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body

        Raises:
            SMTPException: On SMTP errors
        """
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Message-ID'] = f"<{uuid.uuid4()}@tutormax.com>"

        # Add text part
        if text_body:
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            msg.attach(part1)

        # Add HTML part
        part2 = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(part2)

        # Send via SMTP
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
            if self.smtp_use_tls:
                server.starttls()

            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    def _update_message_in_db(
        self,
        message: EmailMessage,
        result: Dict[str, Any]
    ):
        """
        Update email message record in database.

        Args:
            message: EmailMessage object
            result: Send result dictionary
        """
        if not self.db_session:
            return

        try:
            # This would update the email_messages table
            # Simplified for now
            logger.debug(f"Updated message {message.message_id} in database")
        except Exception as e:
            logger.error(f"Error updating message in database: {e}", exc_info=True)


def get_email_service_from_settings() -> EnhancedEmailService:
    """
    Create EnhancedEmailService from application settings.

    Returns:
        Configured EnhancedEmailService instance
    """
    from src.api.config import settings

    return EnhancedEmailService(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password=settings.smtp_password,
        smtp_use_tls=settings.smtp_use_tls,
        from_email=settings.smtp_from_email,
        from_name=settings.smtp_from_name
    )
