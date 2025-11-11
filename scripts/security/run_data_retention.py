#!/usr/bin/env python3
"""
Automated Data Retention Script

Runs scheduled data retention tasks:
- Scans for records eligible for archival
- Archives data past FERPA 7-year retention period
- Anonymizes data for analytics
- Generates compliance reports

Usage:
    python scripts/run_data_retention.py [options]

Options:
    --dry-run          Run scan only, don't perform actions (default: True)
    --perform-actions  Actually perform archival operations
    --report-only      Generate retention report only
    --days DAYS        Report period in days (default: 90)

Examples:
    # Dry run - see what would be archived
    python scripts/run_data_retention.py --dry-run

    # Actually perform archival
    python scripts/run_data_retention.py --perform-actions

    # Generate 30-day report
    python scripts/run_data_retention.py --report-only --days 30

Recommended schedule:
    - Weekly dry run to monitor eligible records
    - Monthly/quarterly actual archival with --perform-actions
"""

import asyncio
import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.database import AsyncSessionLocal
from src.api.compliance.data_retention import DataRetentionService


async def run_scan(dry_run: bool = True):
    """Run retention scan."""
    print(f"\n{'='*80}")
    print(f"DATA RETENTION SCAN - {'DRY RUN' if dry_run else 'LIVE MODE'}")
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print(f"{'='*80}\n")

    async with AsyncSessionLocal() as session:
        results = await DataRetentionService.scan_for_retention_actions(
            session=session,
            dry_run=dry_run
        )

        print("SCAN RESULTS")
        print("-" * 80)
        print(json.dumps(results["summary"], indent=2))
        print()

        if results["summary"]["total_students_for_archival"] > 0:
            print("\nSTUDENTS ELIGIBLE FOR ARCHIVAL:")
            print("-" * 80)
            for student in results["eligible_for_archival"]["students"][:5]:
                print(f"  • {student['name']} ({student['student_id']})")
                print(f"    Last activity: {student['last_activity']}")
                print(f"    Days since activity: {student['days_since_activity']}")
            if len(results["eligible_for_archival"]["students"]) > 5:
                print(f"  ... and {len(results['eligible_for_archival']['students']) - 5} more")
            print()

        if results["summary"]["total_tutors_for_archival"] > 0:
            print("\nTUTORS ELIGIBLE FOR ARCHIVAL:")
            print("-" * 80)
            for tutor in results["eligible_for_archival"]["tutors"][:5]:
                print(f"  • {tutor['name']} ({tutor['tutor_id']})")
                print(f"    Last activity: {tutor['last_activity']}")
                print(f"    Days since activity: {tutor['days_since_activity']}")
            if len(results["eligible_for_archival"]["tutors"]) > 5:
                print(f"  ... and {len(results['eligible_for_archival']['tutors']) - 5} more")
            print()

        if results["summary"]["total_sessions_for_archival"] > 0:
            print(f"\nSESSIONS ELIGIBLE FOR ARCHIVAL: {results['summary']['total_sessions_for_archival']}")
            print("-" * 80)

        if results["summary"]["total_feedback_for_archival"] > 0:
            print(f"\nFEEDBACK RECORDS ELIGIBLE FOR ARCHIVAL: {results['summary']['total_feedback_for_archival']}")
            print("-" * 80)

        print(f"\n{'='*80}")
        print("SCAN COMPLETED")
        print(f"{'='*80}\n")

        return results


async def run_scheduled_archival(perform_actions: bool = False):
    """Run scheduled archival process."""
    print(f"\n{'='*80}")
    print(f"SCHEDULED ARCHIVAL - {'LIVE MODE' if perform_actions else 'DRY RUN'}")
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print(f"{'='*80}\n")

    async with AsyncSessionLocal() as session:
        results = await DataRetentionService.schedule_automated_archival(
            session=session,
            perform_actions=perform_actions
        )

        print("ARCHIVAL RESULTS")
        print("-" * 80)
        print(json.dumps(results, indent=2))
        print()

        if perform_actions:
            print("\nACTIONS PERFORMED:")
            print("-" * 80)
            print(f"  Students archived: {results['actions_performed']['students_archived']}")
            print(f"  Tutors archived: {results['actions_performed']['tutors_archived']}")
            if results['actions_performed']['errors']:
                print(f"\n  Errors encountered: {len(results['actions_performed']['errors'])}")
                for error in results['actions_performed']['errors']:
                    print(f"    • {error['entity_type']} {error['entity_id']}: {error['error']}")
            print()

        print(f"\n{'='*80}")
        print("ARCHIVAL COMPLETED")
        print(f"{'='*80}\n")

        return results


async def generate_report(days: int = 90):
    """Generate retention compliance report."""
    print(f"\n{'='*80}")
    print(f"DATA RETENTION COMPLIANCE REPORT")
    print(f"Period: Last {days} days")
    print(f"Generated at: {datetime.utcnow().isoformat()}")
    print(f"{'='*80}\n")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    async with AsyncSessionLocal() as session:
        report = await DataRetentionService.get_retention_report(
            session=session,
            start_date=start_date,
            end_date=end_date
        )

        print("CURRENT DATA INVENTORY")
        print("-" * 80)
        print(f"  Active students: {report['current_data_inventory']['active_students']}")
        print(f"  Active tutors: {report['current_data_inventory']['active_tutors']}")
        print(f"  Total sessions: {report['current_data_inventory']['total_sessions']}")
        print()

        print("RETENTION ACTIONS TAKEN (Last {} days)".format(days))
        print("-" * 80)
        print(f"  Archival operations: {report['retention_actions_taken']['archival_operations']}")
        print(f"  Anonymization operations: {report['retention_actions_taken']['anonymization_operations']}")
        print(f"  Deletion requests processed: {report['retention_actions_taken']['deletion_requests_processed']}")
        print()

        print("COMPLIANCE STATUS")
        print("-" * 80)
        print(f"  FERPA retention policy: {report['compliance_status']['ferpa_retention_policy']}")
        print(f"  GDPR anonymization eligible after: {report['compliance_status']['gdpr_anonymization_eligible_after']}")
        print(f"  Audit log retention: {report['compliance_status']['audit_log_retention']}")
        print()

        if report['archival_details']:
            print("RECENT ARCHIVAL OPERATIONS")
            print("-" * 80)
            for detail in report['archival_details'][:10]:
                print(f"  • {detail['timestamp']} - {detail['resource_type']} {detail['resource_id']}")
            if len(report['archival_details']) > 10:
                print(f"  ... and {len(report['archival_details']) - 10} more")
            print()

        if report['deletion_details']:
            print("RECENT DELETION REQUESTS")
            print("-" * 80)
            for detail in report['deletion_details'][:10]:
                print(f"  • {detail['timestamp']} - {detail['resource_type']} {detail['resource_id']}")
                if detail.get('reason'):
                    print(f"    Reason: {detail['reason']}")
            if len(report['deletion_details']) > 10:
                print(f"  ... and {len(report['deletion_details']) - 10} more")
            print()

        print(f"\n{'='*80}")
        print("REPORT COMPLETED")
        print(f"{'='*80}\n")

        # Save report to file
        report_dir = Path(__file__).parent.parent / "reports"
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / f"data_retention_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Report saved to: {report_file}\n")

        return report


async def main():
    parser = argparse.ArgumentParser(
        description="Automated Data Retention Script for TutorMax",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help='Run scan only without performing archival actions (default)'
    )

    parser.add_argument(
        '--perform-actions',
        action='store_true',
        default=False,
        help='Actually perform archival operations (WARNING: This will modify data)'
    )

    parser.add_argument(
        '--report-only',
        action='store_true',
        default=False,
        help='Generate compliance report only'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Report period in days (default: 90)'
    )

    args = parser.parse_args()

    try:
        if args.report_only:
            # Generate report only
            await generate_report(days=args.days)
        elif args.perform_actions:
            # Live mode - actually perform archival
            print("WARNING: Running in LIVE MODE - data will be archived!")
            print("Press Ctrl+C within 5 seconds to cancel...\n")
            await asyncio.sleep(5)
            await run_scheduled_archival(perform_actions=True)
        else:
            # Dry run (default)
            await run_scan(dry_run=True)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
