"""Unit tests for TruckService Phase A warehouse capacity validation & OrderService integration."""

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from core.truck_service import TruckService
from core.order_service import OrderService
from models.logistics import Truck
from models.order import Order
from models.inventory import InventoryItem


@pytest.fixture
def sample_truck():
    tenant_id = uuid4()
    return Truck(
        id=uuid4(),
        tenant_id=tenant_id,
        license_plate="AP 16 AB 9999",
        max_capacity_kg=Decimal("1000.00"),
    )


@pytest.fixture
def sample_order(sample_truck):
    return Order(
        id=uuid4(),
        tenant_id=sample_truck.tenant_id,
        retailer_id=uuid4(),
        item_type="BROILER",
        quantity_kg=Decimal("300.00"),
        status="confirmed",
    )


@pytest.mark.asyncio
async def test_assign_truck_within_capacity_succeeds(sample_truck, sample_order):
    mock_db = AsyncMock()

    # Mock get_truck_for_tenant
    mock_truck_res = MagicMock()
    mock_truck_res.scalar_one_or_none.return_value = sample_truck

    # Mock get_current_loaded_weight_kg = 200 KG
    mock_weight_res = MagicMock()
    mock_weight_res.scalar.return_value = Decimal("200.00")
    mock_weight_res.scalar_one_or_none.return_value = Decimal("200.00")

    mock_db.execute.side_effect = [mock_truck_res, mock_weight_res]

    success, msg = await TruckService.assign_truck_to_order(
        db=mock_db,
        tenant_id=sample_truck.tenant_id,
        order=sample_order,
        truck_id=sample_truck.id,
        performed_by="DISPATCHER_RAM",
        commit=False,
    )

    assert success is True
    assert sample_order.truck_id == sample_truck.id
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_assign_truck_exceeding_capacity_fails(sample_truck, sample_order):
    """PR 4 Phase A: Reject truck assignment when projected payload exceeds max_capacity_kg."""
    mock_db = AsyncMock()

    sample_truck.max_capacity_kg = Decimal("500.00")
    sample_order.quantity_kg = Decimal("200.00")

    mock_truck_res = MagicMock()
    mock_truck_res.scalar_one_or_none.return_value = sample_truck

    # Current loaded weight is 400 KG -> 400 + 200 = 600 KG > 500 KG max
    mock_weight_res = MagicMock()
    mock_weight_res.scalar.return_value = Decimal("400.00")
    mock_weight_res.scalar_one_or_none.return_value = Decimal("400.00")

    mock_db.execute.side_effect = [mock_truck_res, mock_weight_res]

    success, msg = await TruckService.assign_truck_to_order(
        db=mock_db,
        tenant_id=sample_truck.tenant_id,
        order=sample_order,
        truck_id=sample_truck.id,
        performed_by="DISPATCHER_RAM",
        commit=False,
    )

    assert success is False
    assert "Truck over capacity" in msg
    assert sample_order.truck_id is None


@pytest.mark.asyncio
async def test_order_service_load_order_over_capacity_rolls_back(sample_truck, sample_order):
    """Verify OrderService transaction rolls back atomically when TruckService rejects capacity."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    sample_truck.max_capacity_kg = Decimal("400.00")
    sample_order.quantity_kg = Decimal("300.00")

    mock_truck_res = MagicMock()
    mock_truck_res.scalar_one_or_none.return_value = sample_truck

    # Currently loaded weight = 250 KG -> 250 + 300 = 550 > 400
    mock_weight_res = MagicMock()
    mock_weight_res.scalar.return_value = Decimal("250.00")
    mock_weight_res.scalar_one_or_none.return_value = Decimal("250.00")

    mock_db.execute.side_effect = [mock_truck_res, mock_weight_res]

    res = await OrderService.load_order(
        db=mock_db,
        tenant_id=sample_order.tenant_id,
        order=sample_order,
        truck_id=sample_truck.id,
        performed_by="WAREHOUSE_LEAD",
    )

    assert res.success is False
    assert "Truck over capacity" in res.message
    assert sample_order.status == "confirmed"  # State rolled back
    mock_db.rollback.assert_awaited_once()
