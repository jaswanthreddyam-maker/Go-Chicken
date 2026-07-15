"""Logistics and Delivery Proof Pydantic Schemas for PR 4B."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DispatchOrderRequest(BaseModel):
    """Payload to dispatch a loaded order with driver details."""
    driver_name: Optional[str] = Field(None, max_length=100, json_schema_extra={"example": "Ramesh Driver"})
    driver_phone: Optional[str] = Field(None, max_length=20, json_schema_extra={"example": "+919876543210"})
    dispatch_time: Optional[str] = Field(None, json_schema_extra={"example": "2026-07-10T09:30:00Z"})


class DeliverOrderRequest(BaseModel):
    """Payload containing physical delivery proof and actual weight reconciliation."""
    actual_delivered_kg: Optional[Decimal] = Field(None, gt=0, json_schema_extra={"example": "298.50"})
    waste_kg: Optional[Decimal] = Field(Decimal("0.00"), ge=0, json_schema_extra={"example": "1.50"})
    receiver_name: Optional[str] = Field(None, max_length=100, json_schema_extra={"example": "Ali Retailer"})
    receiver_phone: Optional[str] = Field(None, max_length=20, json_schema_extra={"example": "+919811122233"})
    delivery_gps_lat: Optional[float] = Field(None, ge=-90, le=90, json_schema_extra={"example": 17.3850})
    delivery_gps_lng: Optional[float] = Field(None, ge=-180, le=180, json_schema_extra={"example": 78.4867})
    delivery_photo_url: Optional[str] = Field(None, max_length=500)
    delivery_signature_url: Optional[str] = Field(None, max_length=500)
    remarks: Optional[str] = Field(None, max_length=500, json_schema_extra={"example": "Delivered in good condition"})

    model_config = ConfigDict(from_attributes=True)
