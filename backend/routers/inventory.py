"""Enterprise Inventory Router — endpoints for inventory snapshots & movements."""

import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.auth import get_current_tenant
from core.inventory_service import InventoryService
from schemas.inventory import (
    InventoryItemResponse,
    InventoryTransactionResponse,
    PurchaseStockRequest,
    ReserveStockRequest,
    ReleaseStockRequest,
    LoadStockRequest,
    DeliverStockRequest,
    WasteStockRequest,
    AdjustmentStockRequest,
)

logger = logging.getLogger("go_chicken.inventory")

router = APIRouter(
    prefix="/api/v1/inventory",
    tags=["Inventory"],
)


def _to_response(item) -> InventoryItemResponse:
    """Format ORM InventoryItem into API response schema with status check."""
    status_str = "Healthy"
    if item.available_qty < item.minimum_stock:
        status_str = "Low"
    return InventoryItemResponse(
        id=item.id,
        item=item.item_type,
        unit=item.unit,
        available=item.available_qty,
        reserved=item.reserved_qty,
        loaded=item.loaded_qty,
        delivered_qty=item.delivered_qty,
        waste_qty=item.waste_qty,
        returned_qty=item.returned_qty,
        minimum=item.minimum_stock,
        reorder_level=item.reorder_level,
        status=status_str,
    )


@router.get("", response_model=List[InventoryItemResponse])
@router.get("/", response_model=List[InventoryItemResponse])
async def get_inventory(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get current inventory snapshots across all items for the tenant."""
    items = await InventoryService.get_all_inventory(db, tenant_id)
    return [_to_response(it) for it in items]


@router.get("/transactions", response_model=List[InventoryTransactionResponse])
async def get_transactions(
    item_type: Optional[str] = None,
    limit: int = 50,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get recent ledger transactions (audit trail)."""
    txns = await InventoryService.get_recent_transactions(
        db=db, tenant_id=tenant_id, item_type=item_type, limit=limit
    )
    return txns


@router.post("/purchase", response_model=InventoryItemResponse)
async def purchase_stock(
    payload: PurchaseStockRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Purchase incoming stock (+ available_qty)."""
    try:
        item = await InventoryService.purchase_stock(
            db=db,
            tenant_id=tenant_id,
            item_type=payload.item_type,
            quantity=payload.quantity,
            remarks=payload.remarks,
        )
        return _to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reserve", response_model=InventoryItemResponse)
async def reserve_stock(
    payload: ReserveStockRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Reserve inventory for an order."""
    try:
        success, msg, item = await InventoryService.reserve_stock(
            db=db,
            tenant_id=tenant_id,
            item_type=payload.item_type,
            quantity=payload.quantity,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return _to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/release", response_model=InventoryItemResponse)
async def release_stock(
    payload: ReleaseStockRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Release reserved stock back to available."""
    try:
        item = await InventoryService.release_stock(
            db=db,
            tenant_id=tenant_id,
            item_type=payload.item_type,
            quantity=payload.quantity,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )
        return _to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/load", response_model=InventoryItemResponse)
async def load_stock(
    payload: LoadStockRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Load reserved stock onto a truck."""
    try:
        item = await InventoryService.load_stock(
            db=db,
            tenant_id=tenant_id,
            item_type=payload.item_type,
            quantity=payload.quantity,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )
        return _to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/deliver", response_model=InventoryItemResponse)
async def deliver_stock(
    payload: DeliverStockRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Deliver loaded stock to retailer."""
    try:
        item = await InventoryService.deliver_stock(
            db=db,
            tenant_id=tenant_id,
            item_type=payload.item_type,
            quantity=payload.quantity,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )
        return _to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/waste", response_model=InventoryItemResponse)
async def waste_stock(
    payload: WasteStockRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Record inventory waste / mortality."""
    try:
        item = await InventoryService.record_waste(
            db=db,
            tenant_id=tenant_id,
            item_type=payload.item_type,
            quantity=payload.quantity,
            reason=payload.reason,
        )
        return _to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/adjustment", response_model=InventoryItemResponse)
async def adjustment_stock(
    payload: AdjustmentStockRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Manual inventory audit adjustment (+ or - quantity)."""
    try:
        item = await InventoryService.record_adjustment(
            db=db,
            tenant_id=tenant_id,
            item_type=payload.item_type,
            quantity=payload.quantity,
            remarks=payload.remarks,
        )
        return _to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
