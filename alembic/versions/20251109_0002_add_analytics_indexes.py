"""Add analytics performance indexes

Revision ID: 20251109_0002
Revises: 20251109_0001
Create Date: 2025-11-09 18:30:00.000000

Adds database indexes to optimize analytics queries for Task 9.
Improves performance of churn heatmaps, cohort analysis, and intervention effectiveness queries.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251109_0002'
down_revision = '20251109_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add indexes for analytics performance optimization.

    Indexes target:
    - Churn prediction queries (date range + risk level)
    - Intervention effectiveness queries (date range + type + status)
    - Cohort analysis queries (onboarding date ranges)
    - Session-based metrics (date ranges)
    """

    # Churn predictions - composite index for heatmap queries
    op.create_index(
        'idx_churn_pred_date_risk',
        'churn_predictions',
        ['prediction_date', 'risk_level'],
        unique=False
    )

    # Interventions - composite index for effectiveness analysis
    op.create_index(
        'idx_intervention_date_type_status',
        'interventions',
        ['recommended_date', 'intervention_type', 'status'],
        unique=False
    )

    # Interventions - index for completion analysis
    op.create_index(
        'idx_intervention_completed',
        'interventions',
        ['completed_date', 'outcome'],
        unique=False
    )

    # Tutors - index for cohort analysis
    op.create_index(
        'idx_tutor_onboarding_status',
        'tutors',
        ['onboarding_date', 'status'],
        unique=False
    )

    # Sessions - index for time-based analytics
    op.create_index(
        'idx_session_scheduled_tutor',
        'sessions',
        ['scheduled_start', 'tutor_id'],
        unique=False
    )

    # Performance metrics - index for trend analysis
    op.create_index(
        'idx_perf_metric_date_window',
        'tutor_performance_metrics',
        ['calculation_date', 'window'],
        unique=False
    )

    # Feedback - index for rating trends
    op.create_index(
        'idx_feedback_submitted_tutor',
        'student_feedback',
        ['submitted_at', 'tutor_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove analytics indexes."""

    op.drop_index('idx_feedback_submitted_tutor', table_name='student_feedback')
    op.drop_index('idx_perf_metric_date_window', table_name='tutor_performance_metrics')
    op.drop_index('idx_session_scheduled_tutor', table_name='sessions')
    op.drop_index('idx_tutor_onboarding_status', table_name='tutors')
    op.drop_index('idx_intervention_completed', table_name='interventions')
    op.drop_index('idx_intervention_date_type_status', table_name='interventions')
    op.drop_index('idx_churn_pred_date_risk', table_name='churn_predictions')
