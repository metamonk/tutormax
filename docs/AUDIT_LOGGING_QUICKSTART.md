# Audit Logging System - Quick Start Guide

## 5-Minute Setup

### 1. Run Database Migration (if needed)

```bash
# Navigate to project directory
cd /Users/zeno/Projects/tutormax

# Run migration to add performance indexes
alembic upgrade head

# Verify migration
alembic current
```

### 2. Verify System is Running

The audit logging middleware is already integrated into `main.py`. Just restart your application:

```bash
# If using uvicorn directly
uvicorn src.api.main:app --reload

# If using systemd
sudo systemctl restart tutormax

# If using docker
docker-compose restart api
```

### 3. Test Audit Logging

```bash
# Make a test request (this will be logged)
curl -X POST http://localhost:8000/api/tutors \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"tutor_id":"test-123","name":"Test Tutor","email":"test@example.com"}'

# View audit logs (requires admin token)
curl http://localhost:8000/api/audit/logs?limit=10 \
     -H "Authorization: Bearer ADMIN_TOKEN"
```

### 4. Access Frontend (Optional)

The audit log viewer is available at:
- **Audit Logs**: `http://localhost:3000/admin/audit-logs`
- **Compliance Reports**: `http://localhost:3000/admin/compliance-reports`

*Note: You need to add routes to your React app's router to access these components.*

### 5. Set Up Automated Cleanup (Optional)

```bash
# Option A: Systemd Timer (Linux)
sudo cp scripts/audit-cleanup.{service,timer} /etc/systemd/system/
sudo systemctl enable audit-cleanup.timer
sudo systemctl start audit-cleanup.timer

# Option B: Cron Job
crontab -e
# Add: 0 2 * * * cd /opt/tutormax && python scripts/cleanup_audit_logs.py
```

---

## What's Being Logged?

### Automatically Logged Events

✅ **Authentication**
- Login attempts (success/failure)
- Logout
- Registration
- Password resets

✅ **Data Access** (GET requests)
- Viewing tutor/student profiles
- Accessing performance metrics
- Viewing predictions
- Accessing interventions

✅ **Data Modifications** (POST/PUT/DELETE)
- Creating records
- Updating records
- Deleting records

✅ **Administrative Actions**
- User management
- Role changes
- System configuration

### Excluded (Not Logged)
- Health checks (`/health`)
- Static files (`/static/`)
- Documentation (`/docs`, `/redoc`)
- Root endpoint (`/`)

---

## Common Use Cases

### 1. View Recent Activity

```bash
# Get last 50 audit logs
curl http://localhost:8000/api/audit/logs?limit=50 \
     -H "Authorization: Bearer ADMIN_TOKEN"
```

### 2. Find Failed Login Attempts

```bash
# Get failed logins in last 24 hours
curl http://localhost:8000/api/audit/reports/failed-logins?hours=24 \
     -H "Authorization: Bearer ADMIN_TOKEN"
```

### 3. Track User Activity

```bash
# Get activity for specific user
curl http://localhost:8000/api/audit/reports/user-activity/123?days=30 \
     -H "Authorization: Bearer ADMIN_TOKEN"
```

### 4. Export Audit Logs

```bash
# Export to CSV
curl http://localhost:8000/api/audit/logs/export/csv?start_date=2025-01-01 \
     -H "Authorization: Bearer ADMIN_TOKEN" \
     -o audit_logs.csv

# Export to JSON
curl http://localhost:8000/api/audit/logs/export/json?start_date=2025-01-01 \
     -H "Authorization: Bearer ADMIN_TOKEN" \
     -o audit_logs.json
```

### 5. Get Statistics

```bash
# Get audit statistics for last 30 days
curl http://localhost:8000/api/audit/statistics \
     -H "Authorization: Bearer ADMIN_TOKEN"
```

### 6. Manual Cleanup

```bash
# Preview what would be deleted (dry run)
python scripts/cleanup_audit_logs.py --retention-days 365 --dry-run

# View statistics
python scripts/cleanup_audit_logs.py --stats

# Actually delete old logs
python scripts/cleanup_audit_logs.py --retention-days 365
```

---

## Integrating Frontend Components

### Add to Your React Router

```tsx
// In your App.tsx or router configuration
import AuditLogViewer from './components/AuditLogViewer';
import ComplianceReports from './components/ComplianceReports';

// Add routes (admin only)
{
  path: '/admin/audit-logs',
  element: <ProtectedRoute requiredRole="admin"><AuditLogViewer /></ProtectedRoute>
},
{
  path: '/admin/compliance-reports',
  element: <ProtectedRoute requiredRole="admin"><ComplianceReports /></ProtectedRoute>
}
```

### Add Navigation Links

```tsx
// In your admin navigation menu
<MenuItem onClick={() => navigate('/admin/audit-logs')}>
  <ListItemIcon><Security /></ListItemIcon>
  <ListItemText>Audit Logs</ListItemText>
</MenuItem>
<MenuItem onClick={() => navigate('/admin/compliance-reports')}>
  <ListItemIcon><Assessment /></ListItemIcon>
  <ListItemText>Compliance Reports</ListItemText>
</MenuItem>
```

---

## Manual Logging in Code

### Log Custom Events

```python
from src.api.audit_service import AuditService
from src.database.database import get_async_session

async def my_custom_function(user_id: int):
    async with async_session_maker() as session:
        # Log custom action
        await AuditService.log(
            session=session,
            action="custom_action",
            user_id=user_id,
            resource_type="custom_resource",
            resource_id="resource-123",
            success=True,
            metadata={"custom_field": "custom_value"}
        )
```

### Log in FastAPI Endpoints

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.database import get_async_session
from src.api.audit_service import AuditService

@app.post("/api/custom-endpoint")
async def custom_endpoint(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    # Your business logic here
    result = do_something()

    # Log the action
    await AuditService.log_data_modification(
        session=session,
        user_id=current_user.id,
        action=AuditService.ACTION_CREATE,
        resource_type="custom_resource",
        resource_id=result.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        request_method="POST",
        request_path="/api/custom-endpoint",
        success=True,
        metadata={"details": "additional context"}
    )

    return result
```

---

## Troubleshooting

### Audit Logs Not Being Created

**Check middleware is active:**
```python
# In src/api/main.py, verify this line exists:
app.add_middleware(AuditLoggingMiddleware, log_all_requests=False)
```

**Check database:**
```bash
# Connect to PostgreSQL
psql -U tutormax -d tutormax

# Check if audit_logs table exists
\dt audit_logs

# Check if any logs exist
SELECT COUNT(*) FROM audit_logs;
```

### Can't Access Audit Log Endpoints

**Verify admin role:**
```bash
# Check your user has admin role
psql -U tutormax -d tutormax -c "SELECT id, email, roles FROM users WHERE email='your@email.com';"
```

**Test authentication:**
```bash
# Verify your JWT token is valid
curl http://localhost:8000/api/audit/logs \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -v
```

### Frontend Components Not Working

**Install dependencies:**
```bash
cd frontend
npm install @mui/material @mui/icons-material date-fns
```

**Check routes are added:**
Ensure the components are imported and routed in your App.tsx

---

## Performance Tips

1. **Use pagination** for large result sets (default: 100, max: 1000)
2. **Filter by date** to reduce query size
3. **Run cleanup regularly** to keep table manageable
4. **Monitor growth** with `--stats` command
5. **Use indexes** - migration creates optimal indexes

---

## Security Best Practices

1. **Admin-only access**: Only admins can view audit logs
2. **Don't log sensitive data**: Passwords, tokens never logged
3. **Regular reviews**: Check failed logins weekly
4. **Set up alerts**: For unusual patterns
5. **Backup logs**: Before running cleanup

---

## Next Steps

1. ✅ Verify system is working (make test requests)
2. ✅ Set up automated cleanup
3. ✅ Add frontend routes (optional)
4. ✅ Configure alerting (optional)
5. ✅ Review compliance requirements
6. ✅ Document retention policy
7. ✅ Train team on audit log access

---

## Need Help?

- **Documentation**: See `docs/AUDIT_LOGGING_SYSTEM.md`
- **Tests**: Run `pytest tests/test_audit_logging.py -v`
- **Implementation**: See `TASK_14.5_AUDIT_LOGGING_IMPLEMENTATION.md`
- **Issues**: Check application logs for errors

---

## Quick Reference

### API Endpoints (Admin Only)
- `GET /api/audit/logs` - Search audit logs
- `GET /api/audit/logs/{log_id}` - Get specific log
- `GET /api/audit/logs/export/csv` - Export CSV
- `GET /api/audit/logs/export/json` - Export JSON
- `GET /api/audit/statistics` - Get statistics
- `GET /api/audit/reports/user-activity/{user_id}` - User activity
- `GET /api/audit/reports/failed-logins` - Failed logins
- `GET /api/audit/reports/data-access/{type}/{id}` - Data access
- `DELETE /api/audit/cleanup` - Cleanup old logs

### Action Types
- `login`, `logout`, `login_failed`
- `register`, `password_reset`
- `view`, `list`, `search`, `export`
- `create`, `update`, `delete`

### Resource Types
- `user`, `tutor`, `student`, `session`
- `feedback`, `performance_metric`
- `churn_prediction`, `intervention`

---

**That's it! The audit logging system is ready to use.**
