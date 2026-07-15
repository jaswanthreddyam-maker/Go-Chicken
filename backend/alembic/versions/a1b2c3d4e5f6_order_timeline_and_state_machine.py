"""add order_timeline table and order state machine columns

Revision ID: a1b2c3d4e5f6
Revises: 8f4b1a2c3d4e
Create Date: 2026-07-10 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '8f4b1a2c3d4e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to orders table
    op.add_column('orders', sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('orders', sa.Column('driver_phone', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('driver_name', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('dispatch_time', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('orders', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True))

    # Create order_timeline table
    op.create_table(
        'order_timeline',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_status', sa.String(), nullable=True),
        sa.Column('to_status', sa.String(), nullable=False),
        sa.Column('performed_by', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('transition_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_index(op.f('ix_order_timeline_tenant_id'), 'order_timeline', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_order_timeline_order_id'), 'order_timeline', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_timeline_created_at'), 'order_timeline', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_order_timeline_created_at'), table_name='order_timeline')
    op.drop_index(op.f('ix_order_timeline_order_id'), table_name='order_timeline')
    op.drop_index(op.f('ix_order_timeline_tenant_id'), table_name='order_timeline')
    op.drop_table('order_timeline')
    op.drop_column('orders', 'updated_at')
    op.drop_column('orders', 'version')
    op.drop_column('orders', 'dispatch_time')
    op.drop_column('orders', 'driver_name')
    op.drop_column('orders', 'driver_phone')
    op.drop_column('orders', 'unit_price')
