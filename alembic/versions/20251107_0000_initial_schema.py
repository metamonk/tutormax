"""Initial database schema for TutorMax

Revision ID: 20251107_0000
Revises:
Create Date: 2025-11-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251107_0000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables for TutorMax system."""

    # Create tutors table
    op.create_table(
        'tutors',
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('onboarding_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('subjects', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('education_level', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('baseline_sessions_per_week', sa.Float(), nullable=True),
        sa.Column('behavioral_archetype', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('tutor_id')
    )
    op.create_index('ix_tutors_email', 'tutors', ['email'], unique=True)
    op.create_index('ix_tutors_status', 'tutors', ['status'], unique=False)

    # Create students table
    op.create_table(
        'students',
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('grade_level', sa.String(length=50), nullable=True),
        sa.Column('subjects_interested', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('student_id')
    )

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('session_number', sa.Integer(), nullable=False),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('session_type', sa.String(length=50), nullable=False),
        sa.Column('tutor_initiated_reschedule', sa.Boolean(), nullable=False),
        sa.Column('no_show', sa.Boolean(), nullable=False),
        sa.Column('late_start_minutes', sa.Integer(), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('learning_objectives_met', sa.Boolean(), nullable=True),
        sa.Column('technical_issues', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.tutor_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index('ix_sessions_tutor_id', 'sessions', ['tutor_id'], unique=False)
    op.create_index('ix_sessions_student_id', 'sessions', ['student_id'], unique=False)
    op.create_index('ix_sessions_scheduled_start', 'sessions', ['scheduled_start'], unique=False)
    op.create_index('ix_sessions_subject', 'sessions', ['subject'], unique=False)

    # Create student_feedback table
    op.create_table(
        'student_feedback',
        sa.Column('feedback_id', sa.String(length=50), nullable=False),
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('overall_rating', sa.Integer(), nullable=False),
        sa.Column('is_first_session', sa.Boolean(), nullable=False),
        sa.Column('subject_knowledge_rating', sa.Integer(), nullable=True),
        sa.Column('communication_rating', sa.Integer(), nullable=True),
        sa.Column('patience_rating', sa.Integer(), nullable=True),
        sa.Column('engagement_rating', sa.Integer(), nullable=True),
        sa.Column('helpfulness_rating', sa.Integer(), nullable=True),
        sa.Column('would_recommend', sa.Boolean(), nullable=True),
        sa.Column('improvement_areas', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('free_text_feedback', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.tutor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('feedback_id')
    )
    op.create_index('ix_student_feedback_session_id', 'student_feedback', ['session_id'], unique=True)
    op.create_index('ix_student_feedback_student_id', 'student_feedback', ['student_id'], unique=False)
    op.create_index('ix_student_feedback_tutor_id', 'student_feedback', ['tutor_id'], unique=False)

    # Create tutor_performance_metrics table
    op.create_table(
        'tutor_performance_metrics',
        sa.Column('metric_id', sa.String(length=50), nullable=False),
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('calculation_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window', sa.String(length=20), nullable=False),
        sa.Column('sessions_completed', sa.Integer(), nullable=False),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('first_session_success_rate', sa.Float(), nullable=True),
        sa.Column('reschedule_rate', sa.Float(), nullable=True),
        sa.Column('no_show_count', sa.Integer(), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('learning_objectives_met_pct', sa.Float(), nullable=True),
        sa.Column('response_time_avg_minutes', sa.Float(), nullable=True),
        sa.Column('performance_tier', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.tutor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('metric_id')
    )
    op.create_index('ix_tutor_performance_metrics_tutor_id', 'tutor_performance_metrics', ['tutor_id'], unique=False)
    op.create_index('ix_tutor_performance_metrics_calculation_date', 'tutor_performance_metrics', ['calculation_date'], unique=False)

    # Create churn_predictions table
    op.create_table(
        'churn_predictions',
        sa.Column('prediction_id', sa.String(length=50), nullable=False),
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('churn_score', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('window_1day_probability', sa.Float(), nullable=True),
        sa.Column('window_7day_probability', sa.Float(), nullable=True),
        sa.Column('window_30day_probability', sa.Float(), nullable=True),
        sa.Column('window_90day_probability', sa.Float(), nullable=True),
        sa.Column('contributing_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.tutor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('prediction_id')
    )
    op.create_index('ix_churn_predictions_tutor_id', 'churn_predictions', ['tutor_id'], unique=False)
    op.create_index('ix_churn_predictions_prediction_date', 'churn_predictions', ['prediction_date'], unique=False)
    op.create_index('ix_churn_predictions_risk_level', 'churn_predictions', ['risk_level'], unique=False)

    # Create interventions table
    op.create_table(
        'interventions',
        sa.Column('intervention_id', sa.String(length=50), nullable=False),
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('intervention_type', sa.String(length=100), nullable=False),
        sa.Column('trigger_reason', sa.Text(), nullable=True),
        sa.Column('recommended_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assigned_to', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.tutor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('intervention_id')
    )
    op.create_index('ix_interventions_tutor_id', 'interventions', ['tutor_id'], unique=False)
    op.create_index('ix_interventions_status', 'interventions', ['status'], unique=False)

    # Create tutor_events table
    op.create_table(
        'tutor_events',
        sa.Column('event_id', sa.String(length=50), nullable=False),
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.tutor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('event_id')
    )
    op.create_index('ix_tutor_events_tutor_id', 'tutor_events', ['tutor_id'], unique=False)
    op.create_index('ix_tutor_events_event_type', 'tutor_events', ['event_type'], unique=False)
    op.create_index('ix_tutor_events_event_timestamp', 'tutor_events', ['event_timestamp'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('tutor_events')
    op.drop_table('interventions')
    op.drop_table('churn_predictions')
    op.drop_table('tutor_performance_metrics')
    op.drop_table('student_feedback')
    op.drop_table('sessions')
    op.drop_table('students')
    op.drop_table('tutors')
