"""IntegrationOutbox ORM Model — Implements the Transactional Outbox pattern for guaranteed event delivery."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class IntegrationOutbox(Base):
    """Stores domain/integration events in the same ACID transaction as state mutations."""

    __tablename__ = "integration_outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, unique=True, index=True, nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    aggregate_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False, index=True
    )
    correlation_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    causation_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", index=True
    )  # "PENDING", "PROCESSED", "FAILED"
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
    )
    last_error: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    tenant = relationship("Tenant")

    __table_args__ = (
        Index("ix_outbox_status_created", "status", "created_at"),
    )
