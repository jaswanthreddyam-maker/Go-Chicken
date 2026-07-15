"""PR 9 Layer 3 Analytics Event Consumers (Operational, Financial, Communication)."""

import logging
from datetime import date
from typing import Callable, AsyncContextManager
from sqlalchemy.ext.asyncio import AsyncSession

from core.outbox_worker import EventHandler, IntegrationEvent
from core.analytics_service import AnalyticsService

logger = logging.getLogger("gochicken.analytics_consumers")


class OperationalAnalyticsConsumer(EventHandler):
    """Consumer asynchronously populating OperationalDailyKPI projections."""

    def __init__(self, analytics_service: AnalyticsService, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.analytics_service = analytics_service
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        if event.event_type not in ("OrderConfirmedIntegrationEvent", "OrderDeliveredIntegrationEvent"):
            return

        metric_date = event.occurred_at.date() if hasattr(event.occurred_at, "date") else date.today()
        async with self.session_factory() as db:
            await self.analytics_service.record_event(
                db=db,
                tenant_id=event.tenant_id,
                event_id=str(event.event_id),
                event_type=event.event_type,
                metric_date=metric_date,
                payload=event.payload,
                commit=True,
            )


class FinancialAnalyticsConsumer(EventHandler):
    """Consumer asynchronously populating FinancialDailyKPI projections."""

    def __init__(self, analytics_service: AnalyticsService, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.analytics_service = analytics_service
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        if event.event_type not in ("OrderInvoiceGeneratedIntegrationEvent", "PaymentReceivedIntegrationEvent"):
            return

        metric_date = event.occurred_at.date() if hasattr(event.occurred_at, "date") else date.today()
        async with self.session_factory() as db:
            await self.analytics_service.record_event(
                db=db,
                tenant_id=event.tenant_id,
                event_id=str(event.event_id),
                event_type=event.event_type,
                metric_date=metric_date,
                payload=event.payload,
                commit=True,
            )


class CommunicationAnalyticsConsumer(EventHandler):
    """Consumer asynchronously populating CommunicationDailyKPI projections."""

    def __init__(self, analytics_service: AnalyticsService, session_factory: Callable[[], AsyncContextManager[AsyncSession]]):
        self.analytics_service = analytics_service
        self.session_factory = session_factory

    async def handle(self, event: IntegrationEvent) -> None:
        if event.event_type not in ("CommunicationDispatched", "CommunicationDelivered", "CommunicationFailed"):
            return

        metric_date = event.occurred_at.date() if hasattr(event.occurred_at, "date") else date.today()
        async with self.session_factory() as db:
            await self.analytics_service.record_event(
                db=db,
                tenant_id=event.tenant_id,
                event_id=str(event.event_id),
                event_type=event.event_type,
                metric_date=metric_date,
                payload=event.payload,
                commit=True,
            )
