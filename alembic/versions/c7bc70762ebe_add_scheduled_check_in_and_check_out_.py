"""add scheduled check-in and check-out time columns

Revision ID: c7bc70762ebe
Revises: 4cacb97e5a14
Create Date: 2026-03-05 17:31:26.398873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7bc70762ebe'
down_revision: Union[str, Sequence[str], None] = '4cacb97e5a14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('scheduled_check_in_time', sa.String(length=10), nullable=True))
    op.add_column('bookings', sa.Column('scheduled_check_out_time', sa.String(length=10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bookings', 'scheduled_check_out_time')
    op.drop_column('bookings', 'scheduled_check_in_time')

    op.drop_index(op.f('ix_bookings_id'), table_name='bookings')
    op.alter_column('bookings', 'notes',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)
    op.alter_column('bookings', 'additional_charges',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               nullable=False,
               existing_server_default=sa.text('0'))
    op.alter_column('bookings', 'amount_paid',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               nullable=False,
               existing_server_default=sa.text('0'))
    op.alter_column('bookings', 'payment_status',
               existing_type=sa.VARCHAR(length=20),
               nullable=False,
               existing_server_default=sa.text("'PENDING'::character varying"))
    op.alter_column('bookings', 'booking_status',
               existing_type=sa.VARCHAR(length=20),
               nullable=False,
               existing_server_default=sa.text("'PENDING'::character varying"))
    op.drop_column('bookings', 'scheduled_check_out_time')
    op.drop_column('bookings', 'scheduled_check_in_time')
    # ### end Alembic commands ###
