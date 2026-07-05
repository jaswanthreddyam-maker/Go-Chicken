import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from models.base import Base


class AIForecast(Base):
    """AI-generated demand prediction with vector embedding for semantic search."""

    __tablename__ = "ai_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    weather_condition: Mapped[str | None] = mapped_column(String(100))
    predicted_demand_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    actual_demand_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    historical_context: Mapped[str | None] = mapped_column(Text)

    # 768-dim vector for nomic-embed-text (Ollama)
    embedding = mapped_column(Vector(768))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="ai_forecasts")
