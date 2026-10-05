"""Add order_date and distance_km to orders table

Revision ID: 003_add_order_date_and_distance
Revises: 002_add_delivery_price
Create Date: 2026-10-05 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_order_date_and_distance'
down_revision: Union[str, None] = '002_add_delivery_price'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add order_date column (nullable for safe migration across databases)
    op.add_column(
        'orders',
        sa.Column(
            'order_date',
            sa.Date(),
            nullable=True,
        )
    )

    # 2. Backfill existing records: populate order_date with created_at::date
    op.execute(
        sa.text("UPDATE orders SET order_date = created_at::date WHERE order_date IS NULL")
    )

    # 3. Set order_date to NOT NULL with CURRENT_DATE server default, and create index
    op.alter_column(
        'orders',
        'order_date',
        nullable=False,
        server_default=sa.text('CURRENT_DATE'),
    )
    op.create_index(op.f('ix_orders_order_date'), 'orders', ['order_date'], unique=False)

    # 4. Add distance_km column for road routing mileage
    op.add_column(
        'orders',
        sa.Column(
            'distance_km',
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        )
    )


def downgrade() -> None:
    op.drop_column('orders', 'distance_km')
    op.drop_index(op.f('ix_orders_order_date'), table_name='orders')
    op.drop_column('orders', 'order_date')
