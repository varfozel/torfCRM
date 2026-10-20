"""Add unavailable_dates table for calendar undesirable dates

Revision ID: 006_add_unavailable_dates
Revises: 005_add_manual_total_amount
Create Date: 2026-10-20 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_add_unavailable_dates'
down_revision: Union[str, None] = '005_add_manual_total_amount'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'unavailable_dates',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), primary_key=True, autoincrement=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_unavailable_dates_date'), 'unavailable_dates', ['date'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_unavailable_dates_date'), table_name='unavailable_dates')
    op.drop_table('unavailable_dates')
