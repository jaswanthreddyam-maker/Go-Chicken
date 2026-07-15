"""Orders Router for Management Dashboard and Webhook Ingestion.

Provides APIs to list live poultry orders and update their fulfillment status.
When an admin updates an order status (e.g. clicks 'Delivered'), an automated
WhatsApp notification is sent immediately to the retailer!
"""

import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import get_settings
from core.database import get_db
from core.auth import get_current_tenant
from models.order import Order
from schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from routers.whatsapp import _send_whatsapp_reply

logger = logging.getLogger("go_chicken.orders")
settings = get_settings()

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"]
)


@router.api_route("/status", methods=["GET", "POST"])
async def get_order_status_by_phone(
    phone: str = "",
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Fetch recent order status by phone number for WhatsApp/n8n inquiries."""
    stmt = select(Order).where(Order.tenant_id == tenant_id)
    if phone:
        clean_phone = phone.replace("+", "").strip()
        stmt = stmt.where(Order.phone_number.contains(clean_phone[-10:]))
    stmt = stmt.order_by(Order.created_at.desc())
    res = await db.execute(stmt)
    order = res.scalars().first()
    
    if not order:
        return {
            "order_number": "N/A",
            "status": "No active orders found for this phone number.",
            "estimated_delivery": "-"
        }
        
    return {
        "order_number": f"ORD-{str(order.id)[:8].upper()}",
        "status": order.status.title(),
        "estimated_delivery": "Today by 5:00 PM"
    }


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Webhook / REST endpoint to manually or externally create an order."""
    new_order = Order(
        tenant_id=tenant_id,
        phone_number=order_data.phone_number,
        item_type=order_data.item_type,
        quantity_kg=order_data.quantity_kg,
        total_amount=order_data.total_amount,
        status="pending"
    )
    
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    return new_order


@router.get("/", response_model=List[OrderResponse])
async def get_all_orders(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Dashboard endpoint: Fetch all poultry orders ordered by newest first."""
    result = await db.execute(
        select(Order).where(Order.tenant_id == tenant_id).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return orders


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    background_tasks: BackgroundTasks,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Admin Dashboard endpoint: Toggle order fulfillment status.
    
    Automatically triggers a WhatsApp notification to the retailer when status changes!
    """
    result = await db.execute(select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    old_status = order.status
    new_status = payload.status.lower()
    order.status = new_status
    
    await db.commit()
    await db.refresh(order)
    
    logger.info(f"📋 Order {order_id} status changed: {old_status} -> {new_status}")
    
    # Trigger automated WhatsApp status notification if phone number exists
    if order.phone_number:
        msg = _format_status_notification_message(order, new_status)
        background_tasks.add_task(
            _send_whatsapp_reply,
            phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
            to=order.phone_number,
            message=msg
        )
        
    return order


def _format_status_notification_message(order: Order, status_val: str) -> str:
    """Format the customer WhatsApp notification message based on fulfillment status."""
    if status_val == "delivered":
        return (
            f"🎉 *Order Delivered!*\n\n"
            f"Your order for *{order.quantity_kg}kg {order.item_type}* "
            f"(Total: ₹{order.total_amount or 0}) has been successfully delivered! 🚛\n\n"
            "Thank you for partnering with *Go Chicken*! 🐔\n\n"
            f"_Order ID: {order.id}_"
        )
    elif status_val == "processing":
        return (
            f"⚙️ *Order Processing*\n\n"
            f"Your order for *{order.quantity_kg}kg {order.item_type}* is currently being prepared "
            "and packed at our hub. We will dispatch it shortly! 🐔\n\n"
            f"_Order ID: {order.id}_"
        )
    elif status_val in ("shipped", "dispatched", "out_for_delivery"):
        return (
            f"🚛 *Out for Delivery!*\n\n"
            f"Your order for *{order.quantity_kg}kg {order.item_type}* has left our dispatch hub "
            "and is on its way to your shop!\n\n"
            f"_Order ID: {order.id}_"
        )
    elif status_val == "cancelled":
        return (
            f"❌ *Order Cancelled*\n\n"
            f"Your order for *{order.quantity_kg}kg {order.item_type}* has been marked as cancelled. "
            "Please reach out to our support team if you have any questions.\n\n"
            f"_Order ID: {order.id}_"
        )
    else:
        return (
            f"ℹ️ *Order Update*\n\n"
            f"Your order for *{order.quantity_kg}kg {order.item_type}* status has been updated to: *{status_val.upper()}*\n\n"
            f"_Order ID: {order.id}_"
        )
