# GDPR Quick Reference Guide

## For Developers

Quick reference for implementing GDPR features in TutorMax.

---

## Import Statements

```python
# Import GDPR services
from src.api.compliance import (
    gdpr_service,
    consent_manager,
    data_breach_notifier
)

# Import audit service
from src.api.audit_service import AuditService

# Import security services
from src.api.security import encryption_service, anonymization_service
```

---

## Common Operations

### Check Consent Before Processing

```python
# Check if user has consented to marketing
can_send_marketing = await consent_manager.get_consent_status(
    session=session,
    user_id=user_id,
    purpose=consent_manager.PURPOSE_MARKETING
)

if can_send_marketing:
    # Send marketing email
    pass
else:
    # Skip marketing email
    pass
```

### Export User Data

```python
# Export all user data in JSON format
data = await gdpr_service.export_user_data(
    session=session,
    user_id=user_id,
    include_encrypted=False,
    format="json"
)
```

### Delete User Data

```python
# Delete all user data (irreversible!)
summary = await gdpr_service.delete_user_data(
    session=session,
    user_id=user_id,
    deletion_reason="User requested deletion",
    retain_audit_logs=True
)
```

### Update User Data

```python
# Correct user data
summary = await gdpr_service.rectify_user_data(
    session=session,
    user_id=user_id,
    corrections={
        "account": {
            "full_name": "Corrected Name",
            "email": "new@example.com"
        }
    },
    requesting_user_id=requesting_user_id
)
```

### Record Consent

```python
# Grant consent
await consent_manager.record_consent(
    session=session,
    user_id=user_id,
    purpose=consent_manager.PURPOSE_ANALYTICS,
    granted=True,
    ip_address="192.168.1.1"
)

# Withdraw consent
await consent_manager.record_consent(
    session=session,
    user_id=user_id,
    purpose=consent_manager.PURPOSE_ANALYTICS,
    granted=False
)
```

### Log Data Breach

```python
from datetime import datetime

breach_id = await data_breach_notifier.log_breach(
    session=session,
    breach_description="Unauthorized access detected",
    affected_data_types=["email", "name"],
    affected_user_count=150,
    severity=data_breach_notifier.SEVERITY_HIGH,
    discovered_at=datetime.utcnow(),
    contained_at=datetime.utcnow(),
    root_cause="SQL injection vulnerability",
    mitigation_steps=[
        "Patched vulnerability",
        "Reset API tokens",
        "Notified users"
    ]
)
```

---

## API Endpoints

### For Frontend Integration

```javascript
// Get user's data export
const response = await fetch('/api/gdpr/export-my-data', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// Download data report
const download = await fetch('/api/gdpr/download-data-report?format=pdf', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
const blob = await download.blob();
// Save blob to file

// Delete account
const deleteResponse = await fetch('/api/gdpr/delete-my-data', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        confirm: true,
        reason: 'User requested',
        retain_audit_logs: true
    })
});

// Manage consent
const consentResponse = await fetch('/api/gdpr/consent', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        purpose: 'marketing',
        granted: true
    })
});

// Get consent status
const statusResponse = await fetch('/api/gdpr/consent', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

---

## Consent Purposes

Use these constants from `ConsentManager`:

- `PURPOSE_MARKETING` - Marketing communications
- `PURPOSE_ANALYTICS` - Usage analytics
- `PURPOSE_PERSONALIZATION` - Personalized content
- `PURPOSE_THIRD_PARTY_SHARING` - Third-party data sharing
- `PURPOSE_PROFILING` - Automated profiling

---

## Breach Severity Levels

Use these constants from `DataBreachNotifier`:

- `SEVERITY_LOW` - Minor incident
- `SEVERITY_MEDIUM` - Limited exposure
- `SEVERITY_HIGH` - Significant exposure
- `SEVERITY_CRITICAL` - Severe breach

---

## Response Time Requirements

According to GDPR:

| Request Type | Response Time |
|-------------|---------------|
| Right to Access | 30 days (extendable to 60) |
| Right to Erasure | 30 days |
| Right to Rectification | 30 days |
| Breach Notification (Authority) | 72 hours |
| Breach Notification (Users) | ASAP |

---

## Testing

```bash
# Run GDPR compliance tests
pytest tests/test_gdpr_compliance.py -v

# Test specific features
pytest tests/test_gdpr_compliance.py::test_export_user_data -v
pytest tests/test_gdpr_compliance.py::test_consent_management -v
```

---

## Common Pitfalls

1. **Don't forget to check consent** before processing data for marketing, analytics, etc.

2. **Delete operations are irreversible** - always require explicit confirmation

3. **Retain audit logs** even after user deletion (anonymized) for compliance

4. **Data portability must be machine-readable** - JSON format is required

5. **Breach notification is time-sensitive** - 72 hours for authorities

---

## Security Considerations

1. **All GDPR endpoints require authentication**
2. **Audit all GDPR operations** (automatically done)
3. **Encrypt sensitive data exports** if needed
4. **Log all consent changes** for compliance audit trail
5. **Anonymize retained data** after user deletion

---

## For More Information

- Full documentation: `/docs/GDPR_COMPLIANCE.md`
- Integration guide: `/docs/GDPR_INTEGRATION_EXAMPLE.md`
- Code location: `/src/api/compliance/gdpr.py`
- API router: `/src/api/gdpr_router.py`

---

**Last Updated**: November 9, 2025
