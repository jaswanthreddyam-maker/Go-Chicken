"""Comprehensive automated unit tests for PR 6 OutboxWorker runtime engine."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from core.outbox_worker import (
    ConsumerRegistration,
    EventHandler,
    HandlerRegistry,
    IntegrationEvent,
    OutboxWorker,
    OutboxWorkerMetrics,
)
from models.outbox import IntegrationOutbox

pytestmark = pytest.mark.asyncio


class DummyHandler(EventHandler):
    def __init__(self, succeed: bool = True, sleep_sec: float = 0.0, exc: Optional[Exception] = None):
        self.succeed = succeed
        self.sleep_sec = sleep_sec
        self.exc = exc
        self.handled_events: list[IntegrationEvent] = []

    async def handle(self, event: IntegrationEvent) -> None:
        self.handled_events.append(event)
        if self.sleep_sec > 0:
            await asyncio.sleep(self.sleep_sec)
        if self.exc:
            raise self.exc
        if not self.succeed:
            raise RuntimeError("Dummy handler failure")


def make_mock_outbox_entry(
    event_type: str = "OrderConfirmedIntegrationEvent",
    status: str = "PENDING",
    retry_count: int = 0,
    max_retries: int = 5,
) -> IntegrationOutbox:
    entry = IntegrationOutbox(
        id=uuid4(),
        event_id=uuid4(),
        tenant_id=uuid4(),
        event_type=event_type,
        aggregate_type="Order",
        aggregate_id=uuid4(),
        correlation_id="corr-123",
        causation_id="cause-123",
        payload={"order_id": "123", "amount": 100},
        status=status,
        retry_count=retry_count,
        max_retries=max_retries,
    )
    entry.created_at = datetime.now(timezone.utc)
    return entry


async def test_handler_registry_registration_and_resolution():
    registry = HandlerRegistry()
    handler = DummyHandler()
    registry.register(
        "OrderConfirmedIntegrationEvent",
        handler,
        max_concurrency=8,
        timeout_seconds=15.0,
        retryable=True,
    )

    resolved = registry.resolve("OrderConfirmedIntegrationEvent")
    assert resolved is not None
    assert resolved.handler == handler
    assert resolved.max_concurrency == 8
    assert resolved.timeout_seconds == 15.0

    unresolved = registry.resolve("NonExistentEvent")
    assert unresolved is None


async def test_worker_empty_queue_polling():
    registry = HandlerRegistry()
    worker = OutboxWorker(registry=registry, batch_size=10)
    mock_db = AsyncMock()

    with patch("core.outbox_worker.OutboxService.get_pending_events", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        processed = await worker.process_batch(mock_db)

    assert processed == 0
    assert worker.metrics.worker_batches_processed_total == 0


async def test_worker_successful_dispatch_and_envelope_mapping():
    registry = HandlerRegistry()
    handler = DummyHandler(succeed=True)
    registry.register("OrderConfirmedIntegrationEvent", handler)

    entry = make_mock_outbox_entry()
    worker = OutboxWorker(registry=registry, batch_size=10)
    mock_db = AsyncMock()

    with patch("core.outbox_worker.OutboxService.get_pending_events", new_callable=AsyncMock) as mock_get, \
         patch("core.outbox_worker.OutboxService.mark_processed", new_callable=AsyncMock) as mock_mark:
        mock_get.return_value = [entry]
        processed = await worker.process_batch(mock_db)

    assert processed == 1
    assert len(handler.handled_events) == 1

    # Verify IntegrationEvent envelope fields
    envelope = handler.handled_events[0]
    assert envelope.event_id == entry.event_id
    assert envelope.event_type == entry.event_type
    assert envelope.aggregate_id == entry.aggregate_id
    assert envelope.correlation_id == "corr-123"
    assert envelope.payload == {"order_id": "123", "amount": 100}

    # Verify mark_processed called
    mock_mark.assert_awaited_once_with(mock_db, entry, commit=True)
    assert worker.metrics.processed_total == 1
    assert worker.metrics.worker_batches_processed_total == 1


async def test_worker_unregistered_event_skips_dispatch():
    registry = HandlerRegistry()
    entry = make_mock_outbox_entry(event_type="UnregisteredEvent")

    worker = OutboxWorker(registry=registry, batch_size=10)
    mock_db = AsyncMock()

    with patch("core.outbox_worker.OutboxService.get_pending_events", new_callable=AsyncMock) as mock_get, \
         patch("core.outbox_worker.OutboxService.mark_processed", new_callable=AsyncMock) as mock_mark:
        mock_get.return_value = [entry]
        processed = await worker.process_batch(mock_db)

    assert processed == 0
    mock_mark.assert_not_called()


async def test_worker_handler_timeout():
    registry = HandlerRegistry()
    # Handler sleeps 0.5s, but registration timeout is 0.05s
    handler = DummyHandler(sleep_sec=0.5)
    registry.register("OrderConfirmedIntegrationEvent", handler, timeout_seconds=0.05)

    entry = make_mock_outbox_entry()
    worker = OutboxWorker(registry=registry, batch_size=10)
    mock_db = AsyncMock()

    with patch("core.outbox_worker.OutboxService.get_pending_events", new_callable=AsyncMock) as mock_get, \
         patch("core.outbox_worker.OutboxService.mark_failed", new_callable=AsyncMock) as mock_failed:
        mock_get.return_value = [entry]
        processed = await worker.process_batch(mock_db)

    assert processed == 0
    mock_failed.assert_awaited_once()
    assert worker.metrics.failed_total == 1
    assert worker.metrics.retry_total == 1


async def test_worker_retry_scheduling_on_handler_exception():
    registry = HandlerRegistry()
    handler = DummyHandler(succeed=False)
    registry.register("OrderConfirmedIntegrationEvent", handler)

    entry = make_mock_outbox_entry(retry_count=1, max_retries=5)
    worker = OutboxWorker(registry=registry)
    mock_db = AsyncMock()

    with patch("core.outbox_worker.OutboxService.get_pending_events", new_callable=AsyncMock) as mock_get, \
         patch("core.outbox_worker.OutboxService.mark_failed", new_callable=AsyncMock) as mock_failed:
        mock_get.return_value = [entry]
        processed = await worker.process_batch(mock_db)

    assert processed == 0
    mock_failed.assert_awaited_once_with(mock_db, entry, error="Dummy handler failure", commit=True)
    assert worker.metrics.failed_total == 1
    assert worker.metrics.retry_total == 1


async def test_worker_dead_letter_transition():
    registry = HandlerRegistry()
    handler = DummyHandler(succeed=False)
    registry.register("OrderConfirmedIntegrationEvent", handler)

    # Entry with status="FAILED" after OutboxService.mark_failed transitions it
    entry = make_mock_outbox_entry(retry_count=4, max_retries=5)

    async def mock_mark_failed_side_effect(db, evt, error, commit=True):
        evt.status = "FAILED"

    worker = OutboxWorker(registry=registry)
    mock_db = AsyncMock()

    with patch("core.outbox_worker.OutboxService.get_pending_events", new_callable=AsyncMock) as mock_get, \
         patch("core.outbox_worker.OutboxService.mark_failed", side_effect=mock_mark_failed_side_effect) as mock_failed:
        mock_get.return_value = [entry]
        processed = await worker.process_batch(mock_db)

    assert processed == 0
    assert worker.metrics.failed_total == 1
    assert worker.metrics.dead_letter_total == 1


async def test_worker_batch_isolation_one_failure_does_not_block_others():
    registry = HandlerRegistry()
    success_handler = DummyHandler(succeed=True)
    failing_handler = DummyHandler(succeed=False)

    registry.register("OrderConfirmedIntegrationEvent", success_handler)
    registry.register("OrderInvoiceGeneratedIntegrationEvent", failing_handler)

    entry1 = make_mock_outbox_entry(event_type="OrderConfirmedIntegrationEvent")
    entry2 = make_mock_outbox_entry(event_type="OrderInvoiceGeneratedIntegrationEvent")
    entry3 = make_mock_outbox_entry(event_type="OrderConfirmedIntegrationEvent")

    worker = OutboxWorker(registry=registry, batch_size=10)
    mock_db = AsyncMock()

    with patch("core.outbox_worker.OutboxService.get_pending_events", new_callable=AsyncMock) as mock_get, \
         patch("core.outbox_worker.OutboxService.mark_processed", new_callable=AsyncMock) as mock_mark, \
         patch("core.outbox_worker.OutboxService.mark_failed", new_callable=AsyncMock) as mock_failed:
        mock_get.return_value = [entry1, entry2, entry3]
        processed = await worker.process_batch(mock_db)

    assert processed == 2
    assert mock_mark.await_count == 2
    assert mock_failed.await_count == 1
    assert worker.metrics.processed_total == 2
    assert worker.metrics.failed_total == 1


async def test_worker_graceful_shutdown():
    registry = HandlerRegistry()
    worker = OutboxWorker(registry=registry, shutdown_grace_period_seconds=0.5)

    worker.metrics.worker_active_handlers = 1

    async def complete_handler_after_delay():
        await asyncio.sleep(0.1)
        worker.metrics.worker_active_handlers = 0

    asyncio.create_task(complete_handler_after_delay())

    worker.is_running = True
    worker.metrics.worker_running = 1
    await worker.shutdown()

    assert worker.is_running is False
    assert worker.metrics.worker_running == 0


async def test_registry_clear_and_multiple_registrations():
    registry = HandlerRegistry()
    registry.register("EventA", DummyHandler())
    registry.register("EventB", DummyHandler())

    assert registry.resolve("EventA") is not None
    assert registry.resolve("EventB") is not None

    registry.clear()
    assert registry.resolve("EventA") is None
    assert registry.resolve("EventB") is None


async def test_worker_start_stop_daemon_loop():
    registry = HandlerRegistry()
    worker = OutboxWorker(registry=registry, poll_interval_seconds=0.05)
    mock_db = AsyncMock()

    def session_factory():
        class MockContextManager:
            async def __aenter__(self):
                return mock_db
            async def __aexit__(self, exc_type, exc, tb):
                pass
        return MockContextManager()

    with patch("core.outbox_worker.OutboxService.get_pending_events", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        task = asyncio.create_task(worker.start(session_factory))
        await asyncio.sleep(0.12)
        await worker.stop()
        await task

    assert worker.is_running is False
    assert worker.metrics.worker_last_poll_timestamp > 0

