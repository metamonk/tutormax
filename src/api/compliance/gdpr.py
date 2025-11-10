"""
GDPR Compliance Service

Implements comprehensive GDPR (General Data Protection Regulation) compliance
for TutorMax, including all data subject rights and required procedures.

Rights Implemented:
- Right to access (Article 15)
- Right to erasure/be forgotten (Article 17)
- Right to rectification (Article 16)
- Right to data portability (Article 20)
- Consent management (Article 7)
- Data breach notification (Article 33-34)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, update
from sqlalchemy.orm import selectinload
import json
import uuid
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from ...database.models import (
    User, Tutor, Student, Session as TutoringSession,
    StudentFeedback, TutorPerformanceMetric, ChurnPrediction,
    Intervention, TutorEvent, Notification, AuditLog, ManagerNote
)
from ..security import encryption_service, anonymization_service
from ..audit_service import AuditService
from ..config import settings


class GDPRService:
    """
    Service for managing GDPR data subject rights.

    Provides comprehensive data export, deletion, and rectification
    capabilities in compliance with GDPR requirements.
    """

    # Data retention constants (in days)
    DEFAULT_RETENTION_PERIOD = 2555  # 7 years for educational records (FERPA)
    ANONYMIZATION_PERIOD = 1095  # 3 years before anonymization
    AUDIT_LOG_RETENTION = 2555  # 7 years for compliance

    @staticmethod
    async def export_user_data(
        session: AsyncSession,
        user_id: int,
        include_encrypted: bool = False,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export all personal data for a user (Right to Access - Article 15).

        Args:
            session: Database session
            user_id: User ID requesting data export
            include_encrypted: Whether to decrypt encrypted fields
            format: Export format ("json" or "pdf")

        Returns:
            Dictionary containing all user data organized by category
        """
        # Get user record
        user_query = select(User).where(User.id == user_id)
        result = await session.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        export_data = {
            "export_metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "data_controller": "TutorMax",
                "gdpr_article": "Article 15 - Right of Access",
            },
            "account_information": {},
            "tutor_data": None,
            "student_data": None,
            "sessions": [],
            "feedback": [],
            "performance_metrics": [],
            "predictions": [],
            "interventions": [],
            "events": [],
            "notifications": [],
            "manager_notes": [],
            "audit_logs": [],
        }

        # Export account information
        export_data["account_information"] = {
            "id": user.id,
            "email": user.email if not include_encrypted else user.email,
            "full_name": user.full_name,
            "roles": [role.value for role in user.roles],
            "oauth_provider": user.oauth_provider.value if user.oauth_provider else None,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

        # Export tutor data if applicable
        if user.tutor_id:
            tutor_query = select(Tutor).where(Tutor.tutor_id == user.tutor_id)
            result = await session.execute(tutor_query)
            tutor = result.scalar_one_or_none()

            if tutor:
                export_data["tutor_data"] = {
                    "tutor_id": tutor.tutor_id,
                    "name": tutor.name,
                    "email": tutor.email,
                    "onboarding_date": tutor.onboarding_date.isoformat(),
                    "status": tutor.status.value,
                    "subjects": tutor.subjects,
                    "education_level": tutor.education_level,
                    "location": tutor.location,
                    "baseline_sessions_per_week": tutor.baseline_sessions_per_week,
                    "behavioral_archetype": tutor.behavioral_archetype.value if tutor.behavioral_archetype else None,
                    "created_at": tutor.created_at.isoformat(),
                    "updated_at": tutor.updated_at.isoformat(),
                }

                # Export tutor sessions
                sessions_query = select(TutoringSession).where(
                    TutoringSession.tutor_id == tutor.tutor_id
                )
                result = await session.execute(sessions_query)
                sessions = result.scalars().all()

                for sess in sessions:
                    export_data["sessions"].append({
                        "session_id": sess.session_id,
                        "student_id": sess.student_id,
                        "session_number": sess.session_number,
                        "scheduled_start": sess.scheduled_start.isoformat(),
                        "actual_start": sess.actual_start.isoformat() if sess.actual_start else None,
                        "duration_minutes": sess.duration_minutes,
                        "subject": sess.subject,
                        "session_type": sess.session_type.value,
                        "tutor_initiated_reschedule": sess.tutor_initiated_reschedule,
                        "no_show": sess.no_show,
                        "late_start_minutes": sess.late_start_minutes,
                        "engagement_score": sess.engagement_score,
                        "learning_objectives_met": sess.learning_objectives_met,
                        "technical_issues": sess.technical_issues,
                    })

                # Export performance metrics
                metrics_query = select(TutorPerformanceMetric).where(
                    TutorPerformanceMetric.tutor_id == tutor.tutor_id
                )
                result = await session.execute(metrics_query)
                metrics = result.scalars().all()

                for metric in metrics:
                    export_data["performance_metrics"].append({
                        "metric_id": metric.metric_id,
                        "calculation_date": metric.calculation_date.isoformat(),
                        "window": metric.window.value,
                        "sessions_completed": metric.sessions_completed,
                        "avg_rating": metric.avg_rating,
                        "first_session_success_rate": metric.first_session_success_rate,
                        "reschedule_rate": metric.reschedule_rate,
                        "no_show_count": metric.no_show_count,
                        "engagement_score": metric.engagement_score,
                        "learning_objectives_met_pct": metric.learning_objectives_met_pct,
                        "response_time_avg_minutes": metric.response_time_avg_minutes,
                        "performance_tier": metric.performance_tier.value if metric.performance_tier else None,
                    })

                # Export churn predictions
                predictions_query = select(ChurnPrediction).where(
                    ChurnPrediction.tutor_id == tutor.tutor_id
                )
                result = await session.execute(predictions_query)
                predictions = result.scalars().all()

                for pred in predictions:
                    export_data["predictions"].append({
                        "prediction_id": pred.prediction_id,
                        "prediction_date": pred.prediction_date.isoformat(),
                        "churn_score": pred.churn_score,
                        "risk_level": pred.risk_level.value,
                        "window_1day_probability": pred.window_1day_probability,
                        "window_7day_probability": pred.window_7day_probability,
                        "window_30day_probability": pred.window_30day_probability,
                        "window_90day_probability": pred.window_90day_probability,
                        "contributing_factors": pred.contributing_factors,
                        "model_version": pred.model_version,
                    })

                # Export interventions
                interventions_query = select(Intervention).where(
                    Intervention.tutor_id == tutor.tutor_id
                )
                result = await session.execute(interventions_query)
                interventions = result.scalars().all()

                for interv in interventions:
                    export_data["interventions"].append({
                        "intervention_id": interv.intervention_id,
                        "intervention_type": interv.intervention_type.value,
                        "trigger_reason": interv.trigger_reason,
                        "recommended_date": interv.recommended_date.isoformat(),
                        "assigned_to": interv.assigned_to,
                        "status": interv.status.value,
                        "due_date": interv.due_date.isoformat() if interv.due_date else None,
                        "completed_date": interv.completed_date.isoformat() if interv.completed_date else None,
                        "outcome": interv.outcome.value if interv.outcome else None,
                        "notes": interv.notes,
                    })

                # Export tutor events
                events_query = select(TutorEvent).where(
                    TutorEvent.tutor_id == tutor.tutor_id
                )
                result = await session.execute(events_query)
                events = result.scalars().all()

                for event in events:
                    export_data["events"].append({
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "event_timestamp": event.event_timestamp.isoformat(),
                        "metadata": event.event_metadata,
                    })

                # Export manager notes
                notes_query = select(ManagerNote).where(
                    ManagerNote.tutor_id == tutor.tutor_id
                )
                result = await session.execute(notes_query)
                notes = result.scalars().all()

                for note in notes:
                    export_data["manager_notes"].append({
                        "note_id": note.note_id,
                        "author_name": note.author_name,
                        "note_text": note.note_text,
                        "is_important": note.is_important,
                        "created_at": note.created_at.isoformat(),
                    })

        # Export student data if applicable
        if user.student_id:
            student_query = select(Student).where(Student.student_id == user.student_id)
            result = await session.execute(student_query)
            student = result.scalar_one_or_none()

            if student:
                export_data["student_data"] = {
                    "student_id": student.student_id,
                    "name": student.name,
                    "age": student.age,
                    "grade_level": student.grade_level,
                    "subjects_interested": student.subjects_interested,
                    "is_under_13": student.is_under_13,
                    "parent_email": student.parent_email,
                    "parent_consent_given": student.parent_consent_given,
                    "parent_consent_date": student.parent_consent_date.isoformat() if student.parent_consent_date else None,
                    "created_at": student.created_at.isoformat(),
                    "updated_at": student.updated_at.isoformat(),
                }

                # Export student sessions
                sessions_query = select(TutoringSession).where(
                    TutoringSession.student_id == student.student_id
                )
                result = await session.execute(sessions_query)
                sessions = result.scalars().all()

                for sess in sessions:
                    # Only add if not already in sessions list (from tutor export)
                    if not any(s["session_id"] == sess.session_id for s in export_data["sessions"]):
                        export_data["sessions"].append({
                            "session_id": sess.session_id,
                            "tutor_id": sess.tutor_id,
                            "session_number": sess.session_number,
                            "scheduled_start": sess.scheduled_start.isoformat(),
                            "actual_start": sess.actual_start.isoformat() if sess.actual_start else None,
                            "duration_minutes": sess.duration_minutes,
                            "subject": sess.subject,
                            "session_type": sess.session_type.value,
                        })

                # Export student feedback
                feedback_query = select(StudentFeedback).where(
                    StudentFeedback.student_id == student.student_id
                )
                result = await session.execute(feedback_query)
                feedbacks = result.scalars().all()

                for fb in feedbacks:
                    export_data["feedback"].append({
                        "feedback_id": fb.feedback_id,
                        "session_id": fb.session_id,
                        "tutor_id": fb.tutor_id,
                        "overall_rating": fb.overall_rating,
                        "is_first_session": fb.is_first_session,
                        "subject_knowledge_rating": fb.subject_knowledge_rating,
                        "communication_rating": fb.communication_rating,
                        "patience_rating": fb.patience_rating,
                        "engagement_rating": fb.engagement_rating,
                        "helpfulness_rating": fb.helpfulness_rating,
                        "would_recommend": fb.would_recommend,
                        "improvement_areas": fb.improvement_areas,
                        "free_text_feedback": fb.free_text_feedback,
                        "submitted_at": fb.submitted_at.isoformat(),
                    })

        # Export notifications
        notifications_query = select(Notification).where(
            Notification.recipient_id == str(user_id)
        )
        result = await session.execute(notifications_query)
        notifications = result.scalars().all()

        for notif in notifications:
            export_data["notifications"].append({
                "notification_id": notif.notification_id,
                "recipient_email": notif.recipient_email,
                "notification_type": notif.notification_type.value,
                "priority": notif.priority.value,
                "status": notif.status.value,
                "subject": notif.subject,
                "body": notif.body,
                "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
                "read_at": notif.read_at.isoformat() if notif.read_at else None,
                "created_at": notif.created_at.isoformat(),
            })

        # Export audit logs (last 90 days for privacy)
        audit_start = datetime.utcnow() - timedelta(days=90)
        audit_query = select(AuditLog).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= audit_start
            )
        ).order_by(AuditLog.timestamp.desc())
        result = await session.execute(audit_query)
        audit_logs = result.scalars().all()

        for log in audit_logs:
            export_data["audit_logs"].append({
                "log_id": log.log_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp.isoformat(),
                "success": log.success,
            })

        return export_data

    @staticmethod
    async def delete_user_data(
        session: AsyncSession,
        user_id: int,
        deletion_reason: str = "User request (GDPR Article 17)",
        retain_audit_logs: bool = True
    ) -> Dict[str, Any]:
        """
        Delete all personal data for a user (Right to Erasure - Article 17).

        Args:
            session: Database session
            user_id: User ID to delete
            deletion_reason: Reason for deletion
            retain_audit_logs: Whether to keep anonymized audit logs

        Returns:
            Summary of deletion operation
        """
        # Get user record
        user_query = select(User).where(User.id == user_id)
        result = await session.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        deletion_summary = {
            "user_id": user_id,
            "deletion_date": datetime.utcnow().isoformat(),
            "deletion_reason": deletion_reason,
            "records_deleted": {},
            "records_anonymized": {},
        }

        # Delete or anonymize tutor data
        if user.tutor_id:
            tutor_id = user.tutor_id

            # Count records before deletion
            sessions_count = await session.execute(
                select(TutoringSession).where(TutoringSession.tutor_id == tutor_id)
            )
            deletion_summary["records_deleted"]["sessions"] = len(sessions_count.scalars().all())

            # Delete sessions
            await session.execute(
                delete(TutoringSession).where(TutoringSession.tutor_id == tutor_id)
            )

            # Delete performance metrics
            metrics_count = await session.execute(
                select(TutorPerformanceMetric).where(TutorPerformanceMetric.tutor_id == tutor_id)
            )
            deletion_summary["records_deleted"]["performance_metrics"] = len(metrics_count.scalars().all())
            await session.execute(
                delete(TutorPerformanceMetric).where(TutorPerformanceMetric.tutor_id == tutor_id)
            )

            # Delete churn predictions
            predictions_count = await session.execute(
                select(ChurnPrediction).where(ChurnPrediction.tutor_id == tutor_id)
            )
            deletion_summary["records_deleted"]["churn_predictions"] = len(predictions_count.scalars().all())
            await session.execute(
                delete(ChurnPrediction).where(ChurnPrediction.tutor_id == tutor_id)
            )

            # Delete interventions
            interventions_count = await session.execute(
                select(Intervention).where(Intervention.tutor_id == tutor_id)
            )
            deletion_summary["records_deleted"]["interventions"] = len(interventions_count.scalars().all())
            await session.execute(
                delete(Intervention).where(Intervention.tutor_id == tutor_id)
            )

            # Delete tutor events
            events_count = await session.execute(
                select(TutorEvent).where(TutorEvent.tutor_id == tutor_id)
            )
            deletion_summary["records_deleted"]["tutor_events"] = len(events_count.scalars().all())
            await session.execute(
                delete(TutorEvent).where(TutorEvent.tutor_id == tutor_id)
            )

            # Delete manager notes
            notes_count = await session.execute(
                select(ManagerNote).where(ManagerNote.tutor_id == tutor_id)
            )
            deletion_summary["records_deleted"]["manager_notes"] = len(notes_count.scalars().all())
            await session.execute(
                delete(ManagerNote).where(ManagerNote.tutor_id == tutor_id)
            )

            # Delete tutor record
            await session.execute(
                delete(Tutor).where(Tutor.tutor_id == tutor_id)
            )
            deletion_summary["records_deleted"]["tutor"] = 1

        # Delete student data
        if user.student_id:
            student_id = user.student_id

            # Delete student sessions
            sessions_count = await session.execute(
                select(TutoringSession).where(TutoringSession.student_id == student_id)
            )
            count = len(sessions_count.scalars().all())
            deletion_summary["records_deleted"]["student_sessions"] = count
            await session.execute(
                delete(TutoringSession).where(TutoringSession.student_id == student_id)
            )

            # Delete student feedback
            feedback_count = await session.execute(
                select(StudentFeedback).where(StudentFeedback.student_id == student_id)
            )
            deletion_summary["records_deleted"]["student_feedback"] = len(feedback_count.scalars().all())
            await session.execute(
                delete(StudentFeedback).where(StudentFeedback.student_id == student_id)
            )

            # Delete student record
            await session.execute(
                delete(Student).where(Student.student_id == student_id)
            )
            deletion_summary["records_deleted"]["student"] = 1

        # Delete notifications
        notifications_count = await session.execute(
            select(Notification).where(Notification.recipient_id == str(user_id))
        )
        deletion_summary["records_deleted"]["notifications"] = len(notifications_count.scalars().all())
        await session.execute(
            delete(Notification).where(Notification.recipient_id == str(user_id))
        )

        # Handle audit logs
        if retain_audit_logs:
            # Anonymize audit logs instead of deleting (for compliance)
            audit_logs_query = select(AuditLog).where(AuditLog.user_id == user_id)
            result = await session.execute(audit_logs_query)
            audit_logs = result.scalars().all()

            for log in audit_logs:
                log.user_id = None  # Anonymize user ID
                if log.audit_metadata:
                    # Remove PII from metadata
                    if isinstance(log.audit_metadata, dict):
                        log.audit_metadata.pop("email", None)
                        log.audit_metadata.pop("name", None)
                        log.audit_metadata["anonymized"] = True

            deletion_summary["records_anonymized"]["audit_logs"] = len(audit_logs)
        else:
            # Delete audit logs
            audit_count = await session.execute(
                select(AuditLog).where(AuditLog.user_id == user_id)
            )
            deletion_summary["records_deleted"]["audit_logs"] = len(audit_count.scalars().all())
            await session.execute(
                delete(AuditLog).where(AuditLog.user_id == user_id)
            )

        # Delete user account
        await session.execute(
            delete(User).where(User.id == user_id)
        )
        deletion_summary["records_deleted"]["user_account"] = 1

        # Commit all deletions
        await session.commit()

        # Log the deletion (in a new session since we deleted the user)
        await AuditService.log(
            session=session,
            action="gdpr_data_deletion",
            user_id=None,  # User is deleted
            resource_type="user",
            resource_id=str(user_id),
            success=True,
            metadata={
                "deletion_reason": deletion_reason,
                "deletion_summary": deletion_summary,
            }
        )

        return deletion_summary

    @staticmethod
    async def rectify_user_data(
        session: AsyncSession,
        user_id: int,
        corrections: Dict[str, Any],
        requesting_user_id: int
    ) -> Dict[str, Any]:
        """
        Correct inaccurate personal data (Right to Rectification - Article 16).

        Args:
            session: Database session
            user_id: User ID whose data to correct
            corrections: Dictionary of field corrections
            requesting_user_id: User requesting the correction

        Returns:
            Summary of rectification operation
        """
        # Get user record
        user_query = select(User).where(User.id == user_id)
        result = await session.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        rectification_summary = {
            "user_id": user_id,
            "rectification_date": datetime.utcnow().isoformat(),
            "requested_by": requesting_user_id,
            "changes_applied": {},
            "changes_rejected": {},
        }

        # Apply corrections to user account
        if "account" in corrections:
            for field, new_value in corrections["account"].items():
                if hasattr(user, field):
                    old_value = getattr(user, field)
                    setattr(user, field, new_value)
                    rectification_summary["changes_applied"][f"account.{field}"] = {
                        "old": str(old_value),
                        "new": str(new_value),
                    }
                else:
                    rectification_summary["changes_rejected"][f"account.{field}"] = "Field not found"

        # Apply corrections to tutor data
        if user.tutor_id and "tutor" in corrections:
            tutor_query = select(Tutor).where(Tutor.tutor_id == user.tutor_id)
            result = await session.execute(tutor_query)
            tutor = result.scalar_one_or_none()

            if tutor:
                for field, new_value in corrections["tutor"].items():
                    if hasattr(tutor, field):
                        old_value = getattr(tutor, field)
                        setattr(tutor, field, new_value)
                        rectification_summary["changes_applied"][f"tutor.{field}"] = {
                            "old": str(old_value),
                            "new": str(new_value),
                        }
                    else:
                        rectification_summary["changes_rejected"][f"tutor.{field}"] = "Field not found"

        # Apply corrections to student data
        if user.student_id and "student" in corrections:
            student_query = select(Student).where(Student.student_id == user.student_id)
            result = await session.execute(student_query)
            student = result.scalar_one_or_none()

            if student:
                for field, new_value in corrections["student"].items():
                    if hasattr(student, field):
                        old_value = getattr(student, field)
                        setattr(student, field, new_value)
                        rectification_summary["changes_applied"][f"student.{field}"] = {
                            "old": str(old_value),
                            "new": str(new_value),
                        }
                    else:
                        rectification_summary["changes_rejected"][f"student.{field}"] = "Field not found"

        # Commit changes
        await session.commit()

        # Log rectification
        await AuditService.log_data_modification(
            session=session,
            user_id=requesting_user_id,
            action="gdpr_data_rectification",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=None,
            user_agent=None,
            request_method="PUT",
            request_path="/gdpr/rectify-data",
            success=True,
            metadata={
                "rectification_summary": rectification_summary,
            }
        )

        return rectification_summary

    @staticmethod
    async def generate_portable_data(
        session: AsyncSession,
        user_id: int,
        format: str = "json"
    ) -> Tuple[bytes, str]:
        """
        Generate portable data export (Right to Data Portability - Article 20).

        Args:
            session: Database session
            user_id: User ID requesting portable data
            format: Export format ("json" or "pdf")

        Returns:
            Tuple of (data bytes, mime type)
        """
        # Get all user data
        data = await GDPRService.export_user_data(session, user_id)

        if format == "json":
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            return json_data.encode('utf-8'), "application/json"

        elif format == "pdf":
            # Generate PDF report
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
            )
            story.append(Paragraph("GDPR Data Export Report", title_style))
            story.append(Spacer(1, 0.2*inch))

            # Export metadata
            story.append(Paragraph("Export Information", styles['Heading2']))
            metadata = data["export_metadata"]
            story.append(Paragraph(f"Export Date: {metadata['export_date']}", styles['Normal']))
            story.append(Paragraph(f"User ID: {metadata['user_id']}", styles['Normal']))
            story.append(Paragraph(f"GDPR Article: {metadata['gdpr_article']}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # Account information
            story.append(Paragraph("Account Information", styles['Heading2']))
            account = data["account_information"]
            for key, value in account.items():
                if value is not None:
                    story.append(Paragraph(f"{key}: {value}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # Summary statistics
            story.append(Paragraph("Data Summary", styles['Heading2']))
            story.append(Paragraph(f"Total Sessions: {len(data['sessions'])}", styles['Normal']))
            story.append(Paragraph(f"Total Feedback: {len(data['feedback'])}", styles['Normal']))
            story.append(Paragraph(f"Performance Metrics: {len(data['performance_metrics'])}", styles['Normal']))
            story.append(Paragraph(f"Notifications: {len(data['notifications'])}", styles['Normal']))
            story.append(Paragraph(f"Audit Log Entries: {len(data['audit_logs'])}", styles['Normal']))

            # Build PDF
            doc.build(story)
            pdf_data = buffer.getvalue()
            buffer.close()

            return pdf_data, "application/pdf"

        else:
            raise ValueError(f"Unsupported format: {format}")


class ConsentManager:
    """
    Manages user consent for data processing (GDPR Article 7).

    Tracks consent for various processing activities and purposes.
    """

    # Consent purposes
    PURPOSE_MARKETING = "marketing"
    PURPOSE_ANALYTICS = "analytics"
    PURPOSE_PERSONALIZATION = "personalization"
    PURPOSE_THIRD_PARTY_SHARING = "third_party_sharing"
    PURPOSE_PROFILING = "profiling"

    @staticmethod
    async def record_consent(
        session: AsyncSession,
        user_id: int,
        purpose: str,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Record user consent for a specific purpose.

        Args:
            session: Database session
            user_id: User granting/withdrawing consent
            purpose: Purpose of data processing
            granted: Whether consent is granted (True) or withdrawn (False)
            ip_address: IP address of consent action
            user_agent: User agent string
        """
        # Log consent in audit log
        await AuditService.log(
            session=session,
            action="consent_granted" if granted else "consent_withdrawn",
            user_id=user_id,
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="POST",
            request_path="/gdpr/consent",
            success=True,
            metadata={
                "purpose": purpose,
                "granted": granted,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @staticmethod
    async def get_consent_status(
        session: AsyncSession,
        user_id: int,
        purpose: str
    ) -> Optional[bool]:
        """
        Get current consent status for a user and purpose.

        Args:
            session: Database session
            user_id: User ID
            purpose: Purpose to check

        Returns:
            True if consent granted, False if withdrawn, None if no record
        """
        # Query most recent consent action for this purpose
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.action.in_(["consent_granted", "consent_withdrawn"]),
                )
            )
            .order_by(AuditLog.timestamp.desc())
        )

        result = await session.execute(query)
        logs = result.scalars().all()

        # Find most recent consent for this purpose
        for log in logs:
            if log.audit_metadata and log.audit_metadata.get("purpose") == purpose:
                return log.audit_metadata.get("granted")

        return None

    @staticmethod
    async def withdraw_all_consents(
        session: AsyncSession,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> int:
        """
        Withdraw all consents for a user.

        Args:
            session: Database session
            user_id: User ID
            ip_address: IP address of withdrawal

        Returns:
            Number of consents withdrawn
        """
        purposes = [
            ConsentManager.PURPOSE_MARKETING,
            ConsentManager.PURPOSE_ANALYTICS,
            ConsentManager.PURPOSE_PERSONALIZATION,
            ConsentManager.PURPOSE_THIRD_PARTY_SHARING,
            ConsentManager.PURPOSE_PROFILING,
        ]

        count = 0
        for purpose in purposes:
            current = await ConsentManager.get_consent_status(session, user_id, purpose)
            if current is True:
                await ConsentManager.record_consent(
                    session, user_id, purpose, False, ip_address
                )
                count += 1

        return count


class DataBreachNotifier:
    """
    Handles data breach notification requirements (GDPR Article 33-34).

    Manages breach logging, assessment, and notification to authorities
    and affected data subjects.
    """

    # Breach severity levels
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"

    @staticmethod
    async def log_breach(
        session: AsyncSession,
        breach_description: str,
        affected_data_types: List[str],
        affected_user_count: int,
        severity: str,
        discovered_at: datetime,
        contained_at: Optional[datetime] = None,
        root_cause: Optional[str] = None,
        mitigation_steps: Optional[List[str]] = None
    ) -> str:
        """
        Log a data breach incident.

        Args:
            session: Database session
            breach_description: Description of the breach
            affected_data_types: Types of data affected (e.g., "email", "passwords")
            affected_user_count: Number of users affected
            severity: Breach severity level
            discovered_at: When breach was discovered
            contained_at: When breach was contained (if applicable)
            root_cause: Root cause analysis
            mitigation_steps: Steps taken to mitigate

        Returns:
            Breach incident ID
        """
        breach_id = str(uuid.uuid4())

        # Log breach in audit log
        await AuditService.log(
            session=session,
            action="data_breach_logged",
            user_id=None,
            resource_type="security",
            resource_id=breach_id,
            ip_address=None,
            user_agent=None,
            request_method="POST",
            request_path="/gdpr/breach",
            success=True,
            metadata={
                "breach_id": breach_id,
                "description": breach_description,
                "affected_data_types": affected_data_types,
                "affected_user_count": affected_user_count,
                "severity": severity,
                "discovered_at": discovered_at.isoformat(),
                "contained_at": contained_at.isoformat() if contained_at else None,
                "root_cause": root_cause,
                "mitigation_steps": mitigation_steps or [],
                "requires_authority_notification": severity in [
                    DataBreachNotifier.SEVERITY_HIGH,
                    DataBreachNotifier.SEVERITY_CRITICAL
                ],
                "requires_user_notification": severity == DataBreachNotifier.SEVERITY_CRITICAL,
            }
        )

        return breach_id

    @staticmethod
    def should_notify_authority(severity: str, affected_count: int) -> bool:
        """
        Determine if breach requires notification to supervisory authority.

        GDPR requires notification within 72 hours if breach poses risk.

        Args:
            severity: Breach severity
            affected_count: Number of affected users

        Returns:
            True if authority notification required
        """
        # High/critical severity always requires notification
        if severity in [DataBreachNotifier.SEVERITY_HIGH, DataBreachNotifier.SEVERITY_CRITICAL]:
            return True

        # Medium severity requires notification if many users affected
        if severity == DataBreachNotifier.SEVERITY_MEDIUM and affected_count > 100:
            return True

        return False

    @staticmethod
    def should_notify_users(severity: str, data_types: List[str]) -> bool:
        """
        Determine if breach requires direct notification to users.

        GDPR requires user notification if breach poses high risk.

        Args:
            severity: Breach severity
            data_types: Types of data affected

        Returns:
            True if user notification required
        """
        # Critical severity always requires user notification
        if severity == DataBreachNotifier.SEVERITY_CRITICAL:
            return True

        # High severity with sensitive data requires notification
        sensitive_types = {"password", "ssn", "payment", "health", "biometric"}
        if severity == DataBreachNotifier.SEVERITY_HIGH:
            if any(dtype in sensitive_types for dtype in data_types):
                return True

        return False

    @staticmethod
    async def get_breach_notification_template(
        severity: str,
        affected_data_types: List[str]
    ) -> Dict[str, str]:
        """
        Get email template for breach notification.

        Args:
            severity: Breach severity
            affected_data_types: Types of data affected

        Returns:
            Dictionary with subject and body templates
        """
        if severity == DataBreachNotifier.SEVERITY_CRITICAL:
            return {
                "subject": "URGENT: Security Incident Affecting Your TutorMax Account",
                "body": """
Dear TutorMax User,

We are writing to inform you of a security incident that may have affected your personal data.

WHAT HAPPENED:
We recently discovered unauthorized access to our systems that may have exposed the following types of data:
{data_types}

WHAT WE ARE DOING:
- We have contained the incident and secured our systems
- We are conducting a thorough investigation
- We have notified relevant authorities as required by law
- We are implementing additional security measures

WHAT YOU SHOULD DO:
- Change your TutorMax password immediately
- Monitor your accounts for suspicious activity
- Be cautious of phishing attempts
- Contact us if you have concerns: support@tutormax.com

We sincerely apologize for this incident and any inconvenience it may cause. The security of your data is our top priority.

Sincerely,
TutorMax Security Team
                """.strip()
            }
        else:
            return {
                "subject": "Important Security Notice - TutorMax",
                "body": """
Dear TutorMax User,

We are writing to inform you of a security incident that may have affected some user data.

We take the security of your information seriously and wanted to make you aware of this incident. The affected data types include: {data_types}

We have taken immediate steps to secure our systems and prevent similar incidents in the future.

If you have any questions or concerns, please contact us at support@tutormax.com.

Sincerely,
TutorMax Security Team
                """.strip()
            }


# Global service instances
gdpr_service = GDPRService()
consent_manager = ConsentManager()
data_breach_notifier = DataBreachNotifier()
