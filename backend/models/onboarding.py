import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class DraftStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"

class RetailerOnboardingDraft(Base):
    """Stores business data for a retailer during the WhatsApp onboarding flow."""
    __tablename__ = "retailer_onboarding_drafts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    invite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("retailer_invitations.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    preferred_language: Mapped[str | None] = mapped_column(String(10))
    owner_name: Mapped[str | None] = mapped_column(String(255))
    shop_name: Mapped[str | None] = mapped_column(String(255))
    
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8))
    
    status: Mapped[DraftStatus] = mapped_column(
        Enum(DraftStatus, name="draft_status", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False, default=DraftStatus.IN_PROGRESS
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    invitation = relationship("RetailerInvitation", back_populates="onboarding_drafts")
    tenant = relationship("Tenant")
    events = relationship("RetailerOnboardingEvent", back_populates="draft", cascade="all, delete-orphan")


class RetailerOnboardingEvent(Base):
    """Stores a timeline event during the WhatsApp onboarding flow."""
    __tablename__ = "retailer_onboarding_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("retailer_onboarding_drafts.id", ondelete="CASCADE"), nullable=False)
    event: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_payload: Mapped[dict | None] = mapped_column(JSON)
    
    draft = relationship("RetailerOnboardingDraft", back_populates="events")
