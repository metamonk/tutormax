"""add authentication models

Revision ID: 20251108_0001
Revises: 20251107_0000
Create Date: 2025-11-08 22:45:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251108_0001'
down_revision = '20251107_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table (FastAPI-Users compatible)
    op.create_table(
        'users',
        # FastAPI-Users required fields
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),

        # Custom TutorMax fields
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('oauth_provider', sa.String(length=50), nullable=True),  # Nullable for local auth
        sa.Column('oauth_subject', sa.String(length=255), nullable=True),
        sa.Column('roles', postgresql.ARRAY(sa.String(length=50)), nullable=False, server_default='{}'),
        sa.Column('tutor_id', sa.String(length=50), nullable=True),
        sa.Column('student_id', sa.String(length=50), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Foreign keys
        sa.ForeignKeyConstraint(['tutor_id'], ['tutors.tutor_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ondelete='SET NULL'),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('tutor_id'),
        sa.UniqueConstraint('student_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),  # Changed to Integer
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('request_method', sa.String(length=10), nullable=True),
        sa.Column('request_path', sa.String(length=500), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),  # Changed to users.id
        sa.PrimaryKeyConstraint('log_id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)


def downgrade() -> None:
    # Drop audit_logs table
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
