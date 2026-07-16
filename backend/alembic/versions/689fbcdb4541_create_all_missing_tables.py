"""create all missing tables

Revision ID: 689fbcdb4541
Revises: cc62db3b7cab
Create Date: 2026-07-16 08:55:18.642372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '689fbcdb4541'
down_revision: Union[str, Sequence[str], None] = 'cc62db3b7cab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    import models
    models.Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Downgrade schema."""
    pass
