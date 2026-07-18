import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Boolean, Date, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class MarketSnapshot(Base):
    """A snapshot of market conditions analyzed by the AI Engine."""
    __tablename__ = "market_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    analysis_status: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPLETED")
    
    # Store arbitrary array of { source: str, signal: str }
    signals: Mapped[list | dict] = mapped_column(JSON, nullable=False, default=list)
    summary: Mapped[str] = mapped_column(String(1024), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    recommendations: Mapped[list["PriceRecommendation"]] = relationship(
        "PriceRecommendation", back_populates="snapshot", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_market_snapshots_tenant_captured", "tenant_id", "captured_at"),
    )


class PriceRecommendation(Base):
    """An AI generated recommendation derived from a MarketSnapshot."""
    __tablename__ = "market_price_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("market_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    recommended_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # JSON array of reason strings
    reasoning: Mapped[list | dict] = mapped_column(JSON, nullable=False, default=list)
    
    # PENDING, ACCEPTED, IGNORED, EXPIRED, SUPERSEDED
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    
    # Store projected outcomes: expected_revenue_delta, estimated_margin_delta, affected_retailers
    impact: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    snapshot: Mapped["MarketSnapshot"] = relationship("MarketSnapshot", back_populates="recommendations")

    __table_args__ = (
        Index("ix_market_recommendations_tenant_status", "tenant_id", "status"),
    )
