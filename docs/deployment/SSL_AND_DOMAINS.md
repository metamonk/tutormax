# SSL/TLS and Domain Configuration

This guide covers SSL/TLS certificate management and custom domain configuration for TutorMax on Render.

## Table of Contents

- [SSL/TLS Overview](#ssltls-overview)
- [Default Render Domains](#default-render-domains)
- [Custom Domain Setup](#custom-domain-setup)
- [SSL Certificate Management](#ssl-certificate-management)
- [Security Best Practices](#security-best-practices)

## SSL/TLS Overview

**Automatic SSL/TLS on Render:**

Render automatically provisions and manages SSL/TLS certificates for all services:

- ✅ Free SSL certificates via Let's Encrypt
- ✅ Automatic certificate renewal
- ✅ TLS 1.2 and TLS 1.3 support
- ✅ HTTP/2 enabled
- ✅ HTTPS redirect (optional)
- ✅ Zero configuration required

**Certificate Details:**
- **Provider**: Let's Encrypt
- **Type**: Domain Validated (DV)
- **Validity**: 90 days (auto-renewed)
- **Wildcard**: Not supported on free tier
- **Multiple domains**: Supported

## Default Render Domains

All services get a free `.onrender.com` subdomain with automatic HTTPS:

**TutorMax Default URLs:**

| Service | URL |
|---------|-----|
| API | `https://tutormax-api.onrender.com` |
| Dashboard | `https://tutormax-dashboard.onrender.com` |
| Flower (optional) | `https://tutormax-flower.onrender.com` |
| PostgreSQL | Internal (not publicly accessible) |
| Redis | Internal (not publicly accessible) |
| Workers | Internal (no public endpoint) |

**Default Domain Format:**
```
https://<service-name>.onrender.com
```

**Accessing Services:**
```bash
# API health check
curl https://tutormax-api.onrender.com/health

# Dashboard
open https://tutormax-dashboard.onrender.com

# Flower monitoring
open https://tutormax-flower.onrender.com
```

## Custom Domain Setup

### Prerequisites

1. Domain name purchased from registrar (GoDaddy, Namecheap, Cloudflare, etc.)
2. Access to DNS management
3. Render service deployed and running

### Step 1: Add Custom Domain to Render

**For API Service:**

1. Log in to Render Dashboard
2. Navigate to **tutormax-api** service
3. Click **Settings** tab
4. Scroll to **Custom Domains** section
5. Click **Add Custom Domain**
6. Enter your domain: `api.tutormax.com`
7. Click **Save**

Render will provide DNS configuration instructions.

**For Dashboard Service:**

1. Navigate to **tutormax-dashboard** service
2. Follow same steps as above
3. Enter domain: `app.tutormax.com` or `tutormax.com`

### Step 2: Configure DNS Records

**Option A: CNAME Record (Recommended for subdomains)**

Add CNAME record in your DNS provider:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | `api` | `tutormax-api.onrender.com` | 3600 |
| CNAME | `app` | `tutormax-dashboard.onrender.com` | 3600 |

**Option B: A Record (For apex/root domain)**

If using root domain (e.g., `tutormax.com`):

1. Get A record IP from Render Dashboard
2. Add A record in DNS:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | `@` | `<IP-from-Render>` | 3600 |

**Option C: ALIAS Record (Recommended for apex domain)**

Some DNS providers (Cloudflare, DNSimple) support ALIAS records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| ALIAS | `@` | `tutormax-dashboard.onrender.com` | 3600 |

### Step 3: Wait for DNS Propagation

- DNS propagation typically takes **5-30 minutes**
- Can take up to **48 hours** in rare cases
- Check propagation: `dig api.tutormax.com`

```bash
# Check DNS propagation
dig api.tutormax.com

# Expected output:
# api.tutormax.com. 3600 IN CNAME tutormax-api.onrender.com.
```

### Step 4: Verify SSL Certificate

Once DNS is propagated, Render automatically provisions SSL certificate:

1. Render Dashboard → Service → Settings
2. Check **Custom Domains** section
3. Status should show: ✅ **SSL Certificate Active**

**Verification:**
```bash
# Check SSL certificate
curl -vI https://api.tutormax.com

# Look for:
# SSL certificate verify ok
# TLSv1.3 or TLSv1.2
```

**Online Tools:**
- https://www.ssllabs.com/ssltest/
- https://www.digicert.com/help/

### Step 5: Update Application Configuration

Update environment variables to use custom domain:

**API Service (tutormax-api):**
```bash
# Update CORS_ORIGINS
CORS_ORIGINS=https://app.tutormax.com,https://tutormax.com

# Update OAuth redirect URL (if using OAuth)
OAUTH_REDIRECT_BASE_URL=https://api.tutormax.com
```

**Dashboard Service (tutormax-dashboard):**
```bash
# Update API URL
REACT_APP_API_URL=https://api.tutormax.com
```

**OAuth Provider Configuration:**

Update redirect URLs in OAuth provider dashboards:

- Google: https://console.cloud.google.com/apis/credentials
- Microsoft: https://portal.azure.com/

Authorized redirect URIs:
```
https://api.tutormax.com/auth/google/callback
https://api.tutormax.com/auth/microsoft/callback
```

### Example DNS Configuration

**Full DNS Setup for tutormax.com:**

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| A | `@` | `76.76.21.21` | Root domain → Dashboard |
| CNAME | `www` | `tutormax.com` | www redirect |
| CNAME | `api` | `tutormax-api.onrender.com` | API endpoint |
| CNAME | `app` | `tutormax-dashboard.onrender.com` | Dashboard (alternative) |
| TXT | `@` | `v=spf1 include:_spf.render.com ~all` | SPF record (optional) |

**URLs:**
- Dashboard: `https://tutormax.com` or `https://app.tutormax.com`
- API: `https://api.tutormax.com`

## SSL Certificate Management

### Automatic Certificate Renewal

Render automatically renews SSL certificates:

- Renewal occurs **30 days before expiration**
- No action required from you
- Email notification if renewal fails

### Certificate Monitoring

Monitor certificate expiration:

```bash
# Check certificate expiration
echo | openssl s_client -servername api.tutormax.com -connect api.tutormax.com:443 2>/dev/null | openssl x509 -noout -dates

# Output:
# notBefore=Jan 15 00:00:00 2024 GMT
# notAfter=Apr 15 23:59:59 2024 GMT
```

### Manual Certificate Upload

For enterprise plans, you can upload custom certificates:

1. Render Dashboard → Service → Settings
2. Custom Domains → Advanced
3. Upload certificate and private key

### Certificate Troubleshooting

**Issue: Certificate not provisioned**

1. Check DNS is correctly configured: `dig api.tutormax.com`
2. Ensure domain points to correct Render service
3. Wait up to 1 hour for propagation
4. Contact Render support if issue persists

**Issue: Mixed content warnings**

Ensure all resources load over HTTPS:

```javascript
// Frontend: Use relative URLs or HTTPS
// Bad
const API_URL = "http://api.tutormax.com"

// Good
const API_URL = "https://api.tutormax.com"
// Or use relative URL
const API_URL = "/api"
```

## Security Best Practices

### 1. Force HTTPS Redirect

Render automatically redirects HTTP → HTTPS.

**Verify:**
```bash
curl -I http://api.tutormax.com
# Should return: 301 Moved Permanently
# Location: https://api.tutormax.com
```

### 2. HSTS (HTTP Strict Transport Security)

Add HSTS header to enforce HTTPS:

```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # HSTS: Force HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.tutormax.com"
        )

        return response

app.add_middleware(SecurityHeadersMiddleware)
```

**For Static Site (in render.yaml):**

```yaml
- type: web
  name: tutormax-dashboard
  runtime: static
  headers:
    - path: /*
      name: Strict-Transport-Security
      value: max-age=31536000; includeSubDomains; preload
    - path: /*
      name: X-Frame-Options
      value: DENY
    - path: /*
      name: X-Content-Type-Options
      value: nosniff
    - path: /*
      name: Referrer-Policy
      value: strict-origin-when-cross-origin
```

### 3. CORS Configuration

Properly configure CORS for production:

```python
# src/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tutormax.com",
        "https://app.tutormax.com",
        "https://www.tutormax.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)
```

### 4. Cookie Security

Configure secure cookies:

```python
# src/api/auth.py
from fastapi import Response

def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,      # Prevent XSS
        secure=True,        # HTTPS only
        samesite="lax",     # CSRF protection
        max_age=1800,       # 30 minutes
        domain=".tutormax.com"  # All subdomains
    )
```

### 5. TLS Configuration

Render enforces strong TLS configuration:

- ✅ TLS 1.2 minimum
- ✅ TLS 1.3 supported
- ✅ Strong cipher suites only
- ✅ Perfect Forward Secrecy (PFS)

**Verify:**
```bash
nmap --script ssl-enum-ciphers -p 443 api.tutormax.com
```

### 6. Security Headers Test

Test security headers:

```bash
# Using curl
curl -I https://api.tutormax.com

# Using online tools
# https://securityheaders.com/
# https://observatory.mozilla.org/
```

### 7. Subdomain Security

If using multiple subdomains, consider:

- Use wildcard certificate (Enterprise plan)
- Configure HSTS with `includeSubDomains`
- Set proper CORS for each subdomain
- Use same-site cookies carefully

## Production Checklist

SSL/TLS and domain configuration checklist:

- [ ] Custom domain added to Render services
- [ ] DNS records configured (CNAME or A record)
- [ ] DNS propagation verified
- [ ] SSL certificates active (automatic via Render)
- [ ] HTTPS redirect working (HTTP → HTTPS)
- [ ] Environment variables updated with custom domain
- [ ] CORS configured with production domains
- [ ] OAuth redirect URLs updated
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] Mixed content warnings resolved
- [ ] Cookies configured as secure
- [ ] SSL Labs test passed (A or A+)
- [ ] All services accessible via HTTPS
- [ ] Certificate expiration monitoring set up

## Common Domain Configurations

### Single Domain (app + api subdomain)

**Domain:** `tutormax.com`

| Service | URL |
|---------|-----|
| Dashboard | `https://tutormax.com` |
| API | `https://api.tutormax.com` |

**DNS:**
```
@    A     76.76.21.21
api  CNAME tutormax-api.onrender.com
```

### Multiple Subdomains

**Domain:** `tutormax.com`

| Service | URL |
|---------|-----|
| Dashboard | `https://app.tutormax.com` |
| API | `https://api.tutormax.com` |
| Flower | `https://monitor.tutormax.com` |

**DNS:**
```
app     CNAME tutormax-dashboard.onrender.com
api     CNAME tutormax-api.onrender.com
monitor CNAME tutormax-flower.onrender.com
```

### www Redirect

Redirect `www.tutormax.com` → `tutormax.com`:

**DNS:**
```
@   A     76.76.21.21
www CNAME tutormax.com
```

**Or use Render redirect service:**
```yaml
- type: redirect
  name: www-redirect
  source: www.tutormax.com
  destination: https://tutormax.com
  type: permanent  # 301 redirect
```

---

**SSL/TLS and domain configuration complete!** 🔒

All traffic is now encrypted and secured with automatic SSL certificates.
