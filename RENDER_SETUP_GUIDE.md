# TutorMax Production Deployment Guide (Render.com)

Complete step-by-step guide to deploy TutorMax to production on Render.com.

---

## Overview

This guide will deploy:
- ✅ PostgreSQL database (managed, $7/month)
- ✅ Redis cache (managed, $7/month)
- ✅ FastAPI backend (web service, $7/month)
- ✅ React frontend (static site, FREE)
- ✅ 5 Celery workers ($35/month total)

**Total Cost:** ~$56/month
**Setup Time:** ~15 minutes
**Auto-Deploy:** Enabled (pushes to `main` branch auto-deploy)

---

## Prerequisites

Before you start, ensure you have:

- ✅ Render.com account (https://render.com/signup)
- ✅ GitHub account with this repo pushed
- ✅ Local development tested and working
- ✅ Git installed
- ⚠️ **Credit card** (required for paid Render plans, even with free trial)

---

## Step 1: Push Code to GitHub

If you haven't already, push your code to GitHub:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - ready for production deployment"

# Create GitHub repository (go to https://github.com/new)
# Name: tutormax
# Visibility: Private (recommended) or Public

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/tutormax.git

# Push to GitHub
git push -u origin main
```

**Verify:** Go to your GitHub repository and ensure all files are pushed.

---

## Step 2: Connect Render to GitHub

1. **Sign in to Render**: https://dashboard.render.com/
2. **Connect GitHub account:**
   - Click your profile (top right) → Settings
   - Click "GitHub" under "Connected Accounts"
   - Click "Connect GitHub Account"
   - Authorize Render to access your repositories
   - Select "All repositories" or "Only select repositories" (choose `tutormax`)
   - Click "Install & Authorize"

**Verify:** You should see "GitHub" with a green checkmark in your Render settings.

---

## Step 3: Create New Blueprint from `render.yaml`

Render will automatically detect your `render.yaml` file and create all services at once.

1. **Go to Render Dashboard:** https://dashboard.render.com/
2. **Click "New" (top right) → "Blueprint"**
3. **Select your repository:**
   - Find `tutormax` in the list
   - Click "Connect"
4. **Configure Blueprint:**
   - **Blueprint Name:** `tutormax-production`
   - **Branch:** `main` (or your default branch)
   - Click "Apply"

Render will now:
- Parse your `render.yaml` file
- Create 8 services simultaneously:
  - PostgreSQL database
  - Redis cache
  - FastAPI web service
  - React static site
  - 5 Celery worker services

**This will take 5-10 minutes.** ☕

---

## Step 4: Monitor Initial Deployment

### Watch Services Deploy

1. **Dashboard:** https://dashboard.render.com/
2. You should see 8 services deploying:
   - ⏳ `tutormax-postgres` (Database)
   - ⏳ `tutormax-redis` (Cache)
   - ⏳ `tutormax-api` (Backend)
   - ⏳ `tutormax-dashboard` (Frontend)
   - ⏳ `tutormax-worker-data-generation`
   - ⏳ `tutormax-worker-evaluation`
   - ⏳ `tutormax-worker-prediction`
   - ⏳ `tutormax-worker-training`
   - ⏳ `tutormax-worker-beat`

### Expected Deployment Order

1. **Databases first** (2-3 minutes):
   - PostgreSQL provisions
   - Redis provisions
2. **Web services** (3-5 minutes):
   - Backend builds dependencies
   - Backend runs migrations (`alembic upgrade head`)
   - Backend starts
   - Frontend builds React app
   - Frontend deploys
3. **Workers** (3-5 minutes):
   - All workers build dependencies
   - Workers connect to Redis/PostgreSQL
   - Workers start listening to queues

---

## Step 5: Configure Production Environment Secrets

Some environment variables need to be manually configured (sensitive values).

### 5.1: Generate Production SECRET_KEY

```bash
# Generate a secure random secret key
openssl rand -hex 32

# Copy the output (64-character hex string)
```

### 5.2: Add SECRET_KEY to Backend Service

1. **Go to:** https://dashboard.render.com/
2. **Click:** `tutormax-api` service
3. **Click:** "Environment" tab (left sidebar)
4. **Find:** `SECRET_KEY` variable
5. **Click:** The value field
6. **Paste:** Your generated secret key
7. **Click:** "Save Changes"

⚠️ **This will trigger a redeployment** (1-2 minutes)

### 5.3: Configure OAuth (Optional)

If you want Google/Microsoft login:

#### Google OAuth Setup

1. **Go to:** https://console.cloud.google.com/
2. **Create a new project:** "TutorMax Production"
3. **Enable Google OAuth API:**
   - APIs & Services → Library
   - Search "Google+ API"
   - Click "Enable"
4. **Create OAuth credentials:**
   - APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: "Web application"
   - Name: "TutorMax Production"
   - Authorized redirect URIs:
     - `https://tutormax-api.onrender.com/api/auth/google/callback`
   - Click "Create"
5. **Copy Client ID & Secret**

#### Add Google OAuth to Render

1. **Go to:** `tutormax-api` service → Environment
2. **Add new environment variable:**
   - Key: `GOOGLE_CLIENT_ID`
   - Value: `your-google-client-id.apps.googleusercontent.com`
3. **Add another:**
   - Key: `GOOGLE_CLIENT_SECRET`
   - Value: `your-google-client-secret`
4. **Click:** "Save Changes"

Repeat similar steps for Microsoft OAuth if needed.

### 5.4: Configure Email (Optional)

For student feedback invitations:

1. **Get SMTP credentials** (e.g., Gmail App Password)
2. **Add to Render:**
   - `SMTP_HOST`: `smtp.gmail.com`
   - `SMTP_PORT`: `587`
   - `SMTP_USER`: `your-email@gmail.com`
   - `SMTP_PASSWORD`: `your-app-password`
   - `SMTP_FROM_EMAIL`: `your-email@gmail.com`
3. **Save Changes**

---

## Step 6: Verify Production Deployment

### 6.1: Check All Services Are Live

Go to https://dashboard.render.com/ and verify:

| Service | Status | URL |
|---------|--------|-----|
| **tutormax-postgres** | ✅ Available | Internal only |
| **tutormax-redis** | ✅ Available | Internal only |
| **tutormax-api** | ✅ Live | https://tutormax-api.onrender.com |
| **tutormax-dashboard** | ✅ Live | https://tutormax-dashboard.onrender.com |
| **tutormax-worker-data-generation** | ✅ Running | N/A (background) |
| **tutormax-worker-evaluation** | ✅ Running | N/A (background) |
| **tutormax-worker-prediction** | ✅ Running | N/A (background) |
| **tutormax-worker-training** | ✅ Running | N/A (background) |
| **tutormax-worker-beat** | ✅ Running | N/A (background) |

### 6.2: Test Backend API

```bash
# Test health check
curl https://tutormax-api.onrender.com/health

# Expected response:
# {"status":"healthy"}

# Test API docs
# Open in browser: https://tutormax-api.onrender.com/docs
```

### 6.3: Test Frontend

1. **Open:** https://tutormax-dashboard.onrender.com
2. **Expected:** Login page loads
3. **Verify:** No console errors (F12 → Console)

### 6.4: Create Production Admin User

**Option A: Use API endpoint (if registration is enabled)**

```bash
# Create admin user via API
curl -X POST https://tutormax-api.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com",
    "username": "admin",
    "password": "SecureP@ssw0rd123",
    "role": "admin"
  }'
```

**Option B: Use Render Shell (direct database access)**

1. **Go to:** `tutormax-api` service
2. **Click:** "Shell" tab (left sidebar)
3. **Run:**

```python
from src.database.database import SessionLocal
from src.database.models import User, UserRole
from passlib.context import CryptContext

db = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create admin
admin = User(
    email="admin@yourcompany.com",
    username="admin",
    hashed_password=pwd_context.hash("YourSecurePassword123"),
    role=UserRole.ADMIN,
    is_active=True,
    is_email_verified=True
)

db.add(admin)
db.commit()

print(f"✅ Created admin: {admin.email}")
exit()
```

### 6.5: Test Login

1. **Go to:** https://tutormax-dashboard.onrender.com/login
2. **Login with:**
   - Email: `admin@yourcompany.com`
   - Password: `YourSecurePassword123`
3. **Expected:** Redirected to dashboard
4. **Verify:** Dashboard loads without errors

---

## Step 7: Configure Custom Domain (Optional)

### 7.1: Add Custom Domain to Frontend

1. **Go to:** `tutormax-dashboard` service → Settings
2. **Click:** "Custom Domain" section
3. **Add domain:** `app.yourdomain.com`
4. **Follow Render's instructions** to add DNS records:
   - **CNAME record:** `app` → `tutormax-dashboard.onrender.com`
5. **Wait for SSL certificate** (auto-provisioned, 2-5 minutes)

### 7.2: Add Custom Domain to Backend

1. **Go to:** `tutormax-api` service → Settings
2. **Add domain:** `api.yourdomain.com`
3. **CNAME record:** `api` → `tutormax-api.onrender.com`

### 7.3: Update CORS Settings

After adding custom domains, update CORS:

1. **Go to:** `tutormax-api` service → Environment
2. **Find:** `CORS_ORIGINS`
3. **Update to:**
   ```
   https://app.yourdomain.com,https://tutormax-dashboard.onrender.com
   ```
4. **Save Changes**

### 7.4: Update Frontend API URL

1. **Go to:** `tutormax-dashboard` service → Environment
2. **Find:** `REACT_APP_API_URL`
3. **Update to:** `https://api.yourdomain.com`
4. **Save Changes**

---

## Step 8: Enable Auto-Deploy from GitHub

Auto-deploy is already enabled via Blueprint! Every push to `main` will:

1. Trigger a new build
2. Run tests (if configured)
3. Deploy automatically
4. Roll back if deployment fails

### Configure Auto-Deploy Settings

1. **Go to:** Each service → Settings
2. **Verify:** "Auto-Deploy" is enabled
3. **Branch:** `main`
4. **Build Command:** (defined in `render.yaml`)

### Test Auto-Deploy

```bash
# Make a small change
echo "# Production deployment test" >> README.md

# Commit and push
git add README.md
git commit -m "test: verify auto-deploy"
git push origin main

# Watch deployment in Render Dashboard
# You should see all affected services redeploy
```

---

## Step 9: Set Up Monitoring & Alerts

### 9.1: Enable Render Monitoring

Render provides built-in monitoring:

1. **Go to:** Any service → "Metrics" tab
2. **View:**
   - CPU usage
   - Memory usage
   - Request count
   - Response time
   - Error rate

### 9.2: Set Up Email Alerts

1. **Go to:** Service → Settings → Notifications
2. **Enable:**
   - ✅ Deploy started
   - ✅ Deploy succeeded
   - ✅ Deploy failed
   - ✅ Service crashed
   - ✅ High memory usage
3. **Add email:** your-email@example.com
4. **Save**

### 9.3: View Logs

```bash
# View live logs for any service:
# Go to: Service → Logs tab

# Or use Render CLI:
npm install -g @render/cli
render login
render logs tutormax-api --tail
```

### 9.4: Set Up Health Checks

Health checks are already configured in `render.yaml`:

```yaml
healthCheckPath: /health  # Backend API
```

Render will:
- Check `/health` endpoint every 30 seconds
- Restart service if unhealthy for 2 minutes
- Send alert if service is down

---

## Step 10: Database Backups

### 10.1: Automatic Backups (Render)

Render automatically backs up PostgreSQL:
- **Frequency:** Daily (Starter plan)
- **Retention:** 7 days
- **Location:** Render's infrastructure
- **Cost:** Included in database plan

### 10.2: Manual Backup

```bash
# Install Render CLI
npm install -g @render/cli
render login

# Create manual backup
render pg:backup create tutormax-postgres

# List backups
render pg:backup list tutormax-postgres

# Restore from backup
render pg:backup restore tutormax-postgres <backup-id>
```

### 10.3: Export Database (Manual)

1. **Go to:** `tutormax-api` service → Shell
2. **Run:**

```bash
# Export entire database
pg_dump $DATABASE_URL > backup.sql

# Download backup.sql via Render dashboard
```

---

## Production URLs Reference

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | https://tutormax-dashboard.onrender.com | Main web UI |
| **Backend API** | https://tutormax-api.onrender.com | REST API |
| **API Docs** | https://tutormax-api.onrender.com/docs | Swagger docs |
| **Health Check** | https://tutormax-api.onrender.com/health | API health |

---

## Cost Breakdown

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| PostgreSQL | Starter | $7/mo | 256MB RAM, 1GB storage |
| Redis | Starter | $7/mo | 25MB RAM |
| Backend API | Starter | $7/mo | 512MB RAM |
| Frontend | Static | FREE | Included in free tier |
| Worker: Data Gen | Starter | $7/mo | 512MB RAM |
| Worker: Evaluation | Starter | $7/mo | 512MB RAM |
| Worker: Prediction | Starter | $7/mo | 512MB RAM |
| Worker: Training | Starter | $7/mo | 512MB RAM |
| Worker: Beat | Starter | $7/mo | 512MB RAM |
| **TOTAL** | | **$56/mo** | + bandwidth overages if any |

### Scaling Options

**If you need more resources:**

- **Standard plan** ($25/mo per service): 2GB RAM, faster CPU
- **Pro plan** ($85/mo per service): 8GB RAM, dedicated CPU
- **Add more workers:** Duplicate worker services for parallel processing

---

## Troubleshooting Production Issues

### Issue: Backend deployment fails

**Solution:**
```bash
# Check deployment logs
# Go to: tutormax-api → Events tab

# Common issues:
# 1. Migration failed → Fix migration, push again
# 2. Dependency error → Update requirements.txt
# 3. Startup error → Check environment variables
```

### Issue: Frontend shows "API connection error"

**Solution:**
```bash
# Check CORS configuration
# Ensure CORS_ORIGINS includes frontend URL

# Check backend is running
curl https://tutormax-api.onrender.com/health

# Check frontend API URL
# Go to: tutormax-dashboard → Environment
# Verify REACT_APP_API_URL is correct
```

### Issue: Workers not processing tasks

**Solution:**
```bash
# Check worker logs
# Go to: tutormax-worker-* → Logs tab

# Verify Redis connection
# Go to: tutormax-redis → Details
# Ensure status is "Available"

# Restart workers
# Go to: Worker service → Manual Deploy → "Clear build cache & deploy"
```

### Issue: Database connection errors

**Solution:**
```bash
# Check PostgreSQL status
# Go to: tutormax-postgres → Details

# Verify environment variables
# Go to: tutormax-api → Environment
# Check POSTGRES_* variables are set

# Restart backend
# Manual Deploy → Deploy
```

### Issue: SSL certificate not provisioning

**Solution:**
```bash
# Ensure DNS is configured correctly
# Check CNAME record: dig app.yourdomain.com

# Wait 5-10 minutes for propagation

# Force SSL renewal
# Go to: Service → Settings → Custom Domain
# Click "Refresh SSL"
```

---

## Security Checklist for Production

Before going live:

- [ ] Changed `SECRET_KEY` from default
- [ ] Set `DEBUG=False` (already in render.yaml)
- [ ] Configured HTTPS only (automatic with Render)
- [ ] Enabled rate limiting (already configured)
- [ ] Set up audit logging (already configured)
- [ ] Configured CORS with specific origins (not `*`)
- [ ] Set strong admin password
- [ ] Enabled account lockout after failed logins
- [ ] Configured SMTP for password resets
- [ ] Set up monitoring alerts
- [ ] Tested database backups
- [ ] Reviewed security headers (already configured)
- [ ] Enabled CSRF protection (already configured)

---

## Daily Production Operations

### View Logs

```bash
# Backend logs
# Dashboard → tutormax-api → Logs

# Worker logs
# Dashboard → tutormax-worker-* → Logs

# Filter by level
# Use search: "ERROR" or "WARNING"
```

### Monitor Performance

```bash
# Check metrics
# Dashboard → tutormax-api → Metrics

# Monitor:
# - Response time (should be < 500ms)
# - Error rate (should be < 1%)
# - CPU usage (should be < 80%)
# - Memory usage (should be < 80%)
```

### Scale Services

```bash
# Increase worker concurrency
# Go to: Worker → Environment
# Add: CELERY_CONCURRENCY=4
# Save and redeploy

# Upgrade plan
# Go to: Service → Settings
# Change plan: Starter → Standard
```

---

## Next Steps After Production Deployment

✅ **Production is live!**

Now you can:
1. **Migrate frontend to Next.js** (see migration plan)
2. **Add more features** (auto-deploys with git push)
3. **Monitor usage** and scale as needed
4. **Set up staging environment** (duplicate blueprint with different name)
5. **Configure CI/CD tests** (GitHub Actions already configured)

---

## Support & Resources

- **Render Docs:** https://render.com/docs
- **Render Status:** https://status.render.com/
- **Support:** https://render.com/support
- **Community:** https://community.render.com/

---

**Questions or issues?** Check the troubleshooting section or contact Render support.
