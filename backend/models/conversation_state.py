"""Conversation State Model for WhatsApp Order Assistant."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class ConversationState(Base):
    """Stores the current state of a retailer's WhatsApp conversation."""
    __tablename__ = "conversation_state"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="IDLE")
    language: Mapped[str | None] = mapped_column(String(10))
    
    pending_intent: Mapped[str | None] = mapped_column(String(50))
    pending_product: Mapped[str | None] = mapped_column(String(50))
    pending_quantity: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    pending_quote_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pricing_quotes.id", ondelete="SET NULL"))
    pending_price_per_kg: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    pending_total: Mapped[Numeric | None] = mapped_column(Numeric(12, 2))
    
    handoff_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_message: Mapped[str | None] = mapped_column(Text)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    quote = relationship("Quote", foreign_keys=[pending_quote_id])

    __table_args__ = (
        Index("ix_conv_state_user", "user_id"),
    )
