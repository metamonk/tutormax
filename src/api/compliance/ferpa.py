"""
FERPA (Family Educational Rights and Privacy Act) Compliance Module

Implements FERPA compliance requirements for TutorMax educational platform:
- 7-year data retention policy enforcement
- Student record access control
- Educational record classification
- Parent/guardian access management
- FERPA disclosure logging

FERPA Overview:
- Protects privacy of student education records
- Applies to all schools and agencies receiving federal education funding
- Requires written consent before disclosing personally identifiable information
- Mandates certain record-keeping and notification requirements

Key Requirements Implemented:
1. Access Control: Only authorized parties can access education records
2. Disclosure Logging: All disclosures must be logged
3. Data Retention: Records must be retained for 7 years
4. Parental Rights: Parents have rights to access minor children's records
5. Student Rights: Students gain rights when they turn 18 or attend postsecondary institution

Reference: 20 U.S.C. § 1232g; 34 CFR Part 99
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

# Use relative imports like coppa.py does
import sys
from pathlib import Path
# Add src to path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import (
    User, Student, Session, StudentFeedback,
    TutorPerformanceMetric, UserRole, AuditLog
)
from src.api.audit_service import AuditService
from src.api.security import encryption_service, anonymization_service
from src.api.config import settings


class FERPARecordType(str, Enum):
    """
    Classification of educational records under FERPA.

    Educational records include any records directly related to a student
    maintained by an educational agency or institution.
    """
    # Core educational records
    ENROLLMENT = "enrollment"  # Student registration, enrollment status
    ACADEMIC_PERFORMANCE = "academic_performance"  # Grades, test scores, session data
    ATTENDANCE = "attendance"  # Session attendance, no-shows
    FEEDBACK = "feedback"  # Student feedback and evaluations
    BEHAVIORAL = "behavioral"  # Disciplinary records, behavioral notes
    PROGRESS = "progress"  # Learning progress, objectives met

    # Supporting records
    PERSONAL_IDENTIFICATION = "personal_identification"  # Name, ID, contact info
    PARENTAL_INFO = "parental_info"  # Parent/guardian information
    TUTOR_ASSIGNMENTS = "tutor_assignments"  # Tutor-student relationships
    COMMUNICATION = "communication"  # Messages, notifications

    # Directory information (can be disclosed without consent if properly designated)
    DIRECTORY_INFO = "directory_info"  # Name, enrollment dates, subjects


class FERPAAccessType(str, Enum):
    """Types of access to educational records."""
    SCHOOL_OFFICIAL = "school_official"  # Legitimate educational interest
    STUDENT = "student"  # Student accessing own records
    PARENT = "parent"  # Parent/guardian of minor student
    AUTHORIZED_THIRD_PARTY = "authorized_third_party"  # With written consent
    COURT_ORDER = "court_order"  # Pursuant to court order or subpoena
    HEALTH_SAFETY_EMERGENCY = "health_safety_emergency"  # Emergency situations
    AUDIT_EVALUATION = "audit_evaluation"  # For audit or evaluation purposes


class FERPADisclosureReason(str, Enum):
    """Reasons for disclosing educational records under FERPA."""
    STUDENT_REQUEST = "student_request"
    PARENT_REQUEST = "parent_request"
    SCHOOL_OFFICIAL = "school_official"
    AUDIT_EVALUATION = "audit_evaluation"
    FINANCIAL_AID = "financial_aid"
    ACCREDITATION = "accreditation"
    COMPLIANCE_LEGAL = "compliance_legal"
    HEALTH_SAFETY = "health_safety"
    WRITTEN_CONSENT = "written_consent"
    DIRECTORY_INFORMATION = "directory_information"


class FERPAService:
    """
    Service for managing FERPA compliance requirements.

    This service provides utilities for:
    - Determining record access eligibility
    - Logging FERPA-compliant disclosures
    - Managing data retention policies
    - Handling parent/guardian access rights
    """

    # FERPA requires 7-year retention for educational records
    RETENTION_PERIOD_DAYS = 2555  # 7 years

    # Student rights transfer at age 18 or postsecondary enrollment
    AGE_OF_MAJORITY = 18

    @staticmethod
    async def can_access_student_record(
        session: AsyncSession,
        requesting_user_id: int,
        student_id: str,
        access_type: Optional[FERPAAccessType] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if a user can access a student's educational records.

        Args:
            session: Database session
            requesting_user_id: ID of user requesting access
            student_id: ID of student whose records are being accessed
            access_type: Type of access being requested

        Returns:
            Tuple of (can_access: bool, reason: str or None)
            If access denied, reason explains why
        """
        # Get requesting user
        user_query = select(User).where(User.id == requesting_user_id)
        user_result = await session.execute(user_query)
        requesting_user = user_result.scalar_one_or_none()

        if not requesting_user:
            return False, "User not found"

        # Get student
        student_query = select(Student).where(Student.student_id == student_id)
        student_result = await session.execute(student_query)
        student = student_result.scalar_one_or_none()

        if not student:
            return False, "Student not found"

        # Check if user is the student themselves
        if requesting_user.student_id == student_id:
            # Student has right to access own records if 18+ or in postsecondary
            if student.age and student.age >= FERPAService.AGE_OF_MAJORITY:
                return True, None
            # For students under 18, check if they're in postsecondary
            # (In TutorMax, we'll allow self-access for all students)
            return True, None

        # Check if user is a parent/guardian (for students under 18)
        if student.age and student.age < FERPAService.AGE_OF_MAJORITY:
            # Check if user's email matches parent email
            if student.parent_email and requesting_user.email == student.parent_email:
                if not student.parent_consent_given:
                    return False, "Parental consent required but not given"
                return True, None

        # Check for school official status (legitimate educational interest)
        if UserRole.ADMIN in requesting_user.roles:
            return True, None

        if UserRole.OPERATIONS_MANAGER in requesting_user.roles:
            return True, None

        if UserRole.PEOPLE_OPS in requesting_user.roles:
            return True, None

        # Check if user is assigned tutor for this student
        if UserRole.TUTOR in requesting_user.roles:
            # Check if tutor has sessions with this student
            session_query = select(Session).where(
                and_(
                    Session.student_id == student_id,
                    Session.tutor_id == requesting_user.tutor_id
                )
            ).limit(1)
            session_result = await session.execute(session_query)
            has_sessions = session_result.scalar_one_or_none() is not None

            if has_sessions:
                return True, None

        return False, "No legitimate educational interest or authorization"

    @staticmethod
    async def log_ferpa_disclosure(
        session: AsyncSession,
        user_id: int,
        student_id: str,
        record_type: FERPARecordType,
        disclosure_reason: FERPADisclosureReason,
        access_type: FERPAAccessType,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log a FERPA-compliant disclosure of educational records.

        FERPA requires institutions to maintain a record of each request for
        access to and each disclosure of personally identifiable information
        from education records.

        Args:
            session: Database session
            user_id: User accessing the records
            student_id: Student whose records are being accessed
            record_type: Type of educational record
            disclosure_reason: Reason for disclosure
            access_type: Type of access granted
            resource_type: Type of resource accessed (e.g., "session", "feedback")
            resource_id: Specific resource ID
            ip_address: IP address of request
            user_agent: User agent string
            additional_metadata: Additional context information

        Returns:
            Created AuditLog entry
        """
        metadata = additional_metadata or {}
        metadata.update({
            "ferpa_disclosure": True,
            "student_id": student_id,
            "record_type": record_type.value,
            "disclosure_reason": disclosure_reason.value,
            "access_type": access_type.value,
            "compliance_framework": "FERPA",
            "timestamp": datetime.utcnow().isoformat(),
        })

        return await AuditService.log(
            session=session,
            action=f"ferpa_disclosure_{record_type.value}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="GET",
            request_path=f"/api/students/{student_id}/{resource_type}",
            status_code=200,
            success=True,
            metadata=metadata,
        )

    @staticmethod
    async def check_retention_policy(
        session: AsyncSession,
        student_id: str,
    ) -> Dict[str, Any]:
        """
        Check if student records meet FERPA retention requirements.

        FERPA doesn't mandate a specific retention period, but 7 years is
        standard practice in educational institutions for legal protection.

        Args:
            session: Database session
            student_id: Student ID to check

        Returns:
            Dictionary with retention status information
        """
        # Get student
        student_query = select(Student).where(Student.student_id == student_id)
        student_result = await session.execute(student_query)
        student = student_result.scalar_one_or_none()

        if not student:
            return {
                "student_id": student_id,
                "exists": False,
                "error": "Student not found"
            }

        # Calculate age of record
        record_age_days = (datetime.utcnow() - student.created_at).days
        retention_deadline = student.created_at + timedelta(days=FERPAService.RETENTION_PERIOD_DAYS)
        days_until_eligible_deletion = (retention_deadline - datetime.utcnow()).days

        # Check for recent activity (last session)
        last_session_query = (
            select(Session)
            .where(Session.student_id == student_id)
            .order_by(Session.scheduled_start.desc())
            .limit(1)
        )
        last_session_result = await session.execute(last_session_query)
        last_session = last_session_result.scalar_one_or_none()

        last_activity_date = None
        if last_session:
            last_activity_date = last_session.scheduled_start
            # Update retention calculation based on last activity
            activity_age_days = (datetime.utcnow() - last_activity_date).days
            activity_retention_deadline = last_activity_date + timedelta(
                days=FERPAService.RETENTION_PERIOD_DAYS
            )
            days_until_eligible_deletion = (activity_retention_deadline - datetime.utcnow()).days

        return {
            "student_id": student_id,
            "exists": True,
            "created_at": student.created_at.isoformat(),
            "record_age_days": record_age_days,
            "last_activity_date": last_activity_date.isoformat() if last_activity_date else None,
            "retention_period_days": FERPAService.RETENTION_PERIOD_DAYS,
            "retention_deadline": retention_deadline.isoformat(),
            "days_until_eligible_deletion": max(0, days_until_eligible_deletion),
            "eligible_for_deletion": days_until_eligible_deletion <= 0,
            "should_retain": days_until_eligible_deletion > 0,
        }

    @staticmethod
    async def get_student_educational_records(
        session: AsyncSession,
        student_id: str,
        record_types: Optional[List[FERPARecordType]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve all educational records for a student, organized by type.

        Args:
            session: Database session
            student_id: Student ID
            record_types: Optional filter for specific record types

        Returns:
            Dictionary containing all educational records organized by type
        """
        records = {
            "student_id": student_id,
            "retrieved_at": datetime.utcnow().isoformat(),
            "records": {}
        }

        # Personal identification information
        if not record_types or FERPARecordType.PERSONAL_IDENTIFICATION in record_types:
            student_query = select(Student).where(Student.student_id == student_id)
            student_result = await session.execute(student_query)
            student = student_result.scalar_one_or_none()

            if student:
                records["records"][FERPARecordType.PERSONAL_IDENTIFICATION.value] = {
                    "student_id": student.student_id,
                    "name": student.name,
                    "age": student.age,
                    "grade_level": student.grade_level,
                    "subjects_interested": student.subjects_interested,
                    "created_at": student.created_at.isoformat(),
                }

        # Parental information (if applicable)
        if not record_types or FERPARecordType.PARENTAL_INFO in record_types:
            student_query = select(Student).where(Student.student_id == student_id)
            student_result = await session.execute(student_query)
            student = student_result.scalar_one_or_none()

            if student and student.is_under_13:
                records["records"][FERPARecordType.PARENTAL_INFO.value] = {
                    "parent_email": anonymization_service.anonymize_email(student.parent_email) if student.parent_email else None,
                    "parent_consent_given": student.parent_consent_given,
                    "parent_consent_date": student.parent_consent_date.isoformat() if student.parent_consent_date else None,
                    "is_under_13": student.is_under_13,
                }

        # Academic performance and attendance
        if not record_types or FERPARecordType.ACADEMIC_PERFORMANCE in record_types or FERPARecordType.ATTENDANCE in record_types:
            sessions_query = select(Session).where(Session.student_id == student_id)
            sessions_result = await session.execute(sessions_query)
            sessions = sessions_result.scalars().all()

            session_records = []
            for sess in sessions:
                session_records.append({
                    "session_id": sess.session_id,
                    "tutor_id": sess.tutor_id,
                    "subject": sess.subject,
                    "scheduled_start": sess.scheduled_start.isoformat(),
                    "actual_start": sess.actual_start.isoformat() if sess.actual_start else None,
                    "duration_minutes": sess.duration_minutes,
                    "attendance": "attended" if sess.actual_start else ("no_show" if sess.no_show else "scheduled"),
                    "engagement_score": sess.engagement_score,
                    "learning_objectives_met": sess.learning_objectives_met,
                    "late_start_minutes": sess.late_start_minutes,
                })

            records["records"][FERPARecordType.ACADEMIC_PERFORMANCE.value] = session_records
            records["records"][FERPARecordType.ATTENDANCE.value] = {
                "total_sessions": len(sessions),
                "attended": sum(1 for s in sessions if s.actual_start),
                "no_shows": sum(1 for s in sessions if s.no_show),
                "attendance_rate": (sum(1 for s in sessions if s.actual_start) / len(sessions) * 100) if sessions else 0,
            }

        # Student feedback
        if not record_types or FERPARecordType.FEEDBACK in record_types:
            feedback_query = select(StudentFeedback).where(StudentFeedback.student_id == student_id)
            feedback_result = await session.execute(feedback_query)
            feedbacks = feedback_result.scalars().all()

            feedback_records = []
            for fb in feedbacks:
                feedback_records.append({
                    "feedback_id": fb.feedback_id,
                    "session_id": fb.session_id,
                    "overall_rating": fb.overall_rating,
                    "submitted_at": fb.submitted_at.isoformat(),
                    "ratings": {
                        "subject_knowledge": fb.subject_knowledge_rating,
                        "communication": fb.communication_rating,
                        "patience": fb.patience_rating,
                        "engagement": fb.engagement_rating,
                        "helpfulness": fb.helpfulness_rating,
                    },
                    "would_recommend": fb.would_recommend,
                })

            records["records"][FERPARecordType.FEEDBACK.value] = feedback_records

        return records

    @staticmethod
    async def verify_parental_consent(
        session: AsyncSession,
        student_id: str,
    ) -> Dict[str, Any]:
        """
        Verify that parental consent is properly documented for students under 13.

        COPPA (Children's Online Privacy Protection Act) requires verifiable
        parental consent for children under 13. This overlaps with FERPA
        parental rights.

        Args:
            session: Database session
            student_id: Student ID

        Returns:
            Dictionary with consent verification status
        """
        student_query = select(Student).where(Student.student_id == student_id)
        student_result = await session.execute(student_query)
        student = student_result.scalar_one_or_none()

        if not student:
            return {
                "student_id": student_id,
                "exists": False,
                "error": "Student not found"
            }

        requires_consent = student.is_under_13
        has_consent = student.parent_consent_given

        return {
            "student_id": student_id,
            "is_under_13": student.is_under_13,
            "requires_parental_consent": requires_consent,
            "parent_email_on_file": bool(student.parent_email),
            "consent_given": has_consent,
            "consent_date": student.parent_consent_date.isoformat() if student.parent_consent_date else None,
            "consent_ip": student.parent_consent_ip,
            "compliant": not requires_consent or (requires_consent and has_consent),
            "issues": [] if not requires_consent or (requires_consent and has_consent) else [
                "Parental consent required but not documented"
            ],
        }

    @staticmethod
    def classify_record_type(
        resource_type: str,
        data_context: Optional[Dict[str, Any]] = None,
    ) -> FERPARecordType:
        """
        Classify a data resource into a FERPA record type.

        Args:
            resource_type: Type of resource (e.g., "session", "feedback")
            data_context: Additional context about the data

        Returns:
            Appropriate FERPARecordType classification
        """
        mapping = {
            "student": FERPARecordType.PERSONAL_IDENTIFICATION,
            "session": FERPARecordType.ACADEMIC_PERFORMANCE,
            "feedback": FERPARecordType.FEEDBACK,
            "performance_metric": FERPARecordType.PROGRESS,
            "tutor": FERPARecordType.TUTOR_ASSIGNMENTS,
            "notification": FERPARecordType.COMMUNICATION,
        }

        return mapping.get(resource_type, FERPARecordType.ACADEMIC_PERFORMANCE)

    @staticmethod
    async def get_disclosure_history(
        session: AsyncSession,
        student_id: str,
        days: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        Get FERPA disclosure history for a student.

        FERPA requires maintaining records of disclosures for inspection.

        Args:
            session: Database session
            student_id: Student ID
            days: Number of days of history to retrieve

        Returns:
            List of disclosure records
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Query audit logs for FERPA disclosures
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.action.like("ferpa_disclosure_%"),
                    AuditLog.timestamp >= start_date,
                )
            )
        )

        result = await session.execute(query)
        logs = result.scalars().all()

        # Filter for this student (metadata contains student_id)
        disclosures = []
        for log in logs:
            if log.audit_metadata and log.audit_metadata.get("student_id") == student_id:
                disclosures.append({
                    "disclosure_id": log.log_id,
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "record_type": log.audit_metadata.get("record_type"),
                    "disclosure_reason": log.audit_metadata.get("disclosure_reason"),
                    "access_type": log.audit_metadata.get("access_type"),
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "ip_address": log.ip_address,
                })

        return disclosures

    @staticmethod
    def get_retention_schedule() -> Dict[str, Any]:
        """
        Get the data retention schedule for FERPA compliance.

        Returns:
            Dictionary describing retention policies
        """
        return {
            "framework": "FERPA",
            "retention_period_years": 7,
            "retention_period_days": FERPAService.RETENTION_PERIOD_DAYS,
            "record_types": {
                FERPARecordType.PERSONAL_IDENTIFICATION.value: {
                    "retention_days": FERPAService.RETENTION_PERIOD_DAYS,
                    "description": "Student identification and contact information",
                },
                FERPARecordType.ACADEMIC_PERFORMANCE.value: {
                    "retention_days": FERPAService.RETENTION_PERIOD_DAYS,
                    "description": "Session data, grades, test scores, performance metrics",
                },
                FERPARecordType.ATTENDANCE.value: {
                    "retention_days": FERPAService.RETENTION_PERIOD_DAYS,
                    "description": "Attendance records, no-shows, scheduling",
                },
                FERPARecordType.FEEDBACK.value: {
                    "retention_days": FERPAService.RETENTION_PERIOD_DAYS,
                    "description": "Student feedback and evaluations",
                },
                FERPARecordType.PARENTAL_INFO.value: {
                    "retention_days": FERPAService.RETENTION_PERIOD_DAYS,
                    "description": "Parental consent and contact information",
                },
                FERPARecordType.PROGRESS.value: {
                    "retention_days": FERPAService.RETENTION_PERIOD_DAYS,
                    "description": "Learning progress and developmental records",
                },
            },
            "audit_logs": {
                "retention_days": FERPAService.RETENTION_PERIOD_DAYS,
                "description": "FERPA disclosure logs and access records",
            },
            "notes": [
                "Records are retained for 7 years from date of last educational activity",
                "Audit logs of disclosures must be maintained for the same period",
                "Student/parent has right to inspect disclosure records",
                "Data can be anonymized for research after retention period",
            ]
        }


class FERPAAccessControl:
    """
    Helper class for enforcing FERPA access control policies.

    Use this in route handlers to verify access before serving data.
    """

    @staticmethod
    async def require_student_access(
        session: AsyncSession,
        requesting_user_id: int,
        student_id: str,
        access_type: FERPAAccessType = FERPAAccessType.SCHOOL_OFFICIAL,
    ) -> None:
        """
        Require access to student records, raising exception if denied.

        Args:
            session: Database session
            requesting_user_id: User requesting access
            student_id: Student whose records are being accessed
            access_type: Type of access being requested

        Raises:
            PermissionError: If access is denied
        """
        can_access, reason = await FERPAService.can_access_student_record(
            session=session,
            requesting_user_id=requesting_user_id,
            student_id=student_id,
            access_type=access_type,
        )

        if not can_access:
            raise PermissionError(
                f"FERPA access denied to student {student_id}: {reason}"
            )

    @staticmethod
    async def log_and_authorize_access(
        session: AsyncSession,
        requesting_user_id: int,
        student_id: str,
        record_type: FERPARecordType,
        disclosure_reason: FERPADisclosureReason,
        access_type: FERPAAccessType,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Verify access AND log the disclosure in one operation.

        This is the recommended method for FERPA-compliant data access.

        Args:
            session: Database session
            requesting_user_id: User requesting access
            student_id: Student whose records are being accessed
            record_type: Type of educational record
            disclosure_reason: Reason for accessing the record
            access_type: Type of access
            resource_type: Type of resource
            resource_id: Specific resource ID
            ip_address: IP address of request
            user_agent: User agent string

        Returns:
            AuditLog entry

        Raises:
            PermissionError: If access is denied
        """
        # First verify access
        await FERPAAccessControl.require_student_access(
            session=session,
            requesting_user_id=requesting_user_id,
            student_id=student_id,
            access_type=access_type,
        )

        # Then log the disclosure
        return await FERPAService.log_ferpa_disclosure(
            session=session,
            user_id=requesting_user_id,
            student_id=student_id,
            record_type=record_type,
            disclosure_reason=disclosure_reason,
            access_type=access_type,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
