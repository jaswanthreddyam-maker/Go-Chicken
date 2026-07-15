"""OrderTimeline model — immutable audit ledger for order lifecycle transitions."""

import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from models.base import Base


class OrderTimeline(Base):
    """Immutable audit log recording every order lifecycle transition."""

    __tablename__ = "order_timeline"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = (
        Column(
            UUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    order_id = (
        Column(
            UUID(as_uuid=True),
            ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    performed_by = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    transition_context = Column(JSONB, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    tenant = relationship("Tenant")
    order = relationship("Order", back_populates="timeline_entries")
