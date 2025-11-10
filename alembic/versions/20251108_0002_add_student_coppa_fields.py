"""Add COPPA compliance fields to Student model

Revision ID: 20251108_0002
Revises: 20251108_0001
Create Date: 2024-11-08 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251108_0002'
down_revision: Union[str, None] = '20251108_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add COPPA compliance fields to students table."""
    # Add COPPA compliance fields
    op.add_column('students', sa.Column('is_under_13', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('students', sa.Column('parent_email', sa.String(length=255), nullable=True))
    op.add_column('students', sa.Column('parent_consent_given', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('students', sa.Column('parent_consent_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('students', sa.Column('parent_consent_ip', sa.String(length=45), nullable=True))


def downgrade() -> None:
    """Remove COPPA compliance fields from students table."""
    op.drop_column('students', 'parent_consent_ip')
    op.drop_column('students', 'parent_consent_date')
    op.drop_column('students', 'parent_consent_given')
    op.drop_column('students', 'parent_email')
    op.drop_column('students', 'is_under_13')
