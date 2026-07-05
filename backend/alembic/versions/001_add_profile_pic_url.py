"""Add profile_pic_url to business_profiles

Revision ID: 001_add_profile_pic_url
Revises:
Create Date: 2026-07-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_add_profile_pic_url"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL with IF NOT EXISTS to be idempotent —
    # the column may already exist from the old startup migration.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'business_profiles'
                AND column_name = 'profile_pic_url'
            ) THEN
                ALTER TABLE business_profiles
                ADD COLUMN profile_pic_url VARCHAR(500);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_column("business_profiles", "profile_pic_url")
