"""
Email alert service for first session prep reminders.

Sends targeted emails to tutors when upcoming first sessions are
predicted to be high-risk, providing context and preparation tips.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

logger = logging.getLogger(__name__)


class FirstSessionEmailService:
    """
    Service for sending first session preparation alert emails to tutors.

    Provides rich context about the student and suggested preparation
    strategies to improve first session outcomes.
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_use_tls: bool = True,
        from_email: str = None,
        from_name: str = "TutorMax Success Team"
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

    def send_first_session_alert(
        self,
        tutor_email: str,
        tutor_name: str,
        student_name: str,
        student_age: int,
        session_date: datetime,
        subject: str,
        risk_score: int,
        risk_level: str,
        top_risk_factors: Dict,
        session_id: str
    ) -> bool:
        """
        Send first session preparation alert to tutor.

        Args:
            tutor_email: Tutor email address
            tutor_name: Tutor name
            student_name: Student name
            student_age: Student age
            session_date: Session scheduled start time
            subject: Session subject
            risk_score: Risk score (0-100)
            risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
            top_risk_factors: Dictionary of top risk factors
            session_id: Session ID

        Returns:
            True if sent successfully, False otherwise
        """
        # Format session date
        session_date_str = session_date.strftime("%A, %B %d at %I:%M %p")

        # Build email subject
        if risk_level in ['HIGH', 'CRITICAL']:
            email_subject = f"Important: Upcoming First Session Prep - {student_name}"
        else:
            email_subject = f"First Session Reminder - {student_name}"

        # Build personalized preparation tips based on risk factors
        prep_tips = self._generate_prep_tips(top_risk_factors, student_age, subject)

        # Build HTML email
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .risk-badge {{ display: inline-block; padding: 8px 16px; border-radius: 4px; font-weight: bold; margin: 10px 0; }}
        .risk-high {{ background-color: #ff5722; color: white; }}
        .risk-medium {{ background-color: #ff9800; color: white; }}
        .risk-low {{ background-color: #4caf50; color: white; }}
        .info-box {{ background-color: #e3f2fd; border-left: 4px solid #2196F3; padding: 15px; margin: 20px 0; }}
        .tips-box {{ background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; }}
        .tip-item {{ margin: 10px 0; padding-left: 20px; }}
        .footer {{ padding: 20px; text-align: center; color: #777; font-size: 12px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>First Session Preparation Alert</h1>
            <p>Help make this first session a success!</p>
        </div>
        <div class="content">
            <p>Hi {tutor_name},</p>

            <p>You have an upcoming <strong>first session</strong> with a new student. First impressions matter, and we want to help you make this session great!</p>

            <div class="info-box">
                <strong>Session Details:</strong><br>
                <strong>Student:</strong> {student_name} (Age {student_age})<br>
                <strong>Subject:</strong> {subject}<br>
                <strong>Date/Time:</strong> {session_date_str}<br>
                <strong>Session ID:</strong> {session_id}
            </div>

            <p><strong>Success Prediction:</strong></p>
            <div class="risk-badge risk-{risk_level.lower()}">
                Risk Level: {risk_level} (Score: {risk_score}/100)
            </div>

            <p>Our AI model has analyzed this upcoming session and identified some factors that may impact student satisfaction. Here's what we found:</p>

            <div class="tips-box">
                <strong>Preparation Tips for This Session:</strong>
                {prep_tips}
            </div>

            <div class="info-box">
                <strong>Best Practices for First Sessions:</strong>
                <ul>
                    <li><strong>Start with an icebreaker:</strong> Spend the first 5 minutes getting to know the student and their learning goals</li>
                    <li><strong>Set clear expectations:</strong> Explain your tutoring approach and what they can expect from sessions</li>
                    <li><strong>Be patient and encouraging:</strong> First sessions can be nerve-wracking for students - create a welcoming environment</li>
                    <li><strong>Assess their level:</strong> Use the first session to understand their current knowledge and learning style</li>
                    <li><strong>End with a plan:</strong> Summarize what you covered and preview the next session</li>
                    <li><strong>Ask for feedback:</strong> Check in during the session to ensure they're following along</li>
                </ul>
            </div>

            <p><strong>Why This Matters:</strong></p>
            <p>Students who have a positive first session are <strong>3x more likely</strong> to continue with regular tutoring and achieve their learning goals. Your preparation can make all the difference!</p>

            <p>If you have any questions or need support, please reach out to your manager or the TutorMax support team.</p>

            <p>Good luck, and thank you for helping students succeed!</p>

            <p><strong>The TutorMax Success Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated alert from the TutorMax performance system.</p>
            <p>&copy; {datetime.now().year} TutorMax. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        # Build plain text version
        text_body = f"""
Hi {tutor_name},

You have an upcoming FIRST SESSION with a new student.

Session Details:
- Student: {student_name} (Age {student_age})
- Subject: {subject}
- Date/Time: {session_date_str}
- Session ID: {session_id}

Success Prediction:
Risk Level: {risk_level} (Score: {risk_score}/100)

Our AI model has identified some factors that may impact student satisfaction. Please take a few minutes to prepare for this session.

{self._generate_prep_tips_text(top_risk_factors, student_age, subject)}

Best Practices for First Sessions:
- Start with an icebreaker
- Set clear expectations
- Be patient and encouraging
- Assess their level
- End with a plan
- Ask for feedback during the session

Students who have a positive first session are 3x more likely to continue with regular tutoring. Your preparation can make all the difference!

Good luck!

The TutorMax Success Team

---
This is an automated alert from the TutorMax performance system.
"""

        return self._send_email(tutor_email, email_subject, html_body, text_body)

    def _generate_prep_tips(
        self,
        top_risk_factors: Dict,
        student_age: int,
        subject: str
    ) -> str:
        """
        Generate personalized preparation tips based on risk factors.

        Args:
            top_risk_factors: Top risk factors from prediction
            student_age: Student age
            subject: Session subject

        Returns:
            HTML formatted tips
        """
        tips = []

        # Analyze risk factors
        for factor_name, factor_data in top_risk_factors.items():
            if 'first_session_success_rate' in factor_name.lower():
                if factor_data.get('value', 0) < 0.7:
                    tips.append("Review your approach to first sessions - consider spending more time on introductions and setting expectations")

            elif 'avg_rating' in factor_name.lower():
                if factor_data.get('value', 0) < 4.0:
                    tips.append("Focus on student engagement and checking for understanding throughout the session")

            elif 'tenure_days' in factor_name.lower():
                if factor_data.get('value', 0) < 90:
                    tips.append("As a newer tutor, take extra time to prepare lesson materials and review best practices for first sessions")

            elif 'engagement_score' in factor_name.lower():
                if factor_data.get('value', 0) < 0.7:
                    tips.append("Plan interactive activities and use engaging teaching methods to keep the student interested")

            elif 'hour' in factor_name.lower() or 'time' in factor_name.lower():
                tips.append("This session is at a time when students may be tired - plan energizing activities and take breaks if needed")

        # Add age-specific tips
        if student_age < 10:
            tips.append(f"Working with a younger student (age {student_age}) - use age-appropriate language, shorter explanations, and more interactive activities")
        elif student_age > 16:
            tips.append(f"Older student (age {student_age}) - they may prefer a more independent learning style with clear goals and minimal hand-holding")

        # Add subject-specific tips
        if subject.lower() in ['math', 'mathematics']:
            tips.append("For math sessions: start with a simple problem to build confidence before moving to challenging concepts")
        elif subject.lower() in ['reading', 'english', 'writing']:
            tips.append("For language arts: find out their interests and incorporate them into examples and activities")
        elif subject.lower() in ['science']:
            tips.append("For science sessions: use real-world examples and demonstrations to make concepts concrete")

        # Default tip if no specific factors identified
        if not tips:
            tips.append("Review the student's background and learning goals before the session")
            tips.append("Prepare 2-3 ice-breaker questions to help the student feel comfortable")

        # Format as HTML list
        tips_html = "<ul>"
        for tip in tips[:5]:  # Limit to top 5 tips
            tips_html += f"<li>{tip}</li>"
        tips_html += "</ul>"

        return tips_html

    def _generate_prep_tips_text(
        self,
        top_risk_factors: Dict,
        student_age: int,
        subject: str
    ) -> str:
        """Generate text-only version of prep tips."""
        tips = []

        # Similar logic as HTML version but plain text
        for factor_name, factor_data in top_risk_factors.items():
            if 'first_session_success_rate' in factor_name.lower():
                if factor_data.get('value', 0) < 0.7:
                    tips.append("- Review your approach to first sessions")

            elif 'avg_rating' in factor_name.lower():
                if factor_data.get('value', 0) < 4.0:
                    tips.append("- Focus on student engagement")

            elif 'tenure_days' in factor_name.lower():
                if factor_data.get('value', 0) < 90:
                    tips.append("- Take extra time to prepare materials")

        if student_age < 10:
            tips.append(f"- Use age-appropriate language for younger student (age {student_age})")

        if not tips:
            tips.append("- Review student background before session")

        return "Preparation Tips:\n" + "\n".join(tips[:5])

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

            logger.info(f"First session alert email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False


def get_first_session_email_service() -> Optional[FirstSessionEmailService]:
    """
    Create FirstSessionEmailService instance from application settings.

    Returns:
        FirstSessionEmailService instance if SMTP is configured, None otherwise
    """
    from ..api.config import settings

    # Check if SMTP is configured
    if not all([settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password]):
        logger.warning("SMTP not configured - first session email alerts disabled")
        return None

    return FirstSessionEmailService(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password=settings.smtp_password,
        smtp_use_tls=settings.smtp_use_tls,
        from_email=settings.smtp_from_email,
        from_name="TutorMax Success Team"
    )
