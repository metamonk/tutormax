"""
Scheduled Report Delivery Tasks

Implements Celery Beat integration for automated report generation and delivery
via email to operations managers. Part of Task 24.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from io import BytesIO

from src.workers.celery_app import celery_app
from src.database.database import get_db_session
from src.api.export_service import ExportService
from src.api.email_service import EmailService
from src.database.models import User, UserRole
from sqlalchemy import select

logger = logging.getLogger(__name__)


@celery_app.task(name="scheduled_reports.generate_weekly_report")
def generate_weekly_report():
    """
    Generate and send weekly tutor performance report.

    Triggered by Celery Beat every Monday at 9am.
    """
    logger.info("Starting weekly report generation")

    try:
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Generate and send report
        _send_performance_report(
            report_type="weekly",
            start_date=start_date,
            end_date=end_date,
            subject=f"Weekly Tutor Performance Report - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )

        logger.info("Weekly report generated successfully")
        return {"status": "success", "report_type": "weekly"}

    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}", exc_info=True)
        raise


@celery_app.task(name="scheduled_reports.generate_monthly_report")
def generate_monthly_report():
    """
    Generate and send monthly tutor performance report.

    Triggered by Celery Beat on the 1st of each month at 9am.
    """
    logger.info("Starting monthly report generation")

    try:
        # Calculate date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Generate and send report
        _send_performance_report(
            report_type="monthly",
            start_date=start_date,
            end_date=end_date,
            subject=f"Monthly Tutor Performance Report - {start_date.strftime('%B %Y')}"
        )

        logger.info("Monthly report generated successfully")
        return {"status": "success", "report_type": "monthly"}

    except Exception as e:
        logger.error(f"Failed to generate monthly report: {e}", exc_info=True)
        raise


@celery_app.task(name="scheduled_reports.generate_intervention_effectiveness_report")
def generate_intervention_effectiveness_report():
    """
    Generate and send intervention effectiveness report.

    Triggered by Celery Beat every Friday at 4pm.
    """
    logger.info("Starting intervention effectiveness report generation")

    try:
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Generate and send report
        _send_intervention_report(
            start_date=start_date,
            end_date=end_date,
            subject=f"Weekly Intervention Effectiveness Report - {start_date.strftime('%Y-%m-%d')}"
        )

        logger.info("Intervention report generated successfully")
        return {"status": "success", "report_type": "intervention_effectiveness"}

    except Exception as e:
        logger.error(f"Failed to generate intervention report: {e}", exc_info=True)
        raise


@celery_app.task(name="scheduled_reports.generate_churn_analytics_report")
def generate_churn_analytics_report():
    """
    Generate and send monthly churn analytics report.

    Triggered by Celery Beat on the 1st of each month at 10am.
    """
    logger.info("Starting churn analytics report generation")

    try:
        # Calculate date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Generate and send report
        _send_churn_report(
            start_date=start_date,
            end_date=end_date,
            subject=f"Monthly Churn Analytics Report - {start_date.strftime('%B %Y')}"
        )

        logger.info("Churn analytics report generated successfully")
        return {"status": "success", "report_type": "churn_analytics"}

    except Exception as e:
        logger.error(f"Failed to generate churn analytics report: {e}", exc_info=True)
        raise


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _send_performance_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    subject: str
):
    """
    Generate and send performance report to operations managers.

    Args:
        report_type: Type of report (weekly, monthly)
        start_date: Start date for report data
        end_date: End date for report data
        subject: Email subject line
    """
    import asyncio

    async def _generate_and_send():
        async with get_db_session() as db:
            # Generate CSV report
            export_service = ExportService(db)
            csv_buffer = await export_service.export_tutor_performance_csv(
                start_date=start_date,
                end_date=end_date
            )

            # Generate PDF report
            pdf_buffer = await export_service.export_tutor_performance_pdf(
                start_date=start_date,
                end_date=end_date
            )

            # Get operations managers
            recipients = await _get_operations_manager_emails(db)

            if not recipients:
                logger.warning("No operations manager emails found for report delivery")
                return

            # Send email with attachments
            email_service = EmailService()

            email_body = f"""
<html>
<body>
<h2>{report_type.capitalize()} Tutor Performance Report</h2>

<p>This is your automated {report_type} tutor performance report for the period:</p>
<p><strong>{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}</strong></p>

<p>The report includes:</p>
<ul>
    <li>Performance metrics for all active tutors</li>
    <li>Performance tier distribution</li>
    <li>Rating trends and engagement scores</li>
    <li>Session completion statistics</li>
</ul>

<p>Please see the attached CSV and PDF files for detailed data.</p>

<p>This is an automated report generated by the TutorMax Performance Evaluation System.</p>

<p><em>Note: All data is FERPA compliant and does not contain student PII.</em></p>
</body>
</html>
            """

            # Prepare attachments
            csv_filename = f"tutor_performance_{report_type}_{start_date.strftime('%Y%m%d')}.csv"
            pdf_filename = f"tutor_performance_{report_type}_{start_date.strftime('%Y%m%d')}.pdf"

            attachments = [
                {
                    "filename": csv_filename,
                    "content": csv_buffer.getvalue().encode('utf-8'),
                    "mimetype": "text/csv"
                },
                {
                    "filename": pdf_filename,
                    "content": pdf_buffer.getvalue(),
                    "mimetype": "application/pdf"
                }
            ]

            # Send to each recipient
            for recipient in recipients:
                try:
                    await email_service.send_email(
                        to_email=recipient,
                        subject=subject,
                        html_body=email_body,
                        attachments=attachments
                    )
                    logger.info(f"Sent {report_type} report to {recipient}")
                except Exception as e:
                    logger.error(f"Failed to send report to {recipient}: {e}")

    # Run async function
    asyncio.run(_generate_and_send())


def _send_intervention_report(
    start_date: datetime,
    end_date: datetime,
    subject: str
):
    """
    Generate and send intervention effectiveness report.

    Args:
        start_date: Start date for report data
        end_date: End date for report data
        subject: Email subject line
    """
    import asyncio

    async def _generate_and_send():
        async with get_db_session() as db:
            # Generate CSV report
            export_service = ExportService(db)
            csv_buffer = await export_service.export_interventions_csv(
                start_date=start_date,
                end_date=end_date
            )

            # Get operations managers
            recipients = await _get_operations_manager_emails(db)

            if not recipients:
                logger.warning("No operations manager emails found for intervention report")
                return

            # Send email with attachment
            email_service = EmailService()

            email_body = f"""
<html>
<body>
<h2>Weekly Intervention Effectiveness Report</h2>

<p>This is your automated weekly intervention effectiveness report for the period:</p>
<p><strong>{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}</strong></p>

<p>The report includes:</p>
<ul>
    <li>Intervention completion rates by type</li>
    <li>Outcome analysis (improved, no change, churned)</li>
    <li>Average time to complete interventions</li>
    <li>Effectiveness scores</li>
</ul>

<p>Please see the attached CSV file for detailed data.</p>

<p>This is an automated report generated by the TutorMax Performance Evaluation System.</p>
</body>
</html>
            """

            csv_filename = f"intervention_effectiveness_{start_date.strftime('%Y%m%d')}.csv"

            attachments = [{
                "filename": csv_filename,
                "content": csv_buffer.getvalue().encode('utf-8'),
                "mimetype": "text/csv"
            }]

            # Send to each recipient
            for recipient in recipients:
                try:
                    await email_service.send_email(
                        to_email=recipient,
                        subject=subject,
                        html_body=email_body,
                        attachments=attachments
                    )
                    logger.info(f"Sent intervention report to {recipient}")
                except Exception as e:
                    logger.error(f"Failed to send intervention report to {recipient}: {e}")

    asyncio.run(_generate_and_send())


def _send_churn_report(
    start_date: datetime,
    end_date: datetime,
    subject: str
):
    """
    Generate and send churn analytics report.

    Args:
        start_date: Start date for report data
        end_date: End date for report data
        subject: Email subject line
    """
    import asyncio

    async def _generate_and_send():
        async with get_db_session() as db:
            # Generate PDF report with analytics summary
            export_service = ExportService(db)
            pdf_buffer = await export_service.export_analytics_summary_pdf(
                start_date=start_date,
                end_date=end_date
            )

            # Get operations managers
            recipients = await _get_operations_manager_emails(db)

            if not recipients:
                logger.warning("No operations manager emails found for churn report")
                return

            # Send email with attachment
            email_service = EmailService()

            email_body = f"""
<html>
<body>
<h2>Monthly Churn Analytics Report</h2>

<p>This is your automated monthly churn analytics report for the period:</p>
<p><strong>{start_date.strftime('%B %Y')}</strong></p>

<p>The report includes:</p>
<ul>
    <li>Churn rate trends and predictions</li>
    <li>Risk level distribution</li>
    <li>Contributing factors analysis</li>
    <li>Recommended interventions</li>
</ul>

<p>Please see the attached PDF file for detailed analysis.</p>

<p>This is an automated report generated by the TutorMax Performance Evaluation System.</p>
</body>
</html>
            """

            pdf_filename = f"churn_analytics_{start_date.strftime('%Y%m')}.pdf"

            attachments = [{
                "filename": pdf_filename,
                "content": pdf_buffer.getvalue(),
                "mimetype": "application/pdf"
            }]

            # Send to each recipient
            for recipient in recipients:
                try:
                    await email_service.send_email(
                        to_email=recipient,
                        subject=subject,
                        html_body=email_body,
                        attachments=attachments
                    )
                    logger.info(f"Sent churn analytics report to {recipient}")
                except Exception as e:
                    logger.error(f"Failed to send churn report to {recipient}: {e}")

    asyncio.run(_generate_and_send())


async def _get_operations_manager_emails(db) -> List[str]:
    """
    Get email addresses of all operations managers.

    Args:
        db: Database session

    Returns:
        List of email addresses
    """
    stmt = select(User.email).where(
        User.role == UserRole.OPERATIONS_MANAGER
    )
    result = await db.execute(stmt)
    emails = [row[0] for row in result.all()]
    return emails
