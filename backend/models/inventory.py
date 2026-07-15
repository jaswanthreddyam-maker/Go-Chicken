from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from models.base import Base


class InventoryItem(Base):
    """Enterprise inventory item snapshot model representing current stock across states."""

    __tablename__ = "inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type = Column(String(100), nullable=False, index=True)
    unit = Column(String(20), nullable=False, default="KG")

    available_qty = Column(Numeric(12, 2), nullable=False, default=0)
    reserved_qty = Column(Numeric(12, 2), nullable=False, default=0)
    loaded_qty = Column(Numeric(12, 2), nullable=False, default=0)
    delivered_qty = Column(Numeric(12, 2), nullable=False, default=0)
    waste_qty = Column(Numeric(12, 2), nullable=False, default=0)
    returned_qty = Column(Numeric(12, 2), nullable=False, default=0)

    minimum_stock = Column(Numeric(12, 2), nullable=False, default=300)
    reorder_level = Column(Numeric(12, 2), nullable=False, default=500)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="inventory_items")
    transactions = relationship(
        "InventoryTransaction",
        back_populates="inventory_item",
        cascade="all, delete-orphan",
    )


class InventoryTransaction(Base):
    """Immutable ledger transaction record for every inventory movement."""

    __tablename__ = "inventory_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inventory_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type = Column(String(50), nullable=False, index=True)
    quantity = Column(Numeric(12, 2), nullable=False)
    reference_type = Column(String(100), nullable=True)
    reference_id = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    performed_by = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    tenant = relationship("Tenant")
    inventory_item = relationship("InventoryItem", back_populates="transactions")


# Backwards compatible alias
Inventory = InventoryItem
