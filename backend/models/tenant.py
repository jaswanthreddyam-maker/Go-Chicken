import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class Tenant(Base):
    """Represents a wholesaler organization (top-level tenant)."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    warehouse_latitude: Mapped[float | None] = mapped_column(Numeric(10, 8))
    warehouse_longitude: Mapped[float | None] = mapped_column(Numeric(11, 8))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    trucks = relationship("Truck", back_populates="tenant", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="tenant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="tenant", cascade="all, delete-orphan")
    khata_transactions = relationship("KhataTransaction", back_populates="tenant", cascade="all, delete-orphan")
    ai_forecasts = relationship("AIForecast", back_populates="tenant", cascade="all, delete-orphan")
