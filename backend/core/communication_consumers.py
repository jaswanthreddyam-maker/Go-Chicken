"""PR 8 Layer 3 Communication Event Consumers."""

import logging
from typing import Callable, AsyncContextManager
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from core.outbox_worker import EventHandler, IntegrationEvent
from core.communication_service import CommunicationService

logger = logging.getLogger("gochicken.communication_consumers")


class OrderConfirmedCommunicationConsumer(EventHandler):
    """Dispatches ORDER_CONFIRMED notification upon order confirmation."""

    def __init__(self, comm_service: CommunicationService, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.comm_service = comm_service
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        if event.event_type != "OrderConfirmedIntegrationEvent":
            return
        payload = event.payload
        async with self.session_factory() as db:
            await self.comm_service.send(
                db=db,
                tenant_id=event.tenant_id,
                recipient=payload.get("retailer_phone", "+919999999999"),
                template_id="ORDER_CONFIRMED",
                context=payload,
                idempotency_key=str(event.event_id),
                channel=payload.get("preferred_channel", "WHATSAPP"),
                commit=True,
            )


class OrderLoadedCommunicationConsumer(EventHandler):
    """Dispatches ORDER_LOADED notification upon truck loading."""

    def __init__(self, comm_service: CommunicationService, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.comm_service = comm_service
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        if event.event_type != "OrderLoadedIntegrationEvent":
            return
        payload = event.payload
        async with self.session_factory() as db:
            await self.comm_service.send(
                db=db,
                tenant_id=event.tenant_id,
                recipient=payload.get("retailer_phone", "+919999999999"),
                template_id="ORDER_LOADED",
                context=payload,
                idempotency_key=str(event.event_id),
                commit=True,
            )


class OrderDeliveredCommunicationConsumer(EventHandler):
    """Dispatches ORDER_DELIVERED notification upon delivery completion."""

    def __init__(self, comm_service: CommunicationService, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.comm_service = comm_service
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        if event.event_type != "OrderDeliveredIntegrationEvent":
            return
        payload = event.payload
        async with self.session_factory() as db:
            await self.comm_service.send(
                db=db,
                tenant_id=event.tenant_id,
                recipient=payload.get("retailer_phone", "+919999999999"),
                template_id="ORDER_DELIVERED",
                context=payload,
                idempotency_key=str(event.event_id),
                commit=True,
            )


class InvoiceGeneratedCommunicationConsumer(EventHandler):
    """Dispatches INVOICE_GENERATED notification upon invoice creation."""

    def __init__(self, comm_service: CommunicationService, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.comm_service = comm_service
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        if event.event_type != "OrderInvoiceGenerated":
            return
        payload = event.payload
        async with self.session_factory() as db:
            await self.comm_service.send(
                db=db,
                tenant_id=event.tenant_id,
                recipient=payload.get("retailer_phone", "+919999999999"),
                template_id="INVOICE_GENERATED",
                context=payload,
                idempotency_key=str(event.event_id),
                commit=True,
            )
