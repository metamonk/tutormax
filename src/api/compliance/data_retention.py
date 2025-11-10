"""
Data Retention & Compliance Automation Service

Implements automated data retention, archival, and deletion policies for:
- FERPA 7-year retention requirement
- GDPR 'right to be forgotten'
- Data anonymization for analytics
- Compliance audit reporting

This service manages the full data lifecycle:
1. Active data (within retention period)
2. Archival (past retention period, moved to cold storage)
3. Anonymization (for analytics after retention period)
4. Deletion (on user request or legal requirement)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, update, func, text
from sqlalchemy.orm import selectinload
import uuid
import json
from enum import Enum

from ...database.models import (
    User, Tutor, Student, Session as TutoringSession,
    StudentFeedback, TutorPerformanceMetric, ChurnPrediction,
    Intervention, TutorEvent, Notification, AuditLog, ManagerNote,
    Base
)
from ..audit_service import AuditService
from ..config import settings
from .ferpa import FERPAService
from .gdpr import GDPRService


class RetentionStatus(str, Enum):
    """Data retention status."""
    ACTIVE = "active"  # Within retention period
    ELIGIBLE_FOR_ARCHIVAL = "eligible_for_archival"  # Past retention, can be archived
    ARCHIVED = "archived"  # Moved to cold storage
    ANONYMIZED = "anonymized"  # PII removed, kept for analytics
    DELETED = "deleted"  # Permanently removed


class RetentionAction(str, Enum):
    """Actions that can be taken on data."""
    ARCHIVE = "archive"  # Move to cold storage
    ANONYMIZE = "anonymize"  # Remove PII
    DELETE = "delete"  # Permanent deletion
    RESTORE = "restore"  # Restore from archive


class DataRetentionService:
    """
    Service for automated data retention and lifecycle management.

    Implements compliance requirements for FERPA, GDPR, and COPPA.
    """

    # Retention periods (in days)
    FERPA_RETENTION_DAYS = 2555  # 7 years for educational records
    GDPR_ANONYMIZATION_DAYS = 1095  # 3 years before anonymization eligible
    AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years for compliance logs

    # Grace period before automatic archival
    ARCHIVAL_GRACE_PERIOD_DAYS = 30

    @staticmethod
    async def scan_for_retention_actions(
        session: AsyncSession,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Scan all records and identify those eligible for retention actions.

        Args:
            session: Database session
            dry_run: If True, only report what would be done (don't take action)

        Returns:
            Dictionary with scan results and eligible records
        """
        scan_date = datetime.utcnow()
        retention_deadline = scan_date - timedelta(days=DataRetentionService.FERPA_RETENTION_DAYS)
        anonymization_deadline = scan_date - timedelta(days=DataRetentionService.GDPR_ANONYMIZATION_DAYS)

        results = {
            "scan_date": scan_date.isoformat(),
            "retention_deadline": retention_deadline.isoformat(),
            "anonymization_deadline": anonymization_deadline.isoformat(),
            "dry_run": dry_run,
            "eligible_for_archival": {
                "students": [],
                "tutors": [],
                "sessions": [],
                "feedback": [],
                "audit_logs": [],
            },
            "eligible_for_anonymization": {
                "students": [],
                "audit_logs": [],
            },
            "summary": {},
        }

        # Find students eligible for archival (no activity in 7 years)
        students_query = (
            select(Student)
            .where(Student.updated_at <= retention_deadline)
        )
        students_result = await session.execute(students_query)
        eligible_students = students_result.scalars().all()

        for student in eligible_students:
            # Check last activity (last session)
            last_session_query = (
                select(TutoringSession)
                .where(TutoringSession.student_id == student.student_id)
                .order_by(TutoringSession.scheduled_start.desc())
                .limit(1)
            )
            last_session_result = await session.execute(last_session_query)
            last_session = last_session_result.scalar_one_or_none()

            last_activity = last_session.scheduled_start if last_session else student.created_at
            days_since_activity = (scan_date - last_activity).days

            if days_since_activity >= DataRetentionService.FERPA_RETENTION_DAYS:
                results["eligible_for_archival"]["students"].append({
                    "student_id": student.student_id,
                    "name": student.name,
                    "created_at": student.created_at.isoformat(),
                    "last_activity": last_activity.isoformat(),
                    "days_since_activity": days_since_activity,
                    "eligible_for": RetentionAction.ARCHIVE.value,
                })

        # Find tutors eligible for archival (inactive for 7 years)
        tutors_query = (
            select(Tutor)
            .where(Tutor.updated_at <= retention_deadline)
        )
        tutors_result = await session.execute(tutors_query)
        eligible_tutors = tutors_result.scalars().all()

        for tutor in eligible_tutors:
            # Check last activity (last session)
            last_session_query = (
                select(TutoringSession)
                .where(TutoringSession.tutor_id == tutor.tutor_id)
                .order_by(TutoringSession.scheduled_start.desc())
                .limit(1)
            )
            last_session_result = await session.execute(last_session_query)
            last_session = last_session_result.scalar_one_or_none()

            last_activity = last_session.scheduled_start if last_session else tutor.created_at
            days_since_activity = (scan_date - last_activity).days

            if days_since_activity >= DataRetentionService.FERPA_RETENTION_DAYS:
                results["eligible_for_archival"]["tutors"].append({
                    "tutor_id": tutor.tutor_id,
                    "name": tutor.name,
                    "created_at": tutor.created_at.isoformat(),
                    "last_activity": last_activity.isoformat(),
                    "days_since_activity": days_since_activity,
                    "eligible_for": RetentionAction.ARCHIVE.value,
                })

        # Find old sessions (7+ years old)
        sessions_query = (
            select(TutoringSession)
            .where(TutoringSession.scheduled_start <= retention_deadline)
        )
        sessions_result = await session.execute(sessions_query)
        old_sessions = sessions_result.scalars().all()

        results["eligible_for_archival"]["sessions"] = [
            {
                "session_id": sess.session_id,
                "tutor_id": sess.tutor_id,
                "student_id": sess.student_id,
                "scheduled_start": sess.scheduled_start.isoformat(),
                "subject": sess.subject,
                "eligible_for": RetentionAction.ARCHIVE.value,
            }
            for sess in old_sessions
        ]

        # Find old feedback (7+ years old)
        feedback_query = (
            select(StudentFeedback)
            .where(StudentFeedback.submitted_at <= retention_deadline)
        )
        feedback_result = await session.execute(feedback_query)
        old_feedback = feedback_result.scalars().all()

        results["eligible_for_archival"]["feedback"] = [
            {
                "feedback_id": fb.feedback_id,
                "session_id": fb.session_id,
                "tutor_id": fb.tutor_id,
                "student_id": fb.student_id,
                "submitted_at": fb.submitted_at.isoformat(),
                "eligible_for": RetentionAction.ARCHIVE.value,
            }
            for fb in old_feedback
        ]

        # Find old audit logs (7+ years old) - only keep for compliance
        audit_deadline = scan_date - timedelta(days=DataRetentionService.AUDIT_LOG_RETENTION_DAYS)
        audit_logs_query = (
            select(AuditLog)
            .where(AuditLog.timestamp <= audit_deadline)
        )
        audit_logs_result = await session.execute(audit_logs_query)
        old_audit_logs = audit_logs_result.scalars().all()

        results["eligible_for_archival"]["audit_logs"] = [
            {
                "log_id": log.log_id,
                "action": log.action,
                "timestamp": log.timestamp.isoformat(),
                "eligible_for": RetentionAction.ARCHIVE.value,
            }
            for log in old_audit_logs
        ]

        # Find records eligible for anonymization (3+ years old)
        students_anon_query = (
            select(Student)
            .where(Student.updated_at <= anonymization_deadline)
        )
        students_anon_result = await session.execute(students_anon_query)
        anon_students = students_anon_result.scalars().all()

        results["eligible_for_anonymization"]["students"] = [
            {
                "student_id": student.student_id,
                "name": student.name,
                "created_at": student.created_at.isoformat(),
                "eligible_for": RetentionAction.ANONYMIZE.value,
            }
            for student in anon_students
        ]

        # Generate summary
        results["summary"] = {
            "total_students_for_archival": len(results["eligible_for_archival"]["students"]),
            "total_tutors_for_archival": len(results["eligible_for_archival"]["tutors"]),
            "total_sessions_for_archival": len(results["eligible_for_archival"]["sessions"]),
            "total_feedback_for_archival": len(results["eligible_for_archival"]["feedback"]),
            "total_audit_logs_for_archival": len(results["eligible_for_archival"]["audit_logs"]),
            "total_students_for_anonymization": len(results["eligible_for_anonymization"]["students"]),
        }

        # Log the scan
        await AuditService.log(
            session=session,
            action="data_retention_scan",
            user_id=None,
            resource_type="system",
            resource_id="retention_scanner",
            success=True,
            metadata={
                "scan_results": results["summary"],
                "dry_run": dry_run,
            }
        )

        return results

    @staticmethod
    async def archive_student_data(
        session: AsyncSession,
        student_id: str,
        reason: str = "FERPA retention period expired",
        performed_by_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Archive all data for a student to cold storage.

        This moves data to archival tables and removes from active tables.
        Maintains compliance with FERPA 7-year retention.

        Args:
            session: Database session
            student_id: Student ID to archive
            reason: Reason for archival
            performed_by_user_id: User performing the archival

        Returns:
            Summary of archival operation
        """
        archive_date = datetime.utcnow()
        archive_id = str(uuid.uuid4())

        # Get student record
        student_query = select(Student).where(Student.student_id == student_id)
        student_result = await session.execute(student_query)
        student = student_result.scalar_one_or_none()

        if not student:
            raise ValueError(f"Student {student_id} not found")

        # Check retention eligibility
        retention_check = await FERPAService.check_retention_policy(session, student_id)
        if not retention_check.get("eligible_for_deletion"):
            raise ValueError(
                f"Student {student_id} not eligible for archival yet. "
                f"Days until eligible: {retention_check.get('days_until_eligible_deletion')}"
            )

        archival_summary = {
            "archive_id": archive_id,
            "student_id": student_id,
            "archive_date": archive_date.isoformat(),
            "reason": reason,
            "performed_by": performed_by_user_id,
            "archived_records": {},
        }

        # Archive student sessions
        sessions_query = select(TutoringSession).where(TutoringSession.student_id == student_id)
        sessions_result = await session.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        # For now, we'll store archived data as JSON in audit logs
        # In production, you'd create separate archival tables
        archived_sessions = [
            {
                "session_id": sess.session_id,
                "tutor_id": sess.tutor_id,
                "scheduled_start": sess.scheduled_start.isoformat(),
                "duration_minutes": sess.duration_minutes,
                "subject": sess.subject,
                "engagement_score": sess.engagement_score,
            }
            for sess in sessions
        ]

        # Archive student feedback
        feedback_query = select(StudentFeedback).where(StudentFeedback.student_id == student_id)
        feedback_result = await session.execute(feedback_query)
        feedbacks = feedback_result.scalars().all()

        archived_feedback = [
            {
                "feedback_id": fb.feedback_id,
                "session_id": fb.session_id,
                "overall_rating": fb.overall_rating,
                "submitted_at": fb.submitted_at.isoformat(),
            }
            for fb in feedbacks
        ]

        # Store archival record
        archival_summary["archived_records"] = {
            "student_data": {
                "student_id": student.student_id,
                "name": student.name,
                "created_at": student.created_at.isoformat(),
            },
            "sessions": archived_sessions,
            "feedback": archived_feedback,
            "record_counts": {
                "sessions": len(archived_sessions),
                "feedback": len(archived_feedback),
            }
        }

        # Log archival action
        await AuditService.log(
            session=session,
            action="data_archived",
            user_id=performed_by_user_id,
            resource_type="student",
            resource_id=student_id,
            success=True,
            metadata={
                "archive_id": archive_id,
                "archival_summary": archival_summary,
                "ferpa_retention_deadline_met": True,
            }
        )

        # Delete active records (they're now in archival storage via audit log)
        await session.execute(delete(StudentFeedback).where(StudentFeedback.student_id == student_id))
        await session.execute(delete(TutoringSession).where(TutoringSession.student_id == student_id))
        await session.execute(delete(Student).where(Student.student_id == student_id))

        await session.commit()

        return archival_summary

    @staticmethod
    async def anonymize_data_for_analytics(
        session: AsyncSession,
        entity_type: str,
        entity_id: str,
        performed_by_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Anonymize PII while preserving data for analytics.

        Removes personally identifiable information but keeps statistical
        and behavioral data for research and analytics purposes.

        Args:
            session: Database session
            entity_type: Type of entity ("student" or "tutor")
            entity_id: Entity ID to anonymize
            performed_by_user_id: User performing anonymization

        Returns:
            Summary of anonymization operation
        """
        anonymization_date = datetime.utcnow()

        if entity_type == "student":
            # Get student
            student_query = select(Student).where(Student.student_id == entity_id)
            student_result = await session.execute(student_query)
            student = student_result.scalar_one_or_none()

            if not student:
                raise ValueError(f"Student {entity_id} not found")

            # Anonymize PII
            original_data = {
                "name": student.name,
                "parent_email": student.parent_email,
            }

            student.name = f"ANONYMIZED_STUDENT_{entity_id[:8]}"
            student.parent_email = None
            student.parent_consent_ip = None

            # Keep: age, grade_level, subjects_interested (for analytics)

            anonymization_summary = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "anonymization_date": anonymization_date.isoformat(),
                "anonymized_fields": ["name", "parent_email", "parent_consent_ip"],
                "retained_fields": ["age", "grade_level", "subjects_interested"],
                "performed_by": performed_by_user_id,
            }

        elif entity_type == "tutor":
            # Get tutor
            tutor_query = select(Tutor).where(Tutor.tutor_id == entity_id)
            tutor_result = await session.execute(tutor_query)
            tutor = tutor_result.scalar_one_or_none()

            if not tutor:
                raise ValueError(f"Tutor {entity_id} not found")

            # Anonymize PII
            original_data = {
                "name": tutor.name,
                "email": tutor.email,
                "location": tutor.location,
            }

            tutor.name = f"ANONYMIZED_TUTOR_{entity_id[:8]}"
            tutor.email = f"anonymized_{entity_id[:8]}@example.com"
            tutor.location = "REDACTED"

            # Keep: subjects, education_level, behavioral_archetype, performance data

            anonymization_summary = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "anonymization_date": anonymization_date.isoformat(),
                "anonymized_fields": ["name", "email", "location"],
                "retained_fields": ["subjects", "education_level", "behavioral_archetype", "status"],
                "performed_by": performed_by_user_id,
            }
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        # Log anonymization
        await AuditService.log(
            session=session,
            action="data_anonymized",
            user_id=performed_by_user_id,
            resource_type=entity_type,
            resource_id=entity_id,
            success=True,
            metadata=anonymization_summary
        )

        await session.commit()

        return anonymization_summary

    @staticmethod
    async def process_deletion_request(
        session: AsyncSession,
        user_id: int,
        deletion_reason: str = "GDPR Article 17 - Right to Erasure",
        performed_by_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a user's request to delete their data (GDPR Right to be Forgotten).

        This is distinct from archival - it's permanent deletion per user request.

        Args:
            session: Database session
            user_id: User requesting deletion
            deletion_reason: Reason for deletion
            performed_by_user_id: User processing the request (admin)

        Returns:
            Deletion summary from GDPR service
        """
        # Use GDPR service for deletion
        deletion_summary = await GDPRService.delete_user_data(
            session=session,
            user_id=user_id,
            deletion_reason=deletion_reason,
            retain_audit_logs=True  # Keep anonymized logs for compliance
        )

        # Log deletion request processing
        await AuditService.log(
            session=session,
            action="deletion_request_processed",
            user_id=performed_by_user_id,
            resource_type="user",
            resource_id=str(user_id),
            success=True,
            metadata={
                "deletion_reason": deletion_reason,
                "deletion_summary": deletion_summary,
                "gdpr_article_17": True,
            }
        )

        return deletion_summary

    @staticmethod
    async def get_retention_report(
        session: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive data retention compliance report.

        Args:
            session: Database session
            start_date: Report start date (defaults to 90 days ago)
            end_date: Report end date (defaults to now)

        Returns:
            Comprehensive retention report
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        # Get archival actions
        archival_logs_query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.action == "data_archived",
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
        )
        archival_logs_result = await session.execute(archival_logs_query)
        archival_logs = archival_logs_result.scalars().all()

        # Get anonymization actions
        anonymization_logs_query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.action == "data_anonymized",
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
        )
        anonymization_logs_result = await session.execute(anonymization_logs_query)
        anonymization_logs = anonymization_logs_result.scalars().all()

        # Get deletion requests
        deletion_logs_query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.action.in_(["gdpr_data_deletion", "deletion_request_processed"]),
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
        )
        deletion_logs_result = await session.execute(deletion_logs_query)
        deletion_logs = deletion_logs_result.scalars().all()

        # Get current data statistics
        students_count_query = select(func.count(Student.student_id))
        students_count_result = await session.execute(students_count_query)
        total_students = students_count_result.scalar()

        tutors_count_query = select(func.count(Tutor.tutor_id))
        tutors_count_result = await session.execute(tutors_count_query)
        total_tutors = tutors_count_result.scalar()

        sessions_count_query = select(func.count(TutoringSession.session_id))
        sessions_count_result = await session.execute(sessions_count_query)
        total_sessions = sessions_count_result.scalar()

        # Generate report
        report = {
            "report_generated_at": datetime.utcnow().isoformat(),
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "current_data_inventory": {
                "active_students": total_students,
                "active_tutors": total_tutors,
                "total_sessions": total_sessions,
            },
            "retention_actions_taken": {
                "archival_operations": len(archival_logs),
                "anonymization_operations": len(anonymization_logs),
                "deletion_requests_processed": len(deletion_logs),
            },
            "archival_details": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "performed_by": log.user_id,
                }
                for log in archival_logs
            ],
            "anonymization_details": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "performed_by": log.user_id,
                }
                for log in anonymization_logs
            ],
            "deletion_details": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "performed_by": log.user_id,
                    "reason": log.audit_metadata.get("deletion_reason") if log.audit_metadata else None,
                }
                for log in deletion_logs
            ],
            "compliance_status": {
                "ferpa_retention_policy": "7 years (2555 days)",
                "gdpr_anonymization_eligible_after": "3 years (1095 days)",
                "audit_log_retention": "7 years (2555 days)",
            }
        }

        return report

    @staticmethod
    async def schedule_automated_archival(
        session: AsyncSession,
        perform_actions: bool = False
    ) -> Dict[str, Any]:
        """
        Scheduled job to automatically archive eligible data.

        This should be run periodically (e.g., weekly or monthly) to maintain
        compliance with retention policies.

        Args:
            session: Database session
            perform_actions: If True, actually perform archival. If False, dry run.

        Returns:
            Summary of scheduled archival run
        """
        # Scan for eligible records
        scan_results = await DataRetentionService.scan_for_retention_actions(
            session=session,
            dry_run=not perform_actions
        )

        archival_results = {
            "run_date": datetime.utcnow().isoformat(),
            "mode": "live" if perform_actions else "dry_run",
            "scan_summary": scan_results["summary"],
            "actions_performed": {
                "students_archived": 0,
                "tutors_archived": 0,
                "errors": [],
            }
        }

        if perform_actions:
            # Archive eligible students
            for student_info in scan_results["eligible_for_archival"]["students"]:
                try:
                    await DataRetentionService.archive_student_data(
                        session=session,
                        student_id=student_info["student_id"],
                        reason="Automated archival - FERPA retention period expired"
                    )
                    archival_results["actions_performed"]["students_archived"] += 1
                except Exception as e:
                    archival_results["actions_performed"]["errors"].append({
                        "entity_type": "student",
                        "entity_id": student_info["student_id"],
                        "error": str(e)
                    })

        # Log scheduled run
        await AuditService.log(
            session=session,
            action="scheduled_archival_run",
            user_id=None,
            resource_type="system",
            resource_id="retention_scheduler",
            success=True,
            metadata=archival_results
        )

        return archival_results


# Global service instance
data_retention_service = DataRetentionService()
