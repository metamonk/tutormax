# Security Features - Quick Reference Guide

## Quick Start

### 1. Generate Strong Secret
```bash
openssl rand -hex 32
```
Add to `.env`:
```bash
SECRET_KEY="<generated-secret>"
```

### 2. Enable Security Features
```bash
# .env
RATE_LIMIT_ENABLED=true
CSRF_ENABLED=true
SECURITY_HEADERS_ENABLED=true
```

### 3. Add to main.py
```python
from src.api.security import (
    rate_limiter,
    SecurityHeadersMiddleware,
    setup_secure_logging,
)

setup_secure_logging()
app.add_middleware(SecurityHeadersMiddleware)
```

---

## Rate Limiting

### Protect Endpoint
```python
from src.api.security import rate_limiter

@app.post("/endpoint")
@rate_limiter.limit(max_requests=10, window_seconds=60)
async def endpoint(request: Request):
    ...
```

### Predefined Configs
```python
from src.api.security import RateLimitConfig

@rate_limiter.limit(**RateLimitConfig.AUTH_LOGIN)     # 5 per 5 min
@rate_limiter.limit(**RateLimitConfig.AUTH_REGISTER)  # 3 per hour
@rate_limiter.limit(**RateLimitConfig.API_WRITE)      # 30 per min
```

### Custom Key
```python
def custom_key(request: Request) -> str:
    return f"user:{request.state.user.id}"

@rate_limiter.limit(max_requests=100, window_seconds=60, key_func=custom_key)
```

---

## CSRF Protection

### Get Token (Client)
```bash
GET /security/csrf-token
Authorization: Bearer <jwt>

Response: {"csrf_token": "abc.xyz"}
```

### Use Token (Client)
```bash
POST /api/endpoint
X-CSRF-Token: abc.xyz
```

### Protect Endpoint (Server)
```python
from src.api.security import csrf_protect

@app.post("/endpoint")
async def endpoint(
    csrf_token: str = Depends(csrf_protect.require_csrf_token)
):
    ...
```

---

## XSS Prevention

### Sanitize Input
```python
from src.api.security import sanitize_input

clean = sanitize_input(user_data, check_sql_injection=True)
```

### Sanitize HTML
```python
from src.api.security import sanitize_html

safe_html = sanitize_html("<script>alert('XSS')</script>")
# Returns: "&lt;script&gt;alert('XSS')&lt;/script&gt;"
```

### Sanitize Filename
```python
from src.api.security import sanitize_filename

safe_name = sanitize_filename("../../etc/passwd")
# Returns: "etcpasswd"
```

---

## SQL Injection Prevention

### Validate Input
```python
from src.api.security import validate_no_sql_injection

try:
    validate_no_sql_injection(user_input, raise_on_suspicious=True)
except ValueError:
    raise HTTPException(400, "Invalid input")
```

### Pydantic Validator
```python
from pydantic import BaseModel, validator
from src.api.security import validate_safe_string

class UserInput(BaseModel):
    search: str

    @validator('search')
    def safe_search(cls, v):
        return validate_safe_string(v)
```

### Safe Query Pattern
```python
# ✅ SAFE
query = select(User).where(User.email == email)

# ❌ UNSAFE
query = f"SELECT * FROM users WHERE email = '{email}'"
```

---

## Secret Management

### Setup Secure Logging
```python
from src.api.security import setup_secure_logging

setup_secure_logging()  # Automatically redacts secrets from logs
```

### Load and Validate Secrets
```python
from src.api.security import secret_manager

secret_manager.load_secret('API_KEY', required=True, min_length=32)
```

### Validate Secret Strength
```python
from src.api.security import validate_secret_key

if not validate_secret_key(settings.secret_key):
    logger.error("Weak secret key!")
```

### Generate Secure Secret
```python
from src.api.security import generate_secure_secret

new_secret = generate_secure_secret(length=32)
```

### Check Rotation Needs
```python
needs_rotation = secret_manager.validate_all_secrets(max_age_days=90)
```

---

## Common Patterns

### Protect Auth Endpoint
```python
from src.api.security import rate_limiter, RateLimitConfig

@app.post("/auth/login")
@rate_limiter.limit(**RateLimitConfig.AUTH_LOGIN)
async def login(request: Request, credentials: LoginCredentials):
    ...
```

### Protect State-Changing Endpoint
```python
from src.api.security import rate_limiter, csrf_protect, RateLimitConfig

@app.post("/api/update-profile")
@rate_limiter.limit(**RateLimitConfig.API_WRITE)
async def update_profile(
    request: Request,
    data: ProfileUpdate,
    csrf_token: str = Depends(csrf_protect.require_csrf_token),
    user: User = Depends(current_active_user),
):
    # Sanitize input
    from src.api.security import sanitize_input
    clean_data = sanitize_input(data.dict())
    ...
```

### Full Security Pipeline
```python
from src.api.security import (
    rate_limiter,
    csrf_protect,
    sanitize_input,
    RateLimitConfig,
)

@app.post("/api/sensitive-action")
@rate_limiter.limit(**RateLimitConfig.API_WRITE)
async def sensitive_action(
    request: Request,
    data: ActionData,
    csrf_token: str = Depends(csrf_protect.require_csrf_token),
    user: User = Depends(current_active_user),
):
    # Validate and sanitize
    clean_data = sanitize_input(data.dict())

    # Process
    result = await process_action(clean_data, user)

    return result
```

---

## Configuration Quick Reference

### .env File
```bash
# Security
SECRET_KEY="<32+-char-secret>"
RATE_LIMIT_ENABLED=true
CSRF_ENABLED=true
SECURITY_HEADERS_ENABLED=true

# Rate Limits
RATE_LIMIT_AUTH_LOGIN_REQUESTS=5
RATE_LIMIT_AUTH_LOGIN_WINDOW=300

# CSRF
CSRF_TOKEN_EXPIRY_HOURS=24

# Headers
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000

# Sanitization
MAX_INPUT_LENGTH=10000

# Secrets
SECRET_ROTATION_DAYS=90
```

---

## Testing

### Test Rate Limit
```bash
# Should return 429 on 6th request
for i in {1..6}; do
    curl -X POST http://localhost:8000/auth/login
done
```

### Test CSRF
```bash
TOKEN=$(curl http://localhost:8000/security/csrf-token | jq -r '.csrf_token')
curl -X POST http://localhost:8000/api/endpoint -H "X-CSRF-Token: $TOKEN"
```

### Test Security Headers
```bash
curl -I http://localhost:8000/
# Should include: CSP, X-Frame-Options, HSTS, etc.
```

### Test Input Sanitization
```bash
curl -X POST http://localhost:8000/api/endpoint \
  -d '{"text": "<script>alert(\"XSS\")</script>"}'
# Script tags should be escaped
```

---

## Troubleshooting

### Rate limit too strict
```bash
# Increase limits in .env
RATE_LIMIT_API_READ_REQUESTS=200
```

### CSRF token expired
```bash
# Get new token
curl http://localhost:8000/security/csrf-token
```

### CSP blocking resources
```bash
# Update CSP policy in .env
CSP_POLICY="default-src 'self'; script-src 'self' https://trusted-cdn.com"
```

### Secrets in logs
```bash
# Ensure setup_secure_logging() called at startup
```

---

## Security Checklist

### Development
- [ ] Strong SECRET_KEY generated
- [ ] All secrets in .env (not in code)
- [ ] Secure logging enabled
- [ ] Input validation on all endpoints
- [ ] Tests for security features

### Production
- [ ] HTTPS enabled
- [ ] Rate limiting enabled
- [ ] Security headers enabled
- [ ] CSRF protection on state-changing endpoints
- [ ] Secrets rotated
- [ ] Monitoring configured
- [ ] Logs reviewed for secret leaks

---

## API Endpoints

### Get CSRF Token
```
GET /security/csrf-token
Authorization: Bearer <jwt>
```

### Get Security Info
```
GET /security/headers
```

### Check Health
```
GET /health
```

---

## Resources

- Full Documentation: `docs/SECURITY_HARDENING.md`
- Implementation Guide: `TASK_14.4_SECURITY_IMPLEMENTATION_SUMMARY.md`
- Tests: `tests/test_security_features.py`
- Enhanced Main: `src/api/main_enhanced.py`

## OWASP References
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [CSP Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
