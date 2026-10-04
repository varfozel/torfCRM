"""Add delivery_price to orders and set default product_name

Revision ID: 002_add_delivery_price
Revises: 001_initial_tables
Create Date: 2026-10-04 11:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_delivery_price'
down_revision: Union[str, None] = '001_initial_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add delivery_price column with default 0.00 to preserve all existing orders
    op.add_column(
        'orders',
        sa.Column(
            'delivery_price',
            sa.Numeric(precision=10, scale=2),
            server_default='0.00',
            nullable=False,
        )
    )
    # Set default for product_name to "Торф'яний брикет"
    op.alter_column(
        'orders',
        'product_name',
        server_default="Торф'яний брикет",
    )


def downgrade() -> None:
    op.alter_column(
        'orders',
        'product_name',
        server_default=None,
    )
    op.drop_column('orders', 'delivery_price')
