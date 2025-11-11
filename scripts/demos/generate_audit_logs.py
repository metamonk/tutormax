#!/usr/bin/env python3
"""
Generate realistic audit log entries for demo purposes.

Creates various audit log entries to populate the admin audit log viewer
with realistic activity data.
"""

import asyncio
import sys
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.database import async_session_maker
from src.database.models import User, AuditLog
from src.api.audit_service import AuditService
from sqlalchemy import select


async def generate_audit_logs():
    """Generate realistic audit log entries."""
    print("=" * 60)
    print("🔍 TutorMax Audit Log Generator")
    print("=" * 60)

    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()

        if not users:
            print("❌ No users found in database. Please create users first.")
            return

        print(f"\n✓ Found {len(users)} users")
        print("\nGenerating audit log entries...")

        # Generate logs for the past 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        log_count = 0

        # Different types of actions with realistic distribution
        actions = [
            (AuditService.ACTION_LOGIN, 0.30, True),  # 30% success logins
            (AuditService.ACTION_LOGOUT, 0.15, True),  # 15% logouts
            (AuditService.ACTION_LOGIN_FAILED, 0.05, False),  # 5% failed logins
            (AuditService.ACTION_VIEW, 0.20, True),  # 20% view actions
            (AuditService.ACTION_UPDATE, 0.12, True),  # 12% updates
            (AuditService.ACTION_CREATE, 0.08, True),  # 8% creates
            (AuditService.ACTION_SEARCH, 0.07, True),  # 7% searches
            (AuditService.ACTION_EXPORT, 0.03, True),  # 3% exports
        ]

        # Generate 150-200 log entries
        total_logs = random.randint(150, 200)

        for i in range(total_logs):
            # Random timestamp within the 30-day window
            days_ago = random.uniform(0, 30)
            timestamp = end_date - timedelta(days=days_ago)

            # Select random user
            user = random.choice(users)

            # Select random action based on weights
            action_list, weights, _ = zip(*actions)
            action_index = random.choices(range(len(actions)), weights=weights)[0]
            action, _, success = actions[action_index]

            # Generate realistic IP addresses
            ip_addresses = [
                "192.168.1." + str(random.randint(1, 255)),
                "10.0.0." + str(random.randint(1, 255)),
                "172.16.0." + str(random.randint(1, 255)),
            ]
            ip_address = random.choice(ip_addresses)

            # User agents
            user_agents = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
            ]
            user_agent = random.choice(user_agents)

            # HTTP methods and paths based on action
            if action in [AuditService.ACTION_LOGIN, AuditService.ACTION_LOGIN_FAILED]:
                method = "POST"
                path = "/auth/jwt/login"
            elif action == AuditService.ACTION_LOGOUT:
                method = "POST"
                path = "/auth/jwt/logout"
            elif action == AuditService.ACTION_VIEW:
                method = "GET"
                paths = [
                    "/api/v1/tutors/sarah_chen_001/metrics",
                    "/api/v1/tutors/mike_ross_001/sessions",
                    "/api/admin/users",
                    "/api/audit/logs",
                ]
                path = random.choice(paths)
            elif action == AuditService.ACTION_UPDATE:
                method = "PATCH"
                paths = [
                    "/api/admin/users/1",
                    "/api/v1/tutor-profile/sarah_chen_001/notes",
                ]
                path = random.choice(paths)
            elif action == AuditService.ACTION_CREATE:
                method = "POST"
                paths = [
                    "/api/admin/users",
                    "/api/v1/tutor-profile/sarah_chen_001/notes",
                    "/api/interventions",
                ]
                path = random.choice(paths)
            elif action == AuditService.ACTION_SEARCH:
                method = "GET"
                path = "/api/audit/logs?search=tutor"
            elif action == AuditService.ACTION_EXPORT:
                method = "GET"
                path = "/api/audit/logs/export/csv"
            else:
                method = "GET"
                path = "/api/analytics/overview"

            # Status codes
            status_code = 200 if success else random.choice([400, 401, 403, 500])

            # Create audit log entry
            log = AuditLog(
                log_id=str(uuid.uuid4()),
                user_id=user.id,
                action=action,
                resource_type="user" if "users" in path else "tutor" if "tutors" in path else "system",
                resource_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=method,
                request_path=path,
                status_code=status_code,
                success=success,
                error_message=None if success else f"Error during {action}",
                audit_metadata={
                    "user_email": user.email,
                    "user_roles": [role.value for role in user.roles],
                },
                timestamp=timestamp
            )

            session.add(log)
            log_count += 1

            if (i + 1) % 50 == 0:
                print(f"   Generated {i + 1}/{total_logs} log entries...")

        # Commit all logs
        await session.commit()

        print(f"\n✅ Generated {log_count} audit log entries")

        # Print summary statistics
        print("\n" + "=" * 60)
        print("📊 Audit Log Summary")
        print("=" * 60)
        print(f"  Total entries: {log_count}")
        print(f"  Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"  Users: {len(users)}")
        print("\n  Action Distribution:")
        for action, weight, _ in actions:
            expected = int(total_logs * weight)
            print(f"    {action}: ~{expected} entries ({weight * 100:.0f}%)")

        print("\n" + "=" * 60)
        print("✅ Audit log generation complete!")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(generate_audit_logs())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
