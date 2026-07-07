from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Optional
from datetime import datetime
from models.order import OrderStatus

# What we expect when WhatsApp webhook sends a new order
class OrderCreate(BaseModel):
    phone_number: str = Field(..., json_schema_extra={"example": "+919876543210"})
    item_type: str = Field(..., json_schema_extra={"example": "Live Bird"})
    quantity_kg: float = Field(..., gt=0, json_schema_extra={"example": 50.0})
    total_amount: Optional[float] = Field(None, json_schema_extra={"example": 12000.0})

# What our API returns back to the client
class OrderResponse(BaseModel):
    id: UUID4
    phone_number: Optional[str] = None
    item_type: str
    quantity_kg: float
    total_amount: Optional[float] = None
    status: str
    order_source: Optional[str] = "regex"  # "ollama" or "regex"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus = Field(..., description="New status: pending, processing, delivered, cancelled", json_schema_extra={"example": "delivered"})
