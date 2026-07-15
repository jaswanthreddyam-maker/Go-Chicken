"""PR 8 Multi-Channel Communication Platform Unit Tests — Covering all 12 frozen verification categories."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any
import pytest

from models.communication import CommunicationLog
from core.communication_templates import (
    CommunicationTemplate,
    TemplateRegistry,
    TemplateRenderingError,
    default_template_registry,
)
from core.communication_providers import (
    WhatsAppProvider,
    SMSProvider,
    ProviderRegistry,
    UnsupportedChannelError,
)
from core.communication_service import CommunicationService
from core.communication_consumers import OrderConfirmedCommunicationConsumer
from core.outbox_worker import IntegrationEvent

pytestmark = pytest.mark.asyncio


class FakeResult:
    def __init__(self, scalars_list):
        self._list = scalars_list

    def scalars(self):
        return self

    def first(self):
        return self._list[0] if self._list else None

    def all(self):
        return self._list


class FakeCommunicationSession:
    """Deterministic in-memory async session for testing CommunicationService."""

    def __init__(self):
        self.items: list[Any] = []
        self.committed = False

    def add(self, obj: Any) -> None:
        self.items.append(obj)

    async def execute(self, stmt: Any) -> FakeResult:
        stmt_str = str(stmt).lower()
        results = [x for x in self.items if isinstance(x, CommunicationLog)]

        params = stmt.compile().params if hasattr(stmt, "compile") else {}
        for k, val in params.items():
            if "idempotency_key" in k:
                results = [r for r in results if r.idempotency_key == val]
            elif "tenant_id" in k:
                results = [r for r in results if r.tenant_id == val]
            elif "id" in k and isinstance(val, uuid.UUID):
                results = [r for r in results if r.id == val]

        return FakeResult(results)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj: Any) -> None:
        pass


class FakeSessionFactory:
    def __init__(self, session: FakeCommunicationSession):
        self.session = session

    def __call__(self):
        return self

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def test_01_provider_selection_and_routing():
    """Category 1: Dynamic Provider Selection & Routing from registry."""
    registry = ProviderRegistry()
    wa = WhatsAppProvider()
    sms = SMSProvider()
    registry.register(wa)
    registry.register(sms)

    assert registry.resolve("WHATSAPP") is wa
    assert registry.resolve("sms") is sms


async def test_02_template_rendering():
    """Category 2: Parameterized Template Rendering."""
    tmpl = CommunicationTemplate(
        template_id="CUSTOM_HELLO",
        channel="WHATSAPP",
        body_template="Hello {customer_name}, your order #{order_id} is ready!",
    )
    rendered = tmpl.render({"customer_name": "John", "order_id": "105"})
    assert rendered == "Hello John, your order #105 is ready!"


async def test_03_template_validation_error():
    """Category 3: Missing template variable raises typed TemplateRenderingError."""
    tmpl = CommunicationTemplate(
        template_id="STRICT_TMPL",
        channel="WHATSAPP",
        body_template="Order {order_id} total: {total_amount}",
    )
    with pytest.raises(TemplateRenderingError, match="Missing required context variables"):
        tmpl.render({"order_id": "100"})  # missing total_amount


async def test_04_duplicate_event_suppression():
    """Category 4: Duplicate Event Idempotency Suppression (3 calls send exactly 1 message)."""
    db = FakeCommunicationSession()
    provider_reg = ProviderRegistry()
    wa = WhatsAppProvider()
    provider_reg.register(wa)

    service = CommunicationService(provider_registry=provider_reg)
    tenant_id = uuid.uuid4()

    ctx = {"order_number": "101", "quantity_kg": "100.00", "unit_price": "150.00", "total_amount": "15000.00"}
    for _ in range(3):
        log = await service.send(
            db=db,
            tenant_id=tenant_id,
            recipient="+919876543210",
            template_id="ORDER_CONFIRMED",
            context=ctx,
            idempotency_key="event-idem-1",
            channel="WHATSAPP",
            commit=True,
        )

    assert len(wa.sent_messages) == 1
    assert log.idempotency_key == "event-idem-1"


async def test_05_retry_scheduling():
    """Category 5: Network failure transitions status to RETRYING and increments retry_count."""
    db = FakeCommunicationSession()
    provider_reg = ProviderRegistry()
    wa = WhatsAppProvider(fail_simulation=True, error_msg="Timeout")
    provider_reg.register(wa)

    service = CommunicationService(provider_registry=provider_reg, max_retries=3)
    log = await service.send(
        db=db,
        tenant_id=uuid.uuid4(),
        recipient="+919876543210",
        template_id="ORDER_LOADED",
        context={"order_number": "102", "truck_id": "TRK-01"},
        idempotency_key="retry-1",
        channel="WHATSAPP",
    )

    assert log.status == "RETRYING"
    assert log.retry_count == 1
    assert "Timeout" in str(log.error_message)


async def test_06_permanent_failure_handling():
    """Category 6: Exceeding max retries transitions status to FAILED_PERMANENT."""
    db = FakeCommunicationSession()
    provider_reg = ProviderRegistry()
    wa = WhatsAppProvider(fail_simulation=True)
    provider_reg.register(wa)

    service = CommunicationService(provider_registry=provider_reg, max_retries=1)
    log = await service.send(
        db=db,
        tenant_id=uuid.uuid4(),
        recipient="+919876543210",
        template_id="ORDER_LOADED",
        context={"order_number": "103", "truck_id": "TRK-02"},
        idempotency_key="perm-fail-1",
        channel="WHATSAPP",
    )

    assert log.status == "FAILED_PERMANENT"
    assert log.retry_count == 1


async def test_07_provider_timeout_error_handling():
    """Category 7: Resilient capture of provider error messages."""
    db = FakeCommunicationSession()
    provider_reg = ProviderRegistry()
    wa = WhatsAppProvider(fail_simulation=True, error_msg="Meta API Rate Limit Exceeded")
    provider_reg.register(wa)

    service = CommunicationService(provider_registry=provider_reg)
    log = await service.send(
        db=db,
        tenant_id=uuid.uuid4(),
        recipient="+919876543210",
        template_id="ORDER_LOADED",
        context={"order_number": "104", "truck_id": "TRK-03"},
        idempotency_key="timeout-1",
    )
    assert log.error_message == "Meta API Rate Limit Exceeded"


async def test_08_unsupported_channel_rejection():
    """Category 8: Passing unregistered channel raises UnsupportedChannelError."""
    db = FakeCommunicationSession()
    provider_reg = ProviderRegistry()
    service = CommunicationService(provider_registry=provider_reg)

    with pytest.raises(UnsupportedChannelError, match="Unsupported or unregistered communication channel"):
        await service.send(
            db=db,
            tenant_id=uuid.uuid4(),
            recipient="+919876543210",
            template_id="ORDER_LOADED",
            context={"order_number": "105", "truck_id": "TRK-04"},
            idempotency_key="unsup-1",
            channel="TELEGRAM",
        )


async def test_09_multi_channel_dispatch():
    """Category 9: Multi-channel dispatch across WHATSAPP and SMS."""
    db = FakeCommunicationSession()
    provider_reg = ProviderRegistry()
    wa = WhatsAppProvider()
    sms = SMSProvider()
    provider_reg.register(wa)
    provider_reg.register(sms)

    service = CommunicationService(provider_registry=provider_reg)
    tenant_id = uuid.uuid4()
    ctx = {"order_number": "106", "quantity_kg": "50.00", "unit_price": "180.00", "total_amount": "9000.00"}

    log_wa = await service.send(db, tenant_id, "+919876543210", "ORDER_CONFIRMED", ctx, "multi-wa-1", "WHATSAPP")
    log_sms = await service.send(db, tenant_id, "+919876543210", "ORDER_CONFIRMED", ctx, "multi-sms-1", "SMS")

    assert len(wa.sent_messages) == 1
    assert len(sms.sent_messages) == 1
    assert log_wa.channel == "WHATSAPP"
    assert log_sms.channel == "SMS"


async def test_10_delivery_status_transitions():
    """Category 10: Lifecycle progression across PENDING -> QUEUED -> SENT -> DELIVERED -> READ."""
    db = FakeCommunicationSession()
    provider_reg = ProviderRegistry()
    provider_reg.register(WhatsAppProvider())

    service = CommunicationService(provider_registry=provider_reg)
    log = await service.send(
        db=db,
        tenant_id=uuid.uuid4(),
        recipient="+919876543210",
        template_id="ORDER_LOADED",
        context={"order_number": "107", "truck_id": "TRK-05"},
        idempotency_key="life-1",
    )
    assert log.status == "SENT"

    updated = await service.update_delivery_status(db, log.id, "DELIVERED")
    assert updated is not None
    assert updated.status == "DELIVERED"

    updated_read = await service.update_delivery_status(db, log.id, "READ")
    assert updated_read is not None
    assert updated_read.status == "READ"


async def test_11_provider_failure_with_fallback():
    """Category 11: Primary WHATSAPP fails -> automatically falls back to SMS."""
    db = FakeCommunicationSession()
    provider_reg = ProviderRegistry()
    wa_failing = WhatsAppProvider(fail_simulation=True, error_msg="Meta Cloud API Outage")
    sms_working = SMSProvider()
    provider_reg.register(wa_failing)
    provider_reg.register(sms_working)

    service = CommunicationService(provider_registry=provider_reg)
    ctx = {"order_number": "108", "quantity_kg": "75.00", "unit_price": "160.00", "total_amount": "12000.00"}

    log = await service.send(
        db=db,
        tenant_id=uuid.uuid4(),
        recipient="+919876543210",
        template_id="ORDER_CONFIRMED",
        context=ctx,
        idempotency_key="fallback-1",
        channel="WHATSAPP",
        fallback_channels=["SMS"],
    )

    assert len(wa_failing.sent_messages) == 0
    assert len(sms_working.sent_messages) == 1
    assert log.channel == "SMS"
    assert log.status == "SENT"


async def test_12_layer_3_consumer_integration():
    """Category 12: Layer 3 Consumer (OrderConfirmedCommunicationConsumer) integration."""
    db = FakeCommunicationSession()
    factory = FakeSessionFactory(db)
    provider_reg = ProviderRegistry()
    wa = WhatsAppProvider()
    provider_reg.register(wa)

    service = CommunicationService(provider_registry=provider_reg)
    consumer = OrderConfirmedCommunicationConsumer(comm_service=service, session_factory=factory)

    event = IntegrationEvent(
        event_id=uuid.uuid4(),
        event_type="OrderConfirmedIntegrationEvent",
        aggregate_type="Order",
        aggregate_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        occurred_at=datetime.now(timezone.utc),
        payload={
            "order_number": "ORD-505",
            "quantity_kg": "200.00",
            "unit_price": "170.00",
            "total_amount": "34000.00",
            "retailer_phone": "+919988776655",
        },
    )

    await consumer.handle(event)

    assert len(wa.sent_messages) == 1
    assert "ORD-505" in wa.sent_messages[0]["content"]
    assert "34000.00" in wa.sent_messages[0]["content"]
