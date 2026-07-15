from sqlalchemy import Column, String, Numeric, DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
import uuid
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    LOADED = "loaded"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    # Backwards compatibility
    PROCESSING = "processing"
    SHIPPED = "shipped"

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    retailer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    truck_id = Column(UUID(as_uuid=True), ForeignKey("trucks.id", ondelete="SET NULL"), nullable=True)
    
    tenant = relationship("Tenant", back_populates="orders")
    retailer = relationship("User", back_populates="orders")
    truck = relationship("Truck", back_populates="orders")
    khata_transactions = relationship("KhataTransaction", back_populates="order", cascade="all, delete-orphan")
    timeline_entries = relationship("OrderTimeline", back_populates="order", cascade="all, delete-orphan")
    
    item_type = Column(String, default="Live Bird")
    quantity_kg = Column(Numeric(10, 2), nullable=False)
    price_per_kg = Column(Numeric(10, 2), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=True)     # Contract price per KG locked at confirmation
    total_amount = Column(Numeric(12, 2), nullable=True)
    
    status = Column(String, default="pending")
    order_source = Column(String(20), default="regex")  # "ollama" or "regex" — tracks classification method
    delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    driver_phone = Column(String, nullable=True)
    driver_name = Column(String, nullable=True)
    dispatch_time = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __mapper_args__ = {
        "version_id_col": version
    }
