# TutorMax Deployment Guide

This guide covers deploying TutorMax to Render.com as specified in the PRD architecture section.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring](#monitoring)
- [Backup & Disaster Recovery](#backup--disaster-recovery)
- [Troubleshooting](#troubleshooting)

## Overview

TutorMax is deployed on Render.com with the following architecture:

- **FastAPI Backend**: Web service (tutormax-api)
- **React Frontend**: Static site (tutormax-dashboard)
- **PostgreSQL**: Database (tutormax-postgres)
- **Redis**: Cache & message broker (tutormax-redis)
- **5 Celery Workers**: Background task processors
  - Data Generation Worker
  - Performance Evaluation Worker
  - Churn Prediction Worker
  - Model Training Worker
  - Celery Beat Scheduler

**Total Monthly Cost**: ~$56/month (MVP deployment)

## Prerequisites

1. GitHub account with repository containing TutorMax code
2. Render.com account (free tier available)
3. Domain name (optional, for custom domains)

## Initial Setup

### Step 1: Connect Repository to Render

1. Log in to [Render.com](https://render.com)
2. Click **New** → **Blueprint**
3. Connect your GitHub repository
4. Select the repository containing `render.yaml`
5. Click **Apply** to create all services

Render will automatically create:
- All 7+ services defined in render.yaml
- PostgreSQL database with credentials
- Redis instance
- Service-to-service networking
- SSL/TLS certificates

### Step 2: Configure Sensitive Environment Variables

Some environment variables require manual configuration via the Render Dashboard:

**For tutormax-api service:**

1. Navigate to **tutormax-api** service
2. Go to **Environment** tab
3. Add the following secret values:

```bash
# OAuth Configuration (if using OAuth)
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
MICROSOFT_CLIENT_ID=<your-microsoft-client-id>
MICROSOFT_CLIENT_SECRET=<your-microsoft-client-secret>

# Optional: Custom OAuth provider
CUSTOM_OAUTH_CLIENT_ID=<custom-oauth-client-id>
CUSTOM_OAUTH_CLIENT_SECRET=<custom-oauth-client-secret>
OAUTH_REDIRECT_BASE_URL=https://tutormax-api.onrender.com
```

4. Click **Save Changes**

### Step 3: Update CORS Origins

Update the `CORS_ORIGINS` environment variable in **tutormax-api**:

```bash
CORS_ORIGINS=https://tutormax-dashboard.onrender.com,https://www.yourdomain.com
```

### Step 4: Verify Deployment

1. Check that all services show "Live" status in Render Dashboard
2. Visit your API health endpoint: `https://tutormax-api.onrender.com/health`
3. Visit your frontend: `https://tutormax-dashboard.onrender.com`

## Environment Variables

### Environment Variable Management Strategy

**Render manages environment variables through:**

1. **Blueprint (render.yaml)**: Non-sensitive defaults
2. **Render Dashboard**: Sensitive values (API keys, secrets)
3. **Service-to-service references**: Database and Redis URLs (auto-populated)

**Best Practices:**

- ✅ Store all sensitive values (OAuth secrets, API keys) in Render Dashboard
- ✅ Use `fromDatabase` and `fromService` for automatic credential injection
- ✅ Use `generateValue: true` for auto-generated secrets (e.g., SECRET_KEY)
- ❌ Never commit sensitive values to git
- ❌ Never hardcode credentials in render.yaml

### Environment Variable Reference

Complete list of environment variables is documented in `.env.example`.

**Critical Production Variables:**

| Variable | Source | Required | Notes |
|----------|--------|----------|-------|
| POSTGRES_* | Auto (fromDatabase) | Yes | Auto-populated from tutormax-postgres |
| REDIS_URL | Auto (fromService) | Yes | Auto-populated from tutormax-redis |
| SECRET_KEY | Auto-generated | Yes | JWT signing key (auto-generated) |
| GOOGLE_CLIENT_ID | Manual | Optional | For Google OAuth |
| GOOGLE_CLIENT_SECRET | Manual | Optional | For Google OAuth |
| CORS_ORIGINS | Manual | Yes | Frontend URL(s) |

## Database Migrations

### Migration Strategy

TutorMax uses **Alembic** for database schema migrations.

**Automatic Migration on Deployment:**

Database migrations run automatically on every deployment via the API service's `startCommand`:

```bash
alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

This ensures:
- Migrations run before the API starts
- Schema is always up-to-date
- Zero-downtime deployments (for additive changes)

### Creating New Migrations

**Locally:**

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new table"

# Review the generated migration in alembic/versions/

# Test locally
alembic upgrade head

# Commit to git
git add alembic/versions/*.py
git commit -m "Add migration: Add new table"
git push
```

**On Render:**

Migrations will run automatically on next deployment.

### Manual Migration Execution

If needed, you can run migrations manually via Render Shell:

1. Go to **tutormax-api** service in Render Dashboard
2. Click **Shell** tab
3. Run:

```bash
alembic upgrade head  # Apply all pending migrations
alembic current       # Show current migration version
alembic history       # Show migration history
```

### Migration Best Practices

- ✅ Always review auto-generated migrations before committing
- ✅ Test migrations locally before deploying
- ✅ Make migrations backward-compatible when possible
- ✅ Use two-phase migrations for breaking changes:
  1. Phase 1: Add new columns/tables (additive)
  2. Phase 2: Remove old columns/tables (after code update)
- ❌ Never edit existing migrations (create new ones instead)

### Rollback Strategy

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## CI/CD Pipeline

### GitHub Actions Workflow

TutorMax uses GitHub Actions for continuous integration and automated deployments.

**Workflow Location:** `.github/workflows/deploy.yml`

**Trigger Events:**
- Push to `main` branch
- Pull request to `main` branch
- Manual workflow dispatch

**Pipeline Stages:**

1. **Lint & Format Check** (on all branches)
   - Black formatting check
   - Flake8 linting
   - MyPy type checking

2. **Test** (on all branches)
   - Unit tests with pytest
   - Integration tests
   - Code coverage report

3. **Build Validation** (on all branches)
   - Python dependency installation
   - Frontend build (React)

4. **Deploy** (only on `main` branch)
   - Automatic deployment to Render
   - Triggered via Render's deploy hook

### Enabling Auto-Deploy

**Option 1: Render Auto-Deploy (Recommended)**

1. In Render Dashboard, go to each service
2. Under **Settings** → **Build & Deploy**
3. Enable **Auto-Deploy**: Yes
4. Branch: `main`

Changes pushed to `main` will automatically trigger deployment.

**Option 2: GitHub Actions Deploy Hook**

1. In Render Dashboard, go to **tutormax-api**
2. Navigate to **Settings** → **Deploy Hook**
3. Copy the deploy hook URL
4. Add to GitHub repository secrets:
   - Name: `RENDER_DEPLOY_HOOK_API`
   - Value: `<deploy-hook-url>`
5. Repeat for all services

**GitHub Actions will trigger Render deployment** after tests pass.

### Manual Deployment

Trigger deployment manually:

```bash
# Via Render Dashboard
1. Navigate to service
2. Click "Manual Deploy" → "Deploy latest commit"

# Via API (using deploy hook)
curl -X POST <deploy-hook-url>
```

## Monitoring

### Service Health Monitoring

**Built-in Render Monitoring:**

- CPU usage
- Memory usage
- Request rate
- Response time
- Error rate

Access via: Render Dashboard → Service → Metrics

### Celery Worker Monitoring

**Option 1: Flower (Celery Monitoring Tool)**

Flower is included in requirements but not deployed by default.

To enable:

```yaml
# Add to render.yaml
- type: web
  name: tutormax-flower
  runtime: python
  plan: starter
  buildCommand: pip install -r requirements.txt
  startCommand: celery -A src.workers.celery_app flower --port=$PORT
  envVars:
    # Same as workers
```

Access at: `https://tutormax-flower.onrender.com`

**Option 2: Worker Monitoring API**

Built-in monitoring endpoints in tutormax-api:

- `GET /api/workers/health` - Worker health status
- `GET /api/workers/dashboard` - Worker dashboard
- `GET /api/workers/stats` - Worker statistics

### Application Logging

**View Logs:**

1. Render Dashboard → Service → Logs
2. Live tail: Click "Live" button
3. Search/filter logs by timestamp or text

**Log Retention:**
- Free tier: 7 days
- Paid plans: 30+ days

**Log Levels:**

Configure via `LOG_LEVEL` environment variable:
- `DEBUG`: Development (verbose)
- `INFO`: Production (default)
- `WARNING`: Warnings only
- `ERROR`: Errors only

### External Monitoring (Optional)

For production, consider integrating:

- **Sentry**: Error tracking and monitoring
- **Datadog**: Full-stack monitoring
- **New Relic**: APM and monitoring
- **LogDNA/Papertrail**: Log aggregation

Add API keys via environment variables.

## Backup & Disaster Recovery

### Database Backups

**Automatic Backups (Render PostgreSQL):**

- **Free tier**: Manual backups only
- **Paid plans (Starter+)**:
  - Daily automatic backups
  - 7-day retention
  - One-click restore

**Manual Backup:**

```bash
# Via Render Dashboard
1. Go to tutormax-postgres database
2. Click "Backups" tab
3. Click "Create Backup"

# Via pg_dump (local)
pg_dump -h <postgres-host> \
  -U <postgres-user> \
  -d tutormax \
  -F c \
  -f backup_$(date +%Y%m%d_%H%M%S).dump
```

**Restore from Backup:**

```bash
# Via Render Dashboard
1. Go to Backups tab
2. Click "Restore" on desired backup

# Via pg_restore (local)
pg_restore -h <postgres-host> \
  -U <postgres-user> \
  -d tutormax \
  -c \
  backup_20240101_120000.dump
```

### Redis Backups

Redis data is **ephemeral** by design (cache and task queue).

**Important:**
- Celery Beat schedule is stored in Redis
- Consider persisting critical data to PostgreSQL

**Manual Redis Backup (if needed):**

```bash
# Via redis-cli
redis-cli -h <redis-host> --rdb backup.rdb
```

### Disaster Recovery Plan

**Scenario 1: Database Corruption**

1. Identify last known good backup
2. Restore from Render Dashboard backup
3. Verify data integrity
4. Resume services

**Scenario 2: Service Outage**

1. Check Render status page: https://status.render.com
2. Review service logs for errors
3. Restart affected services via Dashboard
4. If persistent, rollback to previous deployment

**Scenario 3: Code Deployment Failure**

1. Check deployment logs in Render Dashboard
2. If migration failed, rollback migration:
   ```bash
   alembic downgrade -1
   ```
3. Revert to previous Git commit
4. Deploy previous version

**Scenario 4: Complete Data Loss**

1. Restore PostgreSQL from latest backup
2. Rebuild Redis (data is ephemeral)
3. Re-run any pending Celery tasks
4. Verify system health

### Backup Best Practices

- ✅ Enable daily automatic backups (Paid plan)
- ✅ Perform manual backup before major migrations
- ✅ Test restore procedure quarterly
- ✅ Store critical data in PostgreSQL (not Redis)
- ✅ Monitor backup success/failure notifications
- ❌ Never rely on Redis for persistent data

### Data Export (for migration)

```bash
# Export all data
pg_dump -h <host> -U <user> -d tutormax -F c -f full_backup.dump

# Export specific tables
pg_dump -h <host> -U <user> -d tutormax -t tutors -t students -F c -f partial_backup.dump

# Export as SQL
pg_dump -h <host> -U <user> -d tutormax -f backup.sql
```

## Troubleshooting

### Common Issues

**Issue: Service fails to start**

1. Check logs in Render Dashboard
2. Verify all environment variables are set
3. Check database connectivity
4. Verify build command succeeded

**Issue: Database migration fails**

```bash
# Check migration status
alembic current

# View pending migrations
alembic history

# Manual migration via Shell
alembic upgrade head
```

**Issue: Worker not processing tasks**

1. Check worker logs
2. Verify Redis connection
3. Check Celery Flower dashboard
4. Restart worker service

**Issue: CORS errors on frontend**

1. Verify `CORS_ORIGINS` includes frontend URL
2. Check for trailing slashes
3. Ensure HTTPS (not HTTP) in production

**Issue: OAuth authentication fails**

1. Verify OAuth credentials in environment variables
2. Check `OAUTH_REDIRECT_BASE_URL` matches API URL
3. Verify callback URLs in OAuth provider settings

### Health Check Endpoints

**API Health:**
```bash
curl https://tutormax-api.onrender.com/health
```

**Database Connectivity:**
```bash
curl https://tutormax-api.onrender.com/api/health/database
```

**Redis Connectivity:**
```bash
curl https://tutormax-api.onrender.com/api/health/redis
```

**Worker Status:**
```bash
curl https://tutormax-api.onrender.com/api/workers/health
```

### Support

- **Render Support**: https://render.com/docs
- **Render Status**: https://status.render.com
- **TutorMax Issues**: GitHub Issues

## Production Checklist

Before going live:

- [ ] All services show "Live" in Render Dashboard
- [ ] Database migrations applied successfully
- [ ] Environment variables configured (especially OAuth secrets)
- [ ] CORS origins updated with production URLs
- [ ] SSL/TLS certificates provisioned (automatic)
- [ ] Custom domain configured (if applicable)
- [ ] Backup strategy enabled
- [ ] Monitoring configured (Flower or external)
- [ ] Log level set to INFO or WARNING
- [ ] Health check endpoints responding
- [ ] Workers processing tasks successfully
- [ ] Frontend can communicate with API
- [ ] OAuth login working (if enabled)
- [ ] Test user accounts created
- [ ] Documentation updated with production URLs

## Scaling

### Vertical Scaling (Increase Resources)

Upgrade service plans in Render Dashboard:

- **Starter** → **Standard** (1GB RAM, better CPU)
- **Standard** → **Pro** (4GB RAM, dedicated CPU)

### Horizontal Scaling (Add More Workers)

Add additional worker instances:

```yaml
# In render.yaml, duplicate worker config
- type: worker
  name: tutormax-worker-evaluation-2
  # ... same config as tutormax-worker-evaluation
```

Or enable **Auto-Scaling** (Pro plans):
- Min instances: 1
- Max instances: 5
- Scale based on CPU/memory

### Database Scaling

- Upgrade PostgreSQL plan for more storage/connections
- Consider read replicas (Enterprise plans)
- Optimize queries and add indexes

---

**Deployment configured successfully!** 🚀

Next steps:
1. Push `render.yaml` to GitHub
2. Connect repository to Render
3. Configure sensitive environment variables
4. Verify all services are live
