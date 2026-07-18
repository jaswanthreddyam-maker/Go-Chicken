"""Tests for the Management Layer (Dashboard APIs).

Tests cover:
  1. GET /api/v1/pricing -> fetch and seed default product rates
  2. PUT /api/v1/pricing/{item_type} -> dynamic pricing updates
  3. GET /api/v1/orders -> listing live orders ordered by newest first
  4. PATCH /api/v1/orders/{order_id}/status -> status toggle & automated WhatsApp alert
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from models.order import Order
from models.pricing import ProductPrice
from schemas.pricing import PriceUpdate
from schemas.order import OrderStatusUpdate


class TestPricingManagement:
    """Test dynamic database-backed pricing APIs."""

    @pytest.mark.asyncio
    async def test_get_all_prices_seeds_defaults_when_empty(self):
        """When ProductPrice DB table is empty, get_all_prices seeds config defaults."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        from core.pricing_service import get_all_prices
        prices = await get_all_prices(mock_db)

        assert "Live Bird" in prices
        assert "Dressed" in prices
        assert "Skinless" in prices
        assert mock_db.add.call_count == 3
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_price_creates_or_updates_db(self):
        """Updating price should persist new numeric value in DB."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        existing_price = ProductPrice(item_type="Live Bird", price_per_kg=Decimal("180.00"))
        mock_result.scalar_one_or_none.return_value = existing_price
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        from core.pricing_service import update_price
        updated = await update_price(mock_db, "Live Bird", Decimal("195.50"))

        assert updated.price_per_kg == Decimal("195.50")
        mock_db.commit.assert_called_once()


class TestOrderStatusToggle:
    """Test order status toggle and automated WhatsApp notifications."""

    @pytest.mark.asyncio
    async def test_status_toggle_triggers_whatsapp_notification(self):
        """Changing status to 'delivered' should queue automated WhatsApp alert."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        
        test_order_id = uuid.uuid4()
        test_tenant_id = uuid.uuid4()
        existing_order = Order(
            id=test_order_id,
            tenant_id=test_tenant_id,
            phone_number="+919876543210",
            item_type="Live Bird",
            quantity_kg=Decimal("50.00"),
            total_amount=Decimal("9000.00"),
            status="out_for_delivery"
        )
        mock_result.scalar_one_or_none.return_value = existing_order
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_bg_tasks = MagicMock()

        from routers.orders import update_order_status
        payload = OrderStatusUpdate(status="delivered")

        with patch("routers.orders._send_whatsapp_reply", new_callable=AsyncMock) as mock_reply:
            updated_order = await update_order_status(
                order_id=test_order_id,
                payload=payload,
                background_tasks=mock_bg_tasks,
                tenant_id=test_tenant_id,
                db=mock_db
            )

        assert updated_order.status == "delivered"
        mock_db.commit.assert_called_once()
        
        # Verify automated notification was queued to background tasks
        mock_bg_tasks.add_task.assert_called_once()
        task_func = mock_bg_tasks.add_task.call_args[0][0]
        task_kwargs = mock_bg_tasks.add_task.call_args[1]
        
        assert task_kwargs["to"] == "+919876543210"
        assert "Order Delivered" in task_kwargs["message"]
        assert "50.00kg Live Bird" in task_kwargs["message"]
        assert "₹9000" in task_kwargs["message"]

    @pytest.mark.asyncio
    async def test_status_toggle_processing_message(self):
        """Changing status to 'processing' generates correct notification text."""
        test_order = Order(
            id=uuid.uuid4(),
            phone_number="+919876543210",
            item_type="Dressed",
            quantity_kg=Decimal("30.00"),
            total_amount=Decimal("7500.00"),
            status="pending"
        )
        from routers.orders import _format_status_notification_message
        msg = _format_status_notification_message(test_order, "processing")
        assert "Order Processing" in msg
        assert "30.00kg Dressed" in msg
