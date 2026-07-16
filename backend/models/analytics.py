"""PR 9 Analytics CQRS Disposable Read Models & Metadata Trackers."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Date, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class OperationalDailyKPI(Base):
    """Disposable daily operational projection (orders, volume, deliveries)."""
    __tablename__ = "analytics_operational_daily_kpi"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    projection_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")

    total_orders_placed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    orders_confirmed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    orders_delivered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_volume_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "metric_date", "projection_version", name="uq_oper_daily_kpi"),
        Index("ix_oper_kpi_tenant_date", "tenant_id", "metric_date"),
    )


class FinancialDailyKPI(Base):
    """Disposable daily financial projection (invoices, collections, outstanding)."""
    __tablename__ = "analytics_financial_daily_kpi"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    projection_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")

    invoices_issued_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    payments_collected_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    outstanding_receivable_net: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "metric_date", "projection_version", name="uq_fin_daily_kpi"),
        Index("ix_fin_kpi_tenant_date", "tenant_id", "metric_date"),
    )


class CommunicationDailyKPI(Base):
    """Disposable daily communication performance projection (dispatched, delivered, failed)."""
    __tablename__ = "analytics_communication_daily_kpi"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    projection_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")

    messages_dispatched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    messages_delivered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    messages_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "metric_date", "projection_version", name="uq_comm_daily_kpi"),
        Index("ix_comm_kpi_tenant_date", "tenant_id", "metric_date"),
    )


class ProjectionMetadata(Base):
    """Operational health & version tracker for analytics read models."""
    __tablename__ = "analytics_projection_metadata"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    projection_name: Mapped[str] = mapped_column(String(64), nullable=False)
    projection_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")

    last_processed_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rebuild_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rebuild_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "projection_name", "projection_version", name="uq_proj_meta_tenant_name_ver"),
    )


class AnalyticsEventProcessed(Base):
    """Idempotent replay protection index guaranteeing exactly-once projection updates."""
    __tablename__ = "analytics_events_processed"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "event_id", name="uq_analytics_event_processed"),
    )
