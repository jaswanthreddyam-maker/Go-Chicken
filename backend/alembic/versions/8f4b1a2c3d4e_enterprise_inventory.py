"""Add enterprise inventory items and transactions tables

Revision ID: 8f4b1a2c3d4e
Revises: 73d08f9fe377
Create Date: 2026-07-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f4b1a2c3d4e'
down_revision: Union[str, None] = '73d08f9fe377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('item_type', sa.String(length=100), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='KG'),
        sa.Column('available_qty', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('reserved_qty', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('loaded_qty', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('delivered_qty', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('waste_qty', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('returned_qty', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('minimum_stock', sa.Numeric(precision=12, scale=2), nullable=False, server_default='300'),
        sa.Column('reorder_level', sa.Numeric(precision=12, scale=2), nullable=False, server_default='500'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_items_tenant_id'), 'inventory_items', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_items_item_type'), 'inventory_items', ['item_type'], unique=False)

    op.create_table(
        'inventory_transactions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('inventory_item_id', sa.Uuid(), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reference_type', sa.String(length=100), nullable=True),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_transactions_tenant_id'), 'inventory_transactions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_inventory_item_id'), 'inventory_transactions', ['inventory_item_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_transaction_type'), 'inventory_transactions', ['transaction_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_transactions_transaction_type'), table_name='inventory_transactions')
    op.drop_index(op.f('ix_inventory_transactions_inventory_item_id'), table_name='inventory_transactions')
    op.drop_index(op.f('ix_inventory_transactions_tenant_id'), table_name='inventory_transactions')
    op.drop_table('inventory_transactions')
    op.drop_index(op.f('ix_inventory_items_item_type'), table_name='inventory_items')
    op.drop_index(op.f('ix_inventory_items_tenant_id'), table_name='inventory_items')
    op.drop_table('inventory_items')
