"""add refundable_amount to bookings

Revision ID: 4cacb97e5a14
Revises: d0d9c14534c3
Create Date: 2026-03-05 15:22:56.903609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cacb97e5a14'
down_revision: Union[str, Sequence[str], None] = 'd0d9c14534c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('refundable_amount', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bookings', 'refundable_amount')
    # ### end Alembic commands ###
