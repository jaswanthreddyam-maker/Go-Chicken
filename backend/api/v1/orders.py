"""Ordering Engine Router — WhatsApp ingestion & daily order views."""

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.user import User, UserRole
from models.order import Order, OrderStatus
from schemas.orders import WhatsAppOrderRequest, OrderOut, DailyOrderSummary

router = APIRouter()


@router.post(
    "/whatsapp",
    response_model=OrderOut,
    summary="Receive an order from the WhatsApp Bot",
)
async def create_whatsapp_order(
    payload: WhatsAppOrderRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for the WhatsApp Business Bot.
    Looks up the retailer by phone, parses the message, and creates an order.
    """
    # 1. Find the retailer by phone
    result = await db.execute(
        select(User).where(
            User.phone == payload.retailer_phone,
            User.role == UserRole.RETAILER,
        )
    )
    retailer = result.scalar_one_or_none()

    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found for this phone number.")

    # 2. Parse the message (simplified — a real implementation would use NLP / regex)
    #    Expected format: "50kg live bird" or "30kg dressed"
    quantity_kg = _parse_quantity(payload.message_text)
    item_type = _parse_item_type(payload.message_text)

    # 3. TODO: Fetch today's price_per_kg from a pricing table or tenant config
    price_per_kg = Decimal("180.00")  # Placeholder
    total_amount = quantity_kg * price_per_kg

    # 4. Create the order
    order = Order(
        tenant_id=payload.tenant_id,
        retailer_id=retailer.id,
        status=OrderStatus.PENDING,
        item_type=item_type,
        quantity_kg=quantity_kg,
        price_per_kg=price_per_kg,
        total_amount=total_amount,
        delivery_date=date.today(),
    )
    db.add(order)
    await db.flush()

    return OrderOut(
        id=order.id,
        retailer_name=retailer.name,
        item_type=order.item_type,
        quantity_kg=order.quantity_kg,
        price_per_kg=order.price_per_kg,
        total_amount=order.total_amount,
        status=order.status.value,
        delivery_date=order.delivery_date,
        created_at=order.created_at,
    )


@router.get(
    "/daily",
    response_model=DailyOrderSummary,
    summary="Get all orders for a specific delivery date",
)
async def get_daily_orders(
    tenant_id: str = Query(...),
    delivery_date: date = Query(default_factory=date.today),
    db: AsyncSession = Depends(get_db),
):
    """Used by the Wholesaler Dashboard to see clustered orders for dispatch."""
    result = await db.execute(
        select(Order).where(
            Order.tenant_id == tenant_id,
            Order.delivery_date == delivery_date,
        )
    )
    orders = result.scalars().all()

    # Build the retailer name lookup
    retailer_ids = {o.retailer_id for o in orders}
    if retailer_ids:
        retailers_result = await db.execute(
            select(User).where(User.id.in_(retailer_ids))
        )
        retailer_map = {u.id: u.name for u in retailers_result.scalars().all()}
    else:
        retailer_map = {}

    order_items = [
        OrderOut(
            id=o.id,
            retailer_name=retailer_map.get(o.retailer_id, "Unknown"),
            item_type=o.item_type,
            quantity_kg=o.quantity_kg,
            price_per_kg=o.price_per_kg,
            total_amount=o.total_amount,
            status=o.status.value,
            delivery_date=o.delivery_date,
            created_at=o.created_at,
        )
        for o in orders
    ]

    total_kg = sum(o.quantity_kg for o in orders)

    return DailyOrderSummary(
        date=delivery_date,
        total_orders=len(orders),
        total_kg=total_kg,
        orders=order_items,
    )


# ── Helper Parsers ─────────────────────────────────────────────


def _parse_quantity(message: str) -> Decimal:
    """Extract numeric kg from a message like '50kg live bird'."""
    import re

    match = re.search(r"(\d+(?:\.\d+)?)\s*kg", message, re.IGNORECASE)
    if match:
        return Decimal(match.group(1))
    return Decimal("0")


def _parse_item_type(message: str) -> str:
    """Extract item type from a message. Defaults to 'Live Bird'."""
    message_lower = message.lower()
    if "dressed" in message_lower:
        return "Dressed"
    if "skinless" in message_lower:
        return "Skinless"
    return "Live Bird"
