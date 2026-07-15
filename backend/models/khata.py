import uuid
import enum
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class TransactionType(str, enum.Enum):
    CHARGE = "charge"
    PAYMENT = "payment"
    ADJUSTMENT = "adjustment"


class KhataTransaction(Base):
    """A single entry in the digital Khata (credit ledger) for a retailer."""

    __tablename__ = "khata_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    retailer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL")
    )
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reference_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="khata_transactions")
    retailer = relationship("User", back_populates="khata_transactions")
    order = relationship("Order", back_populates="khata_transactions")


# ==============================================================================
# PR 7 Enterprise Financial Ledger Models (KHATA_SERVICE_DESIGN.md)
# ==============================================================================

class KhataLedger(Base):
    """Immutable, append-only financial ledger journal entry (PR 7)."""
    __tablename__ = "khata_ledger"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    # Entry classification: INVOICE, PAYMENT, CREDIT_NOTE, DEBIT_NOTE, ADJUSTMENT, REVERSAL
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Signed balance impact (+ increases outstanding balance receivable, - decreases balance)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Polymorphic reference linking ledger entry to business document
    reference_type: Mapped[str] = mapped_column(String(32), nullable=False)  # ORDER, INVOICE, PAYMENT, RETURN, ADJUSTMENT
    reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Strict idempotency key guaranteeing exactly-once financial posting
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_khata_ledger_tenant_idempotency"),
        Index("ix_khata_ledger_tenant_customer", "tenant_id", "customer_id"),
    )


class CustomerBalanceProjection(Base):
    """Read-optimized customer balance projection deterministically rebuildable from KhataLedger."""
    __tablename__ = "customer_balance_projection"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    last_entry_at: Mapped[datetime] = mapped_column(
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
        UniqueConstraint("tenant_id", "customer_id", name="uq_customer_balance_projection"),
    )


class KhataInvoice(Base):
    """Tracks invoice-level FIFO settlement lifecycle across multiple payments."""
    __tablename__ = "khata_invoice"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    settled_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    # UNPAID, PARTIALLY_PAID, PAID, OVERPAID
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNPAID")

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_id", name="uq_khata_invoice_tenant_invoice"),
    )
