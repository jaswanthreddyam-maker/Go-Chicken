"""fix missing columns in prod

Revision ID: dbdd08f82dfa
Revises: e1b2c3d4e5f6
Create Date: 2026-07-16 08:36:49.037563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dbdd08f82dfa'
down_revision: Union[str, Sequence[str], None] = 'e1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE pricing_quotes ADD COLUMN IF NOT EXISTS converted_order_id UUID;")
    op.execute("ALTER TABLE pricing_price_books ADD COLUMN IF NOT EXISTS effective_date TIMESTAMP WITH TIME ZONE;")
    op.execute("ALTER TABLE integration_outbox ADD COLUMN IF NOT EXISTS error_message TEXT;")
    op.execute("ALTER TABLE integration_outbox ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();")


def downgrade() -> None:
    """Downgrade schema."""
    pass
