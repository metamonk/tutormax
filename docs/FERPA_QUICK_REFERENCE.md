# FERPA Compliance Quick Reference

Quick reference guide for implementing FERPA compliance in TutorMax.

## Quick Setup

```python
from src.api.compliance import (
    FERPAService,
    FERPAAccessControl,
    FERPARecordType,
    FERPAAccessType,
    FERPADisclosureReason,
)
```

## Common Patterns

### 1. Verify Access to Student Records

```python
# Check if user can access student records
can_access, reason = await FERPAService.can_access_student_record(
    session=db,
    requesting_user_id=current_user.id,
    student_id="STU001",
    access_type=FERPAAccessType.SCHOOL_OFFICIAL,
)

if not can_access:
    raise HTTPException(status_code=403, detail=f"Access denied: {reason}")
```

### 2. Log FERPA Disclosure

```python
# Log every access to student records
await FERPAService.log_ferpa_disclosure(
    session=db,
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

### 3. Combined Verify + Log (Recommended)

```python
# Best practice: verify access and log in one call
try:
    await FERPAAccessControl.log_and_authorize_access(
        session=db,
        requesting_user_id=current_user.id,
        student_id="STU001",
        record_type=FERPARecordType.FEEDBACK,
        disclosure_reason=FERPADisclosureReason.SCHOOL_OFFICIAL,
        access_type=FERPAAccessType.SCHOOL_OFFICIAL,
        resource_type="feedback",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
except PermissionError as e:
    raise HTTPException(status_code=403, detail=str(e))
```

### 4. Check Retention Policy

```python
# Check if records should be retained
retention = await FERPAService.check_retention_policy(
    session=db,
    student_id="STU001"
)

if retention["eligible_for_deletion"]:
    # Records can be deleted or anonymized
    pass
```

### 5. Verify Parental Consent

```python
# Check parental consent for students under 13
consent = await FERPAService.verify_parental_consent(
    session=db,
    student_id="STU001"
)

if not consent["compliant"]:
    raise HTTPException(
        status_code=403,
        detail=f"Parental consent required: {consent['issues']}"
    )
```

### 6. Get All Educational Records

```python
# Retrieve comprehensive educational records
records = await FERPAService.get_student_educational_records(
    session=db,
    student_id="STU001",
    record_types=[
        FERPARecordType.ACADEMIC_PERFORMANCE,
        FERPARecordType.ATTENDANCE,
    ]  # Optional: filter by type
)
```

### 7. View Disclosure History

```python
# Get disclosure history (students/parents have right to inspect)
disclosures = await FERPAService.get_disclosure_history(
    session=db,
    student_id="STU001",
    days=90  # Last 90 days
)
```

## FastAPI Route Example

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from src.api.compliance import FERPAAccessControl, FERPARecordType, FERPADisclosureReason, FERPAAccessType

router = APIRouter()

@router.get("/students/{student_id}/sessions")
async def get_student_sessions(
    student_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify access and log disclosure
    try:
        await FERPAAccessControl.log_and_authorize_access(
            session=db,
            requesting_user_id=current_user.id,
            student_id=student_id,
            record_type=FERPARecordType.ACADEMIC_PERFORMANCE,
            disclosure_reason=FERPADisclosureReason.SCHOOL_OFFICIAL,
            access_type=FERPAAccessType.SCHOOL_OFFICIAL,
            resource_type="session",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Access granted - fetch data
    sessions = await get_sessions_for_student(db, student_id)
    return {"sessions": sessions}
```

## Access Control Rules

| User Type | Can Access | Requirements |
|-----------|-----------|--------------|
| Student (18+) | Own records | Authenticated |
| Student (<18) | Own records | Authenticated |
| Parent | Child's records | Email matches `parent_email` + consent given |
| Admin | All records | `UserRole.ADMIN` |
| Operations Manager | All records | `UserRole.OPERATIONS_MANAGER` |
| People Ops | All records | `UserRole.PEOPLE_OPS` |
| Assigned Tutor | Student's records | Has sessions with student |

## Record Types

| Type | Description | Examples |
|------|-------------|----------|
| `PERSONAL_IDENTIFICATION` | Student identity | Name, ID, contact info |
| `ACADEMIC_PERFORMANCE` | Performance data | Session scores, metrics |
| `ATTENDANCE` | Attendance records | Session attendance, no-shows |
| `FEEDBACK` | Student feedback | Ratings, evaluations |
| `PARENTAL_INFO` | Parent information | Parent email, consent |
| `PROGRESS` | Learning progress | Progress metrics |
| `TUTOR_ASSIGNMENTS` | Tutor relationships | Assigned tutors |
| `COMMUNICATION` | Communications | Notifications, messages |

## Disclosure Reasons

| Reason | Description | When to Use |
|--------|-------------|-------------|
| `STUDENT_REQUEST` | Student requested | Student accessing own data |
| `PARENT_REQUEST` | Parent requested | Parent accessing child's data |
| `SCHOOL_OFFICIAL` | Legitimate educational interest | Staff accessing for their job |
| `AUDIT_EVALUATION` | Audit purposes | Compliance audits |
| `HEALTH_SAFETY` | Emergency | Health/safety emergency |
| `WRITTEN_CONSENT` | With consent | Third-party with consent |

## Retention Policy

- **Retention Period**: 7 years from last educational activity
- **Audit Logs**: 7 years (same as records)
- **Eligible for Deletion**: After retention period met + no recent activity

```python
# Get retention schedule
schedule = FERPAService.get_retention_schedule()
# Returns complete retention policy details
```

## Verification

```bash
# Run compliance verification
python scripts/verify_ferpa_compliance.py

# Check specific student
python scripts/verify_ferpa_compliance.py --student-id STU001

# Check retention policies
python scripts/verify_ferpa_compliance.py --check-retention
```

## Compliance Checklist

- [ ] All student endpoints use `FERPAAccessControl.log_and_authorize_access()`
- [ ] Access verified BEFORE data retrieval
- [ ] All disclosures logged with complete metadata
- [ ] Parental consent checked for students under 13
- [ ] 7-year retention policy enforced
- [ ] Disclosure history available to students/parents
- [ ] Encryption enabled for PII fields
- [ ] Audit logs retained for 7 years

## Configuration

In `.env` or settings:

```bash
# FERPA compliance settings
PII_DATA_RETENTION_DAYS=2555        # 7 years
AUDIT_LOG_RETENTION_DAYS=2555       # 7 years
ENCRYPTION_ENABLED=true             # Encrypt PII
COPPA_COMPLIANCE_ENABLED=true       # Enable COPPA for under-13
```

## Common Issues

### Issue: Access Denied
```python
# Problem: User can't access student records
# Solution: Check user role and student relationship

can_access, reason = await FERPAService.can_access_student_record(...)
# reason will explain why access was denied
```

### Issue: Missing Parental Consent
```python
# Problem: Student under 13 missing consent
# Solution: Require parent to provide consent

consent = await FERPAService.verify_parental_consent(...)
if not consent["compliant"]:
    # Redirect to parental consent flow
```

### Issue: Retention Period Confusion
```python
# Problem: When can records be deleted?
# Solution: Check retention policy

retention = await FERPAService.check_retention_policy(...)
# eligible_for_deletion indicates if retention period met
```

## Related Documentation

- `docs/FERPA_COMPLIANCE.md` - Full FERPA compliance guide
- `docs/AUDIT_LOGGING_SYSTEM.md` - Audit logging details
- `docs/SECURITY_HARDENING.md` - Security measures
- `src/api/compliance/ferpa.py` - Source code with inline docs

## Support

For FERPA compliance questions:
1. Review inline documentation in `ferpa.py`
2. Check examples in `docs/FERPA_COMPLIANCE.md`
3. Run verification script for diagnostics
4. Consult legal counsel for specific compliance questions
