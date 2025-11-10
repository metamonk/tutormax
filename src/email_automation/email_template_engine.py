"""
Enhanced Email Template Engine with Jinja2.

Provides:
- Professional HTML templates with mobile responsiveness
- Personalization tokens
- Template versioning
- A/B testing support
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailTemplateType(str, Enum):
    """Types of email templates."""
    FEEDBACK_INVITATION = "feedback_invitation"
    FEEDBACK_REMINDER = "feedback_reminder"
    FIRST_SESSION_CHECKIN = "first_session_checkin"
    RESCHEDULING_ALERT = "rescheduling_alert"
    WEEKLY_DIGEST = "weekly_digest"
    MONTHLY_SUMMARY = "monthly_summary"
    PERFORMANCE_REPORT = "performance_report"
    MANAGER_DIGEST = "manager_digest"
    PARENT_NOTIFICATION = "parent_notification"
    INTERVENTION_NOTIFICATION = "intervention_notification"


@dataclass
class EmailTemplate:
    """Represents a compiled email template."""
    template_id: str
    template_type: EmailTemplateType
    version: str
    subject: str
    html_body: str
    text_body: str
    personalization_tokens: List[str]
    ab_test_variant: Optional[str] = None
    metadata: Dict[str, Any] = None


class EmailTemplateEngine:
    """
    Enhanced email template engine using Jinja2.

    Features:
    - Professional responsive HTML templates
    - Personalization with dynamic tokens
    - Template versioning
    - A/B testing support
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the template engine.

        Args:
            templates_dir: Directory containing Jinja2 templates
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self.env.filters['format_date'] = self._format_date
        self.env.filters['format_datetime'] = self._format_datetime
        self.env.filters['format_number'] = self._format_number

        logger.info(f"EmailTemplateEngine initialized with templates from {self.templates_dir}")

    def render_template(
        self,
        template_type: EmailTemplateType,
        context: Dict[str, Any],
        version: str = "v1",
        ab_variant: Optional[str] = None
    ) -> EmailTemplate:
        """
        Render an email template with the given context.

        Args:
            template_type: Type of template to render
            context: Dictionary of variables to render in the template
            version: Template version to use
            ab_variant: A/B test variant (e.g., "A", "B")

        Returns:
            Compiled EmailTemplate object
        """
        try:
            # Determine template filename
            template_name = self._get_template_filename(template_type, version, ab_variant)

            # Load and render HTML template
            html_template = self.env.get_template(f"{template_name}.html")
            html_body = html_template.render(**context)

            # Load and render text template
            try:
                text_template = self.env.get_template(f"{template_name}.txt")
                text_body = text_template.render(**context)
            except Exception:
                # Generate simple text version from context if no text template
                text_body = self._generate_text_fallback(template_type, context)

            # Extract subject from template or context
            subject = context.get('subject', self._get_default_subject(template_type))

            # Get personalization tokens used
            # Note: Jinja2 Template object doesn't have .source, use rendered content instead
            tokens = self._extract_tokens(html_body)

            template_id = f"{template_type.value}_{version}_{ab_variant or 'default'}"

            return EmailTemplate(
                template_id=template_id,
                template_type=template_type,
                version=version,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                personalization_tokens=tokens,
                ab_test_variant=ab_variant,
                metadata={
                    'rendered_at': datetime.utcnow().isoformat(),
                    'context_keys': list(context.keys())
                }
            )

        except Exception as e:
            logger.error(f"Error rendering template {template_type}: {e}", exc_info=True)
            raise

    def render_feedback_invitation(
        self,
        student_name: str,
        tutor_name: str,
        session_date: str,
        feedback_url: str,
        expires_at: str,
        ab_variant: Optional[str] = None
    ) -> EmailTemplate:
        """Render feedback invitation email."""
        context = {
            'student_name': student_name,
            'tutor_name': tutor_name,
            'session_date': session_date,
            'feedback_url': feedback_url,
            'expires_at': expires_at,
            'subject': f"Share Your Feedback - Session with {tutor_name}",
            'current_year': datetime.now().year
        }

        return self.render_template(
            EmailTemplateType.FEEDBACK_INVITATION,
            context,
            ab_variant=ab_variant
        )

    def render_feedback_reminder(
        self,
        student_name: str,
        tutor_name: str,
        session_date: str,
        feedback_url: str,
        hours_since_session: int,
        ab_variant: Optional[str] = None
    ) -> EmailTemplate:
        """Render feedback reminder email (sent 24h after session if no feedback)."""
        context = {
            'student_name': student_name,
            'tutor_name': tutor_name,
            'session_date': session_date,
            'feedback_url': feedback_url,
            'hours_since_session': hours_since_session,
            'subject': f"Reminder: Share Your Feedback - Session with {tutor_name}",
            'current_year': datetime.now().year
        }

        return self.render_template(
            EmailTemplateType.FEEDBACK_REMINDER,
            context,
            ab_variant=ab_variant
        )

    def render_first_session_checkin(
        self,
        tutor_name: str,
        student_name: str,
        session_date: str,
        checkin_url: str,
        ab_variant: Optional[str] = None
    ) -> EmailTemplate:
        """Render first session check-in email (sent 2h after first session)."""
        context = {
            'tutor_name': tutor_name,
            'student_name': student_name,
            'session_date': session_date,
            'checkin_url': checkin_url,
            'subject': f"How Did Your First Session Go with {student_name}?",
            'current_year': datetime.now().year
        }

        return self.render_template(
            EmailTemplateType.FIRST_SESSION_CHECKIN,
            context,
            ab_variant=ab_variant
        )

    def render_rescheduling_alert(
        self,
        tutor_name: str,
        reschedule_count: int,
        days_period: int,
        support_url: str,
        manager_name: Optional[str] = None,
        ab_variant: Optional[str] = None
    ) -> EmailTemplate:
        """Render rescheduling pattern alert email."""
        context = {
            'tutor_name': tutor_name,
            'reschedule_count': reschedule_count,
            'days_period': days_period,
            'support_url': support_url,
            'manager_name': manager_name,
            'subject': "We Noticed You've Been Rescheduling - Need Help?",
            'current_year': datetime.now().year
        }

        return self.render_template(
            EmailTemplateType.RESCHEDULING_ALERT,
            context,
            ab_variant=ab_variant
        )

    def render_manager_digest(
        self,
        manager_name: str,
        period: str,
        summary_data: Dict[str, Any],
        interventions: List[Dict[str, Any]],
        dashboard_url: str,
        ab_variant: Optional[str] = None
    ) -> EmailTemplate:
        """Render manager digest email."""
        context = {
            'manager_name': manager_name,
            'period': period,
            'summary_data': summary_data,
            'interventions': interventions,
            'dashboard_url': dashboard_url,
            'subject': f"TutorMax Manager Digest - {period}",
            'current_year': datetime.now().year
        }

        return self.render_template(
            EmailTemplateType.MANAGER_DIGEST,
            context,
            ab_variant=ab_variant
        )

    def render_performance_report(
        self,
        tutor_name: str,
        period: str,
        metrics: Dict[str, Any],
        achievements: List[str],
        areas_for_improvement: List[str],
        dashboard_url: str,
        ab_variant: Optional[str] = None
    ) -> EmailTemplate:
        """Render tutor performance report email."""
        context = {
            'tutor_name': tutor_name,
            'period': period,
            'metrics': metrics,
            'achievements': achievements,
            'areas_for_improvement': areas_for_improvement,
            'dashboard_url': dashboard_url,
            'subject': f"Your TutorMax Performance Report - {period}",
            'current_year': datetime.now().year
        }

        return self.render_template(
            EmailTemplateType.PERFORMANCE_REPORT,
            context,
            ab_variant=ab_variant
        )

    # Helper methods

    def _get_template_filename(
        self,
        template_type: EmailTemplateType,
        version: str,
        ab_variant: Optional[str]
    ) -> str:
        """Get the template filename."""
        base_name = template_type.value
        if ab_variant:
            return f"{base_name}_{version}_{ab_variant.lower()}"
        return f"{base_name}_{version}"

    def _get_default_subject(self, template_type: EmailTemplateType) -> str:
        """Get default subject line for template type."""
        subjects = {
            EmailTemplateType.FEEDBACK_INVITATION: "Share Your Feedback - TutorMax Session",
            EmailTemplateType.FEEDBACK_REMINDER: "Reminder: Share Your Session Feedback",
            EmailTemplateType.FIRST_SESSION_CHECKIN: "How Did Your First Session Go?",
            EmailTemplateType.RESCHEDULING_ALERT: "We Noticed You've Been Rescheduling",
            EmailTemplateType.WEEKLY_DIGEST: "Your Weekly TutorMax Summary",
            EmailTemplateType.MONTHLY_SUMMARY: "Your Monthly TutorMax Summary",
            EmailTemplateType.PERFORMANCE_REPORT: "Your Performance Report",
            EmailTemplateType.MANAGER_DIGEST: "Manager Digest",
        }
        return subjects.get(template_type, "TutorMax Notification")

    def _extract_tokens(self, template_source: str) -> List[str]:
        """Extract personalization tokens from template source."""
        # Simple extraction - could be enhanced
        import re
        tokens = re.findall(r'\{\{\s*(\w+)\s*\}\}', template_source)
        return list(set(tokens))

    def _generate_text_fallback(
        self,
        template_type: EmailTemplateType,
        context: Dict[str, Any]
    ) -> str:
        """Generate a simple text version when no text template exists."""
        return f"""
{context.get('subject', 'TutorMax Notification')}

This is an automated message from TutorMax.

{context.get('tutor_name', context.get('student_name', 'Hello'))}

---
TutorMax
{datetime.now().year}
"""

    @staticmethod
    def _format_date(value: Any) -> str:
        """Format date for template display."""
        if isinstance(value, datetime):
            return value.strftime('%B %d, %Y')
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return dt.strftime('%B %d, %Y')
            except:
                return str(value)
        return str(value)

    @staticmethod
    def _format_datetime(value: Any) -> str:
        """Format datetime for template display."""
        if isinstance(value, datetime):
            return value.strftime('%B %d, %Y at %I:%M %p')
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                return str(value)
        return str(value)

    @staticmethod
    def _format_number(value: Any, decimal_places: int = 1) -> str:
        """Format number for template display."""
        try:
            num = float(value)
            return f"{num:.{decimal_places}f}"
        except:
            return str(value)
