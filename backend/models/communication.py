"""PR 8 Communication Platform Audit & Delivery Log Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class CommunicationLog(Base):
    """Immutable audit ledger and lifecycle tracker for customer communication requests."""
    __tablename__ = "communication_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    recipient: Mapped[str] = mapped_column(String(128), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)  # WHATSAPP, SMS, EMAIL
    template_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rendered_content: Mapped[str] = mapped_column(Text, nullable=False)

    # Lifecycle: PENDING -> QUEUED -> SENT -> DELIVERED -> READ (or FAILED -> RETRYING -> FAILED_PERMANENT)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")

    # Strict idempotency preventing duplicate customer messages across outbox retries
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_communication_log_tenant_idempotency"),
        Index("ix_comm_log_tenant_status", "tenant_id", "status"),
    )
