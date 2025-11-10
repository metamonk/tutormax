# COPPA Compliance Guide for TutorMax

## Table of Contents
1. [Overview](#overview)
2. [What is COPPA?](#what-is-coppa)
3. [Implementation Summary](#implementation-summary)
4. [Age Verification Process](#age-verification-process)
5. [Parental Consent Workflow](#parental-consent-workflow)
6. [Data Minimization for Under-13 Users](#data-minimization-for-under-13-users)
7. [Parental Rights and Access](#parental-rights-and-access)
8. [API Endpoints](#api-endpoints)
9. [Email Templates](#email-templates)
10. [Compliance Checklist](#compliance-checklist)
11. [Testing Guide](#testing-guide)

---

## Overview

TutorMax implements comprehensive COPPA (Children's Online Privacy Protection Act) compliance to protect the privacy of students under 13 years old. This guide covers the implementation, workflows, and best practices for maintaining COPPA compliance.

### Key Features
- Automatic age verification
- Parental consent workflow with email verification
- Minimal data collection for under-13 users without consent
- Parental access to child data
- COPPA-compliant data deletion
- Comprehensive audit logging

---

## What is COPPA?

The Children's Online Privacy Protection Act (COPPA) is a U.S. federal law that protects the privacy of children under 13. It requires operators of websites and online services to:

1. **Post a clear privacy policy** describing information practices for children's information
2. **Obtain verifiable parental consent** before collecting, using, or disclosing personal information from children
3. **Provide parents access** to their child's personal information
4. **Allow parents to revoke consent** and delete their child's information
5. **Maintain confidentiality, security, and integrity** of personal information collected from children

### What is "Personal Information" under COPPA?

COPPA defines personal information broadly, including:
- First and last name
- Home or physical address
- Online contact information (email, username)
- Phone number
- Social Security Number
- Persistent identifier (cookies, IP address)
- Photo, video, or audio file containing a child's image or voice
- Geolocation information
- Other information about the child or parent combined with any of the above

---

## Implementation Summary

### Files Created

1. **Core Service**: `/src/api/compliance/coppa.py`
   - `COPPAService` class with all compliance methods
   - Age verification helpers
   - Parental consent management
   - Data deletion functionality

2. **API Router**: `/src/api/coppa_router.py`
   - RESTful endpoints for COPPA workflows
   - Request/response models
   - Email integration

3. **Documentation**: `/docs/COPPA_COMPLIANCE.md` (this file)

### Integration with Existing Systems

COPPA implementation integrates with:
- **Database Models**: Uses existing `Student` model with COPPA fields
- **Encryption Service**: `src/api/security/encryption.py`
- **Anonymization Service**: `src/api/security/encryption.py`
- **Audit Service**: `src/api/audit_service.py`
- **Email Service**: `src/api/email_service.py`
- **Configuration**: `src/api/config.py` (uses `coppa_compliance_enabled`)

---

## Age Verification Process

### Workflow

```
┌─────────────────┐
│ Student Signs Up│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Enter Age     │
└────────┬────────┘
         │
         ▼
    Age < 13?
         │
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│Flag as  │ │Normal Account│
│Under 13 │ │  Creation    │
└────┬────┘ └──────────────┘
     │
     ▼
┌─────────────────┐
│Request Parent   │
│    Email        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Send Consent     │
│  Email to       │
│    Parent       │
└─────────────────┘
```

### Implementation

```python
from src.api.compliance import verify_age, requires_parental_consent

# Check if age requires COPPA protection
age = 12
is_coppa_protected = verify_age(age)  # Returns True

# Check if student requires parental consent
from src.database.models import Student

student = await session.get(Student, student_id)
needs_consent = requires_parental_consent(student)  # Returns True if under 13
```

### Student Model Fields

The `Student` model includes COPPA-specific fields:

```python
class Student(Base):
    # ... other fields ...

    # COPPA Compliance fields
    is_under_13: bool  # Flag for COPPA protection
    parent_email: str  # Parent/guardian email
    parent_consent_given: bool  # Whether consent granted
    parent_consent_date: datetime  # When consent was granted
    parent_consent_ip: str  # IP address of consent action
```

---

## Parental Consent Workflow

### Complete Workflow

```
┌──────────────────┐
│Student Marked as │
│    Under 13      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│Generate Consent  │
│     Token        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Send Email to   │
│   Parent with    │
│  Consent Link    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│Parent Clicks Link│
│  and Reviews     │
│  Information     │
└────────┬─────────┘
         │
         ▼
  Parent Decision
         │
    ┌────┴────┐
    │         │
 Grant      Deny
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Enable  │ │Anonymize &   │
│  Full   │ │Delete Student│
│Account  │ │    Data      │
└─────────┘ └──────────────┘
```

### Step 1: Mark Student as Under 13

**API Endpoint**: `POST /api/coppa/mark-student-under-13`

```python
import requests

response = requests.post(
    "http://localhost:8000/api/coppa/mark-student-under-13",
    json={
        "student_id": "STU-12345",
        "parent_email": "parent@example.com",
        "parent_name": "Jane Doe",
        "send_consent_email": True
    }
)

# Response
{
    "student_id": "STU-12345",
    "is_under_13": True,
    "requires_parental_consent": True,
    "parent_consent_given": False,
    "parent_consent_date": null,
    "can_collect_data": False
}
```

### Step 2: Parent Receives Email

The parent receives an email with:
- Explanation of COPPA requirements
- What data will be collected
- How data will be used
- Parent's rights under COPPA
- Two buttons: "I Give Consent" and "I Deny Consent"

### Step 3: Parent Grants or Denies Consent

**API Endpoint**: `POST /api/coppa/grant-consent`

```python
# Grant consent
response = requests.post(
    "http://localhost:8000/api/coppa/grant-consent",
    json={
        "student_id": "STU-12345",
        "parent_email": "parent@example.com",
        "consent_token": "abc123...xyz789",
        "consent_given": True
    }
)

# Response (consent granted)
{
    "student_id": "STU-12345",
    "is_under_13": True,
    "requires_parental_consent": True,
    "parent_consent_given": True,
    "parent_consent_date": "2025-11-09T10:30:00Z",
    "can_collect_data": True
}
```

### Consent Token Security

Consent tokens are cryptographically secure and include:
- Student ID hash (for verification)
- Random 32-byte token (prevents guessing)
- Format: `{student_hash}_{random_token}`

```python
from src.api.compliance.coppa import COPPAService

# Generate token
token = COPPAService.generate_consent_token("STU-12345")
# Returns: "a1b2c3d4e5f6g7h8_9i10j11k12l13m14n15o16p17q18r19s20t21u22v23w24x25y26z27"

# Validate token
is_valid = COPPAService.validate_consent_token(token, "STU-12345")
# Returns: True
```

### Consent Expiration

- Consent requests expire after **30 days** (configurable)
- Expired requests without response trigger data anonymization
- Automated cleanup via `anonymize_expired_consents()` method

```python
from src.api.compliance.coppa import COPPAService

# Anonymize students with expired consent requests
count = await COPPAService.anonymize_expired_consents(
    session=session,
    expiry_days=30
)
print(f"Anonymized {count} students with expired consent requests")
```

---

## Data Minimization for Under-13 Users

### Allowed Data Without Consent

For students under 13 **without** parental consent, we only collect:

```python
MINIMAL_DATA_FIELDS = {
    'student_id',      # Required for system operation
    'age',             # Required for COPPA determination
    'grade_level',     # Educational necessity
    'subjects_interested',  # Educational necessity
    'created_at',      # System metadata
    'updated_at',      # System metadata
}
```

### Restricted Data (Requires Consent)

These fields require parental consent:
- Student name (full name)
- Parent email (for consent only)
- Session participation details
- Feedback and ratings
- Performance metrics
- Any other personally identifiable information

### Implementation

```python
from src.api.compliance import can_collect_data

student = await session.get(Student, student_id)

if can_collect_data(student):
    # Full data collection allowed
    collect_session_feedback(student)
    collect_performance_metrics(student)
else:
    # Only minimal data - no PII
    # Sessions can occur but minimal logging
    log_minimal_session_data(student)
```

---

## Parental Rights and Access

### Right to Review Child's Data

**API Endpoint**: `POST /api/coppa/parent-data-access`

```python
response = requests.post(
    "http://localhost:8000/api/coppa/parent-data-access",
    json={
        "student_id": "STU-12345",
        "parent_email": "parent@example.com",
        "verification_code": "verify-code-123"
    }
)

# Response includes all stored data
{
    "student_id": "STU-12345",
    "name": "John Doe",
    "age": 12,
    "grade_level": "7th Grade",
    "subjects_interested": ["Math", "Science"],
    "is_under_13": True,
    "parent_consent_given": True,
    "parent_consent_date": "2025-11-09T10:30:00Z",
    "created_at": "2025-11-01T08:00:00Z",
    "updated_at": "2025-11-09T10:30:00Z",
    "sessions_count": 5,
    "feedback_count": 3
}
```

### Right to Delete Child's Data

**API Endpoint**: `POST /api/coppa/delete-child-data`

```python
response = requests.post(
    "http://localhost:8000/api/coppa/delete-child-data",
    json={
        "student_id": "STU-12345",
        "parent_email": "parent@example.com",
        "verification_code": "verify-code-123",
        "confirm_deletion": True
    }
)

# Response
{
    "success": True,
    "message": "Child data has been deleted successfully",
    "student_id": "STU-12345"
}
```

**Note**: Deletion is implemented as **soft delete** (anonymization) to maintain referential integrity and educational records. Personal information is removed but session history is retained in anonymized form.

### Right to Revoke Consent

**API Endpoint**: `POST /api/coppa/revoke-consent`

```python
response = requests.post(
    "http://localhost:8000/api/coppa/revoke-consent",
    json={
        "student_id": "STU-12345",
        "parent_email": "parent@example.com",
        "verification_code": "verify-code-123",
        "delete_data": True  # Optional: delete data when revoking
    }
)

# Response
{
    "student_id": "STU-12345",
    "is_under_13": True,
    "requires_parental_consent": True,
    "parent_consent_given": False,  # Consent revoked
    "parent_consent_date": null,
    "can_collect_data": False
}
```

---

## API Endpoints

### Complete Endpoint List

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/coppa/mark-student-under-13` | POST | Mark student as under 13 and initiate consent workflow |
| `/api/coppa/grant-consent` | POST | Grant or deny parental consent |
| `/api/coppa/revoke-consent` | POST | Revoke previously granted consent |
| `/api/coppa/parent-data-access` | POST | Allow parent to access child's data |
| `/api/coppa/delete-child-data` | POST | Delete child's data at parent's request |
| `/api/coppa/status/{student_id}` | GET | Get COPPA compliance status for a student |

### Request/Response Models

All endpoints use Pydantic models for validation. See `/src/api/coppa_router.py` for complete schemas.

---

## Email Templates

### Parental Consent Request Email

**Subject**: "Parental Consent Required for {student_name}'s TutorMax Account"

**Key Components**:
1. Clear explanation of COPPA requirements
2. List of data collected
3. How data will be used
4. Parent's rights under COPPA
5. Two clear action buttons (Grant/Deny)
6. Expiration date (30 days)
7. Link to Privacy Policy
8. Link to FTC COPPA information

**Template Location**: `src/api/coppa_router.py` (function: `send_parental_consent_email`)

### Customization

To customize email templates:

1. Edit the `send_parental_consent_email` function in `/src/api/coppa_router.py`
2. Update HTML and text templates
3. Ensure all required information is included:
   - COPPA notice
   - Data collection practices
   - Parental rights
   - Consent/denial mechanism

---

## Compliance Checklist

### Initial Setup

- [ ] COPPA compliance enabled in config (`coppa_compliance_enabled = True`)
- [ ] Email service configured (SMTP settings in `.env`)
- [ ] Student model includes COPPA fields (already included)
- [ ] Privacy Policy updated with COPPA notice
- [ ] Parent consent email template reviewed and customized

### Operational Requirements

- [ ] Age verification at student registration
- [ ] Automatic flagging of under-13 students
- [ ] Parental consent email sent within 24 hours
- [ ] Consent tokens expire after 30 days
- [ ] Expired consents trigger data anonymization
- [ ] All COPPA actions logged in audit system

### Parental Rights

- [ ] Parents can review child's data
- [ ] Parents can request data deletion
- [ ] Parents can revoke consent
- [ ] Parent requests processed within 2 business days
- [ ] Confirmation emails sent for all parent actions

### Data Protection

- [ ] Minimal data collection without consent
- [ ] PII encrypted at rest (via EncryptionService)
- [ ] PII anonymized in analytics (via AnonymizationService)
- [ ] Audit logs for all COPPA-related actions
- [ ] Regular compliance audits scheduled

### Legal Requirements

- [ ] Privacy Policy includes COPPA section
- [ ] Clear disclosure of data practices
- [ ] Verifiable parental consent mechanism
- [ ] Parent notification of changes to privacy policy
- [ ] Compliance review every 6 months

---

## Testing Guide

### Unit Tests

Create tests in `/tests/test_coppa_compliance.py`:

```python
import pytest
from src.api.compliance.coppa import COPPAService, verify_age

def test_verify_age():
    """Test age verification."""
    assert verify_age(12) == True  # Under 13
    assert verify_age(13) == False  # 13 or older
    assert verify_age(None) == False  # No age provided

@pytest.mark.asyncio
async def test_mark_student_under_13(async_session):
    """Test marking student as under 13."""
    student = await COPPAService.mark_student_as_under_13(
        session=async_session,
        student_id="TEST-123",
        parent_email="parent@test.com",
    )

    assert student.is_under_13 == True
    assert student.parent_email == "parent@test.com"
    assert student.parent_consent_given == False

@pytest.mark.asyncio
async def test_grant_consent(async_session):
    """Test granting parental consent."""
    # First mark as under 13
    await COPPAService.mark_student_as_under_13(
        session=async_session,
        student_id="TEST-123",
        parent_email="parent@test.com",
    )

    # Grant consent
    student = await COPPAService.grant_parental_consent(
        session=async_session,
        student_id="TEST-123",
        parent_email="parent@test.com",
    )

    assert student.parent_consent_given == True
    assert student.parent_consent_date is not None

@pytest.mark.asyncio
async def test_consent_token_validation():
    """Test consent token generation and validation."""
    student_id = "TEST-123"

    # Generate token
    token = COPPAService.generate_consent_token(student_id)

    # Validate with correct student_id
    assert COPPAService.validate_consent_token(token, student_id) == True

    # Validate with incorrect student_id
    assert COPPAService.validate_consent_token(token, "WRONG-ID") == False
```

### Integration Tests

Test complete workflows:

```python
@pytest.mark.asyncio
async def test_complete_consent_workflow(async_session, test_client):
    """Test complete parental consent workflow."""
    # 1. Mark student as under 13
    response = test_client.post(
        "/api/coppa/mark-student-under-13",
        json={
            "student_id": "TEST-123",
            "parent_email": "parent@test.com",
            "parent_name": "Test Parent",
            "send_consent_email": False,  # Skip email in tests
        }
    )
    assert response.status_code == 200
    assert response.json()["requires_parental_consent"] == True

    # 2. Generate consent token
    token = COPPAService.generate_consent_token("TEST-123")

    # 3. Grant consent
    response = test_client.post(
        "/api/coppa/grant-consent",
        json={
            "student_id": "TEST-123",
            "parent_email": "parent@test.com",
            "consent_token": token,
            "consent_given": True,
        }
    )
    assert response.status_code == 200
    assert response.json()["parent_consent_given"] == True
    assert response.json()["can_collect_data"] == True
```

### Manual Testing

1. **Test Age Verification**:
   - Create student with age < 13
   - Verify automatic flagging
   - Verify parent email request

2. **Test Consent Email**:
   - Use test SMTP server (e.g., Mailhog)
   - Verify email content
   - Test consent/denial links

3. **Test Parent Data Access**:
   - Request child data as parent
   - Verify all data is included
   - Check audit log entry

4. **Test Data Deletion**:
   - Request deletion as parent
   - Verify data anonymization
   - Check referential integrity maintained

---

## Monitoring and Maintenance

### Regular Tasks

**Daily**:
- Monitor consent request emails (delivery success)
- Check for failed parent verification attempts

**Weekly**:
- Review students awaiting parental consent
- Send reminder emails for pending consents

**Monthly**:
- Run `anonymize_expired_consents()` cleanup
- Audit COPPA compliance logs
- Review denied consent cases

**Quarterly**:
- Full COPPA compliance audit
- Privacy policy review
- Update consent email templates if needed

### Audit Queries

```python
# Get students needing consent
students = await COPPAService.get_students_needing_consent(
    session=session,
    limit=100
)

# Get COPPA-related audit logs
from src.api.audit_service import AuditService

logs = await AuditService.search_logs(
    session=session,
    action_prefix="coppa_",
    start_date=datetime.now() - timedelta(days=30)
)
```

### Compliance Reports

Generate monthly reports including:
- Number of under-13 students
- Consent granted vs. denied
- Parent data access requests
- Data deletion requests
- Expired consent requests

---

## Additional Resources

### COPPA Regulation
- [FTC COPPA Rule](https://www.ftc.gov/enforcement/rules/rulemaking-regulatory-reform-proceedings/childrens-online-privacy-protection-rule)
- [COPPA FAQ](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions)

### Best Practices
- [FTC's Six-Step Compliance Plan](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions)
- [COPPA Safe Harbor Programs](https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa)

### Related TutorMax Documentation
- `/docs/SECURITY_HARDENING.md` - Overall security features
- `/docs/AUDIT_LOGGING_SYSTEM.md` - Audit logging for COPPA actions
- `/docs/SECURITY_QUICK_REFERENCE.md` - Security services integration

---

## Support

For questions about COPPA compliance implementation:
1. Review this documentation
2. Check `/src/api/compliance/coppa.py` for implementation details
3. Review audit logs for COPPA-related actions
4. Consult with legal counsel for compliance questions

**Remember**: COPPA compliance is a legal requirement. When in doubt, consult with legal counsel before making changes to data collection or consent workflows.
