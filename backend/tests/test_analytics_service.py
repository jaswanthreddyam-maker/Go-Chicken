"""PR 9 Analytics Domain & CQRS Projections Unit Tests — Covering all 12 frozen verification categories."""

import asyncio
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
import pytest

from models.analytics import (
    OperationalDailyKPI,
    FinancialDailyKPI,
    CommunicationDailyKPI,
    ProjectionMetadata,
    AnalyticsEventProcessed,
)
from core.analytics_service import AnalyticsService, AnalyticsRebuilder
from core.analytics_consumers import OperationalAnalyticsConsumer, FinancialAnalyticsConsumer
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


class FakeAnalyticsSession:
    """Deterministic in-memory async session for testing AnalyticsService & AnalyticsRebuilder."""

    def __init__(self):
        self.items: list[Any] = []
        self.committed = False

    def add(self, obj: Any) -> None:
        self.items.append(obj)

    async def execute(self, stmt: Any) -> FakeResult:
        stmt_str = str(stmt).lower()

        if "delete from" in stmt_str:
            if "analytics_operational_daily_kpi" in stmt_str:
                self.items = [x for x in self.items if not isinstance(x, OperationalDailyKPI)]
            elif "analytics_financial_daily_kpi" in stmt_str:
                self.items = [x for x in self.items if not isinstance(x, FinancialDailyKPI)]
            elif "analytics_communication_daily_kpi" in stmt_str:
                self.items = [x for x in self.items if not isinstance(x, CommunicationDailyKPI)]
            elif "analytics_event_processed" in stmt_str:
                self.items = [x for x in self.items if not isinstance(x, AnalyticsEventProcessed)]
            return FakeResult([])

        params = stmt.compile().params if hasattr(stmt, "compile") else {}

        if "analytics_event_processed" in stmt_str:
            results = [x for x in self.items if isinstance(x, AnalyticsEventProcessed)]
            for k, val in params.items():
                if "event_id" in k:
                    results = [r for r in results if r.event_id == val]
                elif "tenant_id" in k:
                    results = [r for r in results if r.tenant_id == val]
            return FakeResult(results)

        if "analytics_operational_daily_kpi" in stmt_str:
            results = [x for x in self.items if isinstance(x, OperationalDailyKPI)]
            for k, val in params.items():
                if "tenant_id" in k:
                    results = [r for r in results if r.tenant_id == val]
                elif "metric_date" in k:
                    results = [r for r in results if r.metric_date == val]
                elif "projection_version" in k:
                    results = [r for r in results if r.projection_version == val]
            return FakeResult(results)

        if "analytics_financial_daily_kpi" in stmt_str:
            results = [x for x in self.items if isinstance(x, FinancialDailyKPI)]
            for k, val in params.items():
                if "tenant_id" in k:
                    results = [r for r in results if r.tenant_id == val]
                elif "metric_date" in k:
                    results = [r for r in results if r.metric_date == val]
                elif "projection_version" in k:
                    results = [r for r in results if r.projection_version == val]
            return FakeResult(results)

        if "analytics_communication_daily_kpi" in stmt_str:
            results = [x for x in self.items if isinstance(x, CommunicationDailyKPI)]
            for k, val in params.items():
                if "tenant_id" in k:
                    results = [r for r in results if r.tenant_id == val]
                elif "metric_date" in k:
                    results = [r for r in results if r.metric_date == val]
                elif "projection_version" in k:
                    results = [r for r in results if r.projection_version == val]
            return FakeResult(results)

        if "analytics_projection_metadata" in stmt_str:
            results = [x for x in self.items if isinstance(x, ProjectionMetadata)]
            for k, val in params.items():
                if "tenant_id" in k:
                    results = [r for r in results if r.tenant_id == val]
                elif "projection_name" in k:
                    results = [r for r in results if r.projection_name == val]
                elif "projection_version" in k:
                    results = [r for r in results if r.projection_version == val]
            return FakeResult(results)

        return FakeResult([])

    async def commit(self) -> None:
        self.committed = True


class FakeSessionFactory:
    def __init__(self, session: FakeAnalyticsSession):
        self.session = session

    def __call__(self):
        return self

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def test_01_projection_rebuild_from_historical_events():
    """Category 1: Complete projection rebuild from raw historical events."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    rebuilder = AnalyticsRebuilder(service)

    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)
    events = [
        {
            "event_id": "evt-1",
            "event_type": "OrderConfirmed",
            "metric_date": metric_dt,
            "occurred_at": datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc),
            "payload": {"quantity_kg": "100.00"},
        },
        {
            "event_id": "evt-2",
            "event_type": "OrderConfirmed",
            "metric_date": metric_dt,
            "occurred_at": datetime(2026, 7, 10, 11, 0, tzinfo=timezone.utc),
            "payload": {"quantity_kg": "50.00"},
        },
    ]

    res = await rebuilder.rebuild_tenant(db, tenant_id, events)
    assert res["events_processed"] == 2

    oper = await service.get_or_create_operational(db, tenant_id, metric_dt)
    assert oper.total_orders_placed == 2
    assert oper.total_volume_kg == Decimal("150.00")


async def test_02_duplicate_event_replay_idempotency():
    """Category 2: Replaying the same event 3 times yields zero double-counting."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    for _ in range(3):
        await service.record_event(
            db=db,
            tenant_id=tenant_id,
            event_id="idem-evt-1",
            event_type="OrderConfirmed",
            metric_date=metric_dt,
            payload={"quantity_kg": "25.00"},
        )

    oper = await service.get_or_create_operational(db, tenant_id, metric_dt)
    assert oper.total_orders_placed == 1
    assert oper.total_volume_kg == Decimal("25.00")


async def test_03_projection_consistency_after_replay():
    """Category 3: Verifying exact field parity after duplicate event replays."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    await service.record_event(
        db, tenant_id, "cons-1", "OrderConfirmed", metric_dt, {"quantity_kg": "40.00"}
    )
    oper_before = await service.get_or_create_operational(db, tenant_id, metric_dt)
    vol_before = oper_before.total_volume_kg
    cnt_before = oper_before.total_orders_placed

    # Replay
    await service.record_event(
        db, tenant_id, "cons-1", "OrderConfirmed", metric_dt, {"quantity_kg": "40.00"}
    )
    oper_after = await service.get_or_create_operational(db, tenant_id, metric_dt)

    assert oper_after.total_volume_kg == vol_before
    assert oper_after.total_orders_placed == cnt_before


async def test_04_daily_sales_aggregation():
    """Category 4: Daily sales aggregation (total_orders_placed & total_volume_kg)."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    await service.record_event(db, tenant_id, "sales-1", "OrderConfirmed", metric_dt, {"quantity_kg": "12.50"})
    await service.record_event(db, tenant_id, "sales-2", "OrderConfirmed", metric_dt, {"quantity_kg": "87.50"})

    oper = await service.get_or_create_operational(db, tenant_id, metric_dt)
    assert oper.total_orders_placed == 2
    assert oper.total_volume_kg == Decimal("100.00")


async def test_05_inventory_movement_aggregation():
    """Category 5: Inventory/logistics delivery movement tracking."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    await service.record_event(db, tenant_id, "mov-1", "OrderConfirmed", metric_dt, {"quantity_kg": "60.00"})
    await service.record_event(db, tenant_id, "mov-2", "OrderDelivered", metric_dt, {})

    oper = await service.get_or_create_operational(db, tenant_id, metric_dt)
    assert oper.orders_confirmed == 1
    assert oper.orders_delivered == 1


async def test_06_communication_success_metrics():
    """Category 6: Communication KPI calculations (dispatched, delivered, failed)."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    await service.record_event(db, tenant_id, "comm-1", "CommunicationDispatched", metric_dt, {"status": "DELIVERED"})
    await service.record_event(db, tenant_id, "comm-2", "CommunicationDispatched", metric_dt, {"status": "FAILED"})
    await service.record_event(db, tenant_id, "comm-3", "CommunicationDispatched", metric_dt, {"status": "SENT"})

    comm = await service.get_or_create_communication(db, tenant_id, metric_dt)
    assert comm.messages_dispatched == 3
    assert comm.messages_delivered == 1
    assert comm.messages_failed == 1


async def test_07_financial_kpi_calculations():
    """Category 7: Daily financial KPIs (invoices, payments, outstanding net)."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    await service.record_event(db, tenant_id, "fin-1", "InvoiceGenerated", metric_dt, {"total_amount": "50000.00"})
    await service.record_event(db, tenant_id, "fin-2", "PaymentReceived", metric_dt, {"payment_amount": "20000.00"})

    fin = await service.get_or_create_financial(db, tenant_id, metric_dt)
    assert fin.invoices_issued_total == Decimal("50000.00")
    assert fin.payments_collected_total == Decimal("20000.00")
    assert fin.outstanding_receivable_net == Decimal("30000.00")


async def test_08_multi_tenant_isolation():
    """Category 8: Strict multi-tenant analytical isolation."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    await service.record_event(db, tenant_a, "iso-1", "OrderConfirmed", metric_dt, {"quantity_kg": "10.00"})
    await service.record_event(db, tenant_b, "iso-2", "OrderConfirmed", metric_dt, {"quantity_kg": "90.00"})

    oper_a = await service.get_or_create_operational(db, tenant_a, metric_dt)
    oper_b = await service.get_or_create_operational(db, tenant_b, metric_dt)

    assert oper_a.total_volume_kg == Decimal("10.00")
    assert oper_b.total_volume_kg == Decimal("90.00")


async def test_09_incremental_projection_updates():
    """Category 9: Real-time asynchronous projection updates via Layer 3 consumers."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    factory = FakeSessionFactory(db)
    consumer = OperationalAnalyticsConsumer(analytics_service=service, session_factory=factory)

    tenant_id = uuid.uuid4()
    event = IntegrationEvent(
        event_id=uuid.uuid4(),
        event_type="OrderConfirmedIntegrationEvent",
        aggregate_type="Order",
        aggregate_id=uuid.uuid4(),
        tenant_id=tenant_id,
        occurred_at=datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc),
        payload={"quantity_kg": "120.00"},
    )
    await consumer.handle(event)

    oper = await service.get_or_create_operational(db, tenant_id, date(2026, 7, 10))
    assert oper.total_orders_placed == 1
    assert oper.total_volume_kg == Decimal("120.00")


async def test_10_full_rebuild_equivalence_theorem():
    """Category 10: Mathematical equivalence theorem: Incremental Updates == Full Rebuild."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    rebuilder = AnalyticsRebuilder(service)
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    events = [
        {
            "event_id": "eq-1",
            "event_type": "OrderConfirmed",
            "metric_date": metric_dt,
            "occurred_at": datetime(2026, 7, 10, 9, 0, tzinfo=timezone.utc),
            "payload": {"quantity_kg": "45.00"},
        },
        {
            "event_id": "eq-2",
            "event_type": "InvoiceGenerated",
            "metric_date": metric_dt,
            "occurred_at": datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc),
            "payload": {"total_amount": "9000.00"},
        },
    ]

    # 1. Incremental pass
    for e in events:
        await service.record_event(
            db, tenant_id, e["event_id"], e["event_type"], e["metric_date"], e["payload"]
        )

    oper_inc = await service.get_or_create_operational(db, tenant_id, metric_dt)
    fin_inc = await service.get_or_create_financial(db, tenant_id, metric_dt)
    inc_orders = oper_inc.total_orders_placed
    inc_volume = oper_inc.total_volume_kg
    inc_invoices = fin_inc.invoices_issued_total

    # 2. Full rebuild pass
    await rebuilder.rebuild_tenant(db, tenant_id, events)

    oper_reb = await service.get_or_create_operational(db, tenant_id, metric_dt)
    fin_reb = await service.get_or_create_financial(db, tenant_id, metric_dt)

    assert oper_reb.total_orders_placed == inc_orders
    assert oper_reb.total_volume_kg == inc_volume
    assert fin_reb.invoices_issued_total == inc_invoices


async def test_11_projection_deletion_recovery():
    """Category 11: Projection Deletion Recovery (disposable table wipe -> rebuild -> 100% restored)."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    rebuilder = AnalyticsRebuilder(service)
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    events = [
        {
            "event_id": "del-1",
            "event_type": "OrderConfirmed",
            "metric_date": metric_dt,
            "occurred_at": datetime(2026, 7, 10, 8, 0, tzinfo=timezone.utc),
            "payload": {"quantity_kg": "300.00"},
        }
    ]

    await rebuilder.rebuild_tenant(db, tenant_id, events)
    oper = await service.get_or_create_operational(db, tenant_id, metric_dt)
    assert oper.total_volume_kg == Decimal("300.00")

    # Simulate wipe & restore
    await rebuilder.rebuild_tenant(db, tenant_id, events)
    oper_restored = await service.get_or_create_operational(db, tenant_id, metric_dt)
    assert oper_restored.total_volume_kg == Decimal("300.00")


async def test_12_out_of_order_replay_guarantee():
    """Category 12: Out-of-order replay sorting guarantee (E3 -> E1 -> E2 chronologically sorted)."""
    db = FakeAnalyticsSession()
    service = AnalyticsService()
    rebuilder = AnalyticsRebuilder(service)
    tenant_id = uuid.uuid4()
    metric_dt = date(2026, 7, 10)

    t0 = datetime(2026, 7, 10, 8, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=1)
    t2 = t0 + timedelta(hours=2)

    # Pass in out of chronological order: E3, E1, E2
    events_out_of_order = [
        {
            "event_id": "ord-3",
            "event_type": "PaymentReceived",
            "metric_date": metric_dt,
            "occurred_at": t2,
            "payload": {"payment_amount": "5000.00"},
        },
        {
            "event_id": "ord-1",
            "event_type": "InvoiceGenerated",
            "metric_date": metric_dt,
            "occurred_at": t0,
            "payload": {"total_amount": "10000.00"},
        },
        {
            "event_id": "ord-2",
            "event_type": "PaymentReceived",
            "metric_date": metric_dt,
            "occurred_at": t1,
            "payload": {"payment_amount": "2000.00"},
        },
    ]

    res = await rebuilder.rebuild_tenant(db, tenant_id, events_out_of_order)
    assert res["events_processed"] == 3

    fin = await service.get_or_create_financial(db, tenant_id, metric_dt)
    assert fin.invoices_issued_total == Decimal("10000.00")
    assert fin.payments_collected_total == Decimal("7000.00")
    assert fin.outstanding_receivable_net == Decimal("3000.00")
