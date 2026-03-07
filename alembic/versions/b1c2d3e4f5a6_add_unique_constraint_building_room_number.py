"""add unique constraint building room_number

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on building + room_number."""
    op.create_unique_constraint(
        'uq_building_room_number', 'rooms', ['building', 'room_number']
    )


def downgrade() -> None:
    """Remove unique constraint on building + room_number."""
    op.drop_constraint('uq_building_room_number', 'rooms', type_='unique')
