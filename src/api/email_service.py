"""
Email service for sending feedback invitations and notifications.

Supports SMTP email delivery with HTML templates for student feedback links
and parent notifications for COPPA compliance.
"""

import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails related to feedback authentication.

    Supports:
    - Student feedback invitations with token links
    - Parent notifications for under-13 students (COPPA)
    - HTML email templates
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_use_tls: bool = True,
        from_email: str = None,
        from_name: str = "TutorMax"
    ):
        """
        Initialize email service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            smtp_use_tls: Whether to use TLS (default: True)
            from_email: Sender email address (default: smtp_user)
            from_name: Sender display name
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.from_email = from_email or smtp_user
        self.from_name = from_name

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (fallback)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add text and HTML parts
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)

            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()

                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_feedback_invitation(
        self,
        student_email: str,
        student_name: str,
        tutor_name: str,
        session_date: str,
        feedback_url: str,
        expires_at: str
    ) -> bool:
        """
        Send feedback invitation to student.

        Args:
            student_email: Student email address
            student_name: Student name
            tutor_name: Tutor name
            session_date: Session date string
            feedback_url: Complete feedback URL with token
            expires_at: Token expiration date string

        Returns:
            True if sent successfully, False otherwise
        """
        subject = f"Share Your Feedback - Session with {tutor_name}"

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>How Was Your Session?</h1>
        </div>
        <div class="content">
            <p>Hi {student_name},</p>

            <p>Thank you for your recent tutoring session with <strong>{tutor_name}</strong> on {session_date}.</p>

            <p>We'd love to hear your feedback! Your input helps us improve our tutoring services and ensures you get the best learning experience possible.</p>

            <p>Please take a moment to share your thoughts:</p>

            <p style="text-align: center;">
                <a href="{feedback_url}" class="button">Share Your Feedback</a>
            </p>

            <p><strong>This link will expire on {expires_at}</strong></p>

            <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background-color: #eee; padding: 10px;">{feedback_url}</p>

            <p>Thank you for being part of TutorMax!</p>
        </div>
        <div class="footer">
            <p>This is an automated message from TutorMax. Please do not reply to this email.</p>
            <p>&copy; {datetime.now().year} TutorMax. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        text_body = f"""
Hi {student_name},

Thank you for your recent tutoring session with {tutor_name} on {session_date}.

We'd love to hear your feedback! Your input helps us improve our tutoring services.

Please share your feedback by visiting this link:
{feedback_url}

This link will expire on {expires_at}

Thank you for being part of TutorMax!

---
This is an automated message from TutorMax. Please do not reply to this email.
"""

        return self._send_email(student_email, subject, html_body, text_body)

    def send_parent_notification(
        self,
        parent_email: str,
        parent_name: str,
        student_name: str,
        tutor_name: str,
        session_date: str,
        feedback_url: str
    ) -> bool:
        """
        Send notification to parent for under-13 student (COPPA compliance).

        Args:
            parent_email: Parent email address
            parent_name: Parent name
            student_name: Student name
            tutor_name: Tutor name
            session_date: Session date string
            feedback_url: Complete feedback URL with token

        Returns:
            True if sent successfully, False otherwise
        """
        subject = f"Feedback Request for {student_name}'s Tutoring Session"

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .notice {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Parent Notification: Feedback Request</h1>
        </div>
        <div class="content">
            <p>Dear {parent_name},</p>

            <p>Your child, <strong>{student_name}</strong>, recently completed a tutoring session with <strong>{tutor_name}</strong> on {session_date}.</p>

            <div class="notice">
                <strong>Parent Consent Required</strong><br>
                As your child is under 13 years old, we require your consent before collecting feedback in accordance with COPPA (Children's Online Privacy Protection Act) regulations.
            </div>

            <p>We value feedback from our students to help improve our tutoring services. If you consent to your child providing feedback about their session, you can:</p>

            <ol>
                <li>Review the feedback questions together</li>
                <li>Provide parental consent at the beginning of the form</li>
                <li>Help your child submit their feedback</li>
            </ol>

            <p style="text-align: center;">
                <a href="{feedback_url}" class="button">Review Feedback Form</a>
            </p>

            <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background-color: #eee; padding: 10px;">{feedback_url}</p>

            <p>If you have any questions or concerns, please don't hesitate to contact us.</p>

            <p>Thank you for trusting TutorMax with your child's education!</p>
        </div>
        <div class="footer">
            <p>This is an automated message from TutorMax. Please do not reply to this email.</p>
            <p>&copy; {datetime.now().year} TutorMax. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        text_body = f"""
Dear {parent_name},

Your child, {student_name}, recently completed a tutoring session with {tutor_name} on {session_date}.

PARENT CONSENT REQUIRED
As your child is under 13 years old, we require your consent before collecting feedback in accordance with COPPA regulations.

If you consent to your child providing feedback, please visit:
{feedback_url}

Thank you for trusting TutorMax with your child's education!

---
This is an automated message from TutorMax. Please do not reply to this email.
"""

        return self._send_email(parent_email, subject, html_body, text_body)


def get_email_service_from_settings() -> Optional[EmailService]:
    """
    Create EmailService instance from application settings.

    Returns:
        EmailService instance if SMTP is configured, None otherwise
    """
    from .config import settings

    # Check if SMTP is configured
    smtp_host = getattr(settings, 'smtp_host', None)
    smtp_port = getattr(settings, 'smtp_port', None)
    smtp_user = getattr(settings, 'smtp_user', None)
    smtp_password = getattr(settings, 'smtp_password', None)

    if not all([smtp_host, smtp_port, smtp_user, smtp_password]):
        logger.warning("SMTP not configured - email sending disabled")
        return None

    return EmailService(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        smtp_use_tls=getattr(settings, 'smtp_use_tls', True),
        from_email=getattr(settings, 'smtp_from_email', None),
        from_name=getattr(settings, 'smtp_from_name', 'TutorMax')
    )
