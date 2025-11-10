# COPPA Compliance Quick Start Guide

## Overview

Quick reference for implementing COPPA compliance in TutorMax. For detailed documentation, see [COPPA_COMPLIANCE.md](./COPPA_COMPLIANCE.md).

---

## Setup (One-Time)

### 1. Enable COPPA Compliance

In `.env`:
```bash
COPPA_COMPLIANCE_ENABLED=true
```

### 2. Configure Email (Required for Consent Workflow)

In `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@tutormax.com
SMTP_FROM_NAME=TutorMax
```

### 3. Include COPPA Router in Main App

In `src/api/main.py`:
```python
from .coppa_router import router as coppa_router

app.include_router(coppa_router)
```

---

## Basic Usage

### Import Services

```python
from src.api.compliance import (
    COPPAService,
    verify_age,
    requires_parental_consent,
    can_collect_data,
)
```

### Check if Student is Under 13

```python
# Method 1: Check age directly
age = 12
is_protected = verify_age(age)  # Returns True

# Method 2: Check student record
from src.database.models import Student

student = await session.get(Student, student_id)
needs_consent = requires_parental_consent(student)  # Returns True/False
```

### Check if Data Collection is Allowed

```python
student = await session.get(Student, student_id)

if can_collect_data(student):
    # Can collect full data (student is 13+ OR has parental consent)
    collect_session_data(student)
    collect_feedback(student)
else:
    # Limited to minimal data only
    # Student is under 13 without parental consent
    collect_minimal_data_only(student)
```

---

## Common Workflows

### 1. Student Registration (Under 13)

```python
from src.api.compliance.coppa import COPPAService

# Mark student as under 13 and send consent email
student = await COPPAService.mark_student_as_under_13(
    session=session,
    student_id="STU-12345",
    parent_email="parent@example.com",
    user_id=None,  # System action
    ip_address="192.168.1.1",
)

# Email is automatically sent to parent with consent link
```

### 2. Grant Parental Consent

```python
# After parent clicks consent link in email
student = await COPPAService.grant_parental_consent(
    session=session,
    student_id="STU-12345",
    parent_email="parent@example.com",
    ip_address="192.168.1.1",
    consent_method="online_form",
)

# Now can_collect_data(student) returns True
```

### 3. Parent Requests Child's Data

```python
data = await COPPAService.get_child_data_for_parent(
    session=session,
    student_id="STU-12345",
    parent_email="parent@example.com",
)

# Returns all data stored about the child
# {
#   "student_id": "STU-12345",
#   "name": "John Doe",
#   "age": 12,
#   "sessions_count": 5,
#   ...
# }
```

### 4. Parent Deletes Child's Data

```python
success = await COPPAService.delete_child_data(
    session=session,
    student_id="STU-12345",
    parent_email="parent@example.com",
    ip_address="192.168.1.1",
)

# Data is anonymized (soft delete)
# Student record remains but PII is removed
```

### 5. Parent Revokes Consent

```python
student = await COPPAService.revoke_parental_consent(
    session=session,
    student_id="STU-12345",
    parent_email="parent@example.com",
    ip_address="192.168.1.1",
    delete_data=True,  # Also delete data
)

# Consent is revoked and data deleted
```

---

## API Endpoints

### Mark Student as Under 13
```bash
POST /api/coppa/mark-student-under-13
Content-Type: application/json

{
  "student_id": "STU-12345",
  "parent_email": "parent@example.com",
  "parent_name": "Jane Doe",
  "send_consent_email": true
}
```

### Grant or Deny Consent
```bash
POST /api/coppa/grant-consent
Content-Type: application/json

{
  "student_id": "STU-12345",
  "parent_email": "parent@example.com",
  "consent_token": "abc123...xyz789",
  "consent_given": true
}
```

### Get COPPA Status
```bash
GET /api/coppa/status/STU-12345
```

Response:
```json
{
  "student_id": "STU-12345",
  "is_under_13": true,
  "requires_parental_consent": true,
  "parent_consent_given": true,
  "parent_consent_date": "2025-11-09T10:30:00Z",
  "can_collect_data": true
}
```

### Access Child Data (Parent)
```bash
POST /api/coppa/parent-data-access
Content-Type: application/json

{
  "student_id": "STU-12345",
  "parent_email": "parent@example.com",
  "verification_code": "verify-123"
}
```

### Delete Child Data (Parent)
```bash
POST /api/coppa/delete-child-data
Content-Type: application/json

{
  "student_id": "STU-12345",
  "parent_email": "parent@example.com",
  "verification_code": "verify-123",
  "confirm_deletion": true
}
```

---

## Student Model Fields

The `Student` model includes COPPA fields:

```python
class Student(Base):
    # ... existing fields ...

    # COPPA Compliance
    is_under_13: bool = False
    parent_email: Optional[str] = None
    parent_consent_given: bool = False
    parent_consent_date: Optional[datetime] = None
    parent_consent_ip: Optional[str] = None
```

**Note**: These fields already exist in your database schema. No migration needed.

---

## Data Minimization

### What Can Be Collected WITHOUT Parental Consent

For students under 13 **without** consent:
- Student ID (system necessity)
- Age (COPPA determination)
- Grade level (educational necessity)
- Subjects interested (educational necessity)
- Created/updated timestamps

### What REQUIRES Parental Consent

- Full name
- Contact information
- Session participation details
- Feedback and ratings
- Performance metrics
- Any other personally identifiable information

### Implementation Example

```python
from src.api.compliance import can_collect_data

student = await session.get(Student, student_id)

if can_collect_data(student):
    # Full data collection
    data = {
        "name": student.name,
        "email": student.email,
        "session_history": get_all_sessions(student),
        "feedback": get_all_feedback(student),
        "performance": get_performance_metrics(student),
    }
else:
    # Minimal data only
    data = {
        "student_id": student.student_id,
        "age": student.age,
        "grade_level": student.grade_level,
        "subjects": student.subjects_interested,
    }
```

---

## Maintenance Tasks

### Daily Monitoring

```python
# Get students needing consent
from src.api.compliance.coppa import COPPAService

students_needing_consent = await COPPAService.get_students_needing_consent(
    session=session,
    limit=100
)

print(f"Students waiting for consent: {len(students_needing_consent)}")
```

### Monthly Cleanup

```python
# Anonymize students with expired consent requests (30 days)
count = await COPPAService.anonymize_expired_consents(
    session=session,
    expiry_days=30
)

print(f"Anonymized {count} students with expired consents")
```

### Audit COPPA Actions

```python
from src.api.audit_service import AuditService
from datetime import datetime, timedelta

# Get all COPPA actions in last 30 days
logs, total = await AuditService.search_logs(
    session=session,
    start_date=datetime.utcnow() - timedelta(days=30),
    limit=1000
)

# Filter COPPA actions
coppa_logs = [log for log in logs if log.action.startswith('coppa_')]
print(f"COPPA actions in last 30 days: {len(coppa_logs)}")
```

---

## Integration with Existing Features

### With Encryption Service

```python
from src.api.security import encryption_service

# Parent emails are automatically encrypted in database
encrypted_email = encryption_service.encrypt_email("parent@example.com")
decrypted_email = encryption_service.decrypt_email(encrypted_email)
```

### With Anonymization Service

```python
from src.api.security import anonymization_service

# Check if student is COPPA protected
is_protected = anonymization_service.is_coppa_protected(student.age)

# Anonymize email for display/logs
anon_email = anonymization_service.anonymize_email("parent@example.com")
# Returns: "pa****@***.com"
```

### With Audit Service

All COPPA actions are automatically logged:
- `coppa_mark_under_13` - Student marked as under 13
- `coppa_consent_granted` - Parental consent granted
- `coppa_consent_revoked` - Consent revoked
- `coppa_parent_data_access` - Parent accessed child data
- `coppa_child_data_deletion` - Child data deleted
- `coppa_consent_expired` - Consent request expired

---

## Testing

### Quick Test Script

```python
import asyncio
from src.database.database import get_async_session
from src.api.compliance.coppa import COPPAService

async def test_coppa():
    async for session in get_async_session():
        # Mark student as under 13
        student = await COPPAService.mark_student_as_under_13(
            session=session,
            student_id="TEST-001",
            parent_email="test@example.com",
        )
        print(f"Student marked: {student.is_under_13}")

        # Grant consent
        student = await COPPAService.grant_parental_consent(
            session=session,
            student_id="TEST-001",
            parent_email="test@example.com",
        )
        print(f"Consent granted: {student.parent_consent_given}")

        # Get child data
        data = await COPPAService.get_child_data_for_parent(
            session=session,
            student_id="TEST-001",
            parent_email="test@example.com",
        )
        print(f"Child data: {data}")

        break

asyncio.run(test_coppa())
```

---

## Troubleshooting

### Email Not Sending

1. Check SMTP configuration in `.env`
2. Verify SMTP credentials
3. Check email service logs
4. Test with a simple email client

```python
from src.api.email_service import get_email_service_from_settings

email_service = get_email_service_from_settings()
if email_service:
    success = email_service._send_email(
        to_email="test@example.com",
        subject="Test Email",
        html_body="<p>Test</p>",
    )
    print(f"Email sent: {success}")
else:
    print("Email service not configured")
```

### Consent Token Invalid

- Tokens are student-specific (include student ID hash)
- Tokens don't expire (they're cryptographically secure)
- Verify you're using correct student_id with token

```python
from src.api.compliance.coppa import COPPAService

token = COPPAService.generate_consent_token("STU-12345")
is_valid = COPPAService.validate_consent_token(token, "STU-12345")  # True
is_valid = COPPAService.validate_consent_token(token, "WRONG-ID")   # False
```

### Parent Email Mismatch

- Parent email must exactly match what's stored in database
- Email comparison is case-sensitive
- Verify email in database: `student.parent_email`

---

## Quick Reference Card

| Task | Function | Import |
|------|----------|--------|
| Check age | `verify_age(age)` | `from src.api.compliance import verify_age` |
| Check consent needed | `requires_parental_consent(student)` | `from src.api.compliance import requires_parental_consent` |
| Check can collect data | `can_collect_data(student)` | `from src.api.compliance import can_collect_data` |
| Mark under 13 | `COPPAService.mark_student_as_under_13()` | `from src.api.compliance.coppa import COPPAService` |
| Grant consent | `COPPAService.grant_parental_consent()` | `from src.api.compliance.coppa import COPPAService` |
| Revoke consent | `COPPAService.revoke_parental_consent()` | `from src.api.compliance.coppa import COPPAService` |
| Get child data | `COPPAService.get_child_data_for_parent()` | `from src.api.compliance.coppa import COPPAService` |
| Delete child data | `COPPAService.delete_child_data()` | `from src.api.compliance.coppa import COPPAService` |

---

## Next Steps

1. **Enable COPPA** in `.env`
2. **Configure Email** for consent workflow
3. **Add Router** to main app
4. **Test Workflow** with test student
5. **Update Privacy Policy** with COPPA notice
6. **Train Staff** on COPPA requirements

For detailed documentation, see [COPPA_COMPLIANCE.md](./COPPA_COMPLIANCE.md).
