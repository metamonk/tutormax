# FERPA Compliance Guide for TutorMax

## Overview

This document provides a comprehensive guide to TutorMax's implementation of FERPA (Family Educational Rights and Privacy Act) compliance. FERPA is a federal law that protects the privacy of student education records and applies to all educational institutions that receive federal funding.

**Reference**: 20 U.S.C. § 1232g; 34 CFR Part 99

## Table of Contents

1. [FERPA Overview](#ferpa-overview)
2. [Implementation Architecture](#implementation-architecture)
3. [Record Types Covered](#record-types-covered)
4. [Access Control Policies](#access-control-policies)
5. [Data Retention Schedule](#data-retention-schedule)
6. [Usage Examples](#usage-examples)
7. [Compliance Checklist](#compliance-checklist)
8. [Integration with COPPA](#integration-with-coppa)
9. [API Reference](#api-reference)

---

## FERPA Overview

### What is FERPA?

The Family Educational Rights and Privacy Act (FERPA) is a federal law that:
- Protects the privacy of student education records
- Gives parents certain rights with respect to their children's education records
- Transfers these rights to the student when they turn 18 or attend a postsecondary institution
- Applies to all educational agencies and institutions that receive federal funding

### Key FERPA Principles

1. **Educational Records**: Any records directly related to a student and maintained by an educational institution
2. **Consent for Disclosure**: Written consent required before disclosing personally identifiable information
3. **Parental Rights**: Parents have right to inspect and review education records (for students under 18)
4. **Student Rights**: Rights transfer to students at age 18 or upon attending postsecondary education
5. **Exceptions**: Certain parties can access records without consent (school officials with legitimate educational interest)
6. **Record of Disclosures**: Must maintain record of all disclosures

---

## Implementation Architecture

### Module Structure

```
src/api/compliance/
├── __init__.py           # Compliance module exports
├── ferpa.py             # FERPA implementation (NEW)
├── coppa.py             # COPPA implementation (existing)
└── gdpr.py              # GDPR implementation (existing)
```

### Core Components

#### 1. FERPAService
Main service class providing FERPA compliance utilities:
- Access control verification
- Disclosure logging
- Retention policy checking
- Educational records retrieval
- Parental consent verification

#### 2. FERPAAccessControl
Helper class for enforcing access policies:
- Route-level access requirements
- Combined authorization and logging

#### 3. Enumerations
Type-safe classifications:
- `FERPARecordType`: Educational record classifications
- `FERPAAccessType`: Types of authorized access
- `FERPADisclosureReason`: Valid reasons for disclosure

### Integration Points

```python
from src.api.compliance import (
    FERPAService,
    FERPAAccessControl,
    FERPARecordType,
    FERPAAccessType,
    FERPADisclosureReason,
)
from src.api.audit_service import AuditService
from src.api.security import encryption_service, anonymization_service
```

---

## Record Types Covered

### Educational Records Classification

TutorMax implements the following FERPA record types:

#### 1. Personal Identification (`PERSONAL_IDENTIFICATION`)
- Student name
- Student ID
- Contact information
- Age and grade level
- Subjects of interest
- **Storage**: Encrypted in database
- **Access**: Student, parents (if minor), authorized school officials

#### 2. Academic Performance (`ACADEMIC_PERFORMANCE`)
- Session attendance data
- Learning outcomes
- Engagement scores
- Objectives met status
- Performance metrics
- **Storage**: Database with audit logging
- **Access**: Student, parents (if minor), assigned tutors, authorized officials

#### 3. Attendance Records (`ATTENDANCE`)
- Session attendance
- No-show incidents
- Late arrivals
- Attendance rates
- **Storage**: Database with audit logging
- **Access**: Student, parents (if minor), assigned tutors, authorized officials

#### 4. Student Feedback (`FEEDBACK`)
- Session ratings
- Tutor evaluations
- Improvement areas
- Free-text feedback
- **Storage**: Database with audit logging
- **Access**: Student, parents (if minor), assigned tutors (aggregated), authorized officials

#### 5. Progress Records (`PROGRESS`)
- Learning progress tracking
- Performance trends
- Developmental milestones
- **Storage**: Derived from performance metrics
- **Access**: Student, parents (if minor), assigned tutors, authorized officials

#### 6. Parental Information (`PARENTAL_INFO`)
- Parent/guardian email
- Parental consent records
- COPPA consent (for under-13)
- **Storage**: Encrypted in database
- **Access**: Student (if 18+), parents, authorized officials

#### 7. Tutor Assignments (`TUTOR_ASSIGNMENTS`)
- Tutor-student relationships
- Session assignments
- Subject assignments
- **Storage**: Database
- **Access**: Student, parents (if minor), assigned tutors, authorized officials

#### 8. Communication Records (`COMMUNICATION`)
- Notifications sent to student
- System messages
- Feedback requests
- **Storage**: Database with retention policy
- **Access**: Student, parents (if minor), authorized officials

### Non-Educational Records (Not Covered by FERPA)

The following are **NOT** considered educational records under FERPA:
- Sole possession notes (personal notes of instructors)
- Law enforcement records
- Employment records
- Medical treatment records (if separate from educational records)
- Post-attendance records (alumni records)

---

## Access Control Policies

### Who Can Access Student Records?

#### 1. The Student
- **Age 18+**: Full access to own records
- **Under 18**: Access to own records (TutorMax grants access to all students)
- **Rights**: Inspect, review, request amendments

#### 2. Parents/Guardians
- **Eligibility**: Parents of students under 18
- **Verification**: Email must match `parent_email` in student record
- **Requirements**: Parental consent must be documented (`parent_consent_given = true`)
- **Rights**: Same as student (inspect, review, request amendments)

#### 3. School Officials
Authorized personnel with legitimate educational interest:
- **Admin** (`UserRole.ADMIN`): Full access to all records
- **Operations Manager** (`UserRole.OPERATIONS_MANAGER`): Access for management purposes
- **People Ops** (`UserRole.PEOPLE_OPS`): Access for HR and compliance purposes

#### 4. Assigned Tutors
- **Eligibility**: Tutors with active sessions with the student
- **Access Level**: Academic performance, attendance, feedback (aggregated)
- **Restrictions**: Limited to students they are actively tutoring

#### 5. Other Authorized Parties
With written consent or under specific exceptions:
- Court orders or lawfully issued subpoenas
- Health and safety emergencies
- Audit or evaluation purposes
- Financial aid determinations

### Access Verification Flow

```python
# Check if user can access student record
can_access, reason = await FERPAService.can_access_student_record(
    session=db_session,
    requesting_user_id=current_user.id,
    student_id="STU001",
    access_type=FERPAAccessType.SCHOOL_OFFICIAL
)

if not can_access:
    raise HTTPException(status_code=403, detail=f"Access denied: {reason}")
```

### Disclosure Logging

Every access to student records MUST be logged:

```python
# Log FERPA disclosure
await FERPAService.log_ferpa_disclosure(
    session=db_session,
    user_id=current_user.id,
    student_id="STU001",
    record_type=FERPARecordType.ACADEMIC_PERFORMANCE,
    disclosure_reason=FERPADisclosureReason.SCHOOL_OFFICIAL,
    access_type=FERPAAccessType.SCHOOL_OFFICIAL,
    resource_type="session",
    resource_id="SESS123",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
)
```

---

## Data Retention Schedule

### Retention Policy

**Standard Retention Period**: **7 Years**

FERPA does not mandate a specific retention period, but 7 years is the industry standard for educational records to ensure:
- Legal protection against claims
- Compliance with state regulations
- Historical record availability
- Adequate time for student/parent review

### Retention Rules

1. **Retention Start Date**: Date of last educational activity
2. **Active Students**: Records retained indefinitely while student is active
3. **Inactive Students**: 7-year retention from last session date
4. **Audit Logs**: Retained for same period as underlying records (7 years)

### Implementation

```python
# Check retention status for a student
retention_status = await FERPAService.check_retention_policy(
    session=db_session,
    student_id="STU001"
)

# Returns:
{
    "student_id": "STU001",
    "exists": true,
    "created_at": "2020-01-15T10:00:00Z",
    "record_age_days": 1825,
    "last_activity_date": "2024-11-01T14:30:00Z",
    "retention_period_days": 2555,
    "retention_deadline": "2031-11-01T14:30:00Z",
    "days_until_eligible_deletion": 2555,
    "eligible_for_deletion": false,
    "should_retain": true
}
```

### Retention Schedule by Record Type

| Record Type | Retention Period | Notes |
|-------------|------------------|-------|
| Personal Identification | 7 years | From last activity |
| Academic Performance | 7 years | From last session |
| Attendance | 7 years | From last session |
| Feedback | 7 years | From submission date |
| Parental Info | 7 years | Until student turns 18, then review |
| Progress Records | 7 years | From last update |
| Audit Logs (FERPA) | 7 years | Same as records |

### Data Lifecycle

```
┌─────────────────┐
│ Student Active  │ ──► Records Maintained
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Last Session    │ ──► Start Retention Clock
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ 7-Year Period   │ ──► Records Retained
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Retention Met   │ ──► Eligible for Deletion/Anonymization
└─────────────────┘
```

---

## Usage Examples

### Example 1: Verify Access Before Serving Data

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.compliance import FERPAService, FERPAAccessType
from src.database.database import get_db
from src.api.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/students/{student_id}/sessions")
async def get_student_sessions(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get sessions for a student with FERPA access control."""

    # Verify FERPA access
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

    # Log the disclosure
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

    # Retrieve and return data
    # ... (query sessions)

    return {"sessions": sessions}
```

### Example 2: Combined Authorization and Logging

```python
from src.api.compliance import FERPAAccessControl, FERPARecordType, FERPADisclosureReason

@router.get("/students/{student_id}/feedback")
async def get_student_feedback(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get feedback for a student with automatic FERPA compliance."""

    # This method verifies access AND logs disclosure in one call
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

    # Access granted, retrieve data
    # ... (query feedback)

    return {"feedback": feedback_items}
```

### Example 3: Retrieve All Educational Records

```python
@router.get("/students/{student_id}/records")
async def get_educational_records(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all educational records for a student."""

    # Verify access
    await FERPAAccessControl.require_student_access(
        session=db,
        requesting_user_id=current_user.id,
        student_id=student_id,
        access_type=FERPAAccessType.STUDENT,
    )

    # Retrieve comprehensive records
    records = await FERPAService.get_student_educational_records(
        session=db,
        student_id=student_id,
    )

    return records
```

### Example 4: Check Parental Consent (COPPA Integration)

```python
@router.post("/students/{student_id}/collect-data")
async def collect_student_data(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Collect data from student with COPPA/FERPA compliance."""

    # Verify parental consent for students under 13
    consent_status = await FERPAService.verify_parental_consent(
        session=db,
        student_id=student_id,
    )

    if not consent_status["compliant"]:
        raise HTTPException(
            status_code=403,
            detail=f"Cannot collect data: {consent_status['issues']}"
        )

    # Proceed with data collection
    # ...

    return {"status": "success"}
```

### Example 5: View Disclosure History

```python
@router.get("/students/{student_id}/disclosure-history")
async def get_disclosure_history(
    student_id: str,
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get FERPA disclosure history for a student.

    Students and parents have right to inspect disclosure records.
    """

    # Verify access
    await FERPAAccessControl.require_student_access(
        session=db,
        requesting_user_id=current_user.id,
        student_id=student_id,
        access_type=FERPAAccessType.STUDENT,
    )

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
    }
```

### Example 6: Get Retention Schedule

```python
@router.get("/compliance/ferpa/retention-schedule")
async def get_retention_schedule():
    """Get FERPA data retention schedule."""

    schedule = FERPAService.get_retention_schedule()

    return schedule
```

---

## Compliance Checklist

Use this checklist to ensure full FERPA compliance:

### Access Control
- [ ] All student record endpoints verify access using `FERPAService.can_access_student_record()`
- [ ] Access is verified BEFORE data is retrieved or displayed
- [ ] Appropriate `FERPAAccessType` is specified for each access request
- [ ] Permission errors return 403 status with clear denial reason

### Disclosure Logging
- [ ] All student record accesses are logged using `FERPAService.log_ferpa_disclosure()`
- [ ] Disclosure logs include complete metadata (user, IP, reason, record type)
- [ ] Audit logs are retained for 7 years minimum
- [ ] Disclosure history is available to students and parents

### Parental Rights
- [ ] Parents can access records for students under 18
- [ ] Parent email is verified against `student.parent_email`
- [ ] Parental consent is checked for COPPA-protected students (under 13)
- [ ] Rights transfer to students at age 18 is implemented

### Data Retention
- [ ] 7-year retention policy is enforced
- [ ] Retention is calculated from last educational activity
- [ ] Retention status can be checked using `check_retention_policy()`
- [ ] Records are not deleted prematurely

### Educational Records
- [ ] All record types are properly classified using `FERPARecordType`
- [ ] Personal identification is encrypted at rest
- [ ] Academic performance data is accessible to authorized parties
- [ ] Feedback is available to students and authorized officials

### Integration Points
- [ ] COPPA compliance integrated (parental consent for under-13)
- [ ] Encryption service used for PII fields
- [ ] Audit service used for all disclosures
- [ ] Anonymization available for research purposes

### API Security
- [ ] Authentication required for all student record endpoints
- [ ] Authorization verified using FERPA access control
- [ ] Rate limiting applied to prevent abuse
- [ ] HTTPS enforced for all data transmission

### Documentation
- [ ] FERPA compliance documented in API documentation
- [ ] Privacy policy mentions FERPA protections
- [ ] User documentation explains student/parent rights
- [ ] Staff training materials include FERPA requirements

---

## Integration with COPPA

FERPA and COPPA (Children's Online Privacy Protection Act) have overlapping requirements for students under 13. TutorMax integrates both frameworks:

### Overlapping Requirements

| Requirement | FERPA | COPPA |
|-------------|-------|-------|
| Parental consent for under-13 | ✓ (for disclosure) | ✓ (for collection) |
| Parental access to records | ✓ | ✓ |
| Data privacy protections | ✓ | ✓ |
| Disclosure logging | ✓ | - |
| Data retention | ✓ (7 years) | - |

### Unified Approach

```python
# TutorMax checks both FERPA and COPPA requirements

# 1. Check parental consent (COPPA + FERPA)
consent_status = await FERPAService.verify_parental_consent(
    session=db,
    student_id=student_id,
)

# 2. Verify access rights (FERPA)
can_access, reason = await FERPAService.can_access_student_record(
    session=db,
    requesting_user_id=current_user.id,
    student_id=student_id,
)

# 3. Log disclosure (FERPA)
await FERPAService.log_ferpa_disclosure(
    session=db,
    user_id=current_user.id,
    student_id=student_id,
    record_type=FERPARecordType.PERSONAL_IDENTIFICATION,
    disclosure_reason=FERPADisclosureReason.PARENT_REQUEST,
    access_type=FERPAAccessType.PARENT,
    resource_type="student",
)
```

---

## API Reference

### FERPAService Class

#### Methods

##### `can_access_student_record()`
Determine if a user can access student records.

**Parameters**:
- `session` (AsyncSession): Database session
- `requesting_user_id` (int): User requesting access
- `student_id` (str): Student whose records are requested
- `access_type` (Optional[FERPAAccessType]): Type of access

**Returns**: `tuple[bool, Optional[str]]` - (can_access, denial_reason)

##### `log_ferpa_disclosure()`
Log a FERPA-compliant disclosure.

**Parameters**:
- `session` (AsyncSession): Database session
- `user_id` (int): User accessing records
- `student_id` (str): Student whose records are accessed
- `record_type` (FERPARecordType): Type of educational record
- `disclosure_reason` (FERPADisclosureReason): Reason for disclosure
- `access_type` (FERPAAccessType): Type of access
- `resource_type` (str): Resource type (e.g., "session")
- `resource_id` (Optional[str]): Specific resource ID
- `ip_address` (Optional[str]): IP address
- `user_agent` (Optional[str]): User agent string
- `additional_metadata` (Optional[Dict]): Additional context

**Returns**: `AuditLog` - Created audit log entry

##### `check_retention_policy()`
Check if student records meet retention requirements.

**Parameters**:
- `session` (AsyncSession): Database session
- `student_id` (str): Student ID

**Returns**: `Dict[str, Any]` - Retention status information

##### `get_student_educational_records()`
Retrieve all educational records for a student.

**Parameters**:
- `session` (AsyncSession): Database session
- `student_id` (str): Student ID
- `record_types` (Optional[List[FERPARecordType]]): Filter by record types

**Returns**: `Dict[str, Any]` - All educational records organized by type

##### `verify_parental_consent()`
Verify parental consent for students under 13.

**Parameters**:
- `session` (AsyncSession): Database session
- `student_id` (str): Student ID

**Returns**: `Dict[str, Any]` - Consent verification status

##### `get_disclosure_history()`
Get FERPA disclosure history for a student.

**Parameters**:
- `session` (AsyncSession): Database session
- `student_id` (str): Student ID
- `days` (int): Number of days of history (default: 90)

**Returns**: `List[Dict[str, Any]]` - List of disclosure records

##### `get_retention_schedule()` (static)
Get the data retention schedule.

**Returns**: `Dict[str, Any]` - Complete retention schedule

### FERPAAccessControl Class

#### Methods

##### `require_student_access()`
Require access, raising exception if denied.

**Parameters**:
- `session` (AsyncSession): Database session
- `requesting_user_id` (int): User requesting access
- `student_id` (str): Student ID
- `access_type` (FERPAAccessType): Type of access

**Raises**: `PermissionError` if access denied

##### `log_and_authorize_access()`
Verify access AND log disclosure in one operation.

**Parameters**: Same as `log_ferpa_disclosure()` plus verification

**Returns**: `AuditLog` - Created audit log entry

**Raises**: `PermissionError` if access denied

### Enumerations

#### FERPARecordType
- `ENROLLMENT`: Student registration
- `ACADEMIC_PERFORMANCE`: Grades, session data
- `ATTENDANCE`: Session attendance
- `FEEDBACK`: Student feedback
- `BEHAVIORAL`: Disciplinary records
- `PROGRESS`: Learning progress
- `PERSONAL_IDENTIFICATION`: Name, ID, contact
- `PARENTAL_INFO`: Parent information
- `TUTOR_ASSIGNMENTS`: Tutor-student relationships
- `COMMUNICATION`: Messages, notifications
- `DIRECTORY_INFO`: Directory information

#### FERPAAccessType
- `SCHOOL_OFFICIAL`: Legitimate educational interest
- `STUDENT`: Student accessing own records
- `PARENT`: Parent/guardian of minor
- `AUTHORIZED_THIRD_PARTY`: With written consent
- `COURT_ORDER`: Court order or subpoena
- `HEALTH_SAFETY_EMERGENCY`: Emergency situations
- `AUDIT_EVALUATION`: Audit purposes

#### FERPADisclosureReason
- `STUDENT_REQUEST`: Student requested
- `PARENT_REQUEST`: Parent requested
- `SCHOOL_OFFICIAL`: School official access
- `AUDIT_EVALUATION`: Audit or evaluation
- `FINANCIAL_AID`: Financial aid determination
- `ACCREDITATION`: Accreditation purposes
- `COMPLIANCE_LEGAL`: Legal compliance
- `HEALTH_SAFETY`: Health/safety emergency
- `WRITTEN_CONSENT`: Written consent provided
- `DIRECTORY_INFORMATION`: Directory info disclosure

---

## Additional Resources

### Legal References
- FERPA Statute: 20 U.S.C. § 1232g
- FERPA Regulations: 34 CFR Part 99
- Department of Education FERPA Guidance: https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html

### Related Documentation
- `docs/AUDIT_LOGGING_SYSTEM.md` - Audit logging implementation
- `docs/SECURITY_HARDENING.md` - Security measures
- `COPPA_COMPLIANCE.md` - COPPA implementation (if exists)
- `GDPR_COMPLIANCE.md` - GDPR implementation (if exists)

### Support
For questions about FERPA compliance in TutorMax:
1. Review this documentation
2. Check the inline code documentation in `src/api/compliance/ferpa.py`
3. Consult legal counsel for specific compliance questions

---

**Document Version**: 1.0
**Last Updated**: November 2024
**Maintained By**: TutorMax Security & Compliance Team
