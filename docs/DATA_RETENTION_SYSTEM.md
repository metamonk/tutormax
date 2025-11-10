# Data Retention & Compliance Automation System

Comprehensive automated data retention, archival, and deletion system implementing FERPA, GDPR, and COPPA compliance requirements.

## Overview

The Data Retention System manages the complete data lifecycle for TutorMax:

1. **Active Data** (within retention period) - Full PII retained
2. **Eligible for Anonymization** (3+ years old) - PII removal for analytics
3. **Eligible for Archival** (7+ years old) - Cold storage migration
4. **Archived** - Retrieved only for legal/compliance needs
5. **Deleted** - Permanent removal (user request only)

## Compliance Frameworks

### FERPA (Family Educational Rights and Privacy Act)
- **7-year retention policy** for educational records
- Automated archival after retention period expires
- Disclosure logging for all educational record access
- Parent/guardian access rights for students under 18

### GDPR (General Data Protection Regulation)
- **Right to be Forgotten** (Article 17) - User-requested deletion
- **Right to Access** (Article 15) - Data export
- **Right to Rectification** (Article 16) - Data correction
- **Right to Data Portability** (Article 20) - Portable data export
- **3-year anonymization threshold** for analytics

### COPPA (Children's Online Privacy Protection Act)
- Parental consent management for users under 13
- Minimal data collection for minors
- Enhanced deletion workflows

## Architecture

### Components

```
src/api/compliance/
├── data_retention.py          # Core retention service
├── ferpa.py                    # FERPA compliance
├── gdpr.py                     # GDPR compliance
└── coppa.py                    # COPPA compliance

src/api/
└── data_retention_router.py   # API endpoints

scripts/
├── run_data_retention.py      # Automated retention script
├── data_retention_cron.txt    # Cron job examples
├── data-retention.service      # Systemd service (scan)
├── data-retention.timer        # Systemd timer (scan)
├── data-retention-archival.service  # Systemd service (archival)
└── data-retention-archival.timer    # Systemd timer (archival)
```

### Data Retention Service

Core service: `src/api/compliance/data_retention.py`

**Key Methods:**
- `scan_for_retention_actions()` - Identifies eligible records
- `archive_student_data()` - Archives student data to cold storage
- `anonymize_data_for_analytics()` - Removes PII, keeps statistics
- `process_deletion_request()` - GDPR deletion (right to be forgotten)
- `get_retention_report()` - Compliance reporting
- `schedule_automated_archival()` - Scheduled job entry point

## API Endpoints

All endpoints require **admin authentication**.

### Scan for Eligible Records

```http
POST /api/data-retention/scan
Content-Type: application/json

{
  "dry_run": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_date": "2025-11-09T...",
    "eligible_for_archival": {
      "students": [...],
      "tutors": [...],
      "sessions": [...],
      "feedback": [...]
    },
    "summary": {
      "total_students_for_archival": 5,
      "total_sessions_for_archival": 150
    }
  }
}
```

### Archive Data

```http
POST /api/data-retention/archive
Content-Type: application/json

{
  "entity_type": "student",
  "entity_id": "STU-001",
  "reason": "FERPA retention period expired"
}
```

### Anonymize Data

```http
POST /api/data-retention/anonymize
Content-Type: application/json

{
  "entity_type": "student",
  "entity_id": "STU-001"
}
```

**Anonymized Fields:**
- Student: name, parent_email, parent_consent_ip
- Tutor: name, email, location

**Retained Fields (for analytics):**
- Student: age, grade_level, subjects_interested
- Tutor: subjects, education_level, performance metrics

### Process GDPR Deletion

```http
POST /api/data-retention/delete
Content-Type: application/json

{
  "user_id": 123,
  "deletion_reason": "GDPR Article 17 - Right to Erasure"
}
```

**What gets deleted:**
- User account
- All tutor/student records
- Sessions, feedback, performance metrics
- Interventions, predictions, events
- Manager notes, notifications

**What's retained:**
- Anonymized audit logs (compliance requirement)

### Generate Compliance Report

```http
GET /api/data-retention/report?start_date=2025-08-01&end_date=2025-11-09
```

**Response:**
```json
{
  "success": true,
  "data": {
    "current_data_inventory": {
      "active_students": 1250,
      "active_tutors": 450,
      "total_sessions": 45000
    },
    "retention_actions_taken": {
      "archival_operations": 12,
      "anonymization_operations": 5,
      "deletion_requests_processed": 3
    },
    "compliance_status": {
      "ferpa_retention_policy": "7 years (2555 days)",
      "gdpr_anonymization_eligible_after": "3 years (1095 days)"
    }
  }
}
```

### Run Scheduled Archival

```http
POST /api/data-retention/scheduled-archival
Content-Type: application/json

{
  "perform_actions": false  // true for live mode
}
```

### Check Retention Status

```http
GET /api/data-retention/check/student/STU-001
```

### Get Retention Policy

```http
GET /api/data-retention/retention-policy
```

## Automated Scheduling

### Option 1: Cron Jobs

```bash
# Install cron jobs
crontab -e

# Add from scripts/data_retention_cron.txt:
# - Weekly scan (Monday 2 AM)
# - Monthly report (1st day 3 AM)
# - Quarterly archival (Jan/Apr/Jul/Oct 4 AM)
```

### Option 2: Systemd Timers

```bash
# Copy service and timer files
sudo cp scripts/data-retention.service /etc/systemd/system/
sudo cp scripts/data-retention.timer /etc/systemd/system/
sudo cp scripts/data-retention-archival.service /etc/systemd/system/
sudo cp scripts/data-retention-archival.timer /etc/systemd/system/

# Enable and start timers
sudo systemctl enable data-retention.timer
sudo systemctl start data-retention.timer
sudo systemctl enable data-retention-archival.timer
sudo systemctl start data-retention-archival.timer

# Check status
sudo systemctl status data-retention.timer
sudo systemctl list-timers
```

### Manual Execution

```bash
# Dry run (see what would be archived)
python scripts/run_data_retention.py --dry-run

# Actually perform archival
python scripts/run_data_retention.py --perform-actions

# Generate 30-day compliance report
python scripts/run_data_retention.py --report-only --days 30
```

## Archival Process

### How Archival Works

1. **Eligibility Check**
   - Record age > 7 years (FERPA requirement)
   - Last activity date > 7 years ago
   - Grace period buffer (30 days)

2. **Data Export**
   - Export all related records to JSON
   - Store in audit log metadata
   - Maintain full data integrity

3. **Active Deletion**
   - Remove from active tables
   - Cascade to related records
   - Maintain referential integrity

4. **Audit Trail**
   - Log archival operation
   - Record reason and performer
   - Timestamp for compliance

### Retrieving Archived Data

Archived data is stored in audit log metadata:

```python
from src.database.models import AuditLog

# Find archival record
query = select(AuditLog).where(
    AuditLog.action == "data_archived",
    AuditLog.resource_id == "STU-001"
)
log = await session.execute(query)
archival_record = log.scalar_one()

# Access archived data
archived_data = archival_record.audit_metadata["archival_summary"]["archived_records"]
```

## Anonymization for Analytics

### Purpose

After 3 years, PII can be removed while keeping statistical data for:
- Performance analytics
- Behavioral research
- Platform improvements
- Trend analysis

### What Gets Anonymized

**Students:**
```python
# Before
name = "John Doe"
parent_email = "parent@example.com"

# After
name = "ANONYMIZED_STUDENT_STU-001"
parent_email = None

# Kept for analytics
age = 12
grade_level = "7th"
subjects_interested = ["Math", "Science"]
```

**Tutors:**
```python
# Before
name = "Jane Smith"
email = "jane@example.com"
location = "New York, NY"

# After
name = "ANONYMIZED_TUTOR_TUT-001"
email = "anonymized_tut-001@example.com"
location = "REDACTED"

# Kept for analytics
subjects = ["Math", "Science"]
education_level = "Master's"
performance_metrics = [all historical data]
```

## GDPR Right to be Forgotten

### User Request Process

1. **User initiates deletion request**
   - Via user portal or email
   - Admin receives request

2. **Admin processes request**
   ```http
   POST /api/data-retention/delete
   {
     "user_id": 123,
     "deletion_reason": "GDPR Article 17 - Right to Erasure"
   }
   ```

3. **Complete data removal**
   - User account deleted
   - All associated records removed
   - Cascade to related entities
   - Audit logs anonymized (not deleted - compliance)

4. **Confirmation**
   - Log deletion in audit trail
   - Notify user of completion
   - Generate deletion report

### Legal Basis

- **GDPR Article 17**: Right to erasure ("right to be forgotten")
- **Grounds for deletion:**
  - Data no longer necessary
  - User withdraws consent
  - User objects to processing
  - Data processed unlawfully
  - Compliance with legal obligation

### Exceptions

Audit logs are **anonymized** but **not deleted** because:
- FERPA requires 7-year audit retention
- Legal compliance requirement
- Financial audit requirements
- Security incident investigation

## Compliance Reporting

### Retention Report

Generated monthly/quarterly for audit purposes:

```python
report = await DataRetentionService.get_retention_report(
    session=session,
    start_date=start_date,
    end_date=end_date
)
```

**Report Contents:**
- Current data inventory
- Archival operations performed
- Anonymization operations
- Deletion requests processed
- Compliance status summary

### Audit Log Tracking

All retention operations are logged:

```python
# Archival
action="data_archived"
metadata={
    "archive_id": "...",
    "student_id": "...",
    "records_archived": {...}
}

# Anonymization
action="data_anonymized"
metadata={
    "entity_type": "student",
    "anonymized_fields": ["name", "parent_email"],
    "retained_fields": ["age", "grade_level"]
}

# Deletion
action="gdpr_data_deletion"
metadata={
    "deletion_reason": "GDPR Article 17",
    "records_deleted": {...}
}
```

## Security Considerations

### Access Control

- All retention endpoints require **admin role**
- Uses RBAC from `src/api/auth/rbac.py`
- All operations logged in audit trail

### Data Integrity

- Archival preserves full data in JSON format
- Cascade deletions maintain referential integrity
- Transaction-based operations (rollback on error)

### Privacy Protection

- Anonymization irreversible
- PII removal follows GDPR guidelines
- Audit logs retain minimal metadata

## Testing

### Manual Testing

```bash
# 1. Check current retention status
curl -X GET http://localhost:8000/api/data-retention/retention-policy \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 2. Scan for eligible records
curl -X POST http://localhost:8000/api/data-retention/scan \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'

# 3. Check specific entity
curl -X GET http://localhost:8000/api/data-retention/check/student/STU-001 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 4. Generate report
curl -X GET http://localhost:8000/api/data-retention/report?days=30 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Unit Tests

```python
# tests/test_data_retention.py
async def test_scan_for_retention_actions():
    async with AsyncSessionLocal() as session:
        results = await DataRetentionService.scan_for_retention_actions(
            session=session,
            dry_run=True
        )
        assert "eligible_for_archival" in results
        assert "summary" in results

async def test_archive_student_data():
    # Create old student record
    # Test archival
    # Verify data moved to audit log
    # Verify active record deleted
    pass

async def test_anonymize_data():
    # Create student with PII
    # Anonymize
    # Verify PII removed
    # Verify analytics data retained
    pass
```

## Monitoring

### Log Files

```bash
# Cron logs
/var/log/tutormax/retention_scan.log
/var/log/tutormax/retention_report.log
/var/log/tutormax/retention_archival.log

# Systemd logs
journalctl -u data-retention.service
journalctl -u data-retention-archival.service
```

### Metrics to Monitor

- Records eligible for archival (weekly trend)
- Successful archival operations (count)
- Failed operations (alerts)
- Storage space freed (GB)
- GDPR deletion requests (count & latency)
- Compliance report generation (success rate)

## Troubleshooting

### Common Issues

**1. "Student not eligible for archival yet"**
- Check retention period: 7 years (2555 days)
- Verify last activity date
- Check grace period (30 days)

**2. "Failed to archive - transaction error"**
- Check database connection
- Verify user permissions
- Review cascade constraints

**3. "Anonymization failed"**
- Verify entity exists
- Check field permissions
- Review transaction logs

### Recovery Procedures

**Restore Archived Data:**
```python
# Find archival record in audit logs
# Extract archived_records from metadata
# Recreate in active tables if legally required
```

**Reverse Anonymization:**
- Not possible - anonymization is irreversible
- Maintain backups before anonymization
- Test thoroughly in staging environment

## Best Practices

1. **Always dry run first**
   - Test with `--dry-run` flag
   - Review eligible records
   - Verify counts before live run

2. **Schedule wisely**
   - Weekly scans for monitoring
   - Quarterly archival for efficiency
   - Off-peak hours (2-4 AM)

3. **Monitor actively**
   - Set up alerts for failures
   - Review logs weekly
   - Track metrics over time

4. **Document everything**
   - Log all manual operations
   - Keep audit trail
   - Document special cases

5. **Test in staging**
   - Full dry run in production-like environment
   - Verify data integrity
   - Test restore procedures

## Compliance Checklist

- [ ] FERPA 7-year retention implemented
- [ ] Automated archival scheduled
- [ ] GDPR deletion workflow functional
- [ ] Anonymization for analytics implemented
- [ ] Audit logging for all operations
- [ ] Admin-only access enforced
- [ ] Compliance reports generated monthly
- [ ] Backup procedures documented
- [ ] Recovery procedures tested
- [ ] Security audit completed

## References

- **FERPA**: 20 U.S.C. § 1232g; 34 CFR Part 99
- **GDPR**: Regulation (EU) 2016/679
- **COPPA**: 15 U.S.C. §§ 6501–6506
- [FERPA Documentation](docs/FERPA_COMPLIANCE.md)
- [GDPR Documentation](docs/GDPR_COMPLIANCE.md)
- [COPPA Documentation](docs/COPPA_COMPLIANCE.md)
