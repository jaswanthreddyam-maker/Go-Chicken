"""PR 7 Layer 3 Event Consumer — InvoiceGeneratedConsumer."""

import logging
from decimal import Decimal
from uuid import UUID
from typing import Callable, AsyncContextManager
from sqlalchemy.ext.asyncio import AsyncSession

from core.outbox_worker import EventHandler, IntegrationEvent
from core.khata_service import KhataService

logger = logging.getLogger("gochicken.khata_consumer")


class InvoiceGeneratedConsumer(EventHandler):
    """Layer 3 outbox event consumer translating OrderInvoiceGenerated events into Khata ledger postings."""

    def __init__(self, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        """Handle an outbox integration event and post to financial ledger."""
        if event.event_type != "OrderInvoiceGenerated":
            logger.warning(f"[KHATA CONSUMER] Unexpected event type {event.event_type} ignored.")
            return

        payload = event.payload
        customer_id = UUID(payload["customer_id"])
        invoice_id = UUID(payload["order_id"])
        amount = Decimal(str(payload["total_amount"]))
        idempotency_key = str(event.event_id)

        async with self.session_factory() as db:
            logger.info(f"[KHATA CONSUMER] Posting invoice {invoice_id} for customer {customer_id} amount ₹{amount}")
            await KhataService.post_invoice(
                db=db,
                tenant_id=event.tenant_id,
                customer_id=customer_id,
                invoice_id=invoice_id,
                amount=amount,
                idempotency_key=idempotency_key,
                notes=f"Auto-generated from Order #{payload.get('order_number', invoice_id)}",
                commit=True,
            )
