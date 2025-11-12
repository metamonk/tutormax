"""Add email tracking models for enhanced email automation

Revision ID: 20251109_0003
Revises: 20251109_0002
Create Date: 2025-11-09 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251109_0003'
down_revision: Union[str, None] = '20251109_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email tracking tables."""

    # Email campaigns table
    op.create_table(
        'email_campaigns',
        sa.Column('campaign_id', sa.String(50), primary_key=True),
        sa.Column('campaign_name', sa.String(200), nullable=False),
        sa.Column('campaign_type', sa.String(50), nullable=False),  # weekly_digest, monthly_summary, etc.
        sa.Column('template_type', sa.String(50), nullable=False),
        sa.Column('template_version', sa.String(20), nullable=False, server_default='v1'),
        sa.Column('ab_test_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ab_variant_a_weight', sa.Float(), nullable=True),
        sa.Column('ab_variant_b_weight', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),  # draft, scheduled, sending, completed, cancelled
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_audience', postgresql.JSONB(), nullable=True),
        sa.Column('total_recipients', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_opened', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_clicked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_bounced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unsubscribes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_email_campaigns_status', 'email_campaigns', ['status'])
    op.create_index('ix_email_campaigns_scheduled_at', 'email_campaigns', ['scheduled_at'])
    op.create_index('ix_email_campaigns_campaign_type', 'email_campaigns', ['campaign_type'])

    # Email messages table (individual emails sent)
    op.create_table(
        'email_messages',
        sa.Column('message_id', sa.String(50), primary_key=True),
        sa.Column('campaign_id', sa.String(50), sa.ForeignKey('email_campaigns.campaign_id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('recipient_email', sa.String(255), nullable=False, index=True),
        sa.Column('recipient_id', sa.String(50), nullable=True, index=True),  # tutor_id, student_id, user_id
        sa.Column('recipient_type', sa.String(20), nullable=True),  # tutor, student, manager, etc.
        sa.Column('template_type', sa.String(50), nullable=False),
        sa.Column('template_version', sa.String(20), nullable=False),
        sa.Column('ab_variant', sa.String(10), nullable=True),  # A, B, or null
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # queued, sending, sent, delivered, bounced, failed
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),  # low, medium, high, critical
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bounced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bounce_type', sa.String(20), nullable=True),  # hard, soft, complaint
        sa.Column('bounce_reason', sa.Text(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('open_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('click_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unsubscribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_email_messages_status', 'email_messages', ['status'])
    op.create_index('ix_email_messages_sent_at', 'email_messages', ['sent_at'])
    op.create_index('ix_email_messages_template_type', 'email_messages', ['template_type'])

    # Email tracking events table (detailed event log)
    op.create_table(
        'email_tracking_events',
        sa.Column('event_id', sa.String(50), primary_key=True),
        sa.Column('message_id', sa.String(50), sa.ForeignKey('email_messages.message_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(20), nullable=False),  # sent, delivered, opened, clicked, bounced, failed, unsubscribed
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('link_url', sa.Text(), nullable=True),  # For click events
        sa.Column('event_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_email_tracking_events_event_type', 'email_tracking_events', ['event_type'])
    op.create_index('ix_email_tracking_events_event_time', 'email_tracking_events', ['event_time'])

    # Email preferences table (unsubscribe management)
    op.create_table(
        'email_preferences',
        sa.Column('preference_id', sa.String(50), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('tutor_id', sa.String(50), sa.ForeignKey('tutors.tutor_id', ondelete='CASCADE'), nullable=True),
        sa.Column('student_id', sa.String(50), sa.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=True),
        sa.Column('unsubscribed_all', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('feedback_reminders', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('session_checkins', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('performance_reports', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('weekly_digests', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('monthly_summaries', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('marketing_emails', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('system_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('unsubscribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Email workflow state table (for tracking automated workflows)
    op.create_table(
        'email_workflow_state',
        sa.Column('workflow_id', sa.String(50), primary_key=True),
        sa.Column('workflow_type', sa.String(50), nullable=False),  # feedback_reminder, first_session_checkin, rescheduling_alert
        sa.Column('entity_type', sa.String(20), nullable=False),  # session, tutor, student
        sa.Column('entity_id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # pending, triggered, completed, cancelled
        sa.Column('trigger_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message_id', sa.String(50), sa.ForeignKey('email_messages.message_id', ondelete='SET NULL'), nullable=True),
        sa.Column('context_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_email_workflow_state_workflow_type', 'email_workflow_state', ['workflow_type'])
    op.create_index('ix_email_workflow_state_status', 'email_workflow_state', ['status'])
    op.create_index('ix_email_workflow_state_trigger_at', 'email_workflow_state', ['trigger_at'])
    op.create_index('ix_email_workflow_state_entity', 'email_workflow_state', ['entity_type', 'entity_id'])


def downgrade() -> None:
    """Remove email tracking tables."""
    op.drop_table('email_workflow_state')
    op.drop_table('email_preferences')
    op.drop_table('email_tracking_events')
    op.drop_table('email_messages')
    op.drop_table('email_campaigns')
