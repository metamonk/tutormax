"""
Export Service for generating PDF and CSV reports.

Provides functionality to export tutor performance data, intervention history,
and analytics in multiple formats with FERPA compliance.
"""

import csv
import io
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus.flowables import HRFlowable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from src.database.models import (
    Tutor,
    TutorPerformanceMetric,
    Intervention,
    InterventionStatus,
    Session as SessionModel,
    StudentFeedback,
    ChurnPrediction,
    MetricWindow,
)

logger = logging.getLogger(__name__)


class ExportService:
    """Service for generating data exports in various formats."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def export_tutor_performance_csv(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tutor_ids: Optional[List[str]] = None,
    ) -> io.StringIO:
        """
        Export tutor performance data to CSV format.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            tutor_ids: Optional list of specific tutor IDs

        Returns:
            StringIO buffer containing CSV data
        """
        # Build query
        query = select(TutorPerformanceMetric).join(
            Tutor, TutorPerformanceMetric.tutor_id == Tutor.tutor_id
        )

        conditions = [TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY]

        if start_date:
            conditions.append(TutorPerformanceMetric.calculation_date >= start_date)
        if end_date:
            conditions.append(TutorPerformanceMetric.calculation_date <= end_date)
        if tutor_ids:
            conditions.append(TutorPerformanceMetric.tutor_id.in_(tutor_ids))

        query = query.where(and_(*conditions)).order_by(
            desc(TutorPerformanceMetric.calculation_date)
        )

        result = await self.session.execute(query)
        metrics = result.scalars().all()

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers (FERPA compliant - no PII)
        writer.writerow([
            'Tutor ID',
            'Calculation Date',
            'Performance Tier',
            'Avg Rating',
            'First Session Success Rate',
            'Reschedule Rate',
            'No-Show Rate',
            'Engagement Score',
            'Learning Objectives Met %',
            'Sessions Completed',
            'Total Session Hours',
        ])

        # Write data
        for metric in metrics:
            writer.writerow([
                metric.tutor_id,
                metric.calculation_date.strftime('%Y-%m-%d'),
                metric.performance_tier.value if metric.performance_tier else 'N/A',
                f"{metric.avg_rating:.2f}" if metric.avg_rating else 'N/A',
                f"{metric.first_session_success_rate:.1f}%" if metric.first_session_success_rate else 'N/A',
                f"{metric.reschedule_rate:.1f}%" if metric.reschedule_rate else 'N/A',
                f"{metric.no_show_rate:.1f}%" if metric.no_show_rate else 'N/A',
                f"{metric.engagement_score:.2f}" if metric.engagement_score else 'N/A',
                f"{metric.learning_objectives_met_pct:.1f}%" if metric.learning_objectives_met_pct else 'N/A',
                metric.sessions_completed or 0,
                f"{metric.total_session_hours:.1f}" if metric.total_session_hours else '0.0',
            ])

        output.seek(0)
        return output

    async def export_interventions_csv(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status_filter: Optional[InterventionStatus] = None,
    ) -> io.StringIO:
        """
        Export intervention data to CSV format.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            status_filter: Filter by intervention status

        Returns:
            StringIO buffer containing CSV data
        """
        query = select(Intervention)

        conditions = []
        if start_date:
            conditions.append(Intervention.created_date >= start_date)
        if end_date:
            conditions.append(Intervention.created_date <= end_date)
        if status_filter:
            conditions.append(Intervention.status == status_filter)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(Intervention.created_date))

        result = await self.session.execute(query)
        interventions = result.scalars().all()

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow([
            'Intervention ID',
            'Tutor ID',
            'Type',
            'Priority',
            'Status',
            'Created Date',
            'Due Date',
            'Completed Date',
            'Assigned To',
            'Outcome',
        ])

        # Write data
        for intervention in interventions:
            writer.writerow([
                intervention.intervention_id,
                intervention.tutor_id,
                intervention.intervention_type.value,
                intervention.priority.value if intervention.priority else 'N/A',
                intervention.status.value,
                intervention.created_date.strftime('%Y-%m-%d %H:%M'),
                intervention.due_date.strftime('%Y-%m-%d') if intervention.due_date else 'N/A',
                intervention.completed_date.strftime('%Y-%m-%d %H:%M') if intervention.completed_date else 'N/A',
                intervention.assigned_to or 'Automated',
                intervention.outcome or 'N/A',
            ])

        output.seek(0)
        return output

    async def export_tutor_performance_pdf(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tutor_ids: Optional[List[str]] = None,
    ) -> io.BytesIO:
        """
        Export tutor performance data to PDF format.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            tutor_ids: Optional list of specific tutor IDs

        Returns:
            BytesIO buffer containing PDF data
        """
        # Get data
        query = select(TutorPerformanceMetric).join(
            Tutor, TutorPerformanceMetric.tutor_id == Tutor.tutor_id
        )

        conditions = [TutorPerformanceMetric.window == MetricWindow.THIRTY_DAY]

        if start_date:
            conditions.append(TutorPerformanceMetric.calculation_date >= start_date)
        if end_date:
            conditions.append(TutorPerformanceMetric.calculation_date <= end_date)
        if tutor_ids:
            conditions.append(TutorPerformanceMetric.tutor_id.in_(tutor_ids))

        query = query.where(and_(*conditions)).order_by(
            desc(TutorPerformanceMetric.calculation_date)
        )

        result = await self.session.execute(query)
        metrics = result.scalars().all()

        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12,
        )

        # Title
        title = Paragraph("Tutor Performance Report", title_style)
        elements.append(title)

        # Metadata
        date_range = f"{start_date.strftime('%Y-%m-%d') if start_date else 'Beginning'} to {end_date.strftime('%Y-%m-%d') if end_date else 'Present'}"
        meta_data = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Date Range:', date_range],
            ['Total Tutors:', str(len(set(m.tutor_id for m in metrics)))],
            ['Total Records:', str(len(metrics))],
        ]
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 0.3*inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        elements.append(Spacer(1, 0.3*inch))

        # Performance Data Table
        heading = Paragraph("Performance Metrics", heading_style)
        elements.append(heading)

        # Table data (limited to first 50 records for PDF)
        table_data = [[
            'Tutor ID',
            'Date',
            'Tier',
            'Rating',
            'Sessions',
            'Engagement',
        ]]

        for metric in metrics[:50]:  # Limit to 50 for readability
            table_data.append([
                metric.tutor_id[:8] + '...' if len(metric.tutor_id) > 8 else metric.tutor_id,
                metric.calculation_date.strftime('%Y-%m-%d'),
                metric.performance_tier.value[:4] if metric.performance_tier else 'N/A',
                f"{metric.avg_rating:.1f}" if metric.avg_rating else 'N/A',
                str(metric.sessions_completed or 0),
                f"{metric.engagement_score:.1f}" if metric.engagement_score else 'N/A',
            ])

        # Create table
        data_table = Table(table_data, colWidths=[1.2*inch, 1*inch, 0.8*inch, 0.7*inch, 0.8*inch, 0.9*inch])
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(data_table)

        if len(metrics) > 50:
            note = Paragraph(
                f"<i>Note: Showing first 50 of {len(metrics)} records. Download CSV for complete data.</i>",
                styles['Normal']
            )
            elements.append(Spacer(1, 0.2*inch))
            elements.append(note)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    async def export_analytics_summary_pdf(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> io.BytesIO:
        """
        Export comprehensive analytics summary to PDF.

        Args:
            start_date: Start date for report
            end_date: End date for report

        Returns:
            BytesIO buffer containing PDF data
        """
        # Gather summary statistics
        # Total tutors
        tutor_count_result = await self.session.execute(
            select(func.count(Tutor.tutor_id)).where(
                Tutor.onboarding_date <= end_date
            )
        )
        total_tutors = tutor_count_result.scalar()

        # Total sessions in period
        session_count_result = await self.session.execute(
            select(func.count(SessionModel.session_id)).where(
                and_(
                    SessionModel.scheduled_start >= start_date,
                    SessionModel.scheduled_start <= end_date,
                    SessionModel.no_show == False
                )
            )
        )
        total_sessions = session_count_result.scalar()

        # Average rating
        avg_rating_result = await self.session.execute(
            select(func.avg(StudentFeedback.overall_rating)).where(
                and_(
                    StudentFeedback.feedback_date >= start_date,
                    StudentFeedback.feedback_date <= end_date
                )
            )
        )
        avg_rating = avg_rating_result.scalar() or 0.0

        # High risk tutors
        high_risk_result = await self.session.execute(
            select(func.count(ChurnPrediction.prediction_id)).where(
                and_(
                    ChurnPrediction.prediction_date >= start_date,
                    ChurnPrediction.prediction_date <= end_date,
                    ChurnPrediction.risk_prediction == 1
                )
            )
        )
        high_risk_count = high_risk_result.scalar()

        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
        )

        # Title
        title = Paragraph("TutorMax Analytics Summary", title_style)
        elements.append(title)

        # Period info
        period_text = f"<b>Reporting Period:</b> {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
        period_para = Paragraph(period_text, styles['Normal'])
        elements.append(period_para)
        elements.append(Spacer(1, 0.3*inch))

        # Summary stats
        summary_data = [
            ['Metric', 'Value'],
            ['Total Active Tutors', f"{total_tutors:,}"],
            ['Total Sessions', f"{total_sessions:,}"],
            ['Average Session Rating', f"{avg_rating:.2f} / 5.0"],
            ['High-Risk Tutors', f"{high_risk_count}"],
        ]

        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(summary_table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
