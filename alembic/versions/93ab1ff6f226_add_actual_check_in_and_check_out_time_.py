"""add actual check-in and check-out time columns

Revision ID: 93ab1ff6f226
Revises: c7bc70762ebe
Create Date: 2026-03-05 17:38:15.162119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93ab1ff6f226'
down_revision: Union[str, Sequence[str], None] = 'c7bc70762ebe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('actual_check_in_time', sa.String(length=10), nullable=True))
    op.add_column('bookings', sa.Column('actual_check_out_time', sa.String(length=10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bookings', 'actual_check_out_time')
    op.drop_column('bookings', 'actual_check_in_time')
