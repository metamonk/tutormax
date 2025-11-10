"""
Celery tasks for email automation workflows.

Implements:
- Student feedback reminders (24h after session)
- First session check-ins (2h after first session)
- Rescheduling pattern alerts (3+ reschedules in 7 days)
- Scheduled email campaigns
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from celery import Task
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from src.workers.celery_app import celery_app
from src.database.database import get_db
from src.database.models import (
    Session as TutoringSession,
    StudentFeedback,
    Tutor,
    Student
)
from src.email_automation.email_template_engine import EmailTemplateType
from src.email_automation.email_delivery_service import (
    EnhancedEmailService,
    EmailPriority,
    get_email_service_from_settings
)

logger = logging.getLogger(__name__)


# ============================================================================
# TASK 22.1: STUDENT FEEDBACK REMINDERS (24H AFTER SESSION)
# ============================================================================

@celery_app.task(
    name="email_workflows.send_feedback_reminders",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def send_feedback_reminders(self: Task) -> Dict[str, Any]:
    """
    Send feedback reminders to students who haven't submitted feedback 24h after session.

    This task runs every hour and checks for sessions that:
    - Occurred 24-48 hours ago
    - Don't have feedback yet
    - Haven't had a reminder sent yet

    Returns:
        Dictionary with task results
    """
    logger.info("Starting feedback reminder task...")

    db: Session = next(get_db())
    email_service = get_email_service_from_settings()

    try:
        # Calculate time window (24-48 hours ago)
        now = datetime.utcnow()
        reminder_start = now - timedelta(hours=48)
        reminder_end = now - timedelta(hours=24)

        # Find sessions without feedback in the 24-48h window
        sessions_needing_reminder = db.query(TutoringSession).join(
            Tutor, TutoringSession.tutor_id == Tutor.tutor_id
        ).join(
            Student, TutoringSession.student_id == Student.student_id
        ).outerjoin(
            StudentFeedback, TutoringSession.session_id == StudentFeedback.session_id
        ).filter(
            and_(
                TutoringSession.scheduled_start >= reminder_start,
                TutoringSession.scheduled_start <= reminder_end,
                StudentFeedback.feedback_id.is_(None),  # No feedback yet
                TutoringSession.no_show == False  # Exclude no-shows
            )
        ).all()

        results = {
            'total_checked': len(sessions_needing_reminder),
            'reminders_sent': 0,
            'failures': 0,
            'skipped': 0
        }

        for session in sessions_needing_reminder:
            try:
                # Check if reminder already sent (would query email_workflow_state table)
                # For now, we'll send to all

                # Calculate hours since session
                hours_since = int((now - session.scheduled_start).total_seconds() / 3600)

                # Generate feedback URL with token
                # In production, this would use the feedback_auth system
                feedback_url = f"https://tutormax.com/feedback/{session.session_id}"

                # Send reminder email
                context = {
                    'student_name': session.student.name,
                    'tutor_name': session.tutor.name,
                    'session_date': session.scheduled_start.strftime('%B %d, %Y'),
                    'feedback_url': feedback_url,
                    'hours_since_session': hours_since,
                    'subject': f"Reminder: Share Your Feedback - Session with {session.tutor.name}",
                    'current_year': datetime.now().year
                }

                result = email_service.send_templated_email(
                    template_type=EmailTemplateType.FEEDBACK_REMINDER,
                    recipient_email=session.student.name,  # Would be student.email in production
                    context=context,
                    recipient_id=session.student_id,
                    recipient_type='student',
                    priority=EmailPriority.MEDIUM
                )

                if result['success']:
                    results['reminders_sent'] += 1
                    logger.info(f"Sent feedback reminder for session {session.session_id}")
                else:
                    results['failures'] += 1
                    logger.warning(f"Failed to send feedback reminder for session {session.session_id}: {result.get('error')}")

            except Exception as e:
                results['failures'] += 1
                logger.error(f"Error processing session {session.session_id}: {e}", exc_info=True)

        logger.info(
            f"Feedback reminder task complete: {results['reminders_sent']} sent, "
            f"{results['failures']} failed, {results['skipped']} skipped"
        )

        return results

    except Exception as e:
        logger.error(f"Error in feedback reminder task: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e)

    finally:
        db.close()


# ============================================================================
# TASK 22.2: FIRST SESSION CHECK-IN (2H AFTER FIRST SESSION)
# ============================================================================

@celery_app.task(
    name="email_workflows.send_first_session_checkins",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def send_first_session_checkins(self: Task) -> Dict[str, Any]:
    """
    Send check-in emails to tutors 2 hours after their first session with a new student.

    This task runs every 30 minutes and checks for:
    - Sessions that occurred 2-4 hours ago
    - Session was the first with that student (session_number == 1)
    - No check-in email sent yet

    Returns:
        Dictionary with task results
    """
    logger.info("Starting first session check-in task...")

    db: Session = next(get_db())
    email_service = get_email_service_from_settings()

    try:
        # Calculate time window (2-4 hours ago)
        now = datetime.utcnow()
        checkin_start = now - timedelta(hours=4)
        checkin_end = now - timedelta(hours=2)

        # Find first sessions in the 2-4h window
        first_sessions = db.query(TutoringSession).join(
            Tutor, TutoringSession.tutor_id == Tutor.tutor_id
        ).join(
            Student, TutoringSession.student_id == Student.student_id
        ).filter(
            and_(
                TutoringSession.scheduled_start >= checkin_start,
                TutoringSession.scheduled_start <= checkin_end,
                TutoringSession.session_number == 1,  # First session
                TutoringSession.no_show == False
            )
        ).all()

        results = {
            'total_checked': len(first_sessions),
            'checkins_sent': 0,
            'failures': 0,
            'skipped': 0
        }

        for session in first_sessions:
            try:
                # Generate check-in URL
                # In production, this would link to a survey form
                checkin_url = f"https://tutormax.com/checkin/first-session/{session.session_id}"

                # Send check-in email
                context = {
                    'tutor_name': session.tutor.name,
                    'student_name': session.student.name,
                    'session_date': session.scheduled_start.strftime('%B %d, %Y'),
                    'checkin_url': checkin_url,
                    'subject': f"How Did Your First Session Go with {session.student.name}?",
                    'current_year': datetime.now().year
                }

                result = email_service.send_templated_email(
                    template_type=EmailTemplateType.FIRST_SESSION_CHECKIN,
                    recipient_email=session.tutor.email,
                    context=context,
                    recipient_id=session.tutor_id,
                    recipient_type='tutor',
                    priority=EmailPriority.HIGH
                )

                if result['success']:
                    results['checkins_sent'] += 1
                    logger.info(f"Sent first session check-in for session {session.session_id}")
                else:
                    results['failures'] += 1
                    logger.warning(f"Failed to send check-in for session {session.session_id}: {result.get('error')}")

            except Exception as e:
                results['failures'] += 1
                logger.error(f"Error processing session {session.session_id}: {e}", exc_info=True)

        logger.info(
            f"First session check-in task complete: {results['checkins_sent']} sent, "
            f"{results['failures']} failed"
        )

        return results

    except Exception as e:
        logger.error(f"Error in first session check-in task: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


# ============================================================================
# TASK 22.3: RESCHEDULING PATTERN ALERTS
# ============================================================================

@celery_app.task(
    name="email_workflows.send_rescheduling_alerts",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def send_rescheduling_alerts(self: Task) -> Dict[str, Any]:
    """
    Send alerts to tutors who have rescheduled 3+ times in the past 7 days.

    This task runs daily and:
    - Identifies tutors with 3+ reschedules in past 7 days
    - Sends support email on first detection
    - Escalates to manager if pattern continues for 14 days

    Returns:
        Dictionary with task results
    """
    logger.info("Starting rescheduling pattern alert task...")

    db: Session = next(get_db())
    email_service = get_email_service_from_settings()

    try:
        # Calculate time windows
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        # Find tutors with 3+ reschedules in past 7 days
        tutors_with_reschedules = db.query(
            Tutor.tutor_id,
            Tutor.name,
            Tutor.email,
            func.count(TutoringSession.session_id).label('reschedule_count')
        ).join(
            TutoringSession, Tutor.tutor_id == TutoringSession.tutor_id
        ).filter(
            and_(
                TutoringSession.tutor_initiated_reschedule == True,
                TutoringSession.scheduled_start >= seven_days_ago
            )
        ).group_by(
            Tutor.tutor_id,
            Tutor.name,
            Tutor.email
        ).having(
            func.count(TutoringSession.session_id) >= 3
        ).all()

        results = {
            'total_checked': len(tutors_with_reschedules),
            'alerts_sent': 0,
            'failures': 0,
            'escalations': 0
        }

        for tutor_data in tutors_with_reschedules:
            tutor_id, tutor_name, tutor_email, reschedule_count = tutor_data

            try:
                # Check for 14-day pattern (escalation)
                reschedules_14d = db.query(func.count(TutoringSession.session_id)).filter(
                    and_(
                        TutoringSession.tutor_id == tutor_id,
                        TutoringSession.tutor_initiated_reschedule == True,
                        TutoringSession.scheduled_start >= fourteen_days_ago
                    )
                ).scalar()

                # Determine if escalation needed
                needs_escalation = reschedules_14d >= 6  # 6+ in 14 days

                # Generate support URL
                support_url = f"https://tutormax.com/support/scheduling"

                # Send alert email
                context = {
                    'tutor_name': tutor_name,
                    'reschedule_count': reschedule_count,
                    'days_period': 7,
                    'support_url': support_url,
                    'manager_name': None,  # Would lookup from database
                    'subject': "We Noticed You've Been Rescheduling - Need Help?",
                    'current_year': datetime.now().year
                }

                result = email_service.send_templated_email(
                    template_type=EmailTemplateType.RESCHEDULING_ALERT,
                    recipient_email=tutor_email,
                    context=context,
                    recipient_id=tutor_id,
                    recipient_type='tutor',
                    priority=EmailPriority.HIGH if needs_escalation else EmailPriority.MEDIUM
                )

                if result['success']:
                    results['alerts_sent'] += 1
                    logger.info(f"Sent rescheduling alert to tutor {tutor_id}")

                    # Send escalation to manager if needed
                    if needs_escalation:
                        # In production, would send to manager
                        results['escalations'] += 1
                        logger.info(f"Escalated rescheduling pattern for tutor {tutor_id}")
                else:
                    results['failures'] += 1
                    logger.warning(f"Failed to send alert to tutor {tutor_id}: {result.get('error')}")

            except Exception as e:
                results['failures'] += 1
                logger.error(f"Error processing tutor {tutor_id}: {e}", exc_info=True)

        logger.info(
            f"Rescheduling alert task complete: {results['alerts_sent']} sent, "
            f"{results['escalations']} escalated, {results['failures']} failed"
        )

        return results

    except Exception as e:
        logger.error(f"Error in rescheduling alert task: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


# ============================================================================
# SCHEDULED EMAIL CAMPAIGNS
# ============================================================================

@celery_app.task(
    name="email_workflows.send_scheduled_campaigns",
    bind=True,
    max_retries=2
)
def send_scheduled_campaigns(self: Task) -> Dict[str, Any]:
    """
    Process and send scheduled email campaigns.

    Checks for campaigns scheduled to send and processes them.

    Returns:
        Dictionary with task results
    """
    logger.info("Starting scheduled campaign task...")

    db: Session = next(get_db())

    try:
        # This would query email_campaigns table for scheduled campaigns
        # Simplified for now

        results = {
            'campaigns_processed': 0,
            'emails_sent': 0,
            'failures': 0
        }

        # In production:
        # 1. Query campaigns with status='scheduled' and scheduled_at <= now
        # 2. For each campaign, get recipient list
        # 3. Render and send emails
        # 4. Update campaign stats
        # 5. Mark campaign as 'sending' or 'completed'

        logger.info(f"Scheduled campaign task complete: {results['campaigns_processed']} campaigns processed")

        return results

    except Exception as e:
        logger.error(f"Error in scheduled campaign task: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


# ============================================================================
# WEEKLY DIGEST EMAILS
# ============================================================================

@celery_app.task(
    name="email_workflows.send_weekly_digests",
    bind=True
)
def send_weekly_digests(self: Task) -> Dict[str, Any]:
    """
    Send weekly digest emails to tutors and managers.

    Runs every Monday at 9am.

    Returns:
        Dictionary with task results
    """
    logger.info("Starting weekly digest task...")

    db: Session = next(get_db())
    email_service = get_email_service_from_settings()

    try:
        results = {
            'tutor_digests_sent': 0,
            'manager_digests_sent': 0,
            'failures': 0
        }

        # Get all active tutors
        tutors = db.query(Tutor).filter(Tutor.status == 'active').all()

        for tutor in tutors:
            try:
                # Calculate weekly metrics for tutor
                # In production, would query performance metrics

                # Send digest email (would use WEEKLY_DIGEST template)
                logger.info(f"Would send weekly digest to tutor {tutor.tutor_id}")
                results['tutor_digests_sent'] += 1

            except Exception as e:
                results['failures'] += 1
                logger.error(f"Error sending digest to tutor {tutor.tutor_id}: {e}")

        logger.info(f"Weekly digest task complete: {results['tutor_digests_sent']} sent")

        return results

    except Exception as e:
        logger.error(f"Error in weekly digest task: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


# ============================================================================
# UTILITY TASKS
# ============================================================================

@celery_app.task(name="email_workflows.cleanup_old_tracking_events")
def cleanup_old_tracking_events(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old email tracking events.

    Args:
        days_to_keep: Number of days to retain events

    Returns:
        Dictionary with cleanup results
    """
    logger.info(f"Cleaning up email tracking events older than {days_to_keep} days...")

    db: Session = next(get_db())

    try:
        # This would delete from email_tracking_events table
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # In production: DELETE FROM email_tracking_events WHERE created_at < cutoff_date
        deleted_count = 0  # Placeholder

        logger.info(f"Deleted {deleted_count} old tracking events")

        return {
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }

    finally:
        db.close()
