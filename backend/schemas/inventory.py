"""Pydantic schemas for Enterprise Inventory management APIs."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class InventoryItemResponse(BaseModel):
    id: uuid.UUID
    item_type: str = Field(..., alias="item")
    unit: str = "KG"
    available_qty: Decimal = Field(..., alias="available")
    reserved_qty: Decimal = Field(..., alias="reserved")
    loaded_qty: Decimal = Field(..., alias="loaded")
    delivered_qty: Decimal = 0
    waste_qty: Decimal = 0
    returned_qty: Decimal = 0
    minimum_stock: Decimal = Field(..., alias="minimum")
    reorder_level: Decimal = 500
    status: str = "Healthy"

    class Config:
        from_attributes = True
        populate_by_name = True


class InventoryTransactionResponse(BaseModel):
    id: uuid.UUID
    inventory_item_id: uuid.UUID
    transaction_type: str
    quantity: Decimal
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    remarks: Optional[str] = None
    performed_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PurchaseStockRequest(BaseModel):
    item_type: str = Field(..., alias="item")
    quantity: Decimal
    remarks: Optional[str] = None

    class Config:
        populate_by_name = True


class ReserveStockRequest(BaseModel):
    item_type: str = Field(..., alias="item")
    quantity: Decimal
    reference_id: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        populate_by_name = True


class ReleaseStockRequest(BaseModel):
    item_type: str = Field(..., alias="item")
    quantity: Decimal
    reference_id: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        populate_by_name = True


class LoadStockRequest(BaseModel):
    item_type: str = Field(..., alias="item")
    quantity: Decimal
    reference_id: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        populate_by_name = True


class DeliverStockRequest(BaseModel):
    item_type: str = Field(..., alias="item")
    quantity: Decimal
    reference_id: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        populate_by_name = True


class WasteStockRequest(BaseModel):
    item_type: str = Field(..., alias="item")
    quantity: Decimal
    reason: Optional[str] = "Dead birds"

    class Config:
        populate_by_name = True


class AdjustmentStockRequest(BaseModel):
    item_type: str = Field(..., alias="item")
    quantity: Decimal
    remarks: Optional[str] = None

    class Config:
        populate_by_name = True
