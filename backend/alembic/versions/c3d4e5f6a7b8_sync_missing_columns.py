"""Sync missing columns on orders and product_prices tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Sync orders columns
    op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS price_per_kg NUMERIC(10, 2) NULL;")
    op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS unit_price NUMERIC(10, 2) NULL;")
    op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS dispatch_time TIMESTAMP WITH TIME ZONE NULL;")
    op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS driver_name VARCHAR NULL;")
    op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS driver_phone VARCHAR NULL;")
    op.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;")
    op.execute("ALTER TABLE orders ALTER COLUMN price_per_kg DROP NOT NULL;")
    op.execute("ALTER TABLE orders ALTER COLUMN unit_price DROP NOT NULL;")
    op.execute("ALTER TABLE orders ALTER COLUMN delivery_date DROP NOT NULL;")
    op.execute("ALTER TABLE orders ALTER COLUMN total_amount DROP NOT NULL;")
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR USING status::text;")
    op.execute("ALTER TABLE orders ALTER COLUMN delivery_date TYPE TIMESTAMP WITH TIME ZONE USING delivery_date AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE orders ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE orders ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE order_timeline ALTER COLUMN from_status TYPE VARCHAR USING from_status::text;")
    op.execute("ALTER TABLE order_timeline ALTER COLUMN to_status TYPE VARCHAR USING to_status::text;")
    op.execute("ALTER TABLE order_timeline ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE error_logs ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE classification_logs ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';")

    # 2. Sync product_prices column (and drop primary key constraint on item_type if needed so id can be primary key or unique ID)
    op.execute("ALTER TABLE product_prices ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid();")
    # Ensure all rows have an id
    op.execute("UPDATE product_prices SET id = gen_random_uuid() WHERE id IS NULL;")
    # Alter id to NOT NULL
    op.execute("ALTER TABLE product_prices ALTER COLUMN id SET NOT NULL;")


def downgrade() -> None:
    op.execute("ALTER TABLE product_prices DROP COLUMN IF EXISTS id;")
    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS version;")
    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS driver_phone;")
    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS driver_name;")
    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS dispatch_time;")
    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS unit_price;")
