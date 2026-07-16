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
    # Migrate InventoryItem
    op.execute("UPDATE inventory_items SET item_type = 'BROILER' WHERE item_type IN ('Live Bird', 'Broiler', 'LIVE_BIRD', 'LIVE BIRD');")
    op.execute("UPDATE inventory_items SET item_type = 'DESI' WHERE item_type = 'Country Chicken';")
    
    # Migrate ProductPrice
    op.execute("UPDATE product_prices SET item_type = 'BROILER' WHERE item_type IN ('Live Bird', 'Broiler', 'LIVE_BIRD', 'LIVE BIRD');")
    op.execute("UPDATE product_prices SET item_type = 'DESI' WHERE item_type = 'Country Chicken';")

    # Migrate PriceBookEntry
    op.execute("UPDATE pricing_price_book_entries SET sku = 'BROILER' WHERE sku IN ('Live Bird', 'Broiler', 'LIVE_BIRD', 'LIVE BIRD');")
    op.execute("UPDATE pricing_price_book_entries SET sku = 'DESI' WHERE sku = 'Country Chicken';")

def downgrade() -> None:
    pass
