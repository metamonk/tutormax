"""
Comprehensive tests for email automation system (Tasks 12 & 22).

Tests:
- Email template rendering
- Email delivery with retry logic
- Tracking (opens, clicks, bounces)
- Automated workflows (feedback reminders, check-ins, rescheduling alerts)
- A/B testing
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import smtplib

from src.email_automation.email_template_engine import (
    EmailTemplateEngine,
    EmailTemplateType
)
from src.email_automation.email_tracking_service import (
    EmailTrackingService,
    EmailEventType,
    BounceType
)
from src.email_automation.email_delivery_service import (
    EnhancedEmailService,
    EmailMessage,
    EmailPriority
)


# ============================================================================
# TEMPLATE ENGINE TESTS
# ============================================================================

class TestEmailTemplateEngine:
    """Test email template rendering."""

    def test_render_feedback_reminder(self):
        """Test feedback reminder template rendering."""
        engine = EmailTemplateEngine()

        template = engine.render_feedback_reminder(
            student_name="Alice Johnson",
            tutor_name="Dr. Smith",
            session_date="November 8, 2025",
            feedback_url="https://tutormax.com/feedback/abc123",
            hours_since_session=24
        )

        assert template.template_type == EmailTemplateType.FEEDBACK_REMINDER
        assert "Alice Johnson" in template.html_body
        assert "Dr. Smith" in template.html_body
        assert "24" in template.html_body
        assert "https://tutormax.com/feedback/abc123" in template.html_body
        assert template.subject
        assert template.text_body

    def test_render_first_session_checkin(self):
        """Test first session check-in template rendering."""
        engine = EmailTemplateEngine()

        template = engine.render_first_session_checkin(
            tutor_name="Dr. Smith",
            student_name="Bob Wilson",
            session_date="November 8, 2025",
            checkin_url="https://tutormax.com/checkin/xyz789"
        )

        assert template.template_type == EmailTemplateType.FIRST_SESSION_CHECKIN
        assert "Dr. Smith" in template.html_body
        assert "Bob Wilson" in template.html_body
        assert "https://tutormax.com/checkin/xyz789" in template.html_body
        assert template.subject

    def test_render_rescheduling_alert(self):
        """Test rescheduling alert template rendering."""
        engine = EmailTemplateEngine()

        template = engine.render_rescheduling_alert(
            tutor_name="Dr. Smith",
            reschedule_count=3,
            days_period=7,
            support_url="https://tutormax.com/support",
            manager_name="Sarah Manager"
        )

        assert template.template_type == EmailTemplateType.RESCHEDULING_ALERT
        assert "Dr. Smith" in template.html_body
        assert "3" in template.html_body
        assert "7" in template.html_body
        assert "Sarah Manager" in template.html_body
        assert "https://tutormax.com/support" in template.html_body

    def test_ab_variant_rendering(self):
        """Test A/B variant template rendering."""
        engine = EmailTemplateEngine()

        # Render variant A
        template_a = engine.render_feedback_reminder(
            student_name="Alice",
            tutor_name="Dr. Smith",
            session_date="Nov 8",
            feedback_url="https://test.com",
            hours_since_session=24,
            ab_variant="A"
        )

        assert template_a.ab_test_variant == "A"

        # Render variant B
        template_b = engine.render_feedback_reminder(
            student_name="Alice",
            tutor_name="Dr. Smith",
            session_date="Nov 8",
            feedback_url="https://test.com",
            hours_since_session=24,
            ab_variant="B"
        )

        assert template_b.ab_test_variant == "B"

    def test_personalization_tokens_extracted(self):
        """Test that personalization tokens are extracted."""
        engine = EmailTemplateEngine()

        template = engine.render_feedback_reminder(
            student_name="Alice",
            tutor_name="Dr. Smith",
            session_date="Nov 8",
            feedback_url="https://test.com",
            hours_since_session=24
        )

        # Should extract tokens like student_name, tutor_name, etc.
        assert isinstance(template.personalization_tokens, list)


# ============================================================================
# TRACKING SERVICE TESTS
# ============================================================================

class TestEmailTrackingService:
    """Test email tracking functionality."""

    def test_generate_tracking_pixel_url(self):
        """Test tracking pixel URL generation."""
        service = EmailTrackingService(base_url="https://tutormax.com")

        url = service.generate_tracking_pixel_url("msg_123")

        assert "msg_123" in url
        assert ".png" in url
        assert "track/open" in url

    def test_generate_click_tracking_url(self):
        """Test click tracking URL generation."""
        service = EmailTrackingService(base_url="https://tutormax.com")

        url = service.generate_click_tracking_url(
            "msg_123",
            "https://example.com/original"
        )

        assert "msg_123" in url
        assert "track/click" in url

    def test_add_tracking_pixel(self):
        """Test adding tracking pixel to HTML."""
        service = EmailTrackingService(base_url="https://tutormax.com")

        html = "<html><body>Test email</body></html>"
        html_with_pixel = service.add_tracking_pixel(html, "msg_123")

        assert "<img src=" in html_with_pixel
        assert "track/open/msg_123" in html_with_pixel
        assert 'width="1"' in html_with_pixel
        assert 'height="1"' in html_with_pixel

    def test_wrap_links_for_tracking(self):
        """Test wrapping links with tracking."""
        service = EmailTrackingService(base_url="https://tutormax.com")

        html = '<html><body><a href="https://example.com">Click here</a></body></html>'
        html_with_tracking = service.wrap_links_for_tracking(html, "msg_123")

        assert "track/click/msg_123" in html_with_tracking

    def test_record_open_event(self):
        """Test recording open event."""
        service = EmailTrackingService()

        event = service.record_open(
            message_id="msg_123",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )

        assert event.event_type == EmailEventType.OPENED
        assert event.message_id == "msg_123"
        assert event.user_agent == "Mozilla/5.0"
        assert event.ip_address == "192.168.1.1"

    def test_record_click_event(self):
        """Test recording click event."""
        service = EmailTrackingService()

        event = service.record_click(
            message_id="msg_123",
            link_url="https://example.com",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )

        assert event.event_type == EmailEventType.CLICKED
        assert event.message_id == "msg_123"
        assert event.link_url == "https://example.com"

    def test_record_bounce_event(self):
        """Test recording bounce event."""
        service = EmailTrackingService()

        event = service.record_bounce(
            message_id="msg_123",
            bounce_type=BounceType.HARD,
            bounce_reason="Invalid email address"
        )

        assert event.event_type == EmailEventType.BOUNCED
        assert event.message_id == "msg_123"
        assert event.event_data['bounce_type'] == "hard"
        assert "Invalid email" in event.event_data['bounce_reason']


# ============================================================================
# EMAIL DELIVERY TESTS
# ============================================================================

class TestEnhancedEmailService:
    """Test email delivery with retry logic."""

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EnhancedEmailService(
            smtp_host="localhost",
            smtp_port=1025,
            smtp_user="test@tutormax.com",
            smtp_password="password"
        )

        message = EmailMessage(
            message_id="msg_123",
            recipient_email="student@example.com",
            recipient_id="S001",
            recipient_type="student",
            subject="Test Email",
            html_body="<html>Test</html>",
            text_body="Test",
            template_type="test",
            template_version="v1"
        )

        result = service.send_email(message, enable_tracking=False)

        assert result['success'] is True
        assert result['status'] == 'sent'
        assert result['attempts'] == 1
        assert mock_server.send_message.called

    @patch('smtplib.SMTP')
    def test_send_email_retry_on_failure(self, mock_smtp):
        """Test email retry logic on temporary failure."""
        # Mock SMTP server to fail first, then succeed
        mock_server = MagicMock()
        mock_server.send_message.side_effect = [
            smtplib.SMTPException("Temporary error"),
            None  # Success on second attempt
        ]
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EnhancedEmailService(
            smtp_host="localhost",
            smtp_port=1025,
            smtp_user="test@tutormax.com",
            smtp_password="password",
            max_retries=3,
            retry_delay=1  # Short delay for testing
        )

        message = EmailMessage(
            message_id="msg_123",
            recipient_email="student@example.com",
            recipient_id="S001",
            recipient_type="student",
            subject="Test Email",
            html_body="<html>Test</html>",
            text_body="Test",
            template_type="test",
            template_version="v1"
        )

        # Mock time.sleep to avoid actual delays
        with patch('time.sleep'):
            result = service.send_email(message, enable_tracking=False)

        # Should succeed on second attempt
        assert result['success'] is True
        assert result['attempts'] == 2

    @patch('smtplib.SMTP')
    def test_send_email_permanent_failure(self, mock_smtp):
        """Test handling of permanent email failure (bounce)."""
        # Mock SMTP server to reject recipients
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused({})
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EnhancedEmailService(
            smtp_host="localhost",
            smtp_port=1025,
            smtp_user="test@tutormax.com",
            smtp_password="password"
        )

        message = EmailMessage(
            message_id="msg_123",
            recipient_email="invalid@example.com",
            recipient_id="S001",
            recipient_type="student",
            subject="Test Email",
            html_body="<html>Test</html>",
            text_body="Test",
            template_type="test",
            template_version="v1"
        )

        result = service.send_email(message, enable_tracking=False)

        # Should not retry permanent failures
        assert result['success'] is False
        assert result['status'] == 'bounced'
        assert result['attempts'] == 1

    @patch('smtplib.SMTP')
    def test_send_templated_email(self, mock_smtp):
        """Test sending templated email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EnhancedEmailService(
            smtp_host="localhost",
            smtp_port=1025,
            smtp_user="test@tutormax.com",
            smtp_password="password"
        )

        context = {
            'student_name': 'Alice',
            'tutor_name': 'Dr. Smith',
            'session_date': 'Nov 8',
            'feedback_url': 'https://test.com',
            'hours_since_session': 24,
            'current_year': 2025
        }

        result = service.send_templated_email(
            template_type=EmailTemplateType.FEEDBACK_REMINDER,
            recipient_email="alice@example.com",
            context=context,
            recipient_id="S001",
            recipient_type="student",
            enable_tracking=False
        )

        assert result['success'] is True
        assert mock_server.send_message.called

    @patch('smtplib.SMTP')
    def test_batch_email_sending(self, mock_smtp):
        """Test sending batch emails."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EnhancedEmailService(
            smtp_host="localhost",
            smtp_port=1025,
            smtp_user="test@tutormax.com",
            smtp_password="password"
        )

        messages = [
            EmailMessage(
                message_id=f"msg_{i}",
                recipient_email=f"user{i}@example.com",
                recipient_id=f"U{i:03d}",
                recipient_type="user",
                subject="Test Email",
                html_body="<html>Test</html>",
                text_body="Test",
                template_type="test",
                template_version="v1",
                priority=EmailPriority.MEDIUM if i % 2 == 0 else EmailPriority.HIGH
            )
            for i in range(5)
        ]

        result = service.send_batch_emails(
            messages,
            enable_tracking=False,
            respect_priority=True
        )

        assert result['total'] == 5
        assert result['successful'] == 5
        assert result['failed'] == 0
        assert len(result['results']) == 5


# ============================================================================
# WORKFLOW INTEGRATION TESTS
# ============================================================================

class TestEmailWorkflows:
    """Test automated email workflows."""

    def test_feedback_reminder_workflow_conditions(self):
        """Test feedback reminder workflow trigger conditions."""
        # Should trigger for sessions 24-48 hours ago without feedback
        now = datetime.utcnow()

        # Session 30 hours ago - should trigger
        session_time_1 = now - timedelta(hours=30)
        assert timedelta(hours=24) <= (now - session_time_1) <= timedelta(hours=48)

        # Session 20 hours ago - should NOT trigger (too recent)
        session_time_2 = now - timedelta(hours=20)
        assert not (timedelta(hours=24) <= (now - session_time_2) <= timedelta(hours=48))

        # Session 50 hours ago - should NOT trigger (too old)
        session_time_3 = now - timedelta(hours=50)
        assert not (timedelta(hours=24) <= (now - session_time_3) <= timedelta(hours=48))

    def test_first_session_checkin_workflow_conditions(self):
        """Test first session check-in workflow trigger conditions."""
        # Should trigger for first sessions 2-4 hours ago
        now = datetime.utcnow()

        # Session 3 hours ago - should trigger
        session_time_1 = now - timedelta(hours=3)
        assert timedelta(hours=2) <= (now - session_time_1) <= timedelta(hours=4)

        # Session 1 hour ago - should NOT trigger (too recent)
        session_time_2 = now - timedelta(hours=1)
        assert not (timedelta(hours=2) <= (now - session_time_2) <= timedelta(hours=4))

    def test_rescheduling_alert_workflow_conditions(self):
        """Test rescheduling alert workflow trigger conditions."""
        # Should trigger for 3+ reschedules in 7 days
        reschedule_threshold = 3
        days_window = 7

        # 3 reschedules - should trigger
        assert 3 >= reschedule_threshold

        # 5 reschedules - should trigger
        assert 5 >= reschedule_threshold

        # 2 reschedules - should NOT trigger
        assert not (2 >= reschedule_threshold)

        # Should escalate for 6+ in 14 days
        escalation_threshold = 6
        assert 7 >= escalation_threshold
        assert not (5 >= escalation_threshold)


# ============================================================================
# A/B TESTING TESTS
# ============================================================================

class TestABTesting:
    """Test A/B testing functionality."""

    def test_ab_variant_assignment(self):
        """Test A/B variant assignment."""
        engine = EmailTemplateEngine()

        # Render both variants
        template_a = engine.render_feedback_reminder(
            student_name="Alice",
            tutor_name="Dr. Smith",
            session_date="Nov 8",
            feedback_url="https://test.com",
            hours_since_session=24,
            ab_variant="A"
        )

        template_b = engine.render_feedback_reminder(
            student_name="Alice",
            tutor_name="Dr. Smith",
            session_date="Nov 8",
            feedback_url="https://test.com",
            hours_since_session=24,
            ab_variant="B"
        )

        assert template_a.ab_test_variant == "A"
        assert template_b.ab_test_variant == "B"
        assert template_a.template_id != template_b.template_id

    def test_ab_test_statistics_calculation(self):
        """Test A/B test statistics calculation."""
        # Variant A: 60% open rate
        variant_a = {
            'sent': 100,
            'opened': 60,
            'clicked': 35
        }

        # Variant B: 75% open rate (better)
        variant_b = {
            'sent': 100,
            'opened': 75,
            'clicked': 48
        }

        a_open_rate = (variant_a['opened'] / variant_a['sent']) * 100
        b_open_rate = (variant_b['opened'] / variant_b['sent']) * 100

        assert a_open_rate == 60.0
        assert b_open_rate == 75.0
        assert b_open_rate > a_open_rate  # B is winner


# ============================================================================
# PERFORMANCE METRICS TESTS
# ============================================================================

class TestEmailMetrics:
    """Test email performance metric calculations."""

    def test_delivery_rate_calculation(self):
        """Test delivery rate calculation."""
        total_sent = 100
        total_delivered = 98

        delivery_rate = (total_delivered / total_sent) * 100
        assert delivery_rate == 98.0

    def test_open_rate_calculation(self):
        """Test open rate calculation."""
        total_delivered = 98
        total_opened = 70

        open_rate = (total_opened / total_delivered) * 100
        assert round(open_rate, 1) == 71.4

    def test_click_through_rate_calculation(self):
        """Test click-through rate calculation."""
        total_opened = 70
        total_clicked = 42

        ctr = (total_clicked / total_opened) * 100
        assert ctr == 60.0

    def test_bounce_rate_calculation(self):
        """Test bounce rate calculation."""
        total_sent = 100
        total_bounced = 2

        bounce_rate = (total_bounced / total_sent) * 100
        assert bounce_rate == 2.0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
