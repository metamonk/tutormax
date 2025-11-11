# Security Hardening - Task 14.4 Implementation

## Overview

This document describes the comprehensive security hardening measures implemented for the TutorMax API, including rate limiting, CSRF protection, XSS prevention, SQL injection prevention, and secure secret management.

## Table of Contents

1. [Rate Limiting](#rate-limiting)
2. [CSRF Protection](#csrf-protection)
3. [XSS Prevention](#xss-prevention)
4. [SQL Injection Prevention](#sql-injection-prevention)
5. [Secret Management](#secret-management)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Security Best Practices](#security-best-practices)

---

## Rate Limiting

### Overview

Distributed rate limiting using Redis to protect against brute force attacks and API abuse.

### Features

- **Distributed**: Uses Redis for multi-instance rate limiting
- **Configurable**: Different limits for different endpoint types
- **Sliding Window**: Accurate rate limiting using sliding window algorithm
- **Proper HTTP Responses**: Returns 429 with Retry-After headers

### Implementation

```python
from src.api.security import rate_limiter, RateLimitConfig

# Apply to endpoint
@app.post("/auth/login")
@rate_limiter.limit(
    max_requests=RateLimitConfig.AUTH_LOGIN["max_requests"],
    window_seconds=RateLimitConfig.AUTH_LOGIN["window_seconds"]
)
async def login(request: Request):
    ...
```

### Rate Limit Tiers

| Endpoint Type | Limit | Window | Use Case |
|---------------|-------|--------|----------|
| Auth Login | 5 requests | 5 minutes | Prevent brute force |
| Auth Register | 3 requests | 1 hour | Prevent spam accounts |
| Auth Password Reset | 3 requests | 1 hour | Prevent email flooding |
| API Read | 100 requests | 1 minute | Normal usage |
| API Write | 30 requests | 1 minute | State changes |
| Batch Operations | 10 requests | 1 minute | Resource intensive |

### Configuration

Environment variables in `.env`:

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_LOGIN_REQUESTS=5
RATE_LIMIT_AUTH_LOGIN_WINDOW=300
RATE_LIMIT_AUTH_REGISTER_REQUESTS=3
RATE_LIMIT_AUTH_REGISTER_WINDOW=3600
```

### Response Format

When rate limit is exceeded:

```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "message": "Too many requests. Please try again in 120 seconds.",
    "retry_after": 120,
    "limit": 5,
    "window": 300
  }
}
```

Headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds until retry is allowed

---

## CSRF Protection

### Overview

Cross-Site Request Forgery protection using double-submit cookie pattern with server-side validation.

### Features

- **Token Generation**: Cryptographically secure tokens
- **Server-Side Validation**: Tokens stored in Redis
- **HMAC Signing**: Tokens signed with secret key
- **Expiry**: Configurable token expiration
- **One-Time Use Option**: Tokens can be consumed on validation

### Implementation

#### Getting a CSRF Token

```bash
GET /security/csrf-token
Authorization: Bearer <jwt-token>
```

Response:
```json
{
  "csrf_token": "abc123.signature",
  "header_name": "X-CSRF-Token",
  "timestamp": "2025-01-09T10:30:00"
}
```

#### Using CSRF Token

```bash
POST /api/endpoint
Authorization: Bearer <jwt-token>
X-CSRF-Token: abc123.signature
Content-Type: application/json

{...}
```

#### Protecting Endpoints

```python
from src.api.security import csrf_protect

@app.post("/api/protected-endpoint")
async def protected_endpoint(
    request: Request,
    csrf_token: str = Depends(csrf_protect.require_csrf_token)
):
    # Endpoint is protected
    ...
```

### Configuration

```bash
CSRF_ENABLED=true
CSRF_TOKEN_EXPIRY_HOURS=24
```

### When to Use CSRF Protection

Apply CSRF protection to all state-changing operations:
- ✅ POST, PUT, DELETE endpoints
- ✅ Admin actions
- ✅ Password changes
- ✅ Account modifications
- ❌ GET, HEAD, OPTIONS (safe methods)
- ❌ Public read-only endpoints

---

## XSS Prevention

### Overview

Cross-Site Scripting prevention through security headers and input sanitization.

### Security Headers

The `SecurityHeadersMiddleware` adds comprehensive security headers to all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| Content-Security-Policy | Custom CSP | Prevents XSS attacks |
| X-Content-Type-Options | nosniff | Prevents MIME type sniffing |
| X-Frame-Options | DENY | Prevents clickjacking |
| X-XSS-Protection | 1; mode=block | Browser XSS filter |
| Strict-Transport-Security | max-age=31536000 | Forces HTTPS |
| Referrer-Policy | strict-origin-when-cross-origin | Controls referrer info |
| Permissions-Policy | Restrictive | Disables unnecessary features |

### Content Security Policy (CSP)

Default CSP (balanced security and functionality):

```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
font-src 'self' https://fonts.gstatic.com;
img-src 'self' data: https:;
connect-src 'self' ws: wss:;
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

For strict mode (may break functionality):

```python
from src.api.security import get_security_headers_middleware

middleware = get_security_headers_middleware(strict_mode=True)
app.add_middleware(SecurityHeadersMiddleware)
```

### Input Sanitization

```python
from src.api.security import sanitize_input

# Sanitize user input
clean_data = sanitize_input(
    user_input,
    max_string_length=1000,
    check_sql_injection=True
)
```

Functions available:
- `sanitize_html()` - Escape HTML entities
- `remove_xss_patterns()` - Remove dangerous patterns
- `sanitize_string()` - Comprehensive string sanitization
- `sanitize_dict()` - Recursively sanitize dictionaries
- `sanitize_list()` - Recursively sanitize lists
- `sanitize_filename()` - Prevent directory traversal

### Configuration

```bash
SECURITY_HEADERS_ENABLED=true
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000
CSP_POLICY=""  # Empty uses default
```

---

## SQL Injection Prevention

### Overview

Multiple layers of protection against SQL injection attacks.

### Protection Layers

#### 1. **ORM Parameterization (Primary Defense)**

SQLAlchemy automatically parameterizes all queries:

```python
# ✅ SAFE - Parameterized
result = session.execute(
    select(User).where(User.email == user_email)
)

# ❌ UNSAFE - Never do this
query = f"SELECT * FROM users WHERE email = '{user_email}'"
```

#### 2. **Input Validation**

```python
from src.api.security import validate_no_sql_injection

# Validate input doesn't contain SQL injection patterns
try:
    validate_no_sql_injection(user_input, raise_on_suspicious=True)
except ValueError as e:
    # Reject input
    raise HTTPException(400, detail=str(e))
```

#### 3. **Pydantic Models**

All API inputs go through Pydantic validation:

```python
from pydantic import BaseModel, validator
from src.api.security import validate_safe_string

class UserInput(BaseModel):
    name: str
    email: str

    @validator('name', 'email')
    def validate_safe(cls, v):
        return validate_safe_string(v)
```

### SQL Injection Patterns Detected

The system detects these suspicious patterns:
- UNION SELECT statements
- DROP TABLE/DATABASE
- INSERT/UPDATE/DELETE with semicolons
- Comment sequences (--,  /* */)
- OR/AND with equals (OR 1=1)
- String concatenation attacks

### Code Review Results

All database queries reviewed:
- ✅ All queries use SQLAlchemy ORM
- ✅ No raw SQL with string interpolation
- ✅ All user inputs validated through Pydantic
- ✅ No f-strings or % formatting in queries

### Safe Query Patterns

```python
# ✅ SAFE - ORM with parameterization
from sqlalchemy import select

query = select(Tutor).where(
    Tutor.tutor_id == tutor_id,
    Tutor.status == status
)
result = session.execute(query)

# ✅ SAFE - Bound parameters
from sqlalchemy import text

query = text("SELECT * FROM tutors WHERE id = :id")
result = session.execute(query, {"id": tutor_id})

# ❌ UNSAFE - NEVER DO THIS
query = f"SELECT * FROM tutors WHERE id = '{tutor_id}'"
query = "SELECT * FROM tutors WHERE id = '%s'" % tutor_id
```

---

## Secret Management

### Overview

Secure handling of secrets including API keys, database passwords, and JWT signing keys.

### Features

- **Automatic Redaction**: Secrets removed from logs
- **Secret Validation**: Enforce minimum security requirements
- **Rotation Tracking**: Monitor secret age
- **Environment Loading**: Secure loading from .env
- **No Hardcoding**: All secrets from environment

### Secret Manager Usage

```python
from src.api.security import secret_manager

# Load secret with validation
api_key = secret_manager.load_secret(
    'API_KEY',
    required=True,
    min_length=32
)

# Check secret age (rotation needed?)
needs_rotation = secret_manager.validate_secret_age('API_KEY', max_age_days=90)

# Redact secrets from logs
safe_message = secret_manager.redact_secrets(error_message)
safe_dict = secret_manager.redact_dict(response_data)
```

### Automatic Log Redaction

All logging automatically redacts secrets:

```python
# This is safe - secrets are automatically redacted
logger.info(f"API response: {response}")  # API keys removed
logger.error(f"Database error: {db_url}")  # Password redacted
```

### Secret Validation Requirements

Secrets must meet these requirements:
- Minimum 32 characters
- No common weak patterns (password, secret, 12345)
- Sufficient entropy (16+ unique characters)

### Generating Secure Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Or in Python
from src.api.security import generate_secure_secret
secret = generate_secure_secret(length=32)
```

### Secret Rotation

Track and rotate secrets regularly:

```python
# Check all secrets
secrets_needing_rotation = secret_manager.validate_all_secrets(max_age_days=90)

if secrets_needing_rotation:
    logger.warning(f"Secrets need rotation: {secrets_needing_rotation}")
```

### Configuration

```bash
SECRET_KEY="<generate-with-openssl-rand-hex-32>"
SECRET_ROTATION_DAYS=90
```

### Secrets Checklist

- ✅ SECRET_KEY - Strong random value
- ✅ Database passwords - Strong, unique
- ✅ OAuth client secrets - From provider
- ✅ SMTP password - App-specific password
- ❌ No secrets in code
- ❌ No secrets in git history
- ❌ No secrets in logs

---

## Configuration

### Environment Variables

Complete list in `.env.example`:

```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_LOGIN_REQUESTS=5
RATE_LIMIT_AUTH_LOGIN_WINDOW=300

# CSRF Protection
CSRF_ENABLED=true
CSRF_TOKEN_EXPIRY_HOURS=24

# Security Headers
SECURITY_HEADERS_ENABLED=true
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000

# Input Sanitization
INPUT_SANITIZATION_ENABLED=true
MAX_INPUT_LENGTH=10000

# Secret Management
SECRET_ROTATION_DAYS=90
SECRET_KEY="<strong-random-value>"
```

### Application Integration

Update `main.py`:

```python
from src.api.security import (
    rate_limiter,
    SecurityHeadersMiddleware,
    csrf_protect,
    setup_secure_logging,
)

# Setup secure logging
setup_secure_logging()

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)

# Initialize security components in lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    await rate_limiter.connect()
    await csrf_protect.connect()
    yield
    await rate_limiter.disconnect()
    await csrf_protect.disconnect()
```

---

## Testing

### Rate Limiting Tests

```python
import pytest
from httpx import AsyncClient

async def test_rate_limit_login(client: AsyncClient):
    # Make 5 requests (should succeed)
    for i in range(5):
        response = await client.post("/auth/login", json={...})
        assert response.status_code == 200

    # 6th request should be rate limited
    response = await client.post("/auth/login", json={...})
    assert response.status_code == 429
    assert "retry_after" in response.json()["detail"]
```

### CSRF Tests

```python
async def test_csrf_protection(client: AsyncClient):
    # Get CSRF token
    response = await client.get("/security/csrf-token")
    token = response.json()["csrf_token"]

    # Request without token fails
    response = await client.post("/api/protected")
    assert response.status_code == 403

    # Request with token succeeds
    response = await client.post(
        "/api/protected",
        headers={"X-CSRF-Token": token}
    )
    assert response.status_code == 200
```

### XSS Tests

```python
async def test_xss_prevention(client: AsyncClient):
    # Malicious input
    xss_payload = "<script>alert('XSS')</script>"

    response = await client.post("/api/feedback", json={
        "comment": xss_payload
    })

    # Verify sanitization
    stored = await get_feedback_from_db()
    assert "<script>" not in stored.comment
    assert "alert" not in stored.comment
```

### SQL Injection Tests

```python
async def test_sql_injection_prevention(client: AsyncClient):
    # SQL injection attempt
    malicious_input = "1' OR '1'='1"

    response = await client.get(f"/api/tutors/{malicious_input}")

    # Should return 400 or 404, not 200 with all data
    assert response.status_code in [400, 404]
```

### Security Headers Tests

```python
async def test_security_headers(client: AsyncClient):
    response = await client.get("/")

    assert "Content-Security-Policy" in response.headers
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "Strict-Transport-Security" in response.headers
```

---

## Security Best Practices

### Development

1. **Never commit secrets**
   - Use `.env` files (in `.gitignore`)
   - Use environment variables
   - Rotate secrets if accidentally committed

2. **Use strong secrets**
   - Minimum 32 characters
   - Generated with cryptographic RNG
   - Unique per environment

3. **Validate all inputs**
   - Use Pydantic models
   - Apply sanitization
   - Check for injection patterns

4. **Test security features**
   - Write tests for rate limiting
   - Test CSRF protection
   - Verify XSS prevention

### Production

1. **HTTPS only**
   - Redirect HTTP to HTTPS
   - Use HSTS headers
   - Valid SSL certificate

2. **Monitor security events**
   - Log rate limit violations
   - Track failed authentication
   - Alert on suspicious patterns

3. **Regular updates**
   - Keep dependencies updated
   - Rotate secrets regularly
   - Review security logs

4. **Least privilege**
   - Database users with minimal permissions
   - API tokens with limited scope
   - Role-based access control

### Deployment Checklist

- [ ] Strong SECRET_KEY generated
- [ ] All secrets in environment variables
- [ ] HTTPS configured with valid cert
- [ ] Rate limiting enabled
- [ ] Security headers enabled
- [ ] CSRF protection enabled
- [ ] Input sanitization enabled
- [ ] Security logging enabled
- [ ] Monitoring configured
- [ ] Incident response plan documented

---

## Security Endpoints

### Get CSRF Token

```
GET /security/csrf-token
Authorization: Bearer <token>

Response:
{
  "csrf_token": "...",
  "header_name": "X-CSRF-Token"
}
```

### Get Security Info

```
GET /security/headers

Response:
{
  "features": {...},
  "rate_limits": {...},
  "recommendations": {...}
}
```

---

## Common Issues & Solutions

### Issue: Rate limit too strict

**Solution**: Adjust limits in `.env`
```bash
RATE_LIMIT_API_READ_REQUESTS=200  # Increase from 100
```

### Issue: CSRF token expired

**Solution**: Get new token from `/security/csrf-token`

### Issue: CSP blocking resources

**Solution**: Update CSP policy
```bash
CSP_POLICY="default-src 'self'; script-src 'self' https://trusted-cdn.com"
```

### Issue: Secrets in logs

**Solution**: Ensure `setup_secure_logging()` is called at startup

---

## Future Enhancements

1. **Advanced Rate Limiting**
   - User-specific limits
   - Graduated throttling
   - Whitelist/blacklist

2. **Enhanced CSRF**
   - Per-request tokens
   - Token rotation
   - Custom token storage

3. **Additional Headers**
   - Report-Only CSP
   - Expect-CT header
   - Certificate Transparency

4. **Secret Rotation**
   - Automated rotation
   - Blue-green rotation
   - Rotation alerts

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
