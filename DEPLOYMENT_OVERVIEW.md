# TutorMax Deployment Overview

Quick reference guide for local development and production deployment.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TUTORMAX PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (React 18)          Backend (FastAPI)            │
│  ┌──────────────┐             ┌──────────────┐            │
│  │ Dashboard    │◄───────────►│ REST API     │            │
│  │ Tutor Portal │   HTTP/WS   │ 8 Routers    │            │
│  │ User Mgmt    │             │ JWT Auth     │            │
│  └──────────────┘             └──────────────┘            │
│                                      ▲                      │
│                                      │                      │
│                          ┌───────────┴──────────┐          │
│                          │                      │          │
│                  ┌───────▼──────┐      ┌───────▼──────┐   │
│                  │ PostgreSQL   │      │    Redis     │   │
│                  │   Database   │      │ Cache/Broker │   │
│                  └──────────────┘      └──────┬───────┘   │
│                                                │           │
│                                      ┌─────────▼────────┐  │
│                                      │ Celery Workers   │  │
│                                      │ • Data Gen       │  │
│                                      │ • Evaluation     │  │
│                                      │ • Prediction     │  │
│                                      │ • Training       │  │
│                                      │ • Beat (Schedule)│  │
│                                      └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start: Choose Your Path

### Path A: Local Development First (Recommended)

**Best for:** Testing features, development, learning the codebase

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Set up environment
cp .env.example .env
# Edit .env - set SECRET_KEY

# 3. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Start backend
uvicorn src.api.main:app --reload

# 6. Start frontend (new terminal)
cd frontend && pnpm install && pnpm dev

# 7. Open http://localhost:3000
```

📖 **Full guide:** `LOCAL_SETUP_GUIDE.md`

---

### Path B: Production Deployment (Render.com)

**Best for:** Going live, customer testing, production use

```bash
# 1. Push to GitHub
git add . && git commit -m "Deploy to production"
git push origin main

# 2. Connect Render to GitHub
# → https://dashboard.render.com/
# → New → Blueprint
# → Select tutormax repo

# 3. Wait for deployment (~10 minutes)

# 4. Configure secrets
# → Set SECRET_KEY
# → Set OAuth credentials (optional)
# → Set SMTP (optional)

# 5. Create admin user
# → Use Render Shell

# 6. Open production URL
# → https://tutormax-dashboard.onrender.com
```

📖 **Full guide:** `RENDER_SETUP_GUIDE.md`

---

## 📊 Environment Comparison

| Aspect | Local Development | Production (Render) |
|--------|-------------------|---------------------|
| **Database** | Docker PostgreSQL | Managed PostgreSQL ($7/mo) |
| **Redis** | Docker Redis | Managed Redis ($7/mo) |
| **Backend** | localhost:8000 | tutormax-api.onrender.com ($7/mo) |
| **Frontend** | localhost:3000 | tutormax-dashboard.onrender.com (FREE) |
| **Workers** | Optional (manual) | 5 workers ($35/mo) |
| **SSL/HTTPS** | No (HTTP only) | Yes (auto-provisioned) |
| **Backups** | Manual | Automatic (daily) |
| **Monitoring** | Manual logs | Built-in metrics + alerts |
| **Auto-deploy** | No | Yes (git push → deploy) |
| **Cost** | FREE (your machine) | ~$56/month |
| **Setup time** | 15 minutes | 15 minutes |

---

## 🗂️ Project Structure

```
tutormax/
├── src/
│   ├── api/                    # FastAPI backend
│   │   ├── main.py            # App entry point
│   │   ├── config.py          # Configuration
│   │   ├── models.py          # Pydantic schemas
│   │   ├── auth/              # Authentication
│   │   ├── security/          # Security features
│   │   └── *_router.py        # API routers (8 total)
│   ├── database/
│   │   ├── models.py          # SQLAlchemy models
│   │   └── database.py        # DB connection
│   ├── workers/               # Celery workers
│   │   ├── celery_app.py      # Celery config
│   │   ├── data_generator.py
│   │   ├── performance_evaluator.py
│   │   ├── churn_predictor.py
│   │   └── model_trainer.py
│   └── evaluation/            # Performance calculation
│
├── frontend/                   # Next.js 16 (migrated)
│   ├── app/                   # App Router pages
│   ├── components/            # shadcn/ui + Kibo UI
│   │   ├── ui/                # 19 shadcn components
│   │   ├── kibo-ui/           # 7 Kibo components
│   │   ├── dashboard/
│   │   ├── tutor-portal/
│   │   ├── admin/
│   │   └── feedback/
│   ├── lib/                   # Utils, API, types
│   ├── contexts/              # Auth context
│   └── package.json           # pnpm
│
├── alembic/                   # Database migrations
│   └── versions/              # 4 migrations
│
├── scripts/                   # Helper scripts
│   ├── start_all_workers.sh
│   └── run_daily_aggregation.py
│
├── docs/                      # Documentation
│
├── .env.example               # Environment template (122 vars)
├── compose.yml                # Local infrastructure (Docker Compose V2)
├── render.yaml                # Production deployment (443 lines)
├── requirements.txt           # Python dependencies
│
└── GUIDES:
    ├── LOCAL_SETUP_GUIDE.md         ← Start here for local dev
    ├── RENDER_SETUP_GUIDE.md        ← Start here for production
    ├── DEPLOYMENT_OVERVIEW.md       ← This file
    ├── MONOREPO_ARCHITECTURE_OVERVIEW.md
    └── MONOREPO_QUICK_REFERENCE.txt
```

---

## 🔑 Key Configuration Files

### `.env` (Local Development)

**Required variables:**
```env
# Database (matches compose.yml)
POSTGRES_USER=tutormax
POSTGRES_PASSWORD=tutormax_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tutormax

# Redis
REDIS_URL="redis://localhost:6379/0"

# Security (GENERATE THIS!)
SECRET_KEY="generate-with-openssl-rand-hex-32"

# Application
DEBUG=True
CORS_ORIGINS="http://localhost:3000"
```

**Total variables:** 122 (see `.env.example`)

---

### `render.yaml` (Production)

**Auto-configures:**
- 2 databases (PostgreSQL, Redis)
- 1 web service (FastAPI)
- 1 static site (React)
- 5 worker services (Celery)

**Total services:** 8
**Total lines:** 443
**Estimated cost:** $56/month

✅ Push to GitHub → Render auto-deploys everything

---

## 🛠️ Daily Development Workflow

### Local Development

```bash
# Morning routine:
docker compose up -d                    # Start databases
source venv/bin/activate                # Activate Python
uvicorn src.api.main:app --reload      # Start backend (Terminal 1)
cd frontend && pnpm dev                # Start frontend (Terminal 2)

# Work on features...

# Evening:
Ctrl+C (both terminals)                # Stop servers
docker compose down                     # Stop databases (optional)
```

### Production Deployment

```bash
# Make changes locally
git add .
git commit -m "feat: add new feature"
git push origin main

# Render auto-deploys in ~3-5 minutes
# Monitor: https://dashboard.render.com/
```

---

## 🧪 Testing Your Setup

### Local Development

```bash
# 1. Test backend
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# 2. Test API docs
open http://localhost:8000/docs

# 3. Test frontend
open http://localhost:3000

# 4. Test login
# Email: admin@tutormax.com
# Password: admin123 (from setup script)
```

### Production

```bash
# 1. Test backend
curl https://tutormax-api.onrender.com/health
# Expected: {"status":"healthy"}

# 2. Test frontend
open https://tutormax-dashboard.onrender.com

# 3. Test login
# Use credentials you created in production
```

---

## 📈 Monitoring & Observability

### Local Development

**Tools:**
- Backend logs: Terminal output
- Redis Commander: http://localhost:8081
- PostgreSQL: `docker exec -it tutormax-postgres psql -U tutormax`
- API Docs: http://localhost:8000/docs

**Debugging:**
```bash
# View all logs
docker compose logs -f

# View specific service
docker logs tutormax-postgres -f

# Check database
docker exec -it tutormax-postgres psql -U tutormax -d tutormax -c "SELECT COUNT(*) FROM users;"
```

### Production (Render)

**Built-in features:**
- Real-time logs (Dashboard → Service → Logs)
- Metrics (CPU, Memory, Requests)
- Email alerts (Deploys, Crashes)
- Health checks (automatic)
- Auto-restart (on failure)

**Access:**
- Dashboard: https://dashboard.render.com/
- Metrics: Service → Metrics tab
- Logs: Service → Logs tab

---

## 🔐 Security Features

### Already Implemented

✅ **Authentication:**
- JWT tokens (HS256)
- OAuth2 flow (Google, Microsoft)
- Role-based access control (RBAC)
- Password hashing (bcrypt)

✅ **Protection:**
- Rate limiting (Redis-backed)
- CSRF protection
- XSS prevention
- SQL injection prevention
- Input sanitization

✅ **Headers:**
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options
- X-Content-Type-Options

✅ **Monitoring:**
- Audit logging (all requests)
- Failed login tracking
- Account lockout (5 attempts)

---

## 💰 Cost Analysis

### Development (Local)

**Total:** $0/month
- Run on your machine
- Docker containers (free)
- No cloud costs

**Pros:**
- Free
- Fast iteration
- Offline capable

**Cons:**
- Requires your machine running
- No public access
- Manual backups

---

### Production (Render)

**Total:** $56/month

| Service | Cost | Specs |
|---------|------|-------|
| PostgreSQL | $7 | 256MB RAM, 1GB storage |
| Redis | $7 | 25MB RAM |
| Backend API | $7 | 512MB RAM |
| Frontend | $0 | Static hosting (free) |
| Workers (5x) | $35 | 512MB RAM each |

**Included:**
- SSL certificates (free)
- Daily backups (free)
- DDoS protection (free)
- Monitoring (free)
- Auto-scaling (free)

**Scaling costs:**
- Standard plan: $25/service (2GB RAM)
- Pro plan: $85/service (8GB RAM)
- Add workers: $7 each

---

## 🚨 Common Issues & Solutions

### Issue: `Port 5432 already in use`

```bash
# Check what's using the port
lsof -i :5432  # macOS/Linux

# Stop existing PostgreSQL
brew services stop postgresql

# Or change port in compose.yml
```

### Issue: `ModuleNotFoundError`

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Frontend CORS error

```bash
# Check backend CORS config in .env:
CORS_ORIGINS="http://localhost:3000"

# Restart backend after changing .env
```

### Issue: Render deployment fails

```bash
# Check deployment logs in Render Dashboard
# Common causes:
# 1. Missing environment variable
# 2. Migration failed
# 3. Build error

# Fix and push again:
git commit --amend
git push origin main --force
```

---

## 📚 Next Steps

### After Local Setup ✅

1. **Test all features locally**
   - Login, dashboard, user management
   - API endpoints
   - WebSocket real-time updates

2. **Deploy to production**
   - Follow `RENDER_SETUP_GUIDE.md`
   - ~15 minutes setup time

3. **Configure production secrets**
   - SECRET_KEY
   - OAuth credentials
   - SMTP for emails

---

### After Production Deployment ✅

1. **Frontend migration complete** ✅
   - Migrated from React 18 to Next.js 16
   - All 11 components built with Kibo UI + shadcn
   - Production build verified

2. **Set up CI/CD**
   - GitHub Actions (already configured)
   - Automated tests
   - Staging environment

3. **Add monitoring**
   - Set up alerts
   - Monitor error rates
   - Track performance

4. **Scale as needed**
   - Upgrade plans
   - Add more workers
   - Configure auto-scaling

---

## 🆘 Getting Help

**Documentation:**
- Local setup: `LOCAL_SETUP_GUIDE.md`
- Production: `RENDER_SETUP_GUIDE.md`
- Architecture: `MONOREPO_ARCHITECTURE_OVERVIEW.md`
- Quick reference: `MONOREPO_QUICK_REFERENCE.txt`

**External resources:**
- FastAPI docs: https://fastapi.tiangolo.com/
- Render docs: https://render.com/docs
- Celery docs: https://docs.celeryq.dev/

**Support:**
- Render support: https://render.com/support
- FastAPI community: https://github.com/tiangolo/fastapi/discussions

---

## ✅ Deployment Checklist

### Local Development

- [ ] Docker Desktop installed
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ & pnpm installed
- [ ] `docker-compose up -d` successful
- [ ] `.env` file created from `.env.example`
- [ ] `SECRET_KEY` generated and set
- [ ] Virtual environment created & activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Migrations run (`alembic upgrade head`)
- [ ] Backend starts successfully
- [ ] Frontend starts successfully
- [ ] Can login at http://localhost:3000
- [ ] Dashboard loads without errors

### Production (Render)

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] GitHub connected to Render
- [ ] Blueprint created from `render.yaml`
- [ ] All 8 services deployed successfully
- [ ] Production `SECRET_KEY` configured
- [ ] OAuth credentials configured (optional)
- [ ] SMTP configured (optional)
- [ ] Admin user created
- [ ] Can login at production URL
- [ ] Health check returns `{"status":"healthy"}`
- [ ] Auto-deploy enabled
- [ ] Monitoring alerts configured
- [ ] Database backups verified
- [ ] Custom domain configured (optional)

---

**You're ready to develop and deploy! 🚀**

Questions? Check the troubleshooting sections in the detailed guides.
