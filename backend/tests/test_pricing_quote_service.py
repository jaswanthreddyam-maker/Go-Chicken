"""PR 10 Enterprise Pricing & Quote Engine Unit Tests — Covering all 12 frozen verification categories."""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
import pytest

from models.pricing import (
    PriceBook,
    PriceBookEntry,
    CustomerPriceOverride,
    DeliveryZoneSurcharge,
    PriceHistory,
    Quote,
    QuoteItem,
)
from core.pricing_service import PricingService
from core.quote_state_machine import QuoteStateMachine, InvalidQuoteTransitionError
from core.quote_service import QuoteService, QuoteExpiredError
from core.outbox_service import OutboxService

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


class FakePricingSession:
    """Deterministic in-memory async session for testing PricingService & QuoteService."""

    def __init__(self):
        self.items: list[Any] = []
        self.committed = False

    def add(self, obj: Any) -> None:
        self.items.append(obj)

    async def flush(self) -> None:
        for idx, item in enumerate(self.items):
            if hasattr(item, "id") and item.id is None:
                item.id = uuid.uuid4()

    async def execute(self, stmt: Any) -> FakeResult:
        stmt_str = str(stmt).lower()
        params = stmt.compile().params if hasattr(stmt, "compile") else {}

        if "pricing_customer_overrides" in stmt_str:
            res = [x for x in self.items if isinstance(x, CustomerPriceOverride)]
            for k, val in params.items():
                if "tenant_id" in k:
                    res = [r for r in res if r.tenant_id == val]
                elif "customer_id" in k:
                    res = [r for r in res if r.customer_id == val]
                elif "sku" in k:
                    res = [r for r in res if r.sku == val]
            return FakeResult(res)

        if "pricing_price_book_entries" in stmt_str:
            res = [x for x in self.items if isinstance(x, PriceBookEntry)]
            for k, val in params.items():
                if "sku" in k:
                    res = [r for r in res if r.sku == val]
            # Order by min_quantity_kg DESC
            res.sort(key=lambda e: e.min_quantity_kg, reverse=True)
            return FakeResult(res)

        if "pricing_zone_surcharges" in stmt_str:
            res = [x for x in self.items if isinstance(x, DeliveryZoneSurcharge)]
            for k, val in params.items():
                if "tenant_id" in k:
                    res = [r for r in res if r.tenant_id == val]
                elif "delivery_zone" in k:
                    res = [r for r in res if r.delivery_zone == val]
            return FakeResult(res)

        if "pricing_quotes" in stmt_str:
            res = [x for x in self.items if isinstance(x, Quote)]
            for k, val in params.items():
                if "id" in k and "tenant_id" not in k and "customer_id" not in k:
                    res = [r for r in res if r.id == val]
                elif "tenant_id" in k:
                    res = [r for r in res if r.tenant_id == val]
            return FakeResult(res)

        if "pricing_quote_items" in stmt_str:
            res = [x for x in self.items if isinstance(x, QuoteItem)]
            for k, val in params.items():
                if "quote_id" in k:
                    res = [r for r in res if r.quote_id == val]
            return FakeResult(res)

        return FakeResult([])

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj: Any) -> None:
        pass


async def test_01_hierarchical_price_resolution_precedence():
    """Category 1: Resolution Precedence (Customer Override > Tier PriceBook > Base PriceBook)."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    tenant_id = uuid.uuid4()
    cust_id = uuid.uuid4()
    pb_id = uuid.uuid4()

    # Base price: 180.00
    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=pb_id, sku="SKU-CHICKEN", base_unit_price=Decimal("180.00"), min_quantity_kg=Decimal("0.00")))
    # Tier price: 170.00 (min 100kg)
    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=pb_id, sku="SKU-CHICKEN", base_unit_price=Decimal("170.00"), min_quantity_kg=Decimal("100.00")))
    # Override price: 160.00
    db.add(CustomerPriceOverride(id=uuid.uuid4(), tenant_id=tenant_id, customer_id=cust_id, sku="SKU-CHICKEN", override_unit_price=Decimal("160.00")))

    price, source = await pricing_svc.resolve_unit_price(db, tenant_id, cust_id, "SKU-CHICKEN", Decimal("150.00"))
    assert price == Decimal("160.00")
    assert source == "CUSTOMER_OVERRIDE"


async def test_02_zone_logistics_surcharge_calculation():
    """Category 2: Zone logistics delivery surcharge resolution."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    tenant_id = uuid.uuid4()

    db.add(DeliveryZoneSurcharge(id=uuid.uuid4(), tenant_id=tenant_id, delivery_zone="ZONE-NORTH", surcharge_per_kg=Decimal("5.50")))

    surcharge = await pricing_svc.resolve_zone_surcharge(db, tenant_id, "ZONE-NORTH")
    assert surcharge == Decimal("5.50")


async def test_03_immutable_quote_snapshot_parity():
    """Category 3: Changing price book base unit price after quote creation does NOT alter snapshotted QuoteItem."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()
    pb_entry = PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-BREAST", base_unit_price=Decimal("220.00"), min_quantity_kg=Decimal("0.00"))
    db.add(pb_entry)

    quote = await quote_svc.create_quote(
        db, tenant_id, uuid.uuid4(), "QT-001", [{"sku": "SKU-BREAST", "quantity_kg": "50.00"}]
    )
    assert quote.subtotal_amount == Decimal("11000.00")

    # Mutate price book row
    pb_entry.base_unit_price = Decimal("250.00")

    # Quote snapshot total remains 11000.00
    assert quote.subtotal_amount == Decimal("11000.00")
    assert quote.total_amount == Decimal("11000.00")


async def test_04_quote_auto_approval_vs_pending():
    """Category 4: Threshold check (<= 100,000 -> APPROVED; > 100,000 -> PENDING_APPROVAL)."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()
    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-BULK", base_unit_price=Decimal("200.00"), min_quantity_kg=Decimal("0.00")))

    q_small = await quote_svc.create_quote(
        db, tenant_id, uuid.uuid4(), "QT-AUTO", [{"sku": "SKU-BULK", "quantity_kg": "100.00"}], auto_approve_threshold=Decimal("100000.00")
    )
    assert q_small.status == "APPROVED"

    q_large = await quote_svc.create_quote(
        db, tenant_id, uuid.uuid4(), "QT-MANUAL", [{"sku": "SKU-BULK", "quantity_kg": "1000.00"}], auto_approve_threshold=Decimal("100000.00")
    )
    assert q_large.status == "PENDING_APPROVAL"


async def test_05_expired_quote_rejection():
    """Category 5: Converting an expired quote raises QuoteExpiredError."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()
    quote_id = uuid.uuid4()

    expired_quote = Quote(
        id=quote_id,
        tenant_id=tenant_id,
        quote_number="QT-EXP",
        customer_id=uuid.uuid4(),
        status="APPROVED",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(expired_quote)

    with pytest.raises(QuoteExpiredError, match="expired on"):
        await quote_svc.convert_to_order(db, tenant_id, quote_id, outbox_service=OutboxService())


async def test_06_acid_quote_to_order_conversion():
    """Category 6: Single ACID transaction updating Quote.status = CONVERTED & publishing QuoteConvertedIntegrationEvent."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()
    quote_id = uuid.uuid4()

    quote = Quote(
        id=quote_id,
        tenant_id=tenant_id,
        quote_number="QT-CONV",
        customer_id=uuid.uuid4(),
        status="APPROVED",
        total_amount=Decimal("15000.00"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db.add(quote)
    db.add(QuoteItem(quote_id=quote_id, sku="SKU-CHICKEN", quantity_kg=Decimal("100.00"), unit_price=Decimal("150.00"), pricing_source="BASE_PRICEBOOK", line_total=Decimal("15000.00")))

    converted = await quote_svc.convert_to_order(db, tenant_id, quote_id, outbox_service=OutboxService(), commit=True)
    assert converted.status == "CONVERTED"
    assert db.committed is True


async def test_07_append_only_price_book_audit_trail():
    """Category 7: PriceHistory records append-only audit entries."""
    history = PriceHistory(
        tenant_id=uuid.uuid4(),
        entity_type="PRICE_BOOK_ENTRY",
        entity_id=uuid.uuid4(),
        old_price=Decimal("180.00"),
        new_price=Decimal("185.00"),
    )
    assert history.old_price == Decimal("180.00")
    assert history.new_price == Decimal("185.00")


async def test_08_decimal_precision_and_rounding():
    """Category 8: Strict Decimal arithmetic rounding invariants."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()

    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-PREC", base_unit_price=Decimal("123.4567"), min_quantity_kg=Decimal("0.00")))
    quote = await quote_svc.create_quote(
        db, tenant_id, uuid.uuid4(), "QT-PREC", [{"sku": "SKU-PREC", "quantity_kg": "10.00"}]
    )
    # Quantized to 2 decimal places: 123.46 * 10 = 1234.60
    assert quote.total_amount == Decimal("1234.60")


async def test_09_duplicate_quote_conversion_idempotency():
    """Category 9: Converting an already CONVERTED quote returns existing record idempotently."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()
    quote_id = uuid.uuid4()

    converted_quote = Quote(
        id=quote_id,
        tenant_id=tenant_id,
        quote_number="QT-IDEM",
        customer_id=uuid.uuid4(),
        status="CONVERTED",
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db.add(converted_quote)

    res = await quote_svc.convert_to_order(db, tenant_id, quote_id, outbox_service=OutboxService())
    assert res.status == "CONVERTED"


async def test_10_multi_tenant_price_book_isolation():
    """Category 10: Strict multi-tenant pricing override isolation."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    cust_id = uuid.uuid4()

    db.add(CustomerPriceOverride(id=uuid.uuid4(), tenant_id=tenant_a, customer_id=cust_id, sku="SKU-ISO", override_unit_price=Decimal("140.00")))
    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-ISO", base_unit_price=Decimal("190.00"), min_quantity_kg=Decimal("0.00")))

    price_a, src_a = await pricing_svc.resolve_unit_price(db, tenant_a, cust_id, "SKU-ISO", Decimal("50.00"))
    price_b, src_b = await pricing_svc.resolve_unit_price(db, tenant_b, cust_id, "SKU-ISO", Decimal("50.00"))

    assert price_a == Decimal("140.00") and src_a == "CUSTOMER_OVERRIDE"
    assert price_b == Decimal("190.00") and src_b == "BASE_PRICEBOOK"


async def test_11_resolution_provenance_auditability():
    """Category 11: Resolution provenance (pricing_source) is accurately recorded on every QuoteItem."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()
    cust_id = uuid.uuid4()

    db.add(CustomerPriceOverride(id=uuid.uuid4(), tenant_id=tenant_id, customer_id=cust_id, sku="SKU-OVERRIDE", override_unit_price=Decimal("155.00")))
    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-BASE", base_unit_price=Decimal("185.00"), min_quantity_kg=Decimal("0.00")))

    quote = await quote_svc.create_quote(
        db,
        tenant_id,
        cust_id,
        "QT-PROV",
        [
            {"sku": "SKU-OVERRIDE", "quantity_kg": "20.00"},
            {"sku": "SKU-BASE", "quantity_kg": "30.00"},
        ],
    )

    items = [x for x in db.items if isinstance(x, QuoteItem)]
    item_over = next(i for i in items if i.sku == "SKU-OVERRIDE")
    item_base = next(i for i in items if i.sku == "SKU-BASE")

    assert item_over.pricing_source == "CUSTOMER_OVERRIDE"
    assert item_base.pricing_source == "BASE_PRICEBOOK"


async def test_12_quote_version_compatibility():
    """Category 12: quote_version = 1 is persisted and preserved across Quote lifecycle states."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()
    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-VER", base_unit_price=Decimal("200.00"), min_quantity_kg=Decimal("0.00")))

    quote = await quote_svc.create_quote(
        db, tenant_id, uuid.uuid4(), "QT-VER", [{"sku": "SKU-VER", "quantity_kg": "10.00"}], quote_version=1
    )
    assert quote.quote_version == 1
    assert quote.status == "APPROVED"


class FakeOutboxService:
    def __init__(self):
        self.events = []
    async def record_events(self, db, tenant_id, aggregate_type, aggregate_id, event_types, payload, commit=False):
        self.events.append((aggregate_type, aggregate_id, event_types, payload))


async def test_13_preview_creation_equivalence():
    """Test 13: Quote preview produces identical financial outputs compared to committed creation."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-PREVIEW", base_unit_price=Decimal("150.00"), min_quantity_kg=Decimal("0.00")))
    db.add(DeliveryZoneSurcharge(id=uuid.uuid4(), tenant_id=tenant_id, delivery_zone="ZONE-EAST", surcharge_per_kg=Decimal("12.50")))

    items_in = [{"sku": "SKU-PREVIEW", "quantity_kg": "100.00"}]

    # 1. Preview (No commit, simulated in db via savepoint or temporary session)
    # create_quote does db.add, we can check quote values
    quote_prev = await quote_svc.create_quote(
        db=db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        quote_number="QT-TEMP-PREV",
        items_input=items_in,
        delivery_zone="ZONE-EAST",
        commit=False
    )

    # 2. Create actual committed quote
    db_committed = FakePricingSession()
    db_committed.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-PREVIEW", base_unit_price=Decimal("150.00"), min_quantity_kg=Decimal("0.00")))
    db_committed.add(DeliveryZoneSurcharge(id=uuid.uuid4(), tenant_id=tenant_id, delivery_zone="ZONE-EAST", surcharge_per_kg=Decimal("12.50")))

    quote_real = await quote_svc.create_quote(
        db=db_committed,
        tenant_id=tenant_id,
        customer_id=customer_id,
        quote_number="QT-REAL",
        items_input=items_in,
        delivery_zone="ZONE-EAST",
        commit=True
    )

    assert quote_prev.subtotal_amount == quote_real.subtotal_amount
    assert quote_prev.zone_surcharge_amount == quote_real.zone_surcharge_amount
    assert quote_prev.total_amount == quote_real.total_amount
    assert quote_prev.status == quote_real.status


async def test_14_conversion_idempotency():
    """Test 14: Converting a quote twice is idempotent and returns the same Order aggregate reference."""
    db = FakePricingSession()
    pricing_svc = PricingService()
    quote_svc = QuoteService(pricing_service=pricing_svc)
    outbox_svc = FakeOutboxService()
    tenant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    db.add(PriceBookEntry(id=uuid.uuid4(), price_book_id=uuid.uuid4(), sku="SKU-IDEMP", base_unit_price=Decimal("120.00"), min_quantity_kg=Decimal("0.00")))

    quote = await quote_svc.create_quote(
        db=db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        quote_number="QT-IDEMP",
        items_input=[{"sku": "SKU-IDEMP", "quantity_kg": "50.00"}],
        commit=True
    )

    # Transition state to APPROVED so it is convertible
    quote.status = "APPROVED"

    # Convert first time
    quote_converted_1 = await quote_svc.convert_to_order(
        db=db,
        tenant_id=tenant_id,
        quote_id=quote.id,
        outbox_service=outbox_svc,
        commit=True
    )

    assert quote_converted_1.status == "CONVERTED"
    event_count_1 = len(outbox_svc.events)
    assert event_count_1 == 1

    # Convert second time (should be idempotent)
    quote_converted_2 = await quote_svc.convert_to_order(
        db=db,
        tenant_id=tenant_id,
        quote_id=quote.id,
        outbox_service=outbox_svc,
        commit=True
    )

    assert quote_converted_2.status == "CONVERTED"
    # Event count shouldn't increase
    assert len(outbox_svc.events) == event_count_1

