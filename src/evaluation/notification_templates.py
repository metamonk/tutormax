"""
Notification Templates for Intervention System

This module provides email and in-app notification templates for each
intervention type in the TutorMax system. Templates support both plain text
and HTML formats.
"""

from typing import Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class InterventionType(str, Enum):
    """Types of interventions (matches intervention_framework.py)."""
    # Automated interventions
    AUTOMATED_COACHING = "automated_coaching"
    TRAINING_MODULE = "training_module"
    FIRST_SESSION_CHECKIN = "first_session_checkin"
    RESCHEDULING_ALERT = "rescheduling_alert"

    # Human-reviewed interventions
    MANAGER_COACHING = "manager_coaching"
    PEER_MENTORING = "peer_mentoring"
    PERFORMANCE_IMPROVEMENT_PLAN = "performance_improvement_plan"
    RETENTION_INTERVIEW = "retention_interview"

    # Positive interventions
    RECOGNITION = "recognition"


@dataclass
class NotificationTemplate:
    """
    Template for a notification.

    Attributes:
        subject: Email subject line
        body_text: Plain text body
        body_html: HTML body
        recipient_type: 'tutor' or 'staff'
    """
    subject: str
    body_text: str
    body_html: str
    recipient_type: str  # 'tutor' or 'staff'


# ============================================================================
# TEMPLATE FORMATTING HELPERS
# ============================================================================

def format_tutor_name(tutor_name: str) -> str:
    """Format tutor name for templates."""
    return tutor_name.split()[0] if tutor_name else "there"


def create_html_wrapper(content: str, title: str = "TutorMax Notification") -> str:
    """Wrap content in HTML email template."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e1e8ed;
            border-top: none;
        }}
        .footer {{
            background: #f7f9fa;
            padding: 20px;
            border-radius: 0 0 8px 8px;
            text-align: center;
            font-size: 0.9em;
            color: #657786;
        }}
        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            margin: 10px 0;
        }}
        .button:hover {{
            background: #5568d3;
        }}
        .critical {{
            color: #e0245e;
            font-weight: bold;
        }}
        .high {{
            color: #f45d22;
            font-weight: bold;
        }}
        .positive {{
            color: #17bf63;
            font-weight: bold;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
    </div>
    <div class="content">
        {content}
    </div>
    <div class="footer">
        <p>This is an automated message from TutorMax.<br>
        For questions, contact support@tutormax.com</p>
    </div>
</body>
</html>
"""


# ============================================================================
# AUTOMATED INTERVENTION TEMPLATES
# ============================================================================

def template_automated_coaching(tutor_name: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for automated coaching intervention."""
    first_name = format_tutor_name(tutor_name)

    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = "💡 Coaching Tips to Enhance Your Performance"

    body_text = f"""Hi {first_name},

We noticed some opportunities to help you succeed even more as a tutor!

{trigger_reason}

Here are some coaching tips for you:

{actions_text}

These small adjustments can make a big difference in your sessions. We're here to support your growth!

Best regards,
The TutorMax Team
"""

    body_html = create_html_wrapper(f"""
        <p>Hi {first_name},</p>

        <p>We noticed some opportunities to help you succeed even more as a tutor!</p>

        <p><strong>Observation:</strong> {trigger_reason}</p>

        <h3>💡 Coaching Tips for You:</h3>
        <ul>
            {actions_html}
        </ul>

        <p>These small adjustments can make a big difference in your sessions. We're here to support your growth!</p>

        <p>Best regards,<br>The TutorMax Team</p>
    """, "Coaching Tips")

    return NotificationTemplate(subject, body_text, body_html, "tutor")


def template_training_module(tutor_name: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for training module assignment."""
    first_name = format_tutor_name(tutor_name)

    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = "📚 New Training Modules Available for You"

    body_text = f"""Hi {first_name},

Great news! We've identified some training resources that could help you level up your tutoring skills.

{trigger_reason}

Recommended training:

{actions_text}

These modules are designed to be practical and immediately applicable to your sessions.

Access your training: https://tutormax.com/training

Best regards,
The TutorMax Team
"""

    body_html = create_html_wrapper(f"""
        <p>Hi {first_name},</p>

        <p>Great news! We've identified some training resources that could help you level up your tutoring skills.</p>

        <p><strong>Why these modules?</strong> {trigger_reason}</p>

        <h3>📚 Recommended Training:</h3>
        <ul>
            {actions_html}
        </ul>

        <p>These modules are designed to be practical and immediately applicable to your sessions.</p>

        <p style="text-align: center; margin: 30px 0;">
            <a href="https://tutormax.com/training" class="button">Access Your Training</a>
        </p>

        <p>Best regards,<br>The TutorMax Team</p>
    """, "New Training Available")

    return NotificationTemplate(subject, body_text, body_html, "tutor")


def template_first_session_checkin(tutor_name: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for first session check-in."""
    first_name = format_tutor_name(tutor_name)

    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = "🎯 First Session Success: Let's Help You Excel"

    body_text = f"""Hi {first_name},

First sessions are crucial for building lasting student relationships. We'd like to help you make them even better!

{trigger_reason}

Support we're offering:

{actions_text}

Remember: a great first session can lead to months of successful tutoring relationships!

Schedule a check-in: https://tutormax.com/coaching

Best regards,
Your TutorMax Coaching Team
"""

    body_html = create_html_wrapper(f"""
        <p>Hi {first_name},</p>

        <p>First sessions are crucial for building lasting student relationships. We'd like to help you make them even better!</p>

        <p><strong class="high">What we noticed:</strong> {trigger_reason}</p>

        <h3>🎯 Support We're Offering:</h3>
        <ul>
            {actions_html}
        </ul>

        <p><strong>Remember:</strong> A great first session can lead to months of successful tutoring relationships!</p>

        <p style="text-align: center; margin: 30px 0;">
            <a href="https://tutormax.com/coaching" class="button">Schedule a Check-In</a>
        </p>

        <p>Best regards,<br>Your TutorMax Coaching Team</p>
    """, "First Session Success")

    return NotificationTemplate(subject, body_text, body_html, "tutor")


def template_rescheduling_alert(tutor_name: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for rescheduling alert."""
    first_name = format_tutor_name(tutor_name)

    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = "📅 Scheduling Reminder: Consistency Matters"

    body_text = f"""Hi {first_name},

We wanted to reach out about your recent scheduling patterns.

{trigger_reason}

Tips for better schedule management:

{actions_text}

Consistent scheduling helps build trust with students and leads to better outcomes for everyone.

Need help? Contact support@tutormax.com

Best regards,
The TutorMax Team
"""

    body_html = create_html_wrapper(f"""
        <p>Hi {first_name},</p>

        <p>We wanted to reach out about your recent scheduling patterns.</p>

        <p><strong class="high">Observation:</strong> {trigger_reason}</p>

        <h3>📅 Tips for Better Schedule Management:</h3>
        <ul>
            {actions_html}
        </ul>

        <p><em>Consistent scheduling helps build trust with students and leads to better outcomes for everyone.</em></p>

        <p>Need help? Contact <a href="mailto:support@tutormax.com">support@tutormax.com</a></p>

        <p>Best regards,<br>The TutorMax Team</p>
    """, "Scheduling Reminder")

    return NotificationTemplate(subject, body_text, body_html, "tutor")


# ============================================================================
# HUMAN-REVIEWED INTERVENTION TEMPLATES (FOR STAFF)
# ============================================================================

def template_manager_coaching(tutor_name: str, tutor_id: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for manager coaching intervention (staff notification)."""
    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = f"🔔 Action Required: Manager Coaching for {tutor_name}"

    body_text = f"""Manager Coaching Intervention Required

Tutor: {tutor_name} ({tutor_id})
Priority: HIGH

Trigger Reason:
{trigger_reason}

Recommended Actions:

{actions_text}

Please schedule a coaching session within the next 5 days.

View full details: https://tutormax.com/interventions/{tutor_id}

Best regards,
TutorMax Intervention System
"""

    body_html = create_html_wrapper(f"""
        <h2 class="high">Manager Coaching Intervention Required</h2>

        <p><strong>Tutor:</strong> {tutor_name} ({tutor_id})<br>
        <strong>Priority:</strong> <span class="high">HIGH</span></p>

        <p><strong>Trigger Reason:</strong><br>{trigger_reason}</p>

        <h3>Recommended Actions:</h3>
        <ul>
            {actions_html}
        </ul>

        <p><strong>Timeline:</strong> Please schedule a coaching session within the next 5 days.</p>

        <p style="text-align: center; margin: 30px 0;">
            <a href="https://tutormax.com/interventions/{tutor_id}" class="button">View Full Details</a>
        </p>

        <p>Best regards,<br>TutorMax Intervention System</p>
    """, "Manager Coaching Required")

    return NotificationTemplate(subject, body_text, body_html, "staff")


def template_peer_mentoring(tutor_name: str, tutor_id: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for peer mentoring intervention (staff notification)."""
    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = f"🤝 Peer Mentoring Recommendation: {tutor_name}"

    body_text = f"""Peer Mentoring Intervention Recommended

Tutor: {tutor_name} ({tutor_id})
Priority: MEDIUM

Trigger Reason:
{trigger_reason}

Recommended Actions:

{actions_text}

Please assign a peer mentor within the next 10 days.

View full details: https://tutormax.com/interventions/{tutor_id}

Best regards,
TutorMax Intervention System
"""

    body_html = create_html_wrapper(f"""
        <h2>🤝 Peer Mentoring Intervention Recommended</h2>

        <p><strong>Tutor:</strong> {tutor_name} ({tutor_id})<br>
        <strong>Priority:</strong> MEDIUM</p>

        <p><strong>Trigger Reason:</strong><br>{trigger_reason}</p>

        <h3>Recommended Actions:</h3>
        <ul>
            {actions_html}
        </ul>

        <p><strong>Timeline:</strong> Please assign a peer mentor within the next 10 days.</p>

        <p style="text-align: center; margin: 30px 0;">
            <a href="https://tutormax.com/interventions/{tutor_id}" class="button">View Full Details</a>
        </p>

        <p>Best regards,<br>TutorMax Intervention System</p>
    """, "Peer Mentoring Recommendation")

    return NotificationTemplate(subject, body_text, body_html, "staff")


def template_performance_improvement_plan(tutor_name: str, tutor_id: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for performance improvement plan (staff notification)."""
    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = f"⚠️ CRITICAL: Performance Improvement Plan - {tutor_name}"

    body_text = f"""CRITICAL: Performance Improvement Plan Required

Tutor: {tutor_name} ({tutor_id})
Priority: CRITICAL

Trigger Reason:
{trigger_reason}

Recommended Actions:

{actions_text}

⚠️ IMMEDIATE ACTION REQUIRED: Please create a formal PIP within 2 days.

View full details: https://tutormax.com/interventions/{tutor_id}

Best regards,
TutorMax Intervention System
"""

    body_html = create_html_wrapper(f"""
        <h2 class="critical">⚠️ CRITICAL: Performance Improvement Plan Required</h2>

        <p><strong>Tutor:</strong> {tutor_name} ({tutor_id})<br>
        <strong>Priority:</strong> <span class="critical">CRITICAL</span></p>

        <p><strong>Trigger Reason:</strong><br>{trigger_reason}</p>

        <h3>Recommended Actions:</h3>
        <ul>
            {actions_html}
        </ul>

        <p class="critical"><strong>⚠️ IMMEDIATE ACTION REQUIRED</strong><br>
        Please create a formal PIP within 2 days.</p>

        <p style="text-align: center; margin: 30px 0;">
            <a href="https://tutormax.com/interventions/{tutor_id}" class="button">View Full Details</a>
        </p>

        <p>Best regards,<br>TutorMax Intervention System</p>
    """, "Performance Improvement Plan Required")

    return NotificationTemplate(subject, body_text, body_html, "staff")


def template_retention_interview(tutor_name: str, tutor_id: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for retention interview (staff notification)."""
    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = f"🚨 URGENT: Retention Interview Required - {tutor_name}"

    body_text = f"""URGENT: Retention Interview Required

Tutor: {tutor_name} ({tutor_id})
Priority: CRITICAL
Risk Level: CRITICAL CHURN RISK

Trigger Reason:
{trigger_reason}

Recommended Actions:

{actions_text}

🚨 IMMEDIATE ACTION: Schedule retention interview within 24-48 hours.

View full details: https://tutormax.com/interventions/{tutor_id}

Best regards,
TutorMax Intervention System
"""

    body_html = create_html_wrapper(f"""
        <h2 class="critical">🚨 URGENT: Retention Interview Required</h2>

        <p><strong>Tutor:</strong> {tutor_name} ({tutor_id})<br>
        <strong>Priority:</strong> <span class="critical">CRITICAL</span><br>
        <strong>Risk Level:</strong> <span class="critical">CRITICAL CHURN RISK</span></p>

        <p><strong>Trigger Reason:</strong><br>{trigger_reason}</p>

        <h3>Recommended Actions:</h3>
        <ul>
            {actions_html}
        </ul>

        <p class="critical"><strong>🚨 IMMEDIATE ACTION</strong><br>
        Schedule retention interview within 24-48 hours.</p>

        <p style="text-align: center; margin: 30px 0;">
            <a href="https://tutormax.com/interventions/{tutor_id}" class="button">View Full Details</a>
        </p>

        <p>Best regards,<br>TutorMax Intervention System</p>
    """, "Retention Interview Required")

    return NotificationTemplate(subject, body_text, body_html, "staff")


# ============================================================================
# POSITIVE INTERVENTION TEMPLATES
# ============================================================================

def template_recognition(tutor_name: str, trigger_reason: str, recommended_actions: list) -> NotificationTemplate:
    """Template for recognition intervention."""
    first_name = format_tutor_name(tutor_name)

    actions_text = "\n".join(f"  • {action}" for action in recommended_actions)
    actions_html = "".join(f"<li>{action}</li>" for action in recommended_actions)

    subject = "🌟 Outstanding Work - You're Making a Difference!"

    body_text = f"""Hi {first_name},

We wanted to take a moment to recognize your outstanding work!

{trigger_reason}

You're an exemplary tutor, and here's what we're doing to celebrate your success:

{actions_text}

Thank you for being such an important part of the TutorMax community. Your dedication and excellence inspire others!

Keep up the amazing work!

Best regards,
The TutorMax Team
"""

    body_html = create_html_wrapper(f"""
        <p>Hi {first_name},</p>

        <p class="positive">🌟 We wanted to take a moment to recognize your outstanding work!</p>

        <p><strong>What makes you exceptional:</strong><br>{trigger_reason}</p>

        <h3 class="positive">🎉 Celebrating Your Success:</h3>
        <ul>
            {actions_html}
        </ul>

        <p><strong>Thank you</strong> for being such an important part of the TutorMax community. Your dedication and excellence inspire others!</p>

        <p class="positive"><em>Keep up the amazing work!</em></p>

        <p>Best regards,<br>The TutorMax Team</p>
    """, "Outstanding Work!")

    return NotificationTemplate(subject, body_text, body_html, "tutor")


# ============================================================================
# TEMPLATE REGISTRY
# ============================================================================

TEMPLATE_REGISTRY: Dict[InterventionType, callable] = {
    InterventionType.AUTOMATED_COACHING: template_automated_coaching,
    InterventionType.TRAINING_MODULE: template_training_module,
    InterventionType.FIRST_SESSION_CHECKIN: template_first_session_checkin,
    InterventionType.RESCHEDULING_ALERT: template_rescheduling_alert,
    InterventionType.MANAGER_COACHING: template_manager_coaching,
    InterventionType.PEER_MENTORING: template_peer_mentoring,
    InterventionType.PERFORMANCE_IMPROVEMENT_PLAN: template_performance_improvement_plan,
    InterventionType.RETENTION_INTERVIEW: template_retention_interview,
    InterventionType.RECOGNITION: template_recognition,
}


def get_notification_template(
    intervention_type: InterventionType,
    tutor_name: str,
    trigger_reason: str,
    recommended_actions: list,
    tutor_id: str = None
) -> NotificationTemplate:
    """
    Get the appropriate notification template for an intervention type.

    Args:
        intervention_type: Type of intervention
        tutor_name: Name of the tutor
        trigger_reason: Reason for the intervention
        recommended_actions: List of recommended actions
        tutor_id: Tutor ID (required for staff notifications)

    Returns:
        NotificationTemplate with subject, body_text, and body_html
    """
    template_func = TEMPLATE_REGISTRY.get(intervention_type)

    if not template_func:
        raise ValueError(f"No template found for intervention type: {intervention_type}")

    # Staff notifications need tutor_id
    if intervention_type in [
        InterventionType.MANAGER_COACHING,
        InterventionType.PEER_MENTORING,
        InterventionType.PERFORMANCE_IMPROVEMENT_PLAN,
        InterventionType.RETENTION_INTERVIEW
    ]:
        if not tutor_id:
            raise ValueError(f"tutor_id required for {intervention_type} notifications")
        return template_func(tutor_name, tutor_id, trigger_reason, recommended_actions)
    else:
        return template_func(tutor_name, trigger_reason, recommended_actions)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Get automated coaching template
    template = get_notification_template(
        intervention_type=InterventionType.AUTOMATED_COACHING,
        tutor_name="John Doe",
        trigger_reason="Your recent session ratings have declined slightly",
        recommended_actions=[
            "Review the session feedback guide",
            "Focus on clear communication",
            "Ask more follow-up questions"
        ]
    )

    print("Subject:", template.subject)
    print("\nPlain Text Body:")
    print(template.body_text)
    print("\nRecipient Type:", template.recipient_type)
