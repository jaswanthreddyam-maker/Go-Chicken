from datetime import datetime
from decimal import Decimal
from typing import Optional
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
