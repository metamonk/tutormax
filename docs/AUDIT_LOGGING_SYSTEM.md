# Audit Logging System

## Overview

The TutorMax Audit Logging System provides comprehensive security and compliance tracking for all sensitive operations in the application. It automatically logs authentication events, data access, data modifications, and administrative actions.

## Features

### 1. Automatic Logging
- **Middleware-based**: Automatically captures all sensitive requests via FastAPI middleware
- **Asynchronous**: Non-blocking logging to minimize performance impact
- **Comprehensive**: Logs authentication, data access, modifications, and admin operations

### 2. Searchable Interface
- **Powerful filters**: Search by user, date range, action type, resource, IP address
- **Pagination**: Efficient handling of large log datasets
- **Export**: CSV and JSON export for external analysis
- **Admin-only access**: Protected by RBAC (admin role required)

### 3. Compliance Reports
- **User Activity Reports**: Track specific user actions over time
- **Failed Login Reports**: Identify potential security threats
- **Data Access Reports**: Audit who accessed what data and when
- **Statistics Dashboard**: Overview of system activity

### 4. Performance Optimization
- **Indexed queries**: Composite indexes for common search patterns
- **Async operations**: Non-blocking database writes
- **Retention policy**: Automated cleanup of old logs

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                   Audit Logging System                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Audit Service│  │  Middleware  │  │  API Router  │ │
│  │              │  │              │  │              │ │
│  │ - Log events │  │ - Auto-log   │  │ - Search     │ │
│  │ - Search     │  │ - Filter     │  │ - Reports    │ │
│  │ - Reports    │  │ - Extract    │  │ - Export     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                            │                            │
│                   ┌────────▼────────┐                  │
│                   │  AuditLog Model │                  │
│                   │  (PostgreSQL)   │                  │
│                   └─────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### Files

**Backend:**
- `src/api/audit_service.py` - Core audit logging service
- `src/api/audit_middleware.py` - FastAPI middleware for automatic logging
- `src/api/audit_router.py` - API endpoints for audit log access
- `src/database/models.py` - AuditLog database model
- `alembic/versions/20251109_0001_add_audit_log_indexes.py` - Performance indexes

**Frontend:**
- `frontend/src/components/AuditLogViewer.tsx` - Audit log search interface
- `frontend/src/components/ComplianceReports.tsx` - Compliance reports dashboard

**Tests:**
- `tests/test_audit_logging.py` - Comprehensive test suite

## Usage

### Automatic Logging (via Middleware)

The middleware automatically logs:

1. **Authentication Events**
   - Login attempts (success/failure)
   - Logout
   - Registration
   - Password resets
   - Email verification

2. **Data Access** (GET requests to sensitive paths)
   - Viewing tutor profiles
   - Accessing student data
   - Viewing performance metrics
   - Accessing predictions and interventions

3. **Data Modifications** (POST, PUT, PATCH, DELETE)
   - Creating records
   - Updating records
   - Deleting records
   - Bulk operations

### Manual Logging (via Audit Service)

For custom logging needs:

```python
from src.api.audit_service import AuditService
from sqlalchemy.ext.asyncio import AsyncSession

# Log authentication event
await AuditService.log_authentication(
    session=session,
    action=AuditService.ACTION_LOGIN,
    user_id=user.id,
    email=user.email,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0",
    success=True,
)

# Log data access
await AuditService.log_data_access(
    session=session,
    user_id=current_user.id,
    resource_type=AuditService.RESOURCE_TUTOR,
    resource_id=tutor_id,
    action=AuditService.ACTION_VIEW,
    ip_address=request.client.host,
    user_agent=request.headers.get("User-Agent"),
    request_path=request.url.path,
    metadata={"fields_viewed": ["name", "email"]},
)

# Log data modification
await AuditService.log_data_modification(
    session=session,
    user_id=current_user.id,
    action=AuditService.ACTION_UPDATE,
    resource_type=AuditService.RESOURCE_TUTOR,
    resource_id=tutor_id,
    ip_address=request.client.host,
    user_agent=request.headers.get("User-Agent"),
    request_method="PUT",
    request_path=request.url.path,
    success=True,
    metadata={"changed_fields": ["email", "subjects"]},
)
```

### Searching Audit Logs

```python
# Search by user
logs, total = await AuditService.search_logs(
    session=session,
    user_id=123,
    limit=100,
    offset=0,
)

# Search by date range
logs, total = await AuditService.search_logs(
    session=session,
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
)

# Search by action type
logs, total = await AuditService.search_logs(
    session=session,
    action=AuditService.ACTION_LOGIN_FAILED,
)

# Complex search
logs, total = await AuditService.search_logs(
    session=session,
    user_id=123,
    action=AuditService.ACTION_UPDATE,
    resource_type=AuditService.RESOURCE_TUTOR,
    start_date=datetime.utcnow() - timedelta(days=30),
    success=True,
)
```

### Generating Reports

```python
# User activity report
activity = await AuditService.get_user_activity(
    session=session,
    user_id=123,
    days=30,
)

# Failed login report
failed_logins = await AuditService.get_failed_logins(
    session=session,
    hours=24,
    ip_address="192.168.1.100",  # Optional
)

# Resource access history
history = await AuditService.get_resource_access_history(
    session=session,
    resource_type=AuditService.RESOURCE_TUTOR,
    resource_id="tutor-123",
    days=90,
)

# Action statistics
stats = await AuditService.get_action_statistics(
    session=session,
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow(),
)
```

## API Endpoints

All endpoints require **Admin role** authentication.

### Search Audit Logs
```
GET /api/audit/logs
Query Parameters:
  - user_id: Filter by user ID
  - action: Filter by action type
  - resource_type: Filter by resource type
  - resource_id: Filter by resource ID
  - success: Filter by success status (true/false)
  - start_date: Start date (ISO format)
  - end_date: End date (ISO format)
  - ip_address: Filter by IP address
  - search_query: Text search in logs
  - limit: Max results (default: 100, max: 1000)
  - offset: Pagination offset (default: 0)
```

### Get Specific Log
```
GET /api/audit/logs/{log_id}
```

### Export to CSV
```
GET /api/audit/logs/export/csv
Query Parameters: Same as search (excluding limit/offset)
```

### Export to JSON
```
GET /api/audit/logs/export/json
Query Parameters: Same as search (excluding limit/offset)
```

### Get Statistics
```
GET /api/audit/statistics
Query Parameters:
  - start_date: Start date (ISO format)
  - end_date: End date (ISO format)
```

### User Activity Report
```
GET /api/audit/reports/user-activity/{user_id}
Query Parameters:
  - days: Number of days of history (default: 30, max: 365)
```

### Failed Logins Report
```
GET /api/audit/reports/failed-logins
Query Parameters:
  - hours: Number of hours to look back (default: 24, max: 720)
```

### Data Access Report
```
GET /api/audit/reports/data-access/{resource_type}/{resource_id}
Query Parameters:
  - days: Number of days of history (default: 90, max: 365)
```

### Cleanup Old Logs
```
DELETE /api/audit/cleanup
Query Parameters:
  - retention_days: Days to retain logs (default: 365, min: 30, max: 3650)
  - confirm: Must be true to proceed
```

## Action Types

### Authentication
- `login` - Successful login
- `logout` - User logout
- `login_failed` - Failed login attempt
- `password_reset` - Password reset request
- `password_change` - Password changed
- `register` - New user registration
- `verify_email` - Email verification

### Data Access
- `view` - View single resource
- `list` - List resources
- `export` - Export data
- `search` - Search operation

### Data Modification
- `create` - Create new resource
- `update` - Update existing resource
- `delete` - Delete resource
- `bulk_update` - Bulk update operation
- `bulk_delete` - Bulk delete operation

### Administrative
- `role_change` - User role changed
- `user_enable` - User account enabled
- `user_disable` - User account disabled
- `intervention_create` - Intervention created
- `intervention_update` - Intervention updated

## Resource Types

- `user` - User accounts
- `tutor` - Tutor profiles
- `student` - Student profiles
- `session` - Tutoring sessions
- `feedback` - Student feedback
- `performance_metric` - Performance metrics
- `churn_prediction` - Churn predictions
- `intervention` - Interventions
- `notification` - Notifications
- `manager_note` - Manager notes

## Database Schema

The `audit_logs` table includes:

```sql
CREATE TABLE audit_logs (
    log_id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER,  -- References users.id
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(50),
    ip_address VARCHAR(45),  -- IPv6 compatible
    user_agent VARCHAR(500),
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    status_code INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB,  -- Additional context
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Indexes for performance
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_resource_timestamp (resource_type, resource_id, timestamp),
    INDEX idx_action_timestamp (action, timestamp),
    INDEX idx_ip_timestamp (ip_address, timestamp),
    INDEX idx_success_timestamp (success, timestamp)
);
```

## Performance Considerations

### Indexes
Composite indexes are created for common query patterns:
- `(user_id, timestamp)` - User activity queries
- `(resource_type, resource_id, timestamp)` - Resource access history
- `(action, timestamp)` - Action-based filtering
- `(ip_address, timestamp)` - IP-based security analysis
- `(success, timestamp)` - Failed operation tracking

### Async Operations
- All audit logging is performed asynchronously
- Middleware logging doesn't block request processing
- Database writes are non-blocking

### Retention Policy
- Default retention: 365 days
- Automated cleanup via scheduled task
- Configurable retention period (30-3650 days)

## Compliance

### GDPR Compliance
- Tracks all personal data access
- Provides audit trail for data subject requests
- Supports right to access (show who accessed user data)
- Retention policy for data deletion

### SOC 2 / ISO 27001
- Comprehensive audit trail
- Failed authentication tracking
- Administrative action logging
- Data modification tracking

### HIPAA (if applicable)
- Access logs for protected health information
- User activity tracking
- Security incident detection

## Security Features

### Threat Detection
- Failed login attempt tracking
- Unusual IP address detection
- Brute force attack identification
- Data exfiltration detection (excessive exports)

### Access Control
- Admin-only access to audit logs
- RBAC enforcement
- Audit log viewing is itself audited

### Data Integrity
- Immutable log records
- Timestamped entries
- Complete request context

## Frontend Components

### AuditLogViewer
React component providing:
- Searchable table interface
- Advanced filtering options
- Expandable row details
- CSV/JSON export buttons
- Pagination

### ComplianceReports
Dashboard showing:
- Audit statistics
- Failed login reports
- User activity reports
- Visual analytics

## Monitoring and Alerts

### Key Metrics to Monitor
- Failed login rate
- Admin action frequency
- Data export volumes
- Unusual access patterns
- Log growth rate

### Recommended Alerts
- 5+ failed logins from same IP in 5 minutes
- 10+ failed logins for same email in 1 hour
- Suspicious data access patterns
- Excessive data exports
- After-hours administrative actions

## Best Practices

### For Developers
1. **Don't log sensitive data** in metadata (passwords, tokens, etc.)
2. **Use appropriate action types** for consistency
3. **Include context** in metadata for debugging
4. **Test audit logging** in development
5. **Review logs regularly** during development

### For Administrators
1. **Regular review** of failed login attempts
2. **Monitor user activity** for anomalies
3. **Export logs** for long-term archival
4. **Set up alerts** for critical events
5. **Enforce retention policy** to manage storage

### For Compliance
1. **Document audit procedures** in compliance docs
2. **Regular audit reviews** (weekly/monthly)
3. **Incident response** based on audit logs
4. **Access reviews** using audit data
5. **Retention compliance** with regulations

## Troubleshooting

### Audit Logs Not Being Created
1. Check middleware is installed in `main.py`
2. Verify database connection
3. Check for errors in application logs
4. Ensure async session maker is configured

### Performance Issues
1. Check index usage with `EXPLAIN ANALYZE`
2. Implement retention policy to reduce table size
3. Consider partitioning by date for very large tables
4. Use pagination in API queries

### Missing Logs
1. Verify endpoint is in `SENSITIVE_PATHS` or uses modifying HTTP method
2. Check if path is in `EXCLUDED_PATHS`
3. Review middleware configuration
4. Check for exceptions in logging code

## Future Enhancements

Potential improvements:
- Real-time alerting system
- Machine learning anomaly detection
- Advanced visualization dashboard
- Log streaming to external SIEM
- Audit log encryption at rest
- Blockchain-based tamper detection

## Maintenance

### Daily Tasks
- Monitor failed login attempts
- Review critical actions

### Weekly Tasks
- Review user activity reports
- Check for anomalies
- Verify log retention

### Monthly Tasks
- Generate compliance reports
- Audit log cleanup (if manual)
- Performance review
- Security incident analysis

## Support

For issues or questions:
1. Check application logs for errors
2. Review this documentation
3. Check tests for usage examples
4. Contact system administrator
