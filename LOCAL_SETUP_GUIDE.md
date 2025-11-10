# TutorMax Local Development Setup Guide

Complete step-by-step guide to run TutorMax on your local machine.

---

## Prerequisites

Before you start, ensure you have these installed:

- **Docker Desktop** (for PostgreSQL + Redis)
  - Download: https://www.docker.com/products/docker-desktop
  - Version: Any recent version (20.x+)
- **Python 3.11+**
  - Download: https://www.python.org/downloads/
  - Check: `python3 --version`
- **Node.js 18+ & pnpm**
  - Download Node.js: https://nodejs.org/
  - Install pnpm: `npm install -g pnpm`
  - Check: `node --version` and `pnpm --version`
- **Git** (for version control)
  - Download: https://git-scm.com/downloads

---

## Step 1: Start Infrastructure (PostgreSQL + Redis)

Open a terminal in the project root and start Docker services:

```bash
# Start PostgreSQL and Redis in detached mode
docker compose up -d

# Verify containers are running
docker ps

# You should see:
# - tutormax-postgres (port 5432)
# - tutormax-redis (port 6379)
# - tutormax-redis-commander (port 8081)
```

**Access Points:**
- PostgreSQL: `localhost:5432` (user: `tutormax`, password: `tutormax_dev`, db: `tutormax`)
- Redis: `localhost:6379`
- Redis Commander UI: http://localhost:8081

**Troubleshooting:**
```bash
# If ports are already in use, stop existing services:
docker compose down

# View logs if containers fail:
docker compose logs postgres
docker compose logs redis

# Reset everything (WARNING: deletes data):
docker compose down -v
docker compose up -d
```

---

## Step 2: Configure Environment Variables

Create your local `.env` file from the example:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file - update these minimal required fields:
# 1. SECRET_KEY - Generate a secure key
# 2. API Keys (optional, for AI features)
```

**Generate a secure SECRET_KEY:**

```bash
# On macOS/Linux:
openssl rand -hex 32

# On Windows (PowerShell):
-join ((48..57) + (97..102) | Get-Random -Count 64 | % {[char]$_})

# Copy the output and paste into .env:
# SECRET_KEY="paste-your-generated-key-here"
```

**Minimal `.env` configuration for local development:**

```env
# Database (matches docker-compose.yml)
POSTGRES_USER=tutormax
POSTGRES_PASSWORD=tutormax_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tutormax

# Redis
REDIS_URL="redis://localhost:6379/0"

# Application
DEBUG=True
API_PREFIX="/api"
HOST="0.0.0.0"
PORT=8000

# CORS (allow local frontend)
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

# Security (REQUIRED - generate with: openssl rand -hex 32)
SECRET_KEY="your-generated-secret-key-here"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: AI API Keys (only if using AI features)
# ANTHROPIC_API_KEY="sk-ant-api03-..."
# PERPLEXITY_API_KEY="pplx-..."
# OPENAI_API_KEY="sk-proj-..."
```

---

## Step 3: Set Up Python Environment

Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt

# Upgrade pip
pip install --upgrade pip

# Install all Python dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
pip list | grep celery
pip list | grep alembic
```

**Expected output:** You should see fastapi, celery, alembic, and ~50 other packages.

---

## Step 4: Run Database Migrations

Initialize the database schema using Alembic:

```bash
# Ensure Docker containers are running
docker ps | grep tutormax-postgres

# Run all migrations
alembic upgrade head

# You should see output like:
# INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial schema
# INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add authentication
# INFO  [alembic.runtime.migration] Running upgrade def456 -> ghi789, add student coppa fields
# INFO  [alembic.runtime.migration] Running upgrade ghi789 -> jkl012, add audit log indexes
```

**Verify migrations:**

```bash
# Connect to PostgreSQL
docker exec -it tutormax-postgres psql -U tutormax -d tutormax

# List all tables
\dt

# You should see tables like:
# - users
# - tutors
# - students
# - sessions
# - performance_metrics
# - churn_predictions
# - interventions
# - audit_logs
# - alembic_version

# Exit psql
\q
```

---

## Step 5: Start FastAPI Backend

In terminal #1 (keep this running):

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start the FastAPI server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
# INFO:     Started server process
# INFO:     Application startup complete.
```

**Test the API:**

Open your browser and go to:
- **API Health Check**: http://localhost:8000/health
  - Should return: `{"status": "healthy"}`
- **API Documentation**: http://localhost:8000/docs
  - Interactive Swagger UI with all endpoints
- **Alternative Docs**: http://localhost:8000/redoc
  - ReDoc UI (alternative documentation)

**API is now running! ✅**

---

## Step 6: Start Celery Workers (Optional for Development)

Celery workers handle background tasks like data generation, performance evaluation, and churn prediction.

**For basic development, you can SKIP this step.** Workers are only needed if you're testing:
- Data generation
- Performance calculations
- Churn predictions
- Model training

### Option A: Run All Workers (Full System)

```bash
# In terminal #2 (workers):
source venv/bin/activate
cd /Users/zeno/Projects/tutormax
./scripts/start_all_workers.sh

# This starts:
# - Data Generation Worker
# - Performance Evaluation Worker
# - Churn Prediction Worker
# - Model Training Worker
# - Celery Beat Scheduler
```

### Option B: Run Individual Workers (Development)

Open a new terminal for each worker:

```bash
# Terminal #2 - Data Generation Worker
source venv/bin/activate
celery -A src.workers.celery_app worker \
  --loglevel=info \
  --queues=data_generation \
  --concurrency=2

# Terminal #3 - Performance Evaluation Worker
source venv/bin/activate
celery -A src.workers.celery_app worker \
  --loglevel=info \
  --queues=evaluation \
  --concurrency=2

# Terminal #4 - Celery Beat (Scheduler - for periodic tasks)
source venv/bin/activate
celery -A src.workers.celery_app beat --loglevel=info
```

**Monitor Workers:**
- Check worker logs in their respective terminals
- Use Redis Commander: http://localhost:8081 to see queued tasks

---

## Step 7: Start React Frontend

In terminal #5 (or #2 if you skipped workers):

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
pnpm install

# Start development server
pnpm start

# You should see:
# Compiled successfully!
# webpack compiled with 1 warning
# You can now view tutormax-dashboard in the browser.
#
#   Local:            http://localhost:3000
#   On Your Network:  http://192.168.x.x:3000
```

**Access the Frontend:**
- Open http://localhost:3000 in your browser
- You should see the TutorMax dashboard login page

---

## Step 8: Create Test User & Login

### Create an Admin User

```bash
# In terminal #6 (or use Python):
source venv/bin/activate
python3

# Then in Python REPL:
```

```python
from src.database.database import SessionLocal
from src.database.models import User, UserRole
from passlib.context import CryptContext

# Create database session
db = SessionLocal()

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create admin user
admin = User(
    email="admin@tutormax.com",
    username="admin",
    hashed_password=pwd_context.hash("admin123"),
    role=UserRole.ADMIN,
    is_active=True,
    is_email_verified=True
)

db.add(admin)
db.commit()

print(f"Created admin user: {admin.email}")

# Create a test tutor
tutor = User(
    email="tutor@tutormax.com",
    username="tutor1",
    hashed_password=pwd_context.hash("tutor123"),
    role=UserRole.TUTOR,
    is_active=True,
    is_email_verified=True
)

db.add(tutor)
db.commit()

print(f"Created tutor user: {tutor.email}")

# Exit Python REPL
exit()
```

### Login to the Frontend

1. Go to http://localhost:3000/login
2. Login with:
   - **Email**: `admin@tutormax.com`
   - **Password**: `admin123`
3. You should be redirected to the dashboard!

---

## Step 9: Verify Everything Works

### ✅ Checklist

- [ ] Docker containers running: `docker ps`
- [ ] PostgreSQL accessible: `docker exec -it tutormax-postgres psql -U tutormax -d tutormax -c "SELECT 1;"`
- [ ] Redis accessible: `docker exec -it tutormax-redis redis-cli ping` (should return `PONG`)
- [ ] Backend running: http://localhost:8000/health returns `{"status": "healthy"}`
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Frontend running: http://localhost:3000 shows login page
- [ ] Can login with test credentials
- [ ] Dashboard loads after login

### 🧪 Test API Endpoints

```bash
# Test health check
curl http://localhost:8000/health

# Test authentication (get JWT token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@tutormax.com&password=admin123"

# You should get a JSON response with:
# {"access_token": "eyJ...", "token_type": "bearer"}
```

### 🔍 View Database Content

```bash
# Connect to PostgreSQL
docker exec -it tutormax-postgres psql -U tutormax -d tutormax

# List all users
SELECT id, email, username, role, is_active FROM users;

# Check migrations
SELECT * FROM alembic_version;

# Exit
\q
```

---

## Common Issues & Solutions

### Issue: Port 5432 already in use

**Solution:**
```bash
# Check what's using port 5432
lsof -i :5432  # macOS/Linux
netstat -ano | findstr :5432  # Windows

# Stop existing PostgreSQL (macOS with Homebrew):
brew services stop postgresql

# Or change port in compose.yml:
# ports:
#   - "5433:5432"  # Use port 5433 locally
# Then update .env:
# POSTGRES_PORT=5433
```

### Issue: Port 6379 already in use (Redis)

**Solution:**
```bash
# Stop existing Redis
brew services stop redis  # macOS

# Or change port in compose.yml to 6380
```

### Issue: Database connection refused

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs tutormax-postgres

# Restart containers
docker compose restart postgres
```

### Issue: `ModuleNotFoundError` when running backend

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Run from project root, not subdirectory
cd /Users/zeno/Projects/tutormax
uvicorn src.api.main:app --reload
```

### Issue: Frontend won't start - "ENOENT: no such file or directory"

**Solution:**
```bash
# Ensure you're in the frontend directory
cd frontend

# Clear cache and reinstall
rm -rf node_modules
rm pnpm-lock.yaml
pnpm install

# Restart
pnpm start
```

### Issue: CORS errors in browser console

**Solution:**
```bash
# Ensure backend CORS is configured for frontend URL
# In .env:
CORS_ORIGINS="http://localhost:3000"

# Restart backend after changing .env
```

---

## Daily Development Workflow

Once everything is set up, this is your daily workflow:

```bash
# 1. Start Docker (if not running)
docker compose up -d

# 2. Activate Python environment & start backend (Terminal #1)
source venv/bin/activate
uvicorn src.api.main:app --reload

# 3. Start frontend (Terminal #2)
cd frontend
pnpm start

# 4. (Optional) Start workers if needed (Terminal #3)
source venv/bin/activate
./scripts/start_all_workers.sh

# 5. Open browser
# http://localhost:3000 (Frontend)
# http://localhost:8000/docs (API Docs)
```

---

## What's Running? (Port Reference)

| Service | URL | Purpose |
|---------|-----|---------|
| **PostgreSQL** | `localhost:5432` | Database |
| **Redis** | `localhost:6379` | Cache & message broker |
| **Redis Commander** | http://localhost:8081 | Redis web UI |
| **FastAPI Backend** | http://localhost:8000 | REST API |
| **API Docs (Swagger)** | http://localhost:8000/docs | Interactive API docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | Alternative API docs |
| **React Frontend** | http://localhost:3000 | Web UI |

---

## Next Steps

- ✅ **Local development is ready!**
- 🚀 **Ready to deploy to production?** See `RENDER_SETUP_GUIDE.md`
- 🎨 **Want to migrate to Next.js?** See migration plan after Render setup
- 📚 **Learn the codebase:** See `MONOREPO_ARCHITECTURE_OVERVIEW.md`

---

## Stopping Services

```bash
# Stop frontend (in frontend terminal)
Ctrl+C

# Stop backend (in backend terminal)
Ctrl+C

# Stop workers (in worker terminals)
Ctrl+C
# Or: ./scripts/stop_all_workers.sh

# Stop Docker containers
docker compose down

# Stop Docker and delete volumes (WARNING: deletes all data)
docker compose down -v
```

---

## Summary: Terminal Layout for Full System

```
┌─────────────────────────────────────────────────────────┐
│ Terminal #1: Backend                                    │
│ $ source venv/bin/activate                              │
│ $ uvicorn src.api.main:app --reload                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Terminal #2: Frontend                                   │
│ $ cd frontend && pnpm start                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Terminal #3: Workers (Optional)                         │
│ $ source venv/bin/activate                              │
│ $ ./scripts/start_all_workers.sh                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Terminal #4: Docker Logs (Optional)                     │
│ $ docker compose logs -f                                │
└─────────────────────────────────────────────────────────┘
```

**Docker runs in background** - started once with `docker compose up -d`

---

**Questions or issues?** Check the troubleshooting section or open an issue in the project repository.
