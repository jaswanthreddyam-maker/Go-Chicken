from sqlalchemy import Column, String, Numeric, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
import uuid
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

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
    
    item_type = Column(String, default="Live Bird")
    quantity_kg = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=True)
    
    status = Column(String, default="pending")
    order_source = Column(String(20), default="regex")  # "ollama" or "regex" — tracks classification method
    delivery_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
