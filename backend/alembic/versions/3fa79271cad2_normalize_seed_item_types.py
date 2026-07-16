"""normalize_seed_item_types

Revision ID: 3fa79271cad2
Revises: c3d4e5f6a7b8
Create Date: 2026-07-16 09:26:26.549248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fa79271cad2'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrate InventoryItem (No unique constraint on item_type alone)
    op.execute("UPDATE inventory_items SET item_type = 'BROILER' WHERE item_type IN ('Live Bird', 'Broiler', 'LIVE_BIRD', 'LIVE BIRD');")
    op.execute("UPDATE inventory_items SET item_type = 'DESI' WHERE item_type = 'Country Chicken';")
    
    # Migrate ProductPrice (Unique constraint on item_type)
    # Safely delete old ones to avoid unique constraint violations, let auto-seeder recreate them
    op.execute("DELETE FROM product_prices WHERE item_type IN ('Live Bird', 'Broiler', 'LIVE_BIRD', 'LIVE BIRD', 'Country Chicken');")

    # Migrate PriceBookEntry (Unique constraint on price_book_id, sku, min_quantity_kg)
    op.execute("DELETE FROM pricing_price_book_entries WHERE sku IN ('Live Bird', 'Broiler', 'LIVE_BIRD', 'LIVE BIRD', 'Country Chicken');")

def downgrade() -> None:
    pass
