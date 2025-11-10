#!/usr/bin/env python3
"""
FERPA Compliance Verification Script

This script verifies that TutorMax meets FERPA compliance requirements by checking:
- Access control implementation
- Disclosure logging
- Data retention policies
- Parental consent documentation
- Educational record classifications

Usage:
    python scripts/verify_ferpa_compliance.py
    python scripts/verify_ferpa_compliance.py --student-id STU001
    python scripts/verify_ferpa_compliance.py --check-retention
    python scripts/verify_ferpa_compliance.py --check-all
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from src.database.database import get_db_session_context
from src.database.models import Student, Session, StudentFeedback, AuditLog, User
from src.api.compliance import FERPAService, FERPARecordType
from src.api.config import settings


class FERPAComplianceVerifier:
    """Verify FERPA compliance across the TutorMax platform."""

    def __init__(self):
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.passed_checks: List[str] = []

    async def verify_all(self) -> Dict[str, Any]:
        """Run all FERPA compliance checks."""
        print("=" * 80)
        print("FERPA COMPLIANCE VERIFICATION")
        print("=" * 80)
        print()

        async with get_db_session_context() as session:
            # Run all checks
            await self._check_configuration(session)
            await self._check_student_records(session)
            await self._check_parental_consent(session)
            await self._check_disclosure_logging(session)
            await self._check_retention_policy(session)
            await self._check_access_controls(session)

        # Print summary
        self._print_summary()

        return {
            "passed": len(self.issues) == 0,
            "passed_checks": len(self.passed_checks),
            "issues": len(self.issues),
            "warnings": len(self.warnings),
            "details": {
                "passed": self.passed_checks,
                "issues": self.issues,
                "warnings": self.warnings,
            }
        }

    async def verify_student(self, student_id: str) -> Dict[str, Any]:
        """Verify FERPA compliance for a specific student."""
        print(f"Verifying FERPA compliance for student: {student_id}")
        print("=" * 80)
        print()

        async with get_db_session_context() as session:
            # Check if student exists
            student_query = select(Student).where(Student.student_id == student_id)
            result = await session.execute(student_query)
            student = result.scalar_one_or_none()

            if not student:
                print(f"❌ ERROR: Student {student_id} not found")
                return {"error": "Student not found"}

            # Check retention policy
            print("1. Checking retention policy...")
            retention = await FERPAService.check_retention_policy(
                session=session,
                student_id=student_id,
            )
            self._print_retention_status(retention)

            # Check parental consent
            print("\n2. Checking parental consent...")
            consent = await FERPAService.verify_parental_consent(
                session=session,
                student_id=student_id,
            )
            self._print_consent_status(consent)

            # Check disclosure history
            print("\n3. Checking disclosure history (last 90 days)...")
            disclosures = await FERPAService.get_disclosure_history(
                session=session,
                student_id=student_id,
                days=90,
            )
            self._print_disclosure_history(disclosures)

            # Get educational records
            print("\n4. Retrieving educational records...")
            records = await FERPAService.get_student_educational_records(
                session=session,
                student_id=student_id,
            )
            self._print_educational_records(records)

        return {
            "student_id": student_id,
            "retention": retention,
            "consent": consent,
            "disclosures": disclosures,
            "records": records,
        }

    async def _check_configuration(self, session):
        """Check FERPA configuration settings."""
        print("1. Configuration Check")
        print("-" * 80)

        # Check retention period
        if settings.pii_data_retention_days == 2555:  # 7 years
            self.passed_checks.append("Retention period set to 7 years (FERPA compliant)")
            print("✓ Retention period: 7 years (2555 days)")
        else:
            self.issues.append(
                f"Retention period is {settings.pii_data_retention_days} days, "
                "should be 2555 days (7 years) for FERPA compliance"
            )
            print(f"✗ Retention period: {settings.pii_data_retention_days} days (should be 2555)")

        # Check audit log retention
        if settings.audit_log_retention_days >= 2555:
            self.passed_checks.append("Audit log retention meets FERPA requirements")
            print(f"✓ Audit log retention: {settings.audit_log_retention_days} days")
        else:
            self.issues.append(
                f"Audit log retention is {settings.audit_log_retention_days} days, "
                "should be at least 2555 days (7 years)"
            )
            print(f"✗ Audit log retention: {settings.audit_log_retention_days} days (too short)")

        # Check encryption
        if settings.encryption_enabled:
            self.passed_checks.append("Data encryption enabled for PII protection")
            print("✓ Encryption enabled for PII")
        else:
            self.issues.append("Data encryption disabled - PII should be encrypted")
            print("✗ Encryption disabled")

        print()

    async def _check_student_records(self, session):
        """Check student record structure."""
        print("2. Student Records Check")
        print("-" * 80)

        # Count total students
        count_query = select(func.count()).select_from(Student)
        result = await session.execute(count_query)
        total_students = result.scalar()

        print(f"Total students: {total_students}")

        # Check for students with sessions
        students_with_sessions = select(func.count(func.distinct(Session.student_id))).select_from(Session)
        result = await session.execute(students_with_sessions)
        active_students = result.scalar()

        print(f"Students with sessions: {active_students}")

        if total_students > 0:
            self.passed_checks.append(f"Found {total_students} student records")
        else:
            self.warnings.append("No student records found in database")

        print()

    async def _check_parental_consent(self, session):
        """Check parental consent for students under 13."""
        print("3. Parental Consent Check (COPPA Integration)")
        print("-" * 80)

        # Find students under 13
        under_13_query = select(Student).where(Student.is_under_13 == True)
        result = await session.execute(under_13_query)
        under_13_students = result.scalars().all()

        print(f"Students under 13: {len(under_13_students)}")

        if len(under_13_students) == 0:
            print("✓ No students under 13 requiring parental consent")
            self.passed_checks.append("No COPPA-protected students requiring consent")
        else:
            # Check each student
            compliant = 0
            non_compliant = 0

            for student in under_13_students:
                if student.parent_consent_given and student.parent_email:
                    compliant += 1
                else:
                    non_compliant += 1
                    self.issues.append(
                        f"Student {student.student_id} is under 13 but lacks parental consent"
                    )

            if non_compliant == 0:
                print(f"✓ All {compliant} students under 13 have parental consent")
                self.passed_checks.append("All COPPA-protected students have consent")
            else:
                print(f"✗ {non_compliant} students under 13 missing parental consent")
                print(f"✓ {compliant} students under 13 have parental consent")

        print()

    async def _check_disclosure_logging(self, session):
        """Check FERPA disclosure logging."""
        print("4. Disclosure Logging Check")
        print("-" * 80)

        # Count FERPA disclosure logs in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        ferpa_logs_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.action.like("ferpa_disclosure_%"),
                AuditLog.timestamp >= thirty_days_ago
            )
        )
        result = await session.execute(ferpa_logs_query)
        ferpa_log_count = result.scalar()

        print(f"FERPA disclosure logs (last 30 days): {ferpa_log_count}")

        if ferpa_log_count > 0:
            self.passed_checks.append(f"Found {ferpa_log_count} FERPA disclosure logs")

            # Check for required metadata
            sample_query = (
                select(AuditLog)
                .where(AuditLog.action.like("ferpa_disclosure_%"))
                .limit(5)
            )
            result = await session.execute(sample_query)
            sample_logs = result.scalars().all()

            valid_logs = 0
            for log in sample_logs:
                if log.audit_metadata and all(
                    key in log.audit_metadata
                    for key in ["ferpa_disclosure", "student_id", "record_type"]
                ):
                    valid_logs += 1

            if valid_logs == len(sample_logs):
                print(f"✓ Sample logs contain required FERPA metadata")
                self.passed_checks.append("Disclosure logs contain required metadata")
            else:
                self.warnings.append(
                    f"Some disclosure logs missing required metadata ({valid_logs}/{len(sample_logs)} valid)"
                )
        else:
            self.warnings.append("No FERPA disclosure logs found (may be normal if no recent access)")

        print()

    async def _check_retention_policy(self, session):
        """Check data retention policy implementation."""
        print("5. Data Retention Policy Check")
        print("-" * 80)

        # Get retention schedule
        schedule = FERPAService.get_retention_schedule()
        print(f"Retention framework: {schedule['framework']}")
        print(f"Retention period: {schedule['retention_period_years']} years")

        # Check for old students that might need review
        seven_years_ago = datetime.utcnow() - timedelta(days=2555)

        old_students_query = (
            select(Student)
            .where(Student.created_at < seven_years_ago)
        )
        result = await session.execute(old_students_query)
        old_students = result.scalars().all()

        if len(old_students) > 0:
            # Check if they have recent activity
            eligible_for_review = 0
            for student in old_students:
                last_session_query = (
                    select(Session)
                    .where(Session.student_id == student.student_id)
                    .order_by(Session.scheduled_start.desc())
                    .limit(1)
                )
                result = await session.execute(last_session_query)
                last_session = result.scalar_one_or_none()

                if not last_session or (
                    datetime.utcnow() - last_session.scheduled_start
                ).days > 2555:
                    eligible_for_review += 1

            if eligible_for_review > 0:
                self.warnings.append(
                    f"{eligible_for_review} student records eligible for retention review"
                )
                print(f"⚠ {eligible_for_review} records eligible for retention review")
            else:
                print(f"✓ {len(old_students)} old records have recent activity")
        else:
            print("✓ No records older than retention period")
            self.passed_checks.append("No records exceed retention period")

        print()

    async def _check_access_controls(self, session):
        """Check access control implementation."""
        print("6. Access Control Check")
        print("-" * 80)

        # Count users by role
        users_query = select(User)
        result = await session.execute(users_query)
        users = result.scalars().all()

        role_counts = {}
        for user in users:
            for role in user.roles:
                role_counts[role.value] = role_counts.get(role.value, 0) + 1

        print("Users by role:")
        for role, count in role_counts.items():
            print(f"  - {role}: {count}")

        if len(users) > 0:
            self.passed_checks.append(f"Found {len(users)} users with role assignments")
        else:
            self.warnings.append("No users found in database")

        print()

    def _print_retention_status(self, retention: Dict[str, Any]):
        """Print retention status information."""
        if not retention.get("exists"):
            print(f"✗ {retention.get('error', 'Unknown error')}")
            return

        print(f"Record age: {retention['record_age_days']} days")
        print(f"Retention deadline: {retention['retention_deadline']}")
        print(f"Days until eligible for deletion: {retention['days_until_eligible_deletion']}")

        if retention['should_retain']:
            print(f"✓ Record should be retained (not eligible for deletion)")
        else:
            print(f"⚠ Record eligible for deletion (retention period met)")

    def _print_consent_status(self, consent: Dict[str, Any]):
        """Print parental consent status."""
        if not consent.get("exists"):
            print(f"✗ {consent.get('error', 'Unknown error')}")
            return

        print(f"Is under 13: {consent['is_under_13']}")
        print(f"Requires parental consent: {consent['requires_parental_consent']}")
        print(f"Consent given: {consent['consent_given']}")

        if consent['compliant']:
            print("✓ Parental consent compliant")
        else:
            print(f"✗ Parental consent issues: {', '.join(consent['issues'])}")

    def _print_disclosure_history(self, disclosures: List[Dict[str, Any]]):
        """Print disclosure history summary."""
        print(f"Total disclosures: {len(disclosures)}")

        if len(disclosures) > 0:
            print("\nRecent disclosures:")
            for disclosure in disclosures[:10]:  # Show last 10
                print(f"  - {disclosure['timestamp']}: {disclosure['record_type']} "
                      f"by user {disclosure['user_id']} ({disclosure['disclosure_reason']})")

            if len(disclosures) > 10:
                print(f"  ... and {len(disclosures) - 10} more")

    def _print_educational_records(self, records: Dict[str, Any]):
        """Print educational records summary."""
        print(f"Student ID: {records['student_id']}")
        print(f"Retrieved at: {records['retrieved_at']}")
        print("\nRecord types available:")

        for record_type, data in records['records'].items():
            if isinstance(data, list):
                print(f"  - {record_type}: {len(data)} records")
            elif isinstance(data, dict):
                print(f"  - {record_type}: {len(data)} fields")

    def _print_summary(self):
        """Print verification summary."""
        print()
        print("=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print()

        print(f"Passed checks: {len(self.passed_checks)}")
        print(f"Issues found: {len(self.issues)}")
        print(f"Warnings: {len(self.warnings)}")
        print()

        if self.issues:
            print("ISSUES:")
            for issue in self.issues:
                print(f"  ✗ {issue}")
            print()

        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
            print()

        if not self.issues:
            print("✓ FERPA COMPLIANCE VERIFIED")
        else:
            print("✗ FERPA COMPLIANCE ISSUES FOUND")

        print()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify FERPA compliance")
    parser.add_argument("--student-id", help="Check specific student")
    parser.add_argument("--check-retention", action="store_true", help="Check retention policies")
    parser.add_argument("--check-all", action="store_true", help="Run all checks (default)")

    args = parser.parse_args()

    verifier = FERPAComplianceVerifier()

    if args.student_id:
        await verifier.verify_student(args.student_id)
    else:
        await verifier.verify_all()


if __name__ == "__main__":
    asyncio.run(main())
