"""PR 10 Enterprise Pricing & Quote Models — Hierarchical Price Books & Immutable Quote Snapshots."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Boolean, Date, DateTime, UniqueConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class ProductPrice(Base):
    """Legacy product price catalog model."""
    __tablename__ = "product_prices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    item_type: Mapped[str] = mapped_column(String(128), nullable=False)
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class PriceBook(Base):
    """Tenant-scoped wholesale or tier price book."""
    __tablename__ = "pricing_price_books"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_price_book_tenant_name"),
    )


class PriceBookEntry(Base):
    """SKU pricing entry within a price book, optionally tiered by minimum order weight (min_quantity_kg)."""
    __tablename__ = "pricing_price_book_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    price_book_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    base_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class CustomerPriceOverride(Base):
    """Specific negotiated SKU price for a customer (Highest Precedence in Resolution Hierarchy)."""
    __tablename__ = "pricing_customer_overrides"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    override_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DeliveryZoneSurcharge(Base):
    """Route/zone logistics delivery surcharge per kg."""
    __tablename__ = "pricing_zone_surcharges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    delivery_zone: Mapped[str] = mapped_column(String(64), nullable=False)
    surcharge_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))


class PriceHistory(Base):
    """Append-only audit log recording every price book or customer override rate change."""
    __tablename__ = "pricing_price_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)  # PRICE_BOOK_ENTRY, CUSTOMER_OVERRIDE
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class Quote(Base):
    """Immutable financial quote snapshot with versioning and explicit approval workflow."""
    __tablename__ = "pricing_quotes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    quote_number: Mapped[str] = mapped_column(String(64), nullable=False)
    quote_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    customer_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    delivery_zone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Lifecycle: DRAFT -> PENDING_APPROVAL -> APPROVED -> CONVERTED / EXPIRED / REJECTED
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")

    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    zone_surcharge_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    converted_order_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    items: Mapped[list["QuoteItem"]] = relationship(
        "QuoteItem", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "quote_number", name="uq_quote_tenant_number"),
        Index("ix_quote_tenant_status", "tenant_id", "status"),
    )


class QuoteItem(Base):
    """Immutable line item within a Quote snapshot storing exact price and resolution provenance."""
    __tablename__ = "pricing_quote_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pricing_quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Provenance auditability: CUSTOMER_OVERRIDE, TIER_PRICEBOOK, BASE_PRICEBOOK
    pricing_source: Mapped[str] = mapped_column(String(64), nullable=False)

    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
