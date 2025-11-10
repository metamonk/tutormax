"""add first session prediction models

Revision ID: 20251109_0004
Revises: 20251109_0003
Create Date: 2025-11-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251109_0004'
down_revision: Union[str, None] = '20251109_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create first_session_predictions table
    op.create_table(
        'first_session_predictions',
        sa.Column('prediction_id', sa.String(length=50), nullable=False),
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('tutor_id', sa.String(length=50), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('risk_probability', sa.Float(), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('risk_prediction', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('top_risk_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('alert_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('alert_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_rating', sa.Integer(), nullable=True),
        sa.Column('actual_poor_session', sa.Boolean(), nullable=True),
        sa.Column('prediction_correct', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.tutor_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('prediction_id'),
        sa.UniqueConstraint('session_id')
    )

    # Create indexes
    op.create_index('ix_first_session_predictions_session_id', 'first_session_predictions', ['session_id'])
    op.create_index('ix_first_session_predictions_tutor_id', 'first_session_predictions', ['tutor_id'])
    op.create_index('ix_first_session_predictions_student_id', 'first_session_predictions', ['student_id'])
    op.create_index('ix_first_session_predictions_prediction_date', 'first_session_predictions', ['prediction_date'])
    op.create_index('ix_first_session_predictions_risk_level', 'first_session_predictions', ['risk_level'])

    # Create model_performance_logs table
    op.create_table(
        'model_performance_logs',
        sa.Column('log_id', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('evaluation_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('precision', sa.Float(), nullable=False),
        sa.Column('recall', sa.Float(), nullable=False),
        sa.Column('f1_score', sa.Float(), nullable=False),
        sa.Column('auc_roc', sa.Float(), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('time_window_days', sa.Integer(), nullable=False),
        sa.Column('metrics_detail', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('log_id')
    )

    # Create indexes
    op.create_index('ix_model_performance_logs_model_type', 'model_performance_logs', ['model_type'])
    op.create_index('ix_model_performance_logs_evaluation_date', 'model_performance_logs', ['evaluation_date'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_model_performance_logs_evaluation_date', table_name='model_performance_logs')
    op.drop_index('ix_model_performance_logs_model_type', table_name='model_performance_logs')
    op.drop_index('ix_first_session_predictions_risk_level', table_name='first_session_predictions')
    op.drop_index('ix_first_session_predictions_prediction_date', table_name='first_session_predictions')
    op.drop_index('ix_first_session_predictions_student_id', table_name='first_session_predictions')
    op.drop_index('ix_first_session_predictions_tutor_id', table_name='first_session_predictions')
    op.drop_index('ix_first_session_predictions_session_id', table_name='first_session_predictions')

    # Drop tables
    op.drop_table('model_performance_logs')
    op.drop_table('first_session_predictions')
