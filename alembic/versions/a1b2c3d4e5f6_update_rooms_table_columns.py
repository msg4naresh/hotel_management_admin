"""update rooms table columns

Revision ID: a1b2c3d4e5f6
Revises: f34a3574c24e
Create Date: 2026-02-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f34a3574c24e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - update rooms table columns."""
    # Drop old columns
    op.drop_column('rooms', 'name')
    op.drop_column('rooms', 'floor')
    op.drop_column('rooms', 'price_per_night')
    op.drop_column('rooms', 'amenities')
    
    # Add new columns
    op.add_column('rooms', sa.Column('room_number', sa.String(20), nullable=False, server_default=''))
    op.add_column('rooms', sa.Column('building', sa.String(20), nullable=False, server_default='building_1'))
    op.add_column('rooms', sa.Column('ac', sa.Boolean(), nullable=False, server_default='false'))
    
    # Alter room_type column size
    op.alter_column('rooms', 'room_type',
                    existing_type=sa.String(50),
                    type_=sa.String(20),
                    existing_nullable=False)
    
    # Remove server defaults after migration
    op.alter_column('rooms', 'room_number', server_default=None)
    op.alter_column('rooms', 'building', server_default=None)
    op.alter_column('rooms', 'ac', server_default=None)


def downgrade() -> None:
    """Downgrade schema - revert rooms table columns."""
    # Drop new columns
    op.drop_column('rooms', 'room_number')
    op.drop_column('rooms', 'building')
    op.drop_column('rooms', 'ac')
    
    # Add back old columns
    op.add_column('rooms', sa.Column('name', sa.String(100), nullable=False, server_default=''))
    op.add_column('rooms', sa.Column('floor', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('rooms', sa.Column('price_per_night', sa.Float(), nullable=False, server_default='0'))
    op.add_column('rooms', sa.Column('amenities', sa.JSON(), nullable=False, server_default='[]'))
    
    # Revert room_type column size
    op.alter_column('rooms', 'room_type',
                    existing_type=sa.String(20),
                    type_=sa.String(50),
                    existing_nullable=False)
    
    # Remove server defaults
    op.alter_column('rooms', 'name', server_default=None)
    op.alter_column('rooms', 'floor', server_default=None)
    op.alter_column('rooms', 'price_per_night', server_default=None)
    op.alter_column('rooms', 'amenities', server_default=None)
