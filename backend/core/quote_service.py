"""PR 10 Enterprise Quote Snapshots & Quote-to-Order Conversion Service (ADR-0012)."""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.pricing import Quote, QuoteItem
from core.pricing_service import PricingService
from core.quote_state_machine import QuoteStateMachine, InvalidQuoteTransitionError
from core.outbox_service import OutboxService

logger = logging.getLogger("gochicken.quote_service")


class QuoteExpiredError(Exception):
    """Raised when attempting to convert or accept a quote that has exceeded its validity expiration window."""
    pass


class QuoteService:
    """Orchestrates immutable quote snapshot creation and transactional quote-to-order conversion."""

    def __init__(self, pricing_service: PricingService) -> None:
        self.pricing_service = pricing_service

    @staticmethod
    def _assert_decimal(value: Any) -> Decimal:
        if isinstance(value, float):
            raise TypeError("Financial calculations must never use float. Use Decimal or str.")
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    async def create_quote(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        quote_number: str,
        items_input: List[Dict[str, Any]],
        delivery_zone: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        auto_approve_threshold: Decimal = Decimal("100000.00"),
        quote_version: int = 1,
        commit: bool = False,
    ) -> Quote:
        """Resolve pricing hierarchically and freeze an immutable Quote snapshot."""
        now = datetime.now(timezone.utc)
        if expires_at is None:
            expires_at = now + timedelta(days=7)

        zone_surcharge_per_kg = await self.pricing_service.resolve_zone_surcharge(db, tenant_id, delivery_zone)

        quote_items: List[QuoteItem] = []
        subtotal = Decimal("0.00")
        total_zone_surcharge = Decimal("0.00")

        for item_in in items_input:
            sku = item_in["sku"]
            qty = self._assert_decimal(item_in["quantity_kg"])
            base_price, pricing_source = await self.pricing_service.resolve_unit_price(
                db, tenant_id, customer_id, sku, qty
            )

            final_unit_price = self._assert_decimal(base_price + zone_surcharge_per_kg)
            line_total = self._assert_decimal(qty * final_unit_price)
            line_surcharge = self._assert_decimal(qty * zone_surcharge_per_kg)

            subtotal += self._assert_decimal(qty * base_price)
            total_zone_surcharge += line_surcharge

            q_item = QuoteItem(
                sku=sku,
                quantity_kg=qty,
                unit_price=final_unit_price,
                pricing_source=pricing_source,
                line_total=line_total,
            )
            quote_items.append(q_item)

        total_amount = self._assert_decimal(subtotal + total_zone_surcharge)

        # Threshold-based auto-approval vs manual pending approval
        initial_status = "APPROVED" if total_amount <= auto_approve_threshold else "PENDING_APPROVAL"

        quote = Quote(
            tenant_id=tenant_id,
            quote_number=quote_number,
            quote_version=quote_version,
            customer_id=customer_id,
            delivery_zone=delivery_zone,
            status=initial_status,
            subtotal_amount=subtotal,
            zone_surcharge_amount=total_zone_surcharge,
            total_amount=total_amount,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        db.add(quote)
        await db.flush()

        for qi in quote_items:
            qi.quote_id = quote.id
            db.add(qi)

        if commit:
            await db.commit()
            await db.refresh(quote)

        return quote

    async def convert_to_order(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        quote_id: UUID,
        outbox_service: OutboxService,
        commit: bool = False,
    ) -> Quote:
        """ACID conversion of an APPROVED quote into an order via outbox event."""
        stmt = select(Quote).where(Quote.id == quote_id, Quote.tenant_id == tenant_id)
        res = await db.execute(stmt)
        quote = res.scalars().first()
        if not quote:
            raise KeyError(f"Quote {quote_id} not found")

        # Idempotency check: if already converted, return safely
        if quote.status == "CONVERTED":
            logger.info(f"[QUOTE CONVERSION IDEMPOTENT] Quote {quote_id} already converted.")
            return quote

        now = datetime.now(timezone.utc)
        
        exp = quote.expires_at.replace(tzinfo=timezone.utc) if quote.expires_at.tzinfo is None else quote.expires_at
        if now > exp:
            raise QuoteExpiredError(f"Quote {quote.quote_number} expired on {quote.expires_at}")

        QuoteStateMachine.validate_transition(quote.status, "CONVERTED")
        quote.status = "CONVERTED"
        quote.updated_at = now

        # Query items for outbox event
        stmt_items = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
        res_items = await db.execute(stmt_items)
        items = res_items.scalars().all()

        payload_items = [
            {
                "sku": i.sku,
                "quantity_kg": str(i.quantity_kg),
                "unit_price": str(i.unit_price),
                "pricing_source": i.pricing_source,
                "line_total": str(i.line_total),
            }
            for i in items
        ]

        await outbox_service.record_events(
            db=db,
            tenant_id=tenant_id,
            aggregate_type="Quote",
            aggregate_id=quote.id,
            event_types=["QuoteConvertedIntegrationEvent"],
            payload={
                "quote_id": str(quote.id),
                "quote_number": quote.quote_number,
                "quote_version": quote.quote_version,
                "customer_id": str(quote.customer_id),
                "delivery_zone": quote.delivery_zone,
                "total_amount": str(quote.total_amount),
                "items": payload_items,
            },
        )

        if commit:
            await db.commit()
            await db.refresh(quote)

        return quote
