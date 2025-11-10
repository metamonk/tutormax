"""Add indexes for audit log performance

Revision ID: 20251109_0001
Revises: 20251108_0001
Create Date: 2025-11-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251109_0001'
down_revision = '20251108_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite indexes for common audit log queries."""
    # Index for user activity queries (user_id + timestamp)
    op.create_index(
        'ix_audit_logs_user_timestamp',
        'audit_logs',
        ['user_id', 'timestamp'],
        unique=False
    )

    # Index for resource access queries (resource_type + resource_id + timestamp)
    op.create_index(
        'ix_audit_logs_resource_timestamp',
        'audit_logs',
        ['resource_type', 'resource_id', 'timestamp'],
        unique=False
    )

    # Index for action-based queries (action + timestamp)
    op.create_index(
        'ix_audit_logs_action_timestamp',
        'audit_logs',
        ['action', 'timestamp'],
        unique=False
    )

    # Index for IP-based queries (ip_address + timestamp)
    op.create_index(
        'ix_audit_logs_ip_timestamp',
        'audit_logs',
        ['ip_address', 'timestamp'],
        unique=False
    )

    # Index for success status filtering (success + timestamp)
    op.create_index(
        'ix_audit_logs_success_timestamp',
        'audit_logs',
        ['success', 'timestamp'],
        unique=False
    )


def downgrade() -> None:
    """Remove audit log indexes."""
    op.drop_index('ix_audit_logs_success_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_ip_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_timestamp', table_name='audit_logs')
