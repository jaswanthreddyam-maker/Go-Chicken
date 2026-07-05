"""Pydantic schemas for the ordering engine."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class WhatsAppOrderRequest(BaseModel):
    """Incoming order request from the WhatsApp Bot webhook."""

    retailer_phone: str = Field(..., description="Verified phone number of the retailer")
    message_text: str = Field(..., description="Raw message text, e.g. '50kg live bird'")
    tenant_id: uuid.UUID = Field(..., description="Which wholesaler this order is for")


class OrderOut(BaseModel):
    """Serialized order for dashboard display."""

    id: uuid.UUID
    retailer_name: str
    item_type: str
    quantity_kg: Decimal
    price_per_kg: Decimal
    total_amount: Decimal
    status: str
    delivery_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class DailyOrderSummary(BaseModel):
    """Aggregated view of daily orders for the dispatch dashboard."""

    date: date
    total_orders: int
    total_kg: Decimal
    orders: list[OrderOut]
