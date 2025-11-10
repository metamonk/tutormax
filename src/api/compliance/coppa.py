"""
COPPA Compliance Service for TutorMax

Implements Children's Online Privacy Protection Act (COPPA) compliance features:
- Age verification for users under 13
- Parental consent workflow
- Minimal data collection for under-13 users
- Parental access to child data
- COPPA-compliant data deletion

COPPA Requirements:
1. Notice: Clear privacy policy about data collection
2. Parental Consent: Verifiable consent before collecting PII from children under 13
3. Data Minimization: Collect only what's necessary for the service
4. Confidentiality: Keep child data secure
5. Deletion: Delete child data upon parent request
6. Parental Access: Allow parents to review and delete child data
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import enum
import uuid
import secrets

from src.database.models import Student, User
from ..security import anonymization_service, encryption_service
from ..audit_service import AuditService
from ..config import settings


class ParentalConsentStatus(str, enum.Enum):
    """Status of parental consent for COPPA compliance."""
    PENDING = "pending"  # Consent request sent, awaiting response
    GRANTED = "granted"  # Parent has granted consent
    DENIED = "denied"    # Parent has denied consent
    EXPIRED = "expired"  # Consent request expired without response
    REVOKED = "revoked"  # Parent revoked previously granted consent


class COPPAService:
    """
    Service for managing COPPA compliance requirements.

    Handles:
    - Age verification
    - Parental consent workflows
    - Data minimization for under-13 users
    - Parental access controls
    - COPPA-compliant data deletion
    """

    # COPPA age threshold (children under 13)
    COPPA_AGE_THRESHOLD = 13

    # Consent token expiration (30 days)
    CONSENT_TOKEN_EXPIRY_DAYS = 30

    # Minimal data fields allowed for under-13 without consent
    MINIMAL_DATA_FIELDS = {
        'student_id',
        'age',
        'grade_level',
        'subjects_interested',  # Educational necessity
        'created_at',
        'updated_at',
    }

    @staticmethod
    def verify_age(age: Optional[int]) -> bool:
        """
        Verify if a user's age requires COPPA protection.

        Args:
            age: User's age in years

        Returns:
            True if user is under 13 (COPPA protected), False otherwise
        """
        return age is not None and age < COPPAService.COPPA_AGE_THRESHOLD

    @staticmethod
    def requires_parental_consent(student: Student) -> bool:
        """
        Check if a student requires parental consent under COPPA.

        Args:
            student: Student record

        Returns:
            True if student is under 13 and needs parental consent
        """
        if not settings.coppa_compliance_enabled:
            return False

        # Check if student is flagged as under 13
        if student.is_under_13:
            return True

        # Check age if available
        if student.age is not None:
            return COPPAService.verify_age(student.age)

        return False

    @staticmethod
    def can_collect_data(student: Student) -> bool:
        """
        Check if we can collect personal data from a student.

        Under COPPA:
        - If student is 13+, we can collect data
        - If student is under 13 and has parental consent, we can collect data
        - If student is under 13 without consent, we can only collect minimal data

        Args:
            student: Student record

        Returns:
            True if data collection is allowed, False if restricted
        """
        if not COPPAService.requires_parental_consent(student):
            return True

        # Check if parental consent has been granted
        return student.parent_consent_given

    @staticmethod
    async def mark_student_as_under_13(
        session: AsyncSession,
        student_id: str,
        parent_email: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Student:
        """
        Mark a student as under 13 and initiate parental consent workflow.

        Args:
            session: Database session
            student_id: Student ID to mark
            parent_email: Parent/guardian email address
            user_id: User performing the action (for audit log)
            ip_address: IP address of the request

        Returns:
            Updated Student record

        Raises:
            ValueError: If student not found
        """
        # Get student
        result = await session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError(f"Student {student_id} not found")

        # Update student record
        student.is_under_13 = True
        student.parent_email = parent_email
        student.parent_consent_given = False
        student.parent_consent_date = None
        student.parent_consent_ip = None
        student.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(student)

        # Audit log
        await AuditService.log(
            session=session,
            action="coppa_mark_under_13",
            user_id=user_id,
            resource_type=AuditService.RESOURCE_STUDENT,
            resource_id=student_id,
            ip_address=ip_address,
            metadata={
                "parent_email": anonymization_service.anonymize_email(parent_email),
                "student_age": student.age,
            }
        )

        return student

    @staticmethod
    async def grant_parental_consent(
        session: AsyncSession,
        student_id: str,
        parent_email: str,
        ip_address: Optional[str] = None,
        consent_method: str = "online_form",
    ) -> Student:
        """
        Record parental consent for a student under 13.

        Args:
            session: Database session
            student_id: Student ID
            parent_email: Parent email (for verification)
            ip_address: IP address where consent was given
            consent_method: How consent was obtained (online_form, email, fax, etc.)

        Returns:
            Updated Student record

        Raises:
            ValueError: If student not found or email doesn't match
        """
        # Get student
        result = await session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError(f"Student {student_id} not found")

        if not student.is_under_13:
            raise ValueError(f"Student {student_id} is not marked as under 13")

        # Verify parent email matches
        if student.parent_email != parent_email:
            raise ValueError("Parent email does not match records")

        # Grant consent
        student.parent_consent_given = True
        student.parent_consent_date = datetime.utcnow()
        student.parent_consent_ip = ip_address
        student.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(student)

        # Audit log
        await AuditService.log(
            session=session,
            action="coppa_consent_granted",
            user_id=None,  # Parent action, not authenticated user
            resource_type=AuditService.RESOURCE_STUDENT,
            resource_id=student_id,
            ip_address=ip_address,
            metadata={
                "parent_email": anonymization_service.anonymize_email(parent_email),
                "consent_method": consent_method,
                "consent_date": student.parent_consent_date.isoformat(),
            }
        )

        return student

    @staticmethod
    async def revoke_parental_consent(
        session: AsyncSession,
        student_id: str,
        parent_email: str,
        ip_address: Optional[str] = None,
        delete_data: bool = True,
    ) -> Student:
        """
        Revoke parental consent and optionally delete student data.

        Under COPPA, when consent is revoked, we must:
        1. Stop collecting data from the child
        2. Delete existing data (unless we have another legal basis)

        Args:
            session: Database session
            student_id: Student ID
            parent_email: Parent email (for verification)
            ip_address: IP address of the request
            delete_data: Whether to delete student data (default: True per COPPA)

        Returns:
            Updated Student record (or minimal record if data deleted)

        Raises:
            ValueError: If student not found or email doesn't match
        """
        # Get student
        result = await session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError(f"Student {student_id} not found")

        # Verify parent email matches
        if student.parent_email != parent_email:
            raise ValueError("Parent email does not match records")

        # Audit log before deletion
        await AuditService.log(
            session=session,
            action="coppa_consent_revoked",
            user_id=None,
            resource_type=AuditService.RESOURCE_STUDENT,
            resource_id=student_id,
            ip_address=ip_address,
            metadata={
                "parent_email": anonymization_service.anonymize_email(parent_email),
                "delete_data": delete_data,
                "previous_consent_date": student.parent_consent_date.isoformat() if student.parent_consent_date else None,
            }
        )

        # Revoke consent
        student.parent_consent_given = False

        if delete_data:
            # Delete PII but keep minimal educational record
            student.name = f"Student_{student.student_id[-6:]}"  # Anonymized name
            student.parent_email = None
            student.parent_consent_date = None
            student.parent_consent_ip = None
            # Keep: student_id, age, grade_level, subjects_interested (educational necessity)

        student.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(student)

        return student

    @staticmethod
    async def get_child_data_for_parent(
        session: AsyncSession,
        student_id: str,
        parent_email: str,
    ) -> Dict[str, Any]:
        """
        Get all data stored about a child for parental review (COPPA requirement).

        Args:
            session: Database session
            student_id: Student ID
            parent_email: Parent email (for verification)

        Returns:
            Dictionary containing all student data

        Raises:
            ValueError: If student not found or email doesn't match
        """
        # Get student with all relationships
        result = await session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError(f"Student {student_id} not found")

        # Verify parent email matches
        if student.parent_email != parent_email:
            raise ValueError("Parent email does not match records")

        # Compile all data
        data = {
            "student_id": student.student_id,
            "name": student.name,
            "age": student.age,
            "grade_level": student.grade_level,
            "subjects_interested": student.subjects_interested,
            "is_under_13": student.is_under_13,
            "parent_consent_given": student.parent_consent_given,
            "parent_consent_date": student.parent_consent_date.isoformat() if student.parent_consent_date else None,
            "created_at": student.created_at.isoformat(),
            "updated_at": student.updated_at.isoformat(),
            "sessions_count": len(student.sessions) if hasattr(student, 'sessions') else 0,
            "feedback_count": len(student.feedback) if hasattr(student, 'feedback') else 0,
        }

        # Audit log
        await AuditService.log(
            session=session,
            action="coppa_parent_data_access",
            user_id=None,
            resource_type=AuditService.RESOURCE_STUDENT,
            resource_id=student_id,
            metadata={
                "parent_email": anonymization_service.anonymize_email(parent_email),
            }
        )

        return data

    @staticmethod
    async def delete_child_data(
        session: AsyncSession,
        student_id: str,
        parent_email: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Delete all data for a child at parent's request (COPPA "right to deletion").

        Note: This performs a soft delete by anonymizing data rather than
        hard deletion to maintain referential integrity for educational records.

        Args:
            session: Database session
            student_id: Student ID
            parent_email: Parent email (for verification)
            ip_address: IP address of the request

        Returns:
            True if deletion successful

        Raises:
            ValueError: If student not found or email doesn't match
        """
        # Get student
        result = await session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError(f"Student {student_id} not found")

        # Verify parent email matches
        if student.parent_email != parent_email:
            raise ValueError("Parent email does not match records")

        # Audit log before deletion
        await AuditService.log(
            session=session,
            action="coppa_child_data_deletion",
            user_id=None,
            resource_type=AuditService.RESOURCE_STUDENT,
            resource_id=student_id,
            ip_address=ip_address,
            metadata={
                "parent_email": anonymization_service.anonymize_email(parent_email),
                "deletion_type": "soft_delete_anonymization",
            }
        )

        # Anonymize student data (soft delete)
        student.name = f"Deleted_Student_{student.student_id[-6:]}"
        student.parent_email = None
        student.parent_consent_given = False
        student.parent_consent_date = None
        student.parent_consent_ip = None
        student.is_under_13 = False  # Remove COPPA protection flag after deletion
        # Keep minimal fields for referential integrity

        student.updated_at = datetime.utcnow()

        await session.commit()

        return True

    @staticmethod
    def generate_consent_token(student_id: str) -> str:
        """
        Generate a secure token for parental consent verification.

        Args:
            student_id: Student ID

        Returns:
            Secure random token (hex encoded)
        """
        # Generate cryptographically secure random token
        random_part = secrets.token_hex(32)

        # Include student_id in token for verification (hashed)
        student_hash = anonymization_service.hash_for_analytics(student_id)[:16]

        return f"{student_hash}_{random_part}"

    @staticmethod
    def validate_consent_token(token: str, student_id: str) -> bool:
        """
        Validate a parental consent token.

        Args:
            token: Token to validate
            student_id: Expected student ID

        Returns:
            True if token is valid for the student
        """
        try:
            parts = token.split('_')
            if len(parts) != 2:
                return False

            student_hash, random_part = parts

            # Verify student_id hash matches
            expected_hash = anonymization_service.hash_for_analytics(student_id)[:16]

            return student_hash == expected_hash
        except Exception:
            return False

    @staticmethod
    async def get_students_needing_consent(
        session: AsyncSession,
        limit: int = 100,
    ) -> List[Student]:
        """
        Get students under 13 who need parental consent.

        Args:
            session: Database session
            limit: Maximum number of students to return

        Returns:
            List of Student records needing consent
        """
        query = (
            select(Student)
            .where(
                and_(
                    Student.is_under_13 == True,
                    Student.parent_consent_given == False,
                )
            )
            .limit(limit)
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def anonymize_expired_consents(
        session: AsyncSession,
        expiry_days: int = 30,
    ) -> int:
        """
        Anonymize data for students whose consent requests expired without response.

        Args:
            session: Database session
            expiry_days: Days after which consent requests expire

        Returns:
            Number of students anonymized
        """
        cutoff_date = datetime.utcnow() - timedelta(days=expiry_days)

        # Find students under 13 without consent that were created before cutoff
        query = select(Student).where(
            and_(
                Student.is_under_13 == True,
                Student.parent_consent_given == False,
                Student.created_at < cutoff_date,
            )
        )

        result = await session.execute(query)
        students = result.scalars().all()

        count = 0
        for student in students:
            # Anonymize data
            student.name = f"Expired_Consent_{student.student_id[-6:]}"
            student.parent_email = None
            student.updated_at = datetime.utcnow()

            # Audit log
            await AuditService.log(
                session=session,
                action="coppa_consent_expired",
                resource_type=AuditService.RESOURCE_STUDENT,
                resource_id=student.student_id,
                metadata={
                    "expiry_days": expiry_days,
                    "created_at": student.created_at.isoformat(),
                }
            )

            count += 1

        await session.commit()

        return count


# Helper functions for easier usage

def verify_age(age: Optional[int]) -> bool:
    """Check if age requires COPPA protection."""
    return COPPAService.verify_age(age)


def requires_parental_consent(student: Student) -> bool:
    """Check if student requires parental consent."""
    return COPPAService.requires_parental_consent(student)


def can_collect_data(student: Student) -> bool:
    """Check if data collection is allowed for student."""
    return COPPAService.can_collect_data(student)


# Global service instance
coppa_service = COPPAService()
