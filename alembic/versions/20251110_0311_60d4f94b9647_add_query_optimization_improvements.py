"""add_query_optimization_improvements

Revision ID: 60d4f94b9647
Revises: b856876663bb
Create Date: 2025-11-10 03:11:00.000000

Additional query optimizations:
- Add composite index on users table for role-based filtering
- Add index on created_at/updated_at for audit queries
- Add partial index for active users only
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '60d4f94b9647'
down_revision = 'b856876663bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add strategic indexes for query optimization.
    """

    # ==================== Users Table ====================
    # Composite index for active users (most common filter)
    op.create_index(
        'idx_users_is_active_email',
        'users',
        ['is_active', 'email'],
        postgresql_using='btree'
    )

    # Index on created_at for user registration analytics
    op.create_index(
        'idx_users_created_at',
        'users',
        ['created_at'],
        postgresql_using='btree'
    )

    # Partial index for active users (optimize active user queries)
    op.create_index(
        'idx_users_active_only',
        'users',
        ['id', 'email', 'full_name'],
        postgresql_using='btree',
        postgresql_where=sa.text("is_active = true")
    )

    # Index for last_login for inactive user cleanup
    op.create_index(
        'idx_users_last_login',
        'users',
        ['last_login'],
        postgresql_using='btree',
        postgresql_where=sa.text("last_login IS NOT NULL")
    )

    # ==================== Tutors Table ====================
    # Index on created_at for onboarding analytics
    op.create_index(
        'idx_tutors_onboarding_date',
        'tutors',
        ['onboarding_date'],
        postgresql_using='btree'
    )

    # Composite index for active tutors by subject
    op.create_index(
        'idx_tutors_status_created',
        'tutors',
        ['status', 'created_at'],
        postgresql_using='btree'
    )

    # ==================== Sessions Table ====================
    # Index for date range queries (common in dashboards)
    op.create_index(
        'idx_sessions_date_range',
        'sessions',
        ['scheduled_start', 'created_at'],
        postgresql_using='btree'
    )

    # Partial index for completed sessions only (most common analytics)
    op.create_index(
        'idx_sessions_completed',
        'sessions',
        ['tutor_id', 'scheduled_start', 'subject'],
        postgresql_using='btree',
        postgresql_where=sa.text("no_show = false AND actual_start IS NOT NULL")
    )

    # ==================== Student Feedback ====================
    # Index on session_id for quick feedback lookup
    op.create_index(
        'idx_feedback_session',
        'student_feedback',
        ['session_id'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    """
    Drop strategic indexes.
    """

    # Users
    op.drop_index('idx_users_is_active_email', 'users')
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_active_only', 'users')
    op.drop_index('idx_users_last_login', 'users')

    # Tutors
    op.drop_index('idx_tutors_onboarding_date', 'tutors')
    op.drop_index('idx_tutors_status_created', 'tutors')

    # Sessions
    op.drop_index('idx_sessions_date_range', 'sessions')
    op.drop_index('idx_sessions_completed', 'sessions')

    # Feedback
    op.drop_index('idx_feedback_session', 'student_feedback')
