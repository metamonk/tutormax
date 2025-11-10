#!/usr/bin/env python3
"""
Cleanup old audit logs based on retention policy.

This script should be run periodically (e.g., via cron) to remove
audit logs older than the specified retention period.

Usage:
    python scripts/cleanup_audit_logs.py [--retention-days DAYS] [--dry-run]

Examples:
    # Delete logs older than 365 days (default)
    python scripts/cleanup_audit_logs.py

    # Delete logs older than 180 days
    python scripts/cleanup_audit_logs.py --retention-days 180

    # Preview what would be deleted without actually deleting
    python scripts/cleanup_audit_logs.py --dry-run
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from src.database.database import async_session_maker
from src.database.models import AuditLog
from src.api.audit_service import AuditService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def preview_cleanup(retention_days: int):
    """
    Preview what would be deleted without actually deleting.

    Args:
        retention_days: Number of days to retain logs
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    async with async_session_maker() as session:
        # Count logs to be deleted
        count_query = select(func.count()).select_from(AuditLog).where(
            AuditLog.timestamp < cutoff_date
        )
        result = await session.execute(count_query)
        count = result.scalar()

        logger.info(f"Retention period: {retention_days} days")
        logger.info(f"Cutoff date: {cutoff_date}")
        logger.info(f"Logs to be deleted: {count:,}")

        if count > 0:
            # Get oldest and newest logs to be deleted
            oldest_query = (
                select(AuditLog)
                .where(AuditLog.timestamp < cutoff_date)
                .order_by(AuditLog.timestamp)
                .limit(1)
            )
            oldest_result = await session.execute(oldest_query)
            oldest = oldest_result.scalar_one_or_none()

            newest_query = (
                select(AuditLog)
                .where(AuditLog.timestamp < cutoff_date)
                .order_by(AuditLog.timestamp.desc())
                .limit(1)
            )
            newest_result = await session.execute(newest_query)
            newest = newest_result.scalar_one_or_none()

            if oldest:
                logger.info(f"Oldest log to delete: {oldest.timestamp}")
            if newest:
                logger.info(f"Newest log to delete: {newest.timestamp}")

            # Get breakdown by action type
            logger.info("\nLogs to delete by action type:")
            action_query = (
                select(AuditLog.action, func.count(AuditLog.log_id))
                .where(AuditLog.timestamp < cutoff_date)
                .group_by(AuditLog.action)
                .order_by(func.count(AuditLog.log_id).desc())
            )
            action_result = await session.execute(action_query)
            for action, action_count in action_result.all():
                logger.info(f"  {action}: {action_count:,}")


async def cleanup_logs(retention_days: int, dry_run: bool = False):
    """
    Clean up old audit logs.

    Args:
        retention_days: Number of days to retain logs
        dry_run: If True, preview without deleting
    """
    if dry_run:
        logger.info("DRY RUN MODE - No logs will be deleted")
        await preview_cleanup(retention_days)
        return

    logger.info(f"Starting audit log cleanup (retention: {retention_days} days)...")

    async with async_session_maker() as session:
        deleted_count = await AuditService.cleanup_old_logs(
            session=session,
            retention_days=retention_days,
        )

        logger.info(f"Cleanup completed: {deleted_count:,} logs deleted")

        # Get current log count
        count_query = select(func.count()).select_from(AuditLog)
        result = await session.execute(count_query)
        remaining = result.scalar()
        logger.info(f"Remaining logs: {remaining:,}")


async def get_statistics():
    """Get current audit log statistics."""
    async with async_session_maker() as session:
        # Total logs
        total_query = select(func.count()).select_from(AuditLog)
        total_result = await session.execute(total_query)
        total = total_result.scalar()

        # Oldest log
        oldest_query = (
            select(AuditLog.timestamp)
            .order_by(AuditLog.timestamp)
            .limit(1)
        )
        oldest_result = await session.execute(oldest_query)
        oldest = oldest_result.scalar_one_or_none()

        # Newest log
        newest_query = (
            select(AuditLog.timestamp)
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        newest_result = await session.execute(newest_query)
        newest = newest_result.scalar_one_or_none()

        logger.info("Current Audit Log Statistics:")
        logger.info(f"  Total logs: {total:,}")
        if oldest:
            logger.info(f"  Oldest log: {oldest}")
            logger.info(f"  Age: {(datetime.utcnow() - oldest.replace(tzinfo=None)).days} days")
        if newest:
            logger.info(f"  Newest log: {newest}")

        # Logs by action
        logger.info("\nLogs by action type (top 10):")
        action_query = (
            select(AuditLog.action, func.count(AuditLog.log_id))
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.log_id).desc())
            .limit(10)
        )
        action_result = await session.execute(action_query)
        for action, count in action_result.all():
            logger.info(f"  {action}: {count:,}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cleanup old audit logs based on retention policy"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=365,
        help="Number of days to retain logs (default: 365)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show current audit log statistics",
    )

    args = parser.parse_args()

    # Validate retention days
    if args.retention_days < 30:
        logger.error("Retention period must be at least 30 days")
        sys.exit(1)
    if args.retention_days > 3650:  # ~10 years
        logger.error("Retention period cannot exceed 3650 days")
        sys.exit(1)

    try:
        if args.stats:
            asyncio.run(get_statistics())
        else:
            asyncio.run(cleanup_logs(args.retention_days, args.dry_run))
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
