"""Add enterprise outbox, khata ledger, communication, analytics, and pricing quote tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-10 13:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Transactional Outbox Table
    op.create_table(
        'integration_outbox',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=128), nullable=False),
        sa.Column('aggregate_type', sa.String(length=64), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('correlation_id', sa.String(length=128), nullable=True),
        sa.Column('causation_id', sa.String(length=128), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_outbox_tenant_status_retry', 'integration_outbox', ['tenant_id', 'status', 'next_retry_at'])

    # 2. Khata Financial Ledger Tables
    op.create_table(
        'khata_ledgers',
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('entry_type', sa.String(length=32), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reference_type', sa.String(length=64), nullable=False),
        sa.Column('reference_id', sa.String(length=128), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'idempotency_key', name='uq_khata_ledger_tenant_idempotency'),
    )

    op.create_table(
        'khata_customer_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('outstanding_balance', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('last_ledger_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_rebuilt_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'customer_id', name='uq_khata_balance_tenant_customer'),
    )

    # 3. Communication Log Table
    op.create_table(
        'communication_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('recipient', sa.String(length=128), nullable=False),
        sa.Column('channel', sa.String(length=32), nullable=False),
        sa.Column('template_id', sa.String(length=64), nullable=False),
        sa.Column('rendered_content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('provider_message_id', sa.String(length=128), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'idempotency_key', name='uq_communication_log_tenant_idempotency'),
    )

    # 4. Analytics Disposable Projections & Metadata Tables
    op.create_table(
        'analytics_operational_daily_kpi',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('metric_date', sa.Date(), nullable=False, index=True),
        sa.Column('projection_version', sa.String(length=16), nullable=False, server_default='v1'),
        sa.Column('total_orders_placed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('orders_confirmed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('orders_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_volume_kg', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'metric_date', 'projection_version', name='uq_oper_daily_kpi'),
    )

    op.create_table(
        'analytics_financial_daily_kpi',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('metric_date', sa.Date(), nullable=False, index=True),
        sa.Column('projection_version', sa.String(length=16), nullable=False, server_default='v1'),
        sa.Column('invoices_issued_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('payments_collected_total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('outstanding_receivable_net', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'metric_date', 'projection_version', name='uq_fin_daily_kpi'),
    )

    op.create_table(
        'analytics_communication_daily_kpi',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('metric_date', sa.Date(), nullable=False, index=True),
        sa.Column('projection_version', sa.String(length=16), nullable=False, server_default='v1'),
        sa.Column('messages_dispatched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('messages_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('messages_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'metric_date', 'projection_version', name='uq_comm_daily_kpi'),
    )

    op.create_table(
        'analytics_projection_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('projection_name', sa.String(length=64), nullable=False),
        sa.Column('projection_version', sa.String(length=16), nullable=False, server_default='v1'),
        sa.Column('last_processed_event_id', sa.String(length=128), nullable=True),
        sa.Column('last_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rebuild_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rebuild_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'projection_name', 'projection_version', name='uq_proj_meta_tenant_name_ver'),
    )

    op.create_table(
        'analytics_events_processed',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('event_id', sa.String(length=128), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'event_id', name='uq_analytics_event_processed_tenant_event'),
    )

    # 5. Pricing & Quote Engine Tables
    op.create_table(
        'pricing_price_books',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='INR'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_pricing_price_book_tenant_name'),
    )

    op.create_table(
        'pricing_price_book_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('price_book_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pricing_price_books.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sku', sa.String(length=64), nullable=False, index=True),
        sa.Column('base_unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('min_quantity_kg', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('price_book_id', 'sku', 'min_quantity_kg', name='uq_price_book_entry_sku_qty'),
    )

    op.create_table(
        'pricing_customer_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('override_unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'customer_id', 'sku', name='uq_customer_price_override_tenant_cust_sku'),
    )

    op.create_table(
        'pricing_zone_surcharges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('delivery_zone', sa.String(length=64), nullable=False),
        sa.Column('surcharge_per_kg', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'delivery_zone', name='uq_pricing_zone_surcharge_tenant_zone'),
    )

    op.create_table(
        'pricing_price_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('new_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('changed_by', sa.String(length=128), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'pricing_quotes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('quote_number', sa.String(length=64), nullable=False),
        sa.Column('quote_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('delivery_zone', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DRAFT'),
        sa.Column('subtotal_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('zone_surcharge_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'quote_number', 'quote_version', name='uq_pricing_quote_tenant_num_ver'),
    )

    op.create_table(
        'pricing_quote_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quote_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pricing_quotes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sku', sa.String(length=64), nullable=False),
        sa.Column('quantity_kg', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('pricing_source', sa.String(length=64), nullable=False),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('pricing_quote_items')
    op.drop_table('pricing_quotes')
    op.drop_table('pricing_price_history')
    op.drop_table('pricing_zone_surcharges')
    op.drop_table('pricing_customer_overrides')
    op.drop_table('pricing_price_book_entries')
    op.drop_table('pricing_price_books')
    op.drop_table('analytics_events_processed')
    op.drop_table('analytics_projection_metadata')
    op.drop_table('analytics_communication_daily_kpi')
    op.drop_table('analytics_financial_daily_kpi')
    op.drop_table('analytics_operational_daily_kpi')
    op.drop_table('communication_logs')
    op.drop_table('khata_customer_balances')
    op.drop_table('khata_ledgers')
    op.drop_table('integration_outbox')
