"""add_monitoring_tables

Revision ID: b856876663bb
Revises: 20251109_0005
Create Date: 2025-11-10 00:32:45.137727+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'b856876663bb'
down_revision: Union[str, None] = '20251109_0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create service_health_checks table
    op.create_table(
        'service_health_checks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('service_name', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_service_health_checks_service_name'),
        'service_health_checks',
        ['service_name']
    )
    op.create_index(
        op.f('ix_service_health_checks_checked_at'),
        'service_health_checks',
        ['checked_at']
    )

    # Create sla_metrics table
    op.create_table(
        'sla_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(length=50), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=True),
        sa.Column('meets_sla', sa.Boolean(), nullable=False),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_sla_metrics_metric_name'),
        'sla_metrics',
        ['metric_name']
    )
    op.create_index(
        op.f('ix_sla_metrics_recorded_at'),
        'sla_metrics',
        ['recorded_at']
    )


def downgrade() -> None:
    # Drop sla_metrics table
    op.drop_index(op.f('ix_sla_metrics_recorded_at'), table_name='sla_metrics')
    op.drop_index(op.f('ix_sla_metrics_metric_name'), table_name='sla_metrics')
    op.drop_table('sla_metrics')

    # Drop service_health_checks table
    op.drop_index(op.f('ix_service_health_checks_checked_at'), table_name='service_health_checks')
    op.drop_index(op.f('ix_service_health_checks_service_name'), table_name='service_health_checks')
    op.drop_table('service_health_checks')
