"""Unit tests for PR 4B — Logistics Dispatch, Delivery Proof, and Invoice Generation Separation."""

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from core.order_service import OrderService
from models.order import Order
from models.logistics import Truck
from models.inventory import InventoryItem


@pytest.fixture
def sample_truck():
    return Truck(
        id=uuid4(),
        tenant_id=uuid4(),
        license_plate="AP 16 TS 4321",
        max_capacity_kg=Decimal("1000.00"),
    )


@pytest.fixture
def sample_order(sample_truck):
    return Order(
        id=uuid4(),
        tenant_id=sample_truck.tenant_id,
        retailer_id=uuid4(),
        item_type="BROILER",
        quantity_kg=Decimal("200.00"),
        status="loaded",
        truck_id=sample_truck.id,
    )


@pytest.mark.asyncio
async def test_dispatch_order_records_driver_and_timeline(sample_order):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    res = await OrderService.dispatch_order(
        db=mock_db,
        tenant_id=sample_order.tenant_id,
        order=sample_order,
        payload={
            "driver_name": "Ramesh Kumar",
            "driver_phone": "+919876543210",
        },
        performed_by="DISPATCHER_1",
    )

    assert res.success is True
    assert sample_order.status == "out_for_delivery"
    assert sample_order.driver_name == "Ramesh Kumar"
    assert sample_order.driver_phone == "+919876543210"
    assert sample_order.dispatch_time is not None
    assert "OrderOutfordeliveryIntegrationEvent" in res.emitted_events


@pytest.mark.asyncio
async def test_deliver_order_records_delivery_proof_and_invoice_event(sample_order):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    # Mock inventory item return for deliver_stock and record_waste
    mock_inv_res = MagicMock()
    mock_inv_res.scalar_one_or_none.return_value = InventoryItem(
        id=uuid4(),
        tenant_id=sample_order.tenant_id,
        item_type="BROILER",
        available_qty=Decimal("500.00"),
        loaded_qty=Decimal("200.00"),
        delivered_qty=Decimal("0.00"),
        waste_qty=Decimal("0.00"),
    )
    mock_db.execute.return_value = mock_inv_res

    sample_order.status = "out_for_delivery"

    delivery_proof_payload = {
        "actual_delivered_kg": "198.50",
        "waste_kg": "1.50",
        "receiver_name": "Ali Poultry Shop",
        "receiver_phone": "+919811122233",
        "delivery_gps_lat": 17.3850,
        "delivery_gps_lng": 78.4867,
        "delivery_photo_url": "https://cdn.gochicken.com/proofs/ord123.jpg",
        "delivery_signature_url": "https://cdn.gochicken.com/sigs/ord123.png",
        "remarks": "Delivered intact with 1.5 KG transit loss",
    }

    res = await OrderService.deliver_order(
        db=mock_db,
        tenant_id=sample_order.tenant_id,
        order=sample_order,
        payload=delivery_proof_payload,
        performed_by="DRIVER_RAMESH",
    )

    assert res.success is True
    assert res.new_status == "delivered"

    # Verify emitted events include both Delivered and InvoiceGenerated
    assert "OrderDeliveredIntegrationEvent" in res.emitted_events
    assert "OrderInvoiceGeneratedIntegrationEvent" in res.emitted_events

    # Verify timeline context enrichment & invoice separation flag
    timeline_entry = next(c[0][0] for c in mock_db.add.call_args_list if hasattr(c[0][0], "transition_context"))
    ctx = timeline_entry.transition_context
    assert ctx["receiver_name"] == "Ali Poultry Shop"
    assert ctx["actual_delivered_kg"] == "198.50"
    assert ctx["waste_kg"] == "1.50"
    assert ctx["delivery_gps_lat"] == 17.3850
    assert ctx["invoice_status"] == "GENERATED_PENDING_KHATA"
