"""
Email Automation Module for TutorMax.

This module provides:
- Enhanced email templates with Jinja2
- Email delivery tracking (opens, clicks, bounces)
- Scheduled email campaigns
- Automated workflow triggers
- A/B testing capabilities
"""

from .email_template_engine import EmailTemplateEngine, EmailTemplate
from .email_tracking_service import EmailTrackingService
from .email_delivery_service import EnhancedEmailService

__all__ = [
    "EmailTemplateEngine",
    "EmailTemplate",
    "EmailTrackingService",
    "EnhancedEmailService",
]
