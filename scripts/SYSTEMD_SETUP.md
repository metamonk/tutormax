# Systemd Timer Setup for Audit Log Cleanup

This guide explains how to set up automated audit log cleanup using systemd timers (recommended for production Linux systems).

## Files

- `audit-cleanup.service` - Systemd service unit
- `audit-cleanup.timer` - Systemd timer unit

## Installation

### 1. Copy Service Files

```bash
# Copy service and timer files to systemd directory
sudo cp scripts/audit-cleanup.service /etc/systemd/system/
sudo cp scripts/audit-cleanup.timer /etc/systemd/system/

# Set proper permissions
sudo chmod 644 /etc/systemd/system/audit-cleanup.service
sudo chmod 644 /etc/systemd/system/audit-cleanup.timer
```

### 2. Update Paths

Edit the service file to match your installation:

```bash
sudo nano /etc/systemd/system/audit-cleanup.service
```

Update these values:
- `User=tutormax` - Your application user
- `Group=tutormax` - Your application group
- `WorkingDirectory=/opt/tutormax` - Your installation directory
- `ExecStart=/opt/tutormax/venv/bin/python ...` - Path to Python and script

### 3. Configure Retention Period

To change the retention period, edit the `ExecStart` line:

```ini
# Retain logs for 180 days instead of 365
ExecStart=/opt/tutormax/venv/bin/python scripts/cleanup_audit_logs.py --retention-days 180
```

### 4. Enable and Start Timer

```bash
# Reload systemd to recognize new units
sudo systemctl daemon-reload

# Enable timer to start on boot
sudo systemctl enable audit-cleanup.timer

# Start timer immediately
sudo systemctl start audit-cleanup.timer

# Verify timer is active
sudo systemctl status audit-cleanup.timer
```

## Management

### Check Timer Status

```bash
# View timer status
sudo systemctl status audit-cleanup.timer

# List all timers
sudo systemctl list-timers --all

# View service logs
sudo journalctl -u audit-cleanup.service

# Follow logs in real-time
sudo journalctl -u audit-cleanup.service -f
```

### Manual Execution

```bash
# Run cleanup manually (without waiting for timer)
sudo systemctl start audit-cleanup.service

# Check last run status
sudo systemctl status audit-cleanup.service
```

### Modify Schedule

Edit the timer file:

```bash
sudo nano /etc/systemd/system/audit-cleanup.timer
```

Change the `OnCalendar` value:

```ini
# Run weekly on Sunday at 3:00 AM
OnCalendar=Sun *-*-* 03:00:00

# Run daily at midnight
OnCalendar=*-*-* 00:00:00

# Run every 6 hours
OnCalendar=*-*-* 00/6:00:00
```

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart audit-cleanup.timer
```

### Disable/Remove

```bash
# Stop and disable timer
sudo systemctl stop audit-cleanup.timer
sudo systemctl disable audit-cleanup.timer

# Remove files
sudo rm /etc/systemd/system/audit-cleanup.service
sudo rm /etc/systemd/system/audit-cleanup.timer
sudo systemctl daemon-reload
```

## Calendar Syntax Examples

```
OnCalendar Examples:
  *-*-* 02:00:00          # Daily at 2:00 AM
  Mon *-*-* 03:00:00      # Mondays at 3:00 AM
  *-*-01 04:00:00         # First day of month at 4:00 AM
  Sat,Sun *-*-* 05:00:00  # Weekends at 5:00 AM
  *-*-* 00/6:00:00        # Every 6 hours
```

## Monitoring

### Email Notifications

To receive email notifications on failure, add to service file:

```ini
[Service]
OnFailure=status-email@%n.service
```

### Slack/Discord Webhooks

Add a wrapper script that sends notifications:

```bash
#!/bin/bash
OUTPUT=$(python scripts/cleanup_audit_logs.py --retention-days 365 2>&1)
if [ $? -ne 0 ]; then
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
         -d "{\"text\": \"Audit cleanup failed: $OUTPUT\"}"
fi
```

## Troubleshooting

### Timer Not Running

```bash
# Check if timer is loaded
systemctl list-unit-files | grep audit-cleanup

# Check if timer is active
systemctl is-active audit-cleanup.timer

# Check for errors
journalctl -u audit-cleanup.timer -b
```

### Service Failing

```bash
# View detailed error logs
journalctl -u audit-cleanup.service -n 50

# Test service manually
sudo systemctl start audit-cleanup.service

# Check exit code
systemctl show -p ExecMainStatus audit-cleanup.service
```

### Permission Issues

```bash
# Ensure service user can access files
sudo -u tutormax python scripts/cleanup_audit_logs.py --dry-run

# Check file ownership
ls -la scripts/cleanup_audit_logs.py
```

## Best Practices

1. **Test First**: Run with `--dry-run` to preview
2. **Monitor Logs**: Check journalctl regularly
3. **Adjust Schedule**: Start with weekly, move to daily if needed
4. **Set Alerts**: Configure notifications for failures
5. **Document Changes**: Keep track of retention policy changes
6. **Regular Review**: Audit the cleanup logs monthly

## Security Notes

The service includes security hardening:
- `PrivateTmp=true` - Isolated /tmp directory
- `NoNewPrivileges=true` - Prevents privilege escalation
- `ProtectSystem=strict` - Read-only system directories
- `ProtectHome=true` - No access to home directories
- `ReadWritePaths=...` - Explicit write access only where needed

These settings follow systemd security best practices for production services.
