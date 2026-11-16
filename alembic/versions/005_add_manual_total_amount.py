"""Add calculated_total_amount and is_total_manual to orders table

Revision ID: 005_add_manual_total_amount
Revises: 004_add_delivery_price_per_km
Create Date: 2026-10-08 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_manual_total_amount'
down_revision: Union[str, None] = '004_add_delivery_price_per_km'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add calculated_total_amount column
    op.add_column(
        'orders',
        sa.Column(
            'calculated_total_amount',
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        )
    )

    # 2. Backfill existing records: calculated_total_amount = total_amount
    op.execute(
        sa.text("UPDATE orders SET calculated_total_amount = total_amount WHERE calculated_total_amount IS NULL")
    )

    # 3. Alter column to NOT NULL with server default 0.00
    op.alter_column(
        'orders',
        'calculated_total_amount',
        nullable=False,
        server_default='0.00',
    )

    # 4. Add is_total_manual column
    op.add_column(
        'orders',
        sa.Column(
            'is_total_manual',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        )
    )


def downgrade() -> None:
    op.drop_column('orders', 'is_total_manual')
    op.drop_column('orders', 'calculated_total_amount')
