"""PR 10 Layer 3 Quote Consumers — Quote-to-Order Conversion & Analytics Integration."""

import logging
from typing import Callable, AsyncContextManager
from sqlalchemy.ext.asyncio import AsyncSession

from core.outbox_worker import EventHandler, IntegrationEvent
from core.order_service import OrderService

logger = logging.getLogger("gochicken.quote_consumers")


class QuoteConvertedOrderConsumer(EventHandler):
    """Consumer that converts QuoteConvertedIntegrationEvent into a confirmed Order."""

    def __init__(self, order_service: OrderService, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.order_service = order_service
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        if event.event_type != "QuoteConvertedIntegrationEvent":
            return

        payload = event.payload
        async with self.session_factory() as db:
            # Create order from converted quote snapshot
            await self.order_service.create_order(
                db=db,
                tenant_id=event.tenant_id,
                order_number=f"ORD-QT-{payload.get('quote_number')}",
                customer_id=payload.get("customer_id"),
                items=payload.get("items", []),
                commit=True,
            )
