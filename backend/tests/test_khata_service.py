"""PR 7 Financial Ledger Unit & Integration Tests — Covering all 8 frozen verification categories."""

import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
import pytest

from models.khata import KhataLedger, CustomerBalanceProjection, KhataInvoice
from core.khata_service import KhataService
from core.khata_consumer import InvoiceGeneratedConsumer
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

    def scalar(self):
        return self._list[0] if self._list else None


class FakeKhataSession:
    """Deterministic in-memory async session for testing Khata financial invariants."""

    def __init__(self):
        self.items: list[Any] = []
        self.committed = False

    def add(self, obj: Any) -> None:
        # Enforce UNIQUE(tenant_id, idempotency_key) constraint simulation for KhataLedger
        if isinstance(obj, KhataLedger):
            for existing in self.items:
                if (
                    isinstance(existing, KhataLedger)
                    and existing.tenant_id == obj.tenant_id
                    and existing.idempotency_key == obj.idempotency_key
                ):
                    return
        self.items.append(obj)

    async def execute(self, stmt: Any) -> FakeResult:
        stmt_str = str(stmt).lower()

        # 1. Sum query for rebuild_projection
        if "sum" in stmt_str or "count" in stmt_str:
            ledgers = [
                x.amount for x in self.items
                if isinstance(x, KhataLedger)
            ]
            total = sum(ledgers, Decimal("0.00"))
            return FakeResult([total])

        # 2. Querying KhataLedger
        if "khata_ledger" in stmt_str:
            # Check if filtering by idempotency_key
            results = [x for x in self.items if isinstance(x, KhataLedger)]
            # Match idempotency key if in statement compiled parameters
            params = stmt.compile().params if hasattr(stmt, "compile") else {}
            for k, val in params.items():
                if "idempotency_key" in k:
                    results = [r for r in results if r.idempotency_key == val]
            return FakeResult(results)

        # 3. Querying CustomerBalanceProjection
        if "customer_balance_projection" in stmt_str:
            results = [x for x in self.items if isinstance(x, CustomerBalanceProjection)]
            return FakeResult(results)

        # 4. Querying KhataInvoice
        if "khata_invoice" in stmt_str:
            results = [x for x in self.items if isinstance(x, KhataInvoice)]
            params = stmt.compile().params if hasattr(stmt, "compile") else {}
            for k, val in params.items():
                if "invoice_id" in k and val is not None:
                    results = [r for r in results if r.invoice_id == val]
            # If filtering for unpaid/partially paid
            if "status" in stmt_str:
                results = [r for r in results if r.status != "PAID"]
            results.sort(key=lambda r: r.issued_at)
            return FakeResult(results)

        return FakeResult([])

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj: Any) -> None:
        pass


class FakeSessionFactory:
    def __init__(self, session: FakeKhataSession):
        self.session = session

    def __call__(self):
        return self

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def test_01_partial_payment_accumulation():
    """Category 1: Partial Payment Accumulation (1000 -> 400 -> 300 -> 300 == PAID)."""
    db = FakeKhataSession()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    invoice_id = uuid.uuid4()

    # 1. Post Invoice ₹1000
    await KhataService.post_invoice(db, tenant_id, customer_id, invoice_id, Decimal("1000.00"), "inv-1", commit=True)

    # 2. Partial payment ₹400
    await KhataService.post_payment_fifo(db, tenant_id, customer_id, Decimal("400.00"), "pay-1", commit=True)
    invoices = [i for i in db.items if isinstance(i, KhataInvoice)]
    assert invoices[0].status == "PARTIALLY_PAID"
    assert invoices[0].settled_amount == Decimal("400.00")

    # 3. Partial payment ₹300
    await KhataService.post_payment_fifo(db, tenant_id, customer_id, Decimal("300.00"), "pay-2", commit=True)
    assert invoices[0].status == "PARTIALLY_PAID"
    assert invoices[0].settled_amount == Decimal("700.00")

    # 4. Partial payment ₹300
    await KhataService.post_payment_fifo(db, tenant_id, customer_id, Decimal("300.00"), "pay-3", commit=True)
    assert invoices[0].status == "PAID"
    assert invoices[0].settled_amount == Decimal("1000.00")

    proj = [p for p in db.items if isinstance(p, CustomerBalanceProjection)][0]
    assert proj.outstanding_balance == Decimal("0.00")


async def test_02_overpayment_tracking():
    """Category 2: Overpayment Tracking (1000 -> 1200 == PAID invoice + credit balance -200)."""
    db = FakeKhataSession()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    invoice_id = uuid.uuid4()

    await KhataService.post_invoice(db, tenant_id, customer_id, invoice_id, Decimal("1000.00"), "inv-over-1", commit=True)
    await KhataService.post_payment_fifo(db, tenant_id, customer_id, Decimal("1200.00"), "pay-over-1", commit=True)

    inv = [i for i in db.items if isinstance(i, KhataInvoice)][0]
    assert inv.status == "PAID"
    assert inv.settled_amount == Decimal("1000.00")

    proj = [p for p in db.items if isinstance(p, CustomerBalanceProjection)][0]
    assert proj.outstanding_balance == Decimal("-200.00")


async def test_03_credit_note_application():
    """Category 3: Credit Note Application (Invoice 1000 -> Credit 200 == Outstanding 800)."""
    db = FakeKhataSession()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    invoice_id = uuid.uuid4()

    await KhataService.post_invoice(db, tenant_id, customer_id, invoice_id, Decimal("1000.00"), "inv-cn-1", commit=True)
    await KhataService.post_credit_note(db, tenant_id, customer_id, Decimal("200.00"), "cn-1", str(invoice_id), commit=True)

    proj = [p for p in db.items if isinstance(p, CustomerBalanceProjection)][0]
    assert proj.outstanding_balance == Decimal("800.00")


async def test_04_duplicate_event_idempotency():
    """Category 4: Sequential Duplicate Event Idempotency (replaying 4 times creates exactly 1 ledger row)."""
    db = FakeKhataSession()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    invoice_id = uuid.uuid4()

    for _ in range(4):
        await KhataService.post_invoice(db, tenant_id, customer_id, invoice_id, Decimal("1000.00"), "idem-event-1", commit=True)

    rows = [r for r in db.items if isinstance(r, KhataLedger)]
    assert len(rows) == 1
    assert rows[0].idempotency_key == "idem-event-1"


async def test_05_concurrent_duplicate_event():
    """Category 5: Concurrent Duplicate Event Idempotency (2 workers processing same idempotency_key)."""
    db = FakeKhataSession()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    invoice_id = uuid.uuid4()

    async def worker_attempt():
        await KhataService.post_invoice(db, tenant_id, customer_id, invoice_id, Decimal("1000.00"), "idem-concurrent-1", commit=True)

    await asyncio.gather(worker_attempt(), worker_attempt())

    rows = [r for r in db.items if isinstance(r, KhataLedger)]
    assert len(rows) == 1


async def test_06_multi_invoice_fifo_allocation():
    """Category 6: Multi-Invoice FIFO Allocation (Invoice A: 1000, Invoice B: 2000, Payment: 1500 -> A=PAID, B=PARTIALLY_PAID)."""
    db = FakeKhataSession()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    inv_a = uuid.uuid4()
    inv_b = uuid.uuid4()

    await KhataService.post_invoice(db, tenant_id, customer_id, inv_a, Decimal("1000.00"), "fifo-inv-a", commit=True)
    await KhataService.post_invoice(db, tenant_id, customer_id, inv_b, Decimal("2000.00"), "fifo-inv-b", commit=True)

    await KhataService.post_payment_fifo(db, tenant_id, customer_id, Decimal("1500.00"), "fifo-pay-1", commit=True)

    invoices = [i for i in db.items if isinstance(i, KhataInvoice)]
    invoices.sort(key=lambda i: i.issued_at)

    assert invoices[0].status == "PAID"
    assert invoices[0].settled_amount == Decimal("1000.00")

    assert invoices[1].status == "PARTIALLY_PAID"
    assert invoices[1].settled_amount == Decimal("500.00")

    proj = [p for p in db.items if isinstance(p, CustomerBalanceProjection)][0]
    assert proj.outstanding_balance == Decimal("1500.00")


async def test_07_adjustments_and_reversals():
    """Category 7: Adjustments & Non-Destructive Reversals."""
    db = FakeKhataSession()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    await KhataService.post_debit_note(db, tenant_id, customer_id, Decimal("500.00"), "debit-1", commit=True)
    proj = [p for p in db.items if isinstance(p, CustomerBalanceProjection)][0]
    assert proj.outstanding_balance == Decimal("500.00")

    await KhataService.post_adjustment(db, tenant_id, customer_id, Decimal("-500.00"), "adj-1", notes="Bad debt write-off", commit=True)
    assert proj.outstanding_balance == Decimal("0.00")


async def test_08_projection_rebuild_verification():
    """Category 8: Projection Rebuild Verification (rebuilding from raw KhataLedger rows yields exact parity)."""
    db = FakeKhataSession()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    await KhataService.post_invoice(db, tenant_id, customer_id, uuid.uuid4(), Decimal("5000.00"), "reb-1", commit=True)
    await KhataService.post_payment_fifo(db, tenant_id, customer_id, Decimal("1500.00"), "reb-2", commit=True)
    await KhataService.post_credit_note(db, tenant_id, customer_id, Decimal("250.00"), "reb-3", commit=True)

    proj = [p for p in db.items if isinstance(p, CustomerBalanceProjection)][0]
    assert proj.outstanding_balance == Decimal("3250.00")

    # Simulate cache drift by corrupting projection balance
    proj.outstanding_balance = Decimal("999999.00")

    # Rebuild from immutable ledger
    rebuilt = await KhataService.rebuild_projection(db, tenant_id, customer_id, commit=True)
    assert rebuilt.outstanding_balance == Decimal("3250.00")


async def test_09_layer_3_consumer_integration():
    """Category 9: Layer 3 Event Consumer (InvoiceGeneratedConsumer) integration."""
    db = FakeKhataSession()
    factory = FakeSessionFactory(db)
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    order_id = uuid.uuid4()
    event_id = uuid.uuid4()

    consumer = InvoiceGeneratedConsumer(factory)
    event = IntegrationEvent(
        event_id=event_id,
        event_type="OrderInvoiceGenerated",
        aggregate_type="Order",
        aggregate_id=order_id,
        tenant_id=tenant_id,
        occurred_at=datetime.now(timezone.utc),
        payload={
            "order_id": str(order_id),
            "customer_id": str(customer_id),
            "total_amount": "8500.50",
            "order_number": "ORD-101",
        },
    )

    await consumer.handle(event)

    rows = [r for r in db.items if isinstance(r, KhataLedger)]
    assert len(rows) == 1
    assert rows[0].amount == Decimal("8500.50")
    assert rows[0].entry_type == "INVOICE"


async def test_10_strict_decimal_invariant():
    """Category 10: Strict Decimal Invariant raises TypeError on float."""
    with pytest.raises(TypeError, match="Decimal"):
        KhataService._assert_decimal(100.50)  # type: ignore
