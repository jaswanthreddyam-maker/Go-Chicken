import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class Truck(Base):
    """Represents a delivery truck with IoT device and capacity constraints."""

    __tablename__ = "trucks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    license_plate: Mapped[str] = mapped_column(String(50), nullable=False)
    iot_device_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    max_capacity_kg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=1000.00
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="trucks")
    driver = relationship("User", back_populates="truck")
    iot_readings = relationship("IoTReading", back_populates="truck", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="truck")


class IoTReading(Base):
    """Time-series temperature log from a truck's IoT sensor."""

    __tablename__ = "iot_readings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    truck_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trucks.id", ondelete="CASCADE"), nullable=False
    )
    temperature: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    alert_triggered: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    truck = relationship("Truck", back_populates="iot_readings")
