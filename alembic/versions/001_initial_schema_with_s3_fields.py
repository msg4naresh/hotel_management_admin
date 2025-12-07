"""Initial schema with S3 fields

Revision ID: 001
Revises:
Create Date: 2025-12-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create customers table (with S3 fields)
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(50), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('address', sa.String(200), nullable=False),
        sa.Column('proof_of_identity', sa.String(200), nullable=False),
        sa.Column('proof_image_url', sa.String(500), nullable=True),
        sa.Column('proof_image_filename', sa.String(255), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create rooms table
    op.create_table(
        'rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('room_type', sa.String(50), nullable=False),
        sa.Column('floor', sa.Integer(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('price_per_night', sa.Float(), nullable=False),
        sa.Column('amenities', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create bookings table (with foreign keys)
    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_check_in', sa.Date(), nullable=True),
        sa.Column('scheduled_check_out', sa.Date(), nullable=True),
        sa.Column('actual_check_in', sa.DateTime(), nullable=True),
        sa.Column('actual_check_out', sa.DateTime(), nullable=True),
        sa.Column('booking_status', sa.String(), nullable=False, server_default='prebooked'),
        sa.Column('payment_status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False, server_default=sa.literal('0')),
        sa.Column('additional_charges', sa.Numeric(10, 2), nullable=False, server_default=sa.literal('0')),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('booking_date', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_id'), 'bookings', ['id'], unique=False)
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)
    op.create_index(op.f('ix_rooms_id'), 'rooms', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_index(op.f('ix_rooms_id'), table_name='rooms')
    op.drop_index(op.f('ix_customers_id'), table_name='customers')
    op.drop_index(op.f('ix_bookings_id'), table_name='bookings')

    op.drop_table('bookings')
    op.drop_table('rooms')
    op.drop_table('customers')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
