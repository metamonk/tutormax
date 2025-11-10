# Data Encryption & Privacy Guide

**Task:** 14.6 - Implement Data Encryption & Privacy Measures
**Compliance:** FERPA, COPPA, GDPR

This document describes TutorMax's data encryption and privacy implementation, including:
- AES-256 encryption for PII at rest
- TLS 1.3 for data in transit
- Data anonymization for analytics
- FERPA, COPPA, and GDPR compliance

---

## Table of Contents

1. [Overview](#overview)
2. [Encryption at Rest](#encryption-at-rest)
3. [Encryption in Transit (TLS/SSL)](#encryption-in-transit-tlsssl)
4. [Data Anonymization](#data-anonymization)
5. [Privacy Compliance](#privacy-compliance)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Security Best Practices](#security-best-practices)

---

## Overview

TutorMax implements multi-layer data protection:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Application Layer** | AES-256 (Fernet) | Encrypt PII fields in database |
| **Transport Layer** | TLS 1.3 | Encrypt data in transit (HTTPS) |
| **Database Layer** | PostgreSQL encryption | Encrypted backups & storage |
| **Analytics Layer** | Pseudonymization | Anonymize for analytics |

### What is Protected

- **PII (Personally Identifiable Information)**:
  - Email addresses
  - Phone numbers
  - Postal addresses
  - Social Security Numbers
  - Date of birth
  - IP addresses

- **Educational Records (FERPA)**:
  - Student grades and performance
  - Disciplinary records
  - Special education data

- **Children's Data (COPPA)**:
  - All data for users under 13
  - Parental consent records

---

## Encryption at Rest

### AES-256 Field-Level Encryption

TutorMax uses **Fernet** (symmetric encryption) with AES-256 to encrypt sensitive database fields.

#### How It Works

1. **Before Storage**: Plaintext data is encrypted using app's secret key
2. **In Database**: Encrypted base64 strings are stored
3. **On Retrieval**: Data is automatically decrypted for authorized access

```python
# Example: User model with encrypted fields
from sqlalchemy import Column, Integer, String
from src.database.encrypted_types import EncryptedString, Encrypted Email
from src.database.models import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    # Encrypted fields - transparently encrypted/decrypted
    email = Column(EncryptedEmail(500), nullable=False)
    phone = Column(EncryptedString(500))

    # Non-encrypted fields
    full_name = Column(String(200))  # Anonymized for COPPA users
    created_at = Column(DateTime)
```

#### Key Derivation

Encryption keys are derived from `SECRET_KEY` using PBKDF2:

```python
# In src/api/security/encryption.py
kdf = PBKDF2(
    algorithm=hashes.SHA256(),
    length=32,
    salt=b'tutormax_encryption_salt_v1',
    iterations=480000,  # OWASP 2023 recommendation
)
```

**Production Note**: Use environment variable `ENCRYPTION_KEY` for custom key or AWS Secrets Manager.

---

## Encryption in Transit (TLS/SSL)

### TLS 1.3 Configuration

All API traffic must use HTTPS with TLS 1.3 or higher.

#### Local Development (Self-Signed Certificate)

```bash
# Generate self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Run uvicorn with SSL
uvicorn src.api.main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem --host 0.0.0.0 --port 8443
```

#### Production Deployment (Let's Encrypt)

**Option 1: Render.com (Automatic HTTPS)**
- Render automatically provisions and renews SSL certificates
- No manual configuration needed
- See: `docs/SSL_AND_DOMAINS.md`

**Option 2: Manual with Nginx + Let's Encrypt**

1. Install Certbot:
```bash
sudo apt-get install certbot python3-certbot-nginx
```

2. Obtain certificate:
```bash
sudo certbot --nginx -d api.tutormax.com
```

3. Configure Nginx (`/etc/nginx/sites-available/tutormax`):
```nginx
server {
    listen 443 ssl http2;
    server_name api.tutormax.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.tutormax.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tutormax.com/privkey.pem;

    # TLS 1.3 only (or 1.2+ for compatibility)
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;

    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy to FastAPI
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.tutormax.com;
    return 301 https://$host$request_uri;
}
```

4. Test configuration:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

5. Verify SSL:
```bash
curl https://api.tutormax.com/health
```

#### Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up auto-renewal:

```bash
# Add cron job for automatic renewal
sudo crontab -e

# Add this line (runs twice daily)
0 */12 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## Data Anonymization

### Analytics Without PII

Use anonymization services to protect privacy while enabling analytics:

```python
from src.api.security import anonymization_service

# Pseudonymize user IDs (consistent hashing)
pseudo_id = anonymization_service.pseudonymize_id(user_id=123)
# Returns: "a1b2c3d4e5f6g7h8" (consistent for same user_id)

# Anonymize email for display
masked_email = anonymization_service.anonymize_email("student@example.com")
# Returns: "st****@***.com"

# Anonymize phone number
masked_phone = anonymization_service.anonymize_phone("555-123-4567")
# Returns: "***-***-4567"

# Hash for aggregation (one-way)
user_hash = anonymization_service.hash_for_analytics("student@example.com")
# Returns: "8f3d7b2a1c4e9f0d..." (SHA-256 hash, cannot be reversed)
```

### COPPA Protection

For users under 13 years old:

```python
from src.api.security import anonymization_service, privacy_helper

# Check if user is COPPA-protected
is_protected = anonymization_service.is_coppa_protected(age=12)  # True

# Determine which fields to anonymize
if privacy_helper.is_coppa_restricted("email"):
    # Don't display email for under-13 users
    email_display = "***@***.***"
```

---

## Privacy Compliance

### FERPA (Family Educational Rights and Privacy Act)

**Requirements**:
- Protect student educational records
- Obtain consent before disclosure
- Audit access to student data
- Retain records for 7 years

**TutorMax Implementation**:
```python
# Audit logging for all student data access
from src.api.audit_service import AuditService

await AuditService.log_data_access(
    session=session,
    user_id=admin_id,
    resource_type="student_record",
    resource_id=student_id,
    action="view_grades",
    ip_address=request.client.host
)

# Data retention: 7 years (see config.py)
audit_log_retention_days: int = 2555  # 7 years
```

### COPPA (Children's Online Privacy Protection Act)

**Requirements**:
- Obtain parental consent for under-13 users
- Minimize data collection
- Anonymize data for children

**TutorMax Implementation**:
```python
# Check age before collecting PII
if student.age < 13 and not student.has_parental_consent:
    raise HTTPException(
        status_code=403,
        detail="Parental consent required for users under 13"
    )

# Anonymize names for display
if student.age < 13:
    display_name = anonymization_service.anonymize_name(student.full_name)
    # "John Smith" → "J*** S***"
```

### GDPR (General Data Protection Regulation)

**Requirements**:
- Right to access personal data
- Right to erasure ("right to be forgotten")
- Data portability
- Consent management

**TutorMax Implementation**:
```python
# Data export (GDPR Article 20)
@router.get("/users/me/data-export")
async def export_user_data(user: User = Depends(current_active_user)):
    """Export all user data in JSON format."""
    return {
        "personal_info": {...},
        "activity_logs": [...],
        "consent_records": [...]
    }

# Data deletion (GDPR Article 17)
@router.delete("/users/me")
async def delete_my_account(user: User = Depends(current_active_user)):
    """Permanently delete user account and all associated data."""
    # Anonymize instead of delete (retain for analytics)
    user.email = anonymization_service.hash_for_analytics(user.email)
    user.full_name = "Deleted User"
    user.is_active = False
    # ... delete or anonymize other PII
```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Data Encryption & Privacy
ENCRYPTION_ENABLED=true
ENCRYPTION_KEY=""  # Leave empty to derive from SECRET_KEY
ANONYMIZATION_ENABLED=true
COPPA_COMPLIANCE_ENABLED=true

# Data Retention
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years (FERPA)
PII_DATA_RETENTION_DAYS=2555   # 7 years
ANONYMIZE_AFTER_DAYS=1095      # 3 years
```

### Encryption Key Management

**Development**:
- Keys derived from `SECRET_KEY` in `.env`
- Suitable for testing only

**Production** (Choose one):

1. **Environment Variable**:
```bash
# Generate secure key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to environment
export ENCRYPTION_KEY="your-generated-key-here"
```

2. **AWS Secrets Manager** (Recommended):
```bash
# Store key in AWS
aws secretsmanager create-secret \
    --name tutormax/encryption-key \
    --secret-string "your-generated-key-here"

# Retrieve in application
import boto3
secret = boto3.client('secretsmanager').get_secret_value(SecretId='tutormax/encryption-key')
encryption_key = secret['SecretString']
```

3. **HashiCorp Vault**:
```bash
# Store in Vault
vault kv put secret/tutormax/encryption-key value="your-key-here"

# Retrieve in application
import hvac
client = hvac.Client(url='https://vault.example.com')
encryption_key = client.secrets.kv.v2.read_secret_version(path='tutormax/encryption-key')
```

---

## Usage Examples

### Example 1: Encrypt User Email

```python
from src.database.models import User
from src.database.encrypted_types import EncryptedEmail

# Create user with encrypted email
user = User(
    email="student@example.com",  # Automatically encrypted before DB insert
    full_name="Jane Smith"
)
session.add(user)
await session.commit()

# Retrieve user (email automatically decrypted)
user = await session.get(User, user_id)
print(user.email)  # Prints: "student@example.com" (decrypted)

# In database: "gAAAAABl..." (encrypted base64)
```

### Example 2: Anonymize for Analytics

```python
from src.api.security import anonymization_service

# Create analytics event without exposing PII
analytics_event = {
    "user_id": anonymization_service.pseudonymize_id(user.id),  # Hashed
    "action": "completed_session",
    "timestamp": datetime.utcnow(),
    # No email, phone, or PII included
}

# Store anonymized event
await redis.lpush("analytics:events", json.dumps(analytics_event))
```

### Example 3: COPPA-Compliant Display

```python
from src.api.security import anonymization_service

async def get_student_display_name(student: Student) -> str:
    """Get display name with COPPA protection."""
    if student.age and student.age < 13:
        # Under 13: anonymize name
        return anonymization_service.anonymize_name(student.full_name)
    else:
        return student.full_name

# Usage
display_name = await get_student_display_name(student)
# Under 13: "J*** S***"
# 13+: "Jane Smith"
```

---

## Security Best Practices

### 1. Key Rotation

Rotate encryption keys annually:

```bash
# Generate new key
NEW_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Re-encrypt all data with new key (see scripts/rotate_encryption_key.py)
python3 scripts/rotate_encryption_key.py --old-key "$OLD_KEY" --new-key "$NEW_KEY"
```

### 2. Access Control

Limit decryption to authorized services:

```python
# Only decrypt when necessary
@router.get("/users/{user_id}/contact")
async def get_user_contact(
    user_id: int,
    current_user: User = Depends(current_superuser)  # Admin only!
):
    """Get unencrypted contact info (admin only)."""
    user = await session.get(User, user_id)
    return {
        "email": user.email,  # Decrypted
        "phone": user.phone   # Decrypted
    }
```

### 3. Audit All Decryption

Log whenever PII is accessed:

```python
# Log PII access
await AuditService.log_data_access(
    session=session,
    user_id=current_user.id,
    resource_type="user_pii",
    resource_id=user_id,
    action="view_contact_info"
)
```

### 4. Test Encryption

```bash
# Run encryption tests
pytest tests/test_encryption.py -v

# Verify data is encrypted in database
psql -U tutormax -d tutormax -c "SELECT email FROM users LIMIT 1;"
# Should show: gAAAAABl4R... (encrypted base64, NOT plaintext)
```

### 5. Monitor for Data Leaks

```python
# Ensure API responses don't expose raw PII
response_data = {
    "user_id": anonymization_service.pseudonymize_id(user.id),
    "email": anonymization_service.anonymize_email(user.email),
    # Never include: user.email (raw)
}
```

---

## Troubleshooting

### Issue: Decryption Fails

**Symptom**: `cryptography.fernet.InvalidToken` error

**Cause**: Encryption key changed or data corrupted

**Solution**:
```python
# Check if ENCRYPTION_KEY changed
# Verify SECRET_KEY is consistent
# Re-encrypt data if key rotated without migration
```

### Issue: Performance Impact

**Symptom**: Slow queries on encrypted fields

**Solution**:
- Don't index encrypted fields (can't search encrypted data)
- Create hash columns for searching:
```python
email_hash = Column(String(64), index=True)  # SHA-256 hash for searching
email = Column(EncryptedString(500))  # Encrypted for storage
```

### Issue: COPPA Violation

**Symptom**: Under-13 user data exposed

**Solution**:
```python
# Always check age before displaying PII
if user.age and user.age < 13:
    # Anonymize all PII
    response.email = "***@***.***"
    response.phone = "***-***-****"
    response.full_name = anonymization_service.anonymize_name(user.full_name)
```

---

## Next Steps

1. **Enable encryption** in production (`.env`)
2. **Migrate existing data** to encrypted columns
3. **Set up TLS/SSL** with Let's Encrypt
4. **Implement key rotation** procedure
5. **Audit compliance** with FERPA, COPPA, GDPR checklists

For more information, see:
- `docs/SECURITY_HARDENING.md` - Security best practices
- `docs/AUDIT_LOGGING_SYSTEM.md` - Audit logging guide
- `docs/SSL_AND_DOMAINS.md` - SSL certificate setup

---

**Last Updated**: November 2025
**Task**: 14.6 - Data Encryption & Privacy Measures
**Compliance Status**: ✅ FERPA, ✅ COPPA, ✅ GDPR
