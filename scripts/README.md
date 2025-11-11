# Scripts Directory

This directory contains operational, testing, and utility scripts organized by purpose.

## Directory Structure

### 🚀 Deployment (`deployment/`)
Production deployment and worker management scripts:

**Database Management:**
- `backup_database.sh` - Database backup script
- `restore_database.sh` - Database restoration script

**Worker Management:**
- `start_all_workers.sh` - Start all Celery workers and Beat scheduler
- `stop_all_workers.sh` - Stop all running workers
- `run_celery_beat.sh` - Run Celery Beat scheduler
- `run_performance_worker.sh` - Run performance evaluation worker
- `run_metrics_worker.py` - Run metrics calculation worker
- `run_daily_aggregation.py` - Run daily aggregation worker
- `run_validation_worker.py` - Run validation worker

**Performance:**
- `deploy_performance_optimizations.sh` - Deploy performance optimizations

### 🧪 Testing (`testing/`)
Security, compliance, and load testing scripts:

**Security Testing:**
- `security_audit.py` - Comprehensive security audit
- `security_vulnerability_scanner.py` - Vulnerability scanning
- `penetration_testing.py` - Penetration testing suite

**Compliance Testing:**
- `verify_ferpa_compliance.py` - FERPA compliance verification

**Load Testing:**
- `locustfile.py` - Locust load testing configuration
- `test_analytics_endpoints.sh` - Analytics API load testing

**Integration Testing:**
- `test_enrichment_pipeline.py` - Test data enrichment pipeline
- `test_data_generator_worker.py` - Test data generation worker

### 🔒 Security (`security/`)
Security and data management scripts:

**Audit Management:**
- `cleanup_audit_logs.py` - Audit log cleanup and archival
- `audit_cleanup_cron.txt` - Cron job example for audit cleanup
- `audit-cleanup.service` - Systemd service for audit cleanup
- `audit-cleanup.timer` - Systemd timer for audit cleanup

**Data Retention:**
- `run_data_retention.py` - Data retention policy execution
- `data_retention_cron.txt` - Cron job examples
- `data-retention.service` - Systemd service for data retention
- `data-retention.timer` - Systemd timer for data retention
- `data-retention-archival.service` - Archival service
- `data-retention-archival.timer` - Archival timer

### 🎯 Demos (`demos/`)
Demo and utility scripts for development:

**Database Utilities:**
- `check_database_data.py` - Check database data integrity
- `create_test_user.py` - Create test users for development

**System Demos:**
- `demo_api_ingestion.py` - Demo API data ingestion
- `demo_data_generation.py` - Demo data generation
- `demo_performance_calculator.py` - Demo performance calculations
- `demo_daily_aggregation.py` - Demo daily aggregation
- `demo_validation.py` - Demo validation system

**Reporting:**
- `performance_report.py` - Generate performance reports
- `list_routes.py` - List all API routes

**Test Data:**
- `generate_feedback_for_sessions.py` - Generate test feedback data

### 📊 Load Tests (`load_tests/`)
Load testing scripts and configurations:
- `run_baseline_test.sh` - Run baseline performance test
- `run_normal_load_test.sh` - Run normal load test
- `run_stress_test.sh` - Run stress test

### 🗄️ Postgres (`postgres/`)
PostgreSQL configuration and initialization:
- `primary-init.sh` - Primary database initialization

## Usage Examples

### Starting Workers

```bash
# Start all workers in production
./scripts/deployment/start_all_workers.sh

# Stop all workers
./scripts/deployment/stop_all_workers.sh

# Start individual worker
./scripts/deployment/run_performance_worker.sh
```

### Database Management

```bash
# Backup database
./scripts/deployment/backup_database.sh

# Restore database
./scripts/deployment/restore_database.sh backups/backup-file.dump
```

### Running Tests

```bash
# Security audit
python scripts/testing/security_audit.py

# FERPA compliance check
python scripts/testing/verify_ferpa_compliance.py

# Load testing
python scripts/testing/locustfile.py
```

### Demo Scripts

```bash
# Create test user
python scripts/demos/create_test_user.py

# Generate test data
python scripts/demos/demo_data_generation.py

# Check database integrity
python scripts/demos/check_database_data.py
```

### Security Maintenance

```bash
# Clean up old audit logs
python scripts/security/cleanup_audit_logs.py --days 90

# Run data retention policies
python scripts/security/run_data_retention.py
```

## Systemd Integration

Some scripts include systemd service files for automated scheduling:

**Audit Log Cleanup:**
```bash
# Install service
sudo cp scripts/security/audit-cleanup.service /etc/systemd/system/
sudo cp scripts/security/audit-cleanup.timer /etc/systemd/system/
sudo systemctl enable audit-cleanup.timer
sudo systemctl start audit-cleanup.timer
```

**Data Retention:**
```bash
# Install services
sudo cp scripts/security/data-retention*.{service,timer} /etc/systemd/system/
sudo systemctl enable data-retention.timer
sudo systemctl enable data-retention-archival.timer
sudo systemctl start data-retention.timer
sudo systemctl start data-retention-archival.timer
```

## Environment Requirements

### Python Scripts
All Python scripts require the project virtual environment:
```bash
source venv/bin/activate  # or ./venv/bin/python script.py
```

### Shell Scripts
Shell scripts should be executed from the project root:
```bash
./scripts/deployment/start_all_workers.sh
```

### Permissions
Deployment scripts are executable. If needed:
```bash
chmod +x scripts/deployment/*.sh
chmod +x scripts/testing/*.sh
```

## Development vs Production

**Development:**
- Use demo scripts for testing features
- Create test users with `demos/create_test_user.py`
- Run individual workers for debugging

**Production:**
- Use deployment scripts for worker management
- Enable systemd timers for maintenance tasks
- Use load testing to verify performance
- Run security audits regularly

## Configuration

Most scripts use environment variables from `.env`:
- Database connection strings
- API keys and secrets
- Redis connection
- Celery broker settings

Ensure `.env` is properly configured before running scripts.

## Maintenance Schedule

**Daily:**
- Workers run continuously (managed by systemd or supervisor)

**Weekly:**
- Audit log cleanup (via timer)

**Monthly:**
- Data retention policies (via timer)
- Security audits
- Performance testing

## Adding New Scripts

When adding new scripts:
1. Place in appropriate category directory
2. Make shell scripts executable: `chmod +x script.sh`
3. Add Python shebang: `#!/usr/bin/env python3`
4. Document environment requirements
5. Update this README

## Troubleshooting

**Workers not starting:**
- Check Redis connection: `redis-cli ping`
- Check PostgreSQL: `psql -U postgres -c "\l"`
- Review logs: `tail -f logs/*.log`

**Permission errors:**
- Ensure scripts are executable
- Check file ownership
- Verify environment activation

**Import errors:**
- Activate virtual environment
- Verify dependencies: `pip install -r requirements.txt`
- Check PYTHONPATH if needed
