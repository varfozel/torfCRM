"""Add delivery_price_per_km to orders table

Revision ID: 004_add_delivery_price_per_km
Revises: 003_add_order_date_and_distance
Create Date: 2026-10-05 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_delivery_price_per_km'
down_revision: Union[str, None] = '003_add_order_date_and_distance'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'orders',
        sa.Column(
            'delivery_price_per_km',
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        )
    )


def downgrade() -> None:
    op.drop_column('orders', 'delivery_price_per_km')
