"""Unit tests for PR 5 — Transactional Outbox Pattern guaranteed event delivery."""

import pytest
from uuid import uuid4
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from core.outbox_service import OutboxService
from core.order_service import OrderService
from models.outbox import IntegrationOutbox
from models.order import Order


@pytest.mark.asyncio
async def test_record_events_adds_to_db_session_uncommitted():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    tenant_id = uuid4()
    order_id = uuid4()

    entries = await OutboxService.record_events(
        db=mock_db,
        tenant_id=tenant_id,
        aggregate_type="Order",
        aggregate_id=order_id,
        event_types=["OrderConfirmedIntegrationEvent"],
        payload={"quantity_kg": "250.00"},
        commit=False,
    )

    assert len(entries) == 1
    assert entries[0].status == "PENDING"
    assert entries[0].event_type == "OrderConfirmedIntegrationEvent"
    mock_db.add.assert_called_once_with(entries[0])
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_order_service_transition_creates_outbox_entry():
    """Verify OrderService._execute_transition writes to outbox before committing."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    order = Order(
        id=uuid4(),
        tenant_id=uuid4(),
        retailer_id=uuid4(),
        item_type="BROILER",
        quantity_kg=Decimal("100.00"),
        status="pending",
    )

    from models.inventory import InventoryItem
    mock_item = InventoryItem(
        id=uuid4(),
        tenant_id=order.tenant_id,
        item_type="BROILER",
        available_qty=Decimal("500.00"),
        reserved_qty=Decimal("0.00"),
    )
    mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_item))

    res = await OrderService.confirm_order(
        db=mock_db,
        tenant_id=order.tenant_id,
        order=order,
        performed_by="OPERATOR_RAM",
    )

    assert res.success is True

    # Verify both OrderTimeline and IntegrationOutbox were added in the transaction
    added_objects = [c[0][0] for c in mock_db.add.call_args_list]
    outbox_entries = [obj for obj in added_objects if isinstance(obj, IntegrationOutbox)]
    assert len(outbox_entries) == 1
    assert outbox_entries[0].event_type == "OrderConfirmedIntegrationEvent"
    assert outbox_entries[0].status == "PENDING"


@pytest.mark.asyncio
async def test_outbox_mark_processed_and_mark_failed_retries():
    mock_db = AsyncMock()
    event = IntegrationOutbox(
        id=uuid4(),
        tenant_id=uuid4(),
        event_type="OrderDeliveredIntegrationEvent",
        aggregate_type="Order",
        aggregate_id=uuid4(),
        payload={},
        status="PENDING",
        retry_count=0,
        max_retries=2,
    )

    # First failure -> retry_count=1, status remains PENDING
    await OutboxService.mark_failed(mock_db, event, "Connection reset by peer", commit=False)
    assert event.retry_count == 1
    assert event.status == "PENDING"
    assert "Connection reset" in event.last_error

    # Second failure -> retry_count=2 >= max_retries(2) -> transitions to FAILED dead letter
    await OutboxService.mark_failed(mock_db, event, "Timeout", commit=False)
    assert event.retry_count == 2
    assert event.status == "FAILED"

    # Mark processed test
    event.status = "PENDING"
    await OutboxService.mark_processed(mock_db, event, commit=False)
    assert event.status == "PROCESSED"
    assert event.processed_at is not None
