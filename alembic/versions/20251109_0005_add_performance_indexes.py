"""Add performance indexes for query optimization

Revision ID: 20251109_0005
Revises: 20251109_0004
Create Date: 2025-11-09 00:00:00.000000

Adds indexes to optimize common query patterns:
- Dashboard queries (tutor metrics by date range)
- Prediction lookups (by tutor_id and date)
- Session statistics (by tutor and scheduled_start)
- Feedback analysis (by tutor and submission date)
- Intervention tracking (by status and due_date)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251109_0005'
down_revision = '20251109_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create performance indexes for optimized query patterns.
    """

    # ==================== Tutor Performance Metrics ====================
    # Composite index for dashboard queries filtering by tutor and date range
    op.create_index(
        'idx_performance_metrics_tutor_date',
        'tutor_performance_metrics',
        ['tutor_id', 'calculation_date'],
        postgresql_using='btree'
    )

    # Index for filtering by performance tier (dashboard filters)
    op.create_index(
        'idx_performance_metrics_tier',
        'tutor_performance_metrics',
        ['performance_tier'],
        postgresql_using='btree',
        postgresql_where=sa.text("performance_tier IS NOT NULL")
    )

    # Composite index for window-based queries
    op.create_index(
        'idx_performance_metrics_window_date',
        'tutor_performance_metrics',
        ['window', 'calculation_date'],
        postgresql_using='btree'
    )

    # ==================== Churn Predictions ====================
    # Composite index for latest predictions by tutor
    op.create_index(
        'idx_churn_predictions_tutor_date',
        'churn_predictions',
        ['tutor_id', 'prediction_date'],
        postgresql_using='btree'
    )

    # Index for filtering by risk level (critical alerts)
    op.create_index(
        'idx_churn_predictions_risk_date',
        'churn_predictions',
        ['risk_level', 'prediction_date'],
        postgresql_using='btree'
    )

    # Index for model version tracking
    op.create_index(
        'idx_churn_predictions_model_version',
        'churn_predictions',
        ['model_version'],
        postgresql_using='btree'
    )

    # ==================== Sessions ====================
    # Composite index for tutor session history queries
    op.create_index(
        'idx_sessions_tutor_scheduled',
        'sessions',
        ['tutor_id', 'scheduled_start'],
        postgresql_using='btree'
    )

    # Index for student session history
    op.create_index(
        'idx_sessions_student_scheduled',
        'sessions',
        ['student_id', 'scheduled_start'],
        postgresql_using='btree'
    )

    # Index for session completion analysis (performance metrics)
    op.create_index(
        'idx_sessions_completion_flags',
        'sessions',
        ['tutor_id', 'no_show', 'tutor_initiated_reschedule'],
        postgresql_using='btree'
    )

    # Covering index for session statistics queries
    op.execute("""
        CREATE INDEX idx_sessions_stats_covering
        ON sessions (tutor_id, scheduled_start)
        INCLUDE (duration_minutes, engagement_score, learning_objectives_met, no_show, late_start_minutes)
    """)

    # ==================== Student Feedback ====================
    # Composite index for tutor feedback analysis
    op.create_index(
        'idx_feedback_tutor_submitted',
        'student_feedback',
        ['tutor_id', 'submitted_at'],
        postgresql_using='btree'
    )

    # Index for first session feedback tracking
    op.create_index(
        'idx_feedback_first_session',
        'student_feedback',
        ['tutor_id', 'is_first_session', 'submitted_at'],
        postgresql_using='btree'
    )

    # Index for low rating alerts
    op.create_index(
        'idx_feedback_low_ratings',
        'student_feedback',
        ['overall_rating', 'submitted_at'],
        postgresql_using='btree',
        postgresql_where=sa.text('overall_rating <= 3')
    )

    # ==================== Interventions ====================
    # Composite index for active interventions by tutor
    op.create_index(
        'idx_interventions_tutor_status',
        'interventions',
        ['tutor_id', 'status'],
        postgresql_using='btree'
    )

    # Index for pending interventions by due date
    op.create_index(
        'idx_interventions_pending_due',
        'interventions',
        ['status', 'due_date'],
        postgresql_using='btree',
        postgresql_where=sa.text("status = 'pending'")
    )

    # Index for intervention type analysis
    op.create_index(
        'idx_interventions_type_status',
        'interventions',
        ['intervention_type', 'status'],
        postgresql_using='btree'
    )

    # ==================== Tutor Events ====================
    # Composite index for event history by tutor
    op.create_index(
        'idx_events_tutor_timestamp',
        'tutor_events',
        ['tutor_id', 'event_timestamp'],
        postgresql_using='btree'
    )

    # Index for event type analysis
    op.create_index(
        'idx_events_type_timestamp',
        'tutor_events',
        ['event_type', 'event_timestamp'],
        postgresql_using='btree'
    )

    # GIN index for event metadata JSONB queries
    op.create_index(
        'idx_events_metadata_gin',
        'tutor_events',
        ['metadata'],
        postgresql_using='gin'
    )

    # ==================== Notifications ====================
    # Index for pending notifications
    op.create_index(
        'idx_notifications_pending',
        'notifications',
        ['status', 'priority', 'created_at'],
        postgresql_using='btree',
        postgresql_where=sa.text("status = 'pending'")
    )

    # Index for recipient notification history
    op.create_index(
        'idx_notifications_recipient',
        'notifications',
        ['recipient_id', 'created_at'],
        postgresql_using='btree'
    )

    # ==================== Audit Logs ====================
    # Composite index for user activity tracking (already created in previous migration)
    # Adding additional index for action-based queries
    op.create_index(
        'idx_audit_logs_action_timestamp',
        'audit_logs',
        ['action', 'timestamp'],
        postgresql_using='btree'
    )

    # Index for resource access tracking
    op.create_index(
        'idx_audit_logs_resource',
        'audit_logs',
        ['resource_type', 'resource_id', 'timestamp'],
        postgresql_using='btree',
        postgresql_where=sa.text('resource_type IS NOT NULL')
    )


def downgrade() -> None:
    """
    Drop performance indexes.
    """

    # Tutor Performance Metrics
    op.drop_index('idx_performance_metrics_tutor_date', 'tutor_performance_metrics')
    op.drop_index('idx_performance_metrics_tier', 'tutor_performance_metrics')
    op.drop_index('idx_performance_metrics_window_date', 'tutor_performance_metrics')

    # Churn Predictions
    op.drop_index('idx_churn_predictions_tutor_date', 'churn_predictions')
    op.drop_index('idx_churn_predictions_risk_date', 'churn_predictions')
    op.drop_index('idx_churn_predictions_model_version', 'churn_predictions')

    # Sessions
    op.drop_index('idx_sessions_tutor_scheduled', 'sessions')
    op.drop_index('idx_sessions_student_scheduled', 'sessions')
    op.drop_index('idx_sessions_completion_flags', 'sessions')
    op.drop_index('idx_sessions_stats_covering', 'sessions')

    # Student Feedback
    op.drop_index('idx_feedback_tutor_submitted', 'student_feedback')
    op.drop_index('idx_feedback_first_session', 'student_feedback')
    op.drop_index('idx_feedback_low_ratings', 'student_feedback')

    # Interventions
    op.drop_index('idx_interventions_tutor_status', 'interventions')
    op.drop_index('idx_interventions_pending_due', 'interventions')
    op.drop_index('idx_interventions_type_status', 'interventions')

    # Tutor Events
    op.drop_index('idx_events_tutor_timestamp', 'tutor_events')
    op.drop_index('idx_events_type_timestamp', 'tutor_events')
    op.drop_index('idx_events_metadata_gin', 'tutor_events')

    # Notifications
    op.drop_index('idx_notifications_pending', 'notifications')
    op.drop_index('idx_notifications_recipient', 'notifications')

    # Audit Logs
    op.drop_index('idx_audit_logs_action_timestamp', 'audit_logs')
    op.drop_index('idx_audit_logs_resource', 'audit_logs')
