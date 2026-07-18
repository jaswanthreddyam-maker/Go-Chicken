from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class PriceUpdate(BaseModel):
    """Schema for updating a product price from the admin dashboard."""
    price_per_kg: float = Field(..., gt=0, description="New price per kg in INR", json_schema_extra={"example": 190.0})


class PriceResponse(BaseModel):
    """Schema for returning a product price item."""
    item_type: str = Field(..., json_schema_extra={"example": "Live Bird"})
    price_per_kg: float = Field(..., json_schema_extra={"example": 180.0})
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Quote Schemas (PR10) ──

class QuoteItemCreate(BaseModel):
    """Item row parameter for quote creation."""
    sku: str = Field(..., description="Poultry item SKU (e.g. 'Live Bird', 'Dressed', 'Skinless')")
    quantity_kg: Decimal = Field(..., gt=0, description="Quantity in kilograms")


class QuoteCreate(BaseModel):
    """Request payload to create a new quote snapshot."""
    customer_id: UUID = Field(..., description="Target retailer customer ID")
    delivery_zone: Optional[str] = Field(None, description="Delivery zone name for surcharge calculation")
    expires_at: Optional[datetime] = Field(None, description="Quote expiration date")
    items: List[QuoteItemCreate] = Field(..., min_length=1, description="List of items in the quote")


class QuotePreviewRequest(BaseModel):
    """Request payload to preview quote financial breakdowns."""
    customer_id: UUID = Field(..., description="Retailer customer ID")
    delivery_zone: Optional[str] = Field(None, description="Target delivery zone")
    items: List[QuoteItemCreate] = Field(..., min_length=1, description="List of items to preview")


class QuoteItemResponse(BaseModel):
    """JSON output representation for quote items."""
    id: UUID
    sku: str
    quantity_kg: Decimal
    unit_price: Decimal
    pricing_source: str
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class QuoteResponse(BaseModel):
    """JSON output representation of a quote snapshot."""
    id: UUID
    quote_number: str
    quote_version: int
    customer_id: UUID
    delivery_zone: Optional[str] = None
    status: str
    subtotal_amount: Decimal
    zone_surcharge_amount: Decimal
    total_amount: Decimal
    expires_at: datetime
    converted_order_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    items: List[QuoteItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class QuotePreviewResponse(BaseModel):
    """JSON output of the batched pricing and surcharge calculations."""
    subtotal_amount: Decimal
    zone_surcharge_amount: Decimal
    total_amount: Decimal
    items: List[QuoteItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
