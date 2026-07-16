"""fix outbox schema

Revision ID: cc62db3b7cab
Revises: dbdd08f82dfa
Create Date: 2026-07-16 08:43:24.319132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc62db3b7cab'
down_revision: Union[str, Sequence[str], None] = 'dbdd08f82dfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TABLE IF EXISTS integration_outbox CASCADE;")
    op.execute("""
        CREATE TABLE integration_outbox (
            id UUID PRIMARY KEY,
            event_id UUID UNIQUE NOT NULL,
            tenant_id UUID NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            aggregate_type VARCHAR(50) NOT NULL,
            aggregate_id UUID NOT NULL,
            correlation_id VARCHAR(100),
            causation_id VARCHAR(100),
            payload JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            retry_count INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 5,
            last_error VARCHAR(500),
            next_retry_at TIMESTAMP WITH TIME ZONE,
            processed_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        CREATE INDEX ix_integration_outbox_event_id ON integration_outbox (event_id);
        CREATE INDEX ix_integration_outbox_tenant_id ON integration_outbox (tenant_id);
        CREATE INDEX ix_integration_outbox_event_type ON integration_outbox (event_type);
        CREATE INDEX ix_integration_outbox_aggregate_id ON integration_outbox (aggregate_id);
        CREATE INDEX ix_integration_outbox_correlation_id ON integration_outbox (correlation_id);
        CREATE INDEX ix_integration_outbox_status ON integration_outbox (status);
        CREATE INDEX ix_outbox_status_created ON integration_outbox (status, created_at);
        CREATE INDEX ix_outbox_tenant_status_retry ON integration_outbox (tenant_id, status, next_retry_at);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
