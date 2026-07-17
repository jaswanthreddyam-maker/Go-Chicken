"""Unit tests for core OrderService 6-step transition engine & Inventory ACID integration."""

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from core.order_service import OrderService, OrderTransitionResult
from models.order import Order
from models.inventory import InventoryItem


def setup_mock_inventory(
    mock_db,
    available_qty="500.00",
    reserved_qty="100.00",
    loaded_qty="100.00",
):
    item = InventoryItem(
        id=uuid4(),
        item_type="BROILER",
        available_qty=Decimal(available_qty),
        reserved_qty=Decimal(reserved_qty),
        loaded_qty=Decimal(loaded_qty),
        delivered_qty=Decimal("0.00"),
        waste_qty=Decimal("0.00"),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = item
    mock_db.execute.return_value = mock_result
    return item


@pytest.fixture
def sample_order():
    tenant_id = uuid4()
    order = Order(
        id=uuid4(),
        tenant_id=tenant_id,
        retailer_id=uuid4(),
        item_type="BROILER",
        quantity_kg=Decimal("100.00"),
        status="pending",
        unit_price=Decimal("150.00"),
        total_amount=Decimal("15000.00"),
    )
    return order


@pytest.mark.asyncio
async def test_confirm_order_freezes_price_and_writes_timeline(sample_order):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    setup_mock_inventory(mock_db, available_qty="500.00")
    tenant_id = sample_order.tenant_id

    result = await OrderService.confirm_order(
        db=mock_db,
        tenant_id=tenant_id,
        order=sample_order,
        unit_price=Decimal("180.50"),
        performed_by="ADMIN_JOHN",
        reason="Market confirmation",
    )

    assert isinstance(result, OrderTransitionResult)
    assert result.success is True
    assert result.previous_status == "pending"
    assert result.new_status == "confirmed"
    assert sample_order.status == "confirmed"
    assert sample_order.unit_price == Decimal("180.50")
    assert sample_order.total_amount == Decimal("18050.00")
    assert "OrderConfirmedIntegrationEvent" in result.emitted_events

    # Verify timeline entry was added to mock_db
    assert mock_db.add.call_count >= 1
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_order_insufficient_stock_rolls_back(sample_order):
    """PR 3 guarantee: If inventory reservation fails, order state rolls back atomically."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    setup_mock_inventory(mock_db, available_qty="20.00")  # Only 20 KG available, need 100 KG
    tenant_id = sample_order.tenant_id

    result = await OrderService.confirm_order(
        db=mock_db,
        tenant_id=tenant_id,
        order=sample_order,
        unit_price=Decimal("180.50"),
    )

    assert result.success is False
    assert "Insufficient stock" in result.message
    assert sample_order.status == "pending"  # Order state unmodified
    mock_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_order_tenant_isolation_rejection(sample_order):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    wrong_tenant_id = uuid4()

    result = await OrderService.confirm_order(
        db=mock_db,
        tenant_id=wrong_tenant_id,
        order=sample_order,
        unit_price=Decimal("180.00"),
    )

    assert result.success is False
    assert "active tenant" in result.message
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_load_order_without_truck_id_fails(sample_order):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    sample_order.status = "confirmed"

    result = await OrderService.load_order(
        db=mock_db,
        tenant_id=sample_order.tenant_id,
        order=sample_order,
        truck_id=None,
    )

    assert result.success is False
    assert "No delivery truck assigned" in result.message
    assert sample_order.status == "confirmed"
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_load_and_dispatch_order_success(sample_order):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    setup_mock_inventory(mock_db, reserved_qty="150.00")
    sample_order.status = "confirmed"
    truck_id = uuid4()

    # Step 1: Load Order
    load_result = await OrderService.load_order(
        db=mock_db,
        tenant_id=sample_order.tenant_id,
        order=sample_order,
        truck_id=truck_id,
        performed_by="OPERATOR_1",
    )
    assert load_result.success is True
    assert sample_order.status == "loaded"
    assert sample_order.truck_id == truck_id

    # Step 2: Dispatch Order
    dispatch_result = await OrderService.dispatch_order(
        db=mock_db,
        tenant_id=sample_order.tenant_id,
        order=sample_order,
        driver_phone="9876543210",
        driver_name="Ramesh Driver",
        performed_by="DISPATCHER",
    )
    assert dispatch_result.success is True
    assert sample_order.status == "out_for_delivery"
    assert sample_order.driver_phone == "9876543210"
    assert sample_order.driver_name == "Ramesh Driver"
    assert sample_order.dispatch_time is not None


@pytest.mark.asyncio
async def test_deliver_order_weight_conservation(sample_order):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    setup_mock_inventory(mock_db, loaded_qty="100.00")
    sample_order.status = "out_for_delivery"

    # Valid conservation: 95 actual + 5 waste == 100 loaded
    deliver_result = await OrderService.deliver_order(
        db=mock_db,
        tenant_id=sample_order.tenant_id,
        order=sample_order,
        actual_delivered_kg=Decimal("95.00"),
        waste_kg=Decimal("5.00"),
        performed_by="DRIVER_RAMESH",
    )
    assert deliver_result.success is True
    assert sample_order.status == "delivered"
    assert sample_order.delivery_date is not None


@pytest.mark.asyncio
async def test_cancel_order_releases_stock(sample_order):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    setup_mock_inventory(mock_db, reserved_qty="100.00")
    sample_order.status = "confirmed"

    cancel_result = await OrderService.cancel_order(
        db=mock_db,
        tenant_id=sample_order.tenant_id,
        order=sample_order,
        reason="Retailer shop closed today",
        performed_by="ADMIN_JOHN",
    )
    assert cancel_result.success is True
    assert sample_order.status == "cancelled"
    assert "OrderCancelledIntegrationEvent" in cancel_result.emitted_events
