"""
FERPA Compliance - Example Usage

This file demonstrates how to use the FERPA compliance module in TutorMax routes.
It shows best practices for access control, disclosure logging, and compliance.

DO NOT run this file directly - it's meant to be reference documentation.
Copy the patterns into your actual route implementations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

# Import FERPA compliance components
from src.api.compliance import (
    FERPAService,
    FERPAAccessControl,
    FERPARecordType,
    FERPAAccessType,
    FERPADisclosureReason,
)

# Import dependencies (these are examples - adjust to your actual dependencies)
from src.database.database import get_db
from src.api.auth.dependencies import get_current_user
from src.database.models import User


# Create router
router = APIRouter(prefix="/api/students", tags=["students"])


# ============================================================================
# EXAMPLE 1: Basic Access Control with Manual Verification
# ============================================================================

@router.get("/{student_id}/sessions")
async def get_student_sessions_basic(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get sessions for a student - BASIC PATTERN.

    This example shows manual access verification and logging.
    For production, use the combined pattern (Example 2) instead.
    """

    # Step 1: Verify access
    can_access, reason = await FERPAService.can_access_student_record(
        session=db,
        requesting_user_id=current_user.id,
        student_id=student_id,
        access_type=FERPAAccessType.SCHOOL_OFFICIAL,
    )

    if not can_access:
        raise HTTPException(
            status_code=403,
            detail=f"FERPA access denied: {reason}"
        )

    # Step 2: Log the disclosure
    await FERPAService.log_ferpa_disclosure(
        session=db,
        user_id=current_user.id,
        student_id=student_id,
        record_type=FERPARecordType.ACADEMIC_PERFORMANCE,
        disclosure_reason=FERPADisclosureReason.SCHOOL_OFFICIAL,
        access_type=FERPAAccessType.SCHOOL_OFFICIAL,
        resource_type="session",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    # Step 3: Retrieve and return data
    # ... (your actual data retrieval logic here)
    sessions = []  # Replace with actual query

    return {
        "student_id": student_id,
        "sessions": sessions,
        "compliance": {
            "ferpa_disclosure_logged": True,
            "access_type": FERPAAccessType.SCHOOL_OFFICIAL.value,
        }
    }


# ============================================================================
# EXAMPLE 2: Recommended Pattern - Combined Verify + Log
# ============================================================================

@router.get("/{student_id}/feedback")
async def get_student_feedback_recommended(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get feedback for a student - RECOMMENDED PATTERN.

    This uses FERPAAccessControl.log_and_authorize_access() which:
    1. Verifies access rights
    2. Logs FERPA disclosure
    3. Raises PermissionError if denied

    This is the best practice for production code.
    """

    # Single call verifies access AND logs disclosure
    try:
        await FERPAAccessControl.log_and_authorize_access(
            session=db,
            requesting_user_id=current_user.id,
            student_id=student_id,
            record_type=FERPARecordType.FEEDBACK,
            disclosure_reason=FERPADisclosureReason.SCHOOL_OFFICIAL,
            access_type=FERPAAccessType.SCHOOL_OFFICIAL,
            resource_type="feedback",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Access granted - retrieve data
    feedback = []  # Replace with actual query

    return {
        "student_id": student_id,
        "feedback": feedback,
    }


# ============================================================================
# EXAMPLE 3: Student Accessing Own Records
# ============================================================================

@router.get("/me/records")
async def get_my_educational_records(
    request: Request,
    record_types: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Student accesses their own educational records.

    FERPA gives students the right to inspect and review their own records.
    """

    # Verify student has a student_id
    if not current_user.student_id:
        raise HTTPException(
            status_code=400,
            detail="User is not a student"
        )

    # Log the disclosure
    try:
        await FERPAAccessControl.log_and_authorize_access(
            session=db,
            requesting_user_id=current_user.id,
            student_id=current_user.student_id,
            record_type=FERPARecordType.ACADEMIC_PERFORMANCE,
            disclosure_reason=FERPADisclosureReason.STUDENT_REQUEST,
            access_type=FERPAAccessType.STUDENT,
            resource_type="educational_records",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Parse record types filter
    ferpa_record_types = None
    if record_types:
        ferpa_record_types = [
            FERPARecordType(rt) for rt in record_types
        ]

    # Retrieve all educational records
    records = await FERPAService.get_student_educational_records(
        session=db,
        student_id=current_user.student_id,
        record_types=ferpa_record_types,
    )

    return records


# ============================================================================
# EXAMPLE 4: Parental Access to Child Records
# ============================================================================

@router.get("/{student_id}/parent-view")
async def parent_access_child_records(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Parent accesses their child's educational records.

    FERPA gives parents rights to access records for students under 18.
    TutorMax verifies:
    1. Student is under 18
    2. User's email matches parent_email
    3. Parental consent is documented
    """

    try:
        await FERPAAccessControl.log_and_authorize_access(
            session=db,
            requesting_user_id=current_user.id,
            student_id=student_id,
            record_type=FERPARecordType.ACADEMIC_PERFORMANCE,
            disclosure_reason=FERPADisclosureReason.PARENT_REQUEST,
            access_type=FERPAAccessType.PARENT,
            resource_type="educational_records",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=f"Parental access denied: {str(e)}"
        )

    # Verify parental consent (for students under 13)
    consent_status = await FERPAService.verify_parental_consent(
        session=db,
        student_id=student_id,
    )

    if not consent_status["compliant"]:
        raise HTTPException(
            status_code=403,
            detail=f"Parental consent issues: {consent_status['issues']}"
        )

    # Retrieve records
    records = await FERPAService.get_student_educational_records(
        session=db,
        student_id=student_id,
    )

    return {
        **records,
        "parental_access": True,
        "consent_status": consent_status,
    }


# ============================================================================
# EXAMPLE 5: View Disclosure History
# ============================================================================

@router.get("/{student_id}/disclosure-history")
async def get_disclosure_history(
    student_id: str,
    request: Request,
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    View FERPA disclosure history for a student.

    Students and parents have the right to inspect records of disclosures.
    """

    # Verify access (student or parent can view disclosure history)
    try:
        await FERPAAccessControl.log_and_authorize_access(
            session=db,
            requesting_user_id=current_user.id,
            student_id=student_id,
            record_type=FERPARecordType.PERSONAL_IDENTIFICATION,
            disclosure_reason=FERPADisclosureReason.STUDENT_REQUEST,
            access_type=FERPAAccessType.STUDENT,
            resource_type="disclosure_history",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Get disclosure history
    disclosures = await FERPAService.get_disclosure_history(
        session=db,
        student_id=student_id,
        days=days,
    )

    return {
        "student_id": student_id,
        "period_days": days,
        "disclosure_count": len(disclosures),
        "disclosures": disclosures,
        "note": "This is a record of who has accessed your educational records"
    }


# ============================================================================
# EXAMPLE 6: Check Data Retention Policy
# ============================================================================

@router.get("/{student_id}/retention-status")
async def check_retention_status(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check data retention status for a student.

    Shows when records can be deleted according to FERPA 7-year retention.
    """

    # Verify access (admin only for this endpoint)
    try:
        await FERPAAccessControl.log_and_authorize_access(
            session=db,
            requesting_user_id=current_user.id,
            student_id=student_id,
            record_type=FERPARecordType.PERSONAL_IDENTIFICATION,
            disclosure_reason=FERPADisclosureReason.AUDIT_EVALUATION,
            access_type=FERPAAccessType.SCHOOL_OFFICIAL,
            resource_type="retention_status",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Check retention policy
    retention = await FERPAService.check_retention_policy(
        session=db,
        student_id=student_id,
    )

    return retention


# ============================================================================
# EXAMPLE 7: Get Retention Schedule
# ============================================================================

@router.get("/compliance/retention-schedule")
async def get_retention_schedule(
    current_user: User = Depends(get_current_user),
):
    """
    Get FERPA data retention schedule.

    Public information about how long records are retained.
    """

    schedule = FERPAService.get_retention_schedule()

    return schedule


# ============================================================================
# EXAMPLE 8: Tutor Accessing Student Records
# ============================================================================

@router.get("/{student_id}/tutor-view")
async def tutor_view_student(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tutor accesses records for assigned student.

    FERPA allows school officials (including tutors) with legitimate
    educational interest to access student records.
    """

    # Verify tutor has sessions with this student
    try:
        await FERPAAccessControl.log_and_authorize_access(
            session=db,
            requesting_user_id=current_user.id,
            student_id=student_id,
            record_type=FERPARecordType.ACADEMIC_PERFORMANCE,
            disclosure_reason=FERPADisclosureReason.SCHOOL_OFFICIAL,
            access_type=FERPAAccessType.SCHOOL_OFFICIAL,
            resource_type="student_overview",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=f"Tutor access denied. You may not have sessions with this student. {str(e)}"
        )

    # Retrieve relevant data for tutoring
    records = await FERPAService.get_student_educational_records(
        session=db,
        student_id=student_id,
        record_types=[
            FERPARecordType.ACADEMIC_PERFORMANCE,
            FERPARecordType.ATTENDANCE,
            FERPARecordType.PROGRESS,
        ]
    )

    return {
        "student_id": student_id,
        "tutor_view": True,
        "records": records["records"],
        "note": "Limited to records relevant for tutoring"
    }


# ============================================================================
# EXAMPLE 9: Verify Parental Consent (COPPA Integration)
# ============================================================================

@router.get("/{student_id}/consent-status")
async def check_parental_consent(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check parental consent status for student.

    Required for students under 13 (COPPA compliance).
    """

    # Verify access
    try:
        await FERPAAccessControl.log_and_authorize_access(
            session=db,
            requesting_user_id=current_user.id,
            student_id=student_id,
            record_type=FERPARecordType.PARENTAL_INFO,
            disclosure_reason=FERPADisclosureReason.SCHOOL_OFFICIAL,
            access_type=FERPAAccessType.SCHOOL_OFFICIAL,
            resource_type="consent_status",
            ip_address="127.0.0.1",
            user_agent="Internal",
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Check consent
    consent = await FERPAService.verify_parental_consent(
        session=db,
        student_id=student_id,
    )

    return consent


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def check_ferpa_access_before_operation(
    db: AsyncSession,
    current_user: User,
    student_id: str,
    operation: str,
) -> bool:
    """
    Helper function to check FERPA access before performing an operation.

    Returns True if access granted, raises HTTPException if denied.
    """
    can_access, reason = await FERPAService.can_access_student_record(
        session=db,
        requesting_user_id=current_user.id,
        student_id=student_id,
        access_type=FERPAAccessType.SCHOOL_OFFICIAL,
    )

    if not can_access:
        raise HTTPException(
            status_code=403,
            detail=f"FERPA: Cannot {operation} - {reason}"
        )

    return True


# ============================================================================
# NOTES FOR PRODUCTION USE
# ============================================================================

"""
IMPORTANT NOTES FOR PRODUCTION:

1. Always use FERPAAccessControl.log_and_authorize_access() in production
   - It combines verification and logging in one atomic operation
   - Ensures disclosures are always logged when access is granted

2. Choose the correct FERPAAccessType:
   - STUDENT: Student accessing own records
   - PARENT: Parent accessing child's records (under 18)
   - SCHOOL_OFFICIAL: Staff, tutors, admins with legitimate interest
   - Other types for special cases (court orders, emergencies, etc.)

3. Choose the correct FERPADisclosureReason:
   - STUDENT_REQUEST: Student requested
   - PARENT_REQUEST: Parent requested
   - SCHOOL_OFFICIAL: Staff accessing for their job
   - Match reason to access type for compliance

4. Always include request metadata:
   - ip_address: request.client.host
   - user_agent: request.headers.get("user-agent")
   - Needed for complete audit trail

5. Handle errors appropriately:
   - 403 for access denied (with clear reason)
   - 400 for invalid student IDs
   - 500 for system errors

6. For students under 13:
   - Always verify parental consent
   - Check COPPA compliance
   - Use FERPAService.verify_parental_consent()

7. Retention:
   - Records retained 7 years from last activity
   - Don't delete records prematurely
   - Use check_retention_policy() before deletion

8. Disclosure History:
   - Must be available to students and parents
   - Shows who accessed what and when
   - Part of FERPA compliance requirements

9. Testing:
   - Test all access control scenarios
   - Verify disclosure logging
   - Check parental access
   - Test unauthorized access attempts

10. Documentation:
    - Document FERPA requirements in API docs
    - Include access denial reasons
    - Explain parental rights
    - Reference retention policies
"""
