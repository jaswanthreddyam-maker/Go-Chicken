"""PR 9 Core Analytics Projections Service & Deterministic Rebuilder Engine."""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.analytics import (
    OperationalDailyKPI,
    FinancialDailyKPI,
    CommunicationDailyKPI,
    ProjectionMetadata,
    AnalyticsEventProcessed,
)

logger = logging.getLogger("gochicken.analytics_service")


class AnalyticsService:
    """Enterprise CQRS read model engine for operational, financial, and communication projections."""

    @staticmethod
    def _assert_decimal(value: Any) -> Decimal:
        if isinstance(value, float):
            raise TypeError("Financial or volumetric calculations must never use float. Use Decimal or str.")
        return Decimal(str(value))

    async def get_or_create_metadata(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        projection_name: str,
        projection_version: str = "v1",
    ) -> ProjectionMetadata:
        stmt = select(ProjectionMetadata).where(
            ProjectionMetadata.tenant_id == tenant_id,
            ProjectionMetadata.projection_name == projection_name,
            ProjectionMetadata.projection_version == projection_version,
        )
        res = await db.execute(stmt)
        meta = res.scalars().first()
        if not meta:
            meta = ProjectionMetadata(
                tenant_id=tenant_id,
                projection_name=projection_name,
                projection_version=projection_version,
            )
            db.add(meta)
        return meta

    async def get_or_create_operational(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_date: date,
        projection_version: str = "v1",
    ) -> OperationalDailyKPI:
        stmt = select(OperationalDailyKPI).where(
            OperationalDailyKPI.tenant_id == tenant_id,
            OperationalDailyKPI.metric_date == metric_date,
            OperationalDailyKPI.projection_version == projection_version,
        )
        res = await db.execute(stmt)
        row = res.scalars().first()
        if not row:
            row = OperationalDailyKPI(
                tenant_id=tenant_id,
                metric_date=metric_date,
                projection_version=projection_version,
                total_orders_placed=0,
                orders_confirmed=0,
                orders_delivered=0,
                total_volume_kg=Decimal("0.00"),
            )
            db.add(row)
        return row

    async def get_or_create_financial(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_date: date,
        projection_version: str = "v1",
    ) -> FinancialDailyKPI:
        stmt = select(FinancialDailyKPI).where(
            FinancialDailyKPI.tenant_id == tenant_id,
            FinancialDailyKPI.metric_date == metric_date,
            FinancialDailyKPI.projection_version == projection_version,
        )
        res = await db.execute(stmt)
        row = res.scalars().first()
        if not row:
            row = FinancialDailyKPI(
                tenant_id=tenant_id,
                metric_date=metric_date,
                projection_version=projection_version,
                invoices_issued_total=Decimal("0.00"),
                payments_collected_total=Decimal("0.00"),
                outstanding_receivable_net=Decimal("0.00"),
            )
            db.add(row)
        return row

    async def get_or_create_communication(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_date: date,
        projection_version: str = "v1",
    ) -> CommunicationDailyKPI:
        stmt = select(CommunicationDailyKPI).where(
            CommunicationDailyKPI.tenant_id == tenant_id,
            CommunicationDailyKPI.metric_date == metric_date,
            CommunicationDailyKPI.projection_version == projection_version,
        )
        res = await db.execute(stmt)
        row = res.scalars().first()
        if not row:
            row = CommunicationDailyKPI(
                tenant_id=tenant_id,
                metric_date=metric_date,
                projection_version=projection_version,
                messages_dispatched=0,
                messages_delivered=0,
                messages_failed=0,
            )
            db.add(row)
        return row

    async def is_event_processed(self, db: AsyncSession, tenant_id: UUID, event_id: str) -> bool:
        stmt = select(AnalyticsEventProcessed).where(
            AnalyticsEventProcessed.tenant_id == tenant_id,
            AnalyticsEventProcessed.event_id == event_id,
        )
        res = await db.execute(stmt)
        return res.scalars().first() is not None

    async def record_event(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        event_id: str,
        event_type: str,
        metric_date: date,
        payload: Dict[str, Any],
        projection_version: str = "v1",
        commit: bool = False,
    ) -> bool:
        """Process event idempotently and update analytical read models."""
        if await self.is_event_processed(db, tenant_id, event_id):
            logger.info(f"[ANALYTICS IDEMPOTENT] Duplicate event {event_id} ignored.")
            return False

        now = datetime.now(timezone.utc)
        processed = AnalyticsEventProcessed(
            tenant_id=tenant_id,
            event_id=event_id,
            event_type=event_type,
            processed_at=now,
        )
        db.add(processed)

        # 1. Operational Events
        if event_type in ("OrderConfirmedIntegrationEvent", "OrderConfirmed"):
            oper = await self.get_or_create_operational(db, tenant_id, metric_date, projection_version)
            oper.total_orders_placed += 1
            oper.orders_confirmed += 1
            qty = self._assert_decimal(payload.get("quantity_kg", "0.00"))
            oper.total_volume_kg += qty
            oper.updated_at = now

            meta = await self.get_or_create_metadata(db, tenant_id, "OPERATIONAL_DAILY_KPI", projection_version)
            meta.last_processed_event_id = event_id
            meta.last_processed_at = now

        elif event_type in ("OrderDeliveredIntegrationEvent", "OrderDelivered"):
            oper = await self.get_or_create_operational(db, tenant_id, metric_date, projection_version)
            oper.orders_delivered += 1
            oper.updated_at = now

            meta = await self.get_or_create_metadata(db, tenant_id, "OPERATIONAL_DAILY_KPI", projection_version)
            meta.last_processed_event_id = event_id
            meta.last_processed_at = now

        # 2. Financial Events
        elif event_type in ("OrderInvoiceGenerated", "OrderInvoiceGeneratedIntegrationEvent", "InvoiceGenerated"):
            fin = await self.get_or_create_financial(db, tenant_id, metric_date, projection_version)
            amt = self._assert_decimal(payload.get("total_amount", "0.00"))
            fin.invoices_issued_total += amt
            fin.outstanding_receivable_net += amt
            fin.updated_at = now

            meta = await self.get_or_create_metadata(db, tenant_id, "FINANCIAL_DAILY_KPI", projection_version)
            meta.last_processed_event_id = event_id
            meta.last_processed_at = now

        elif event_type in ("PaymentReceivedIntegrationEvent", "PaymentReceived"):
            fin = await self.get_or_create_financial(db, tenant_id, metric_date, projection_version)
            amt = self._assert_decimal(payload.get("payment_amount", "0.00"))
            fin.payments_collected_total += amt
            fin.outstanding_receivable_net -= amt
            fin.updated_at = now

            meta = await self.get_or_create_metadata(db, tenant_id, "FINANCIAL_DAILY_KPI", projection_version)
            meta.last_processed_event_id = event_id
            meta.last_processed_at = now

        # 3. Communication Events
        elif event_type in ("CommunicationDispatched", "CommunicationDelivered", "CommunicationFailed"):
            comm = await self.get_or_create_communication(db, tenant_id, metric_date, projection_version)
            status = payload.get("status", "SENT").upper()
            comm.messages_dispatched += 1
            if status in ("DELIVERED", "READ"):
                comm.messages_delivered += 1
            elif status in ("FAILED", "FAILED_PERMANENT"):
                comm.messages_failed += 1
            comm.updated_at = now

            meta = await self.get_or_create_metadata(db, tenant_id, "COMMUNICATION_DAILY_KPI", projection_version)
            meta.last_processed_event_id = event_id
            meta.last_processed_at = now

        if commit:
            await db.commit()

        return True


class AnalyticsRebuilder:
    """Deterministic rebuilder engine capable of wiping and reconstructing projections from historical events."""

    def __init__(self, analytics_service: AnalyticsService) -> None:
        self.analytics_service = analytics_service

    async def rebuild_tenant(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        events: List[Dict[str, Any]],
        projection_version: str = "v1",
        commit: bool = False,
    ) -> Dict[str, Any]:
        """Wipe existing projections for tenant and reconstruct deterministically chronologically sorted by occurred_at."""
        now = datetime.now(timezone.utc)

        # 1. Wipe existing projections and idempotency index for tenant
        await db.execute(
            delete(OperationalDailyKPI).where(
                OperationalDailyKPI.tenant_id == tenant_id,
                OperationalDailyKPI.projection_version == projection_version,
            )
        )
        await db.execute(
            delete(FinancialDailyKPI).where(
                FinancialDailyKPI.tenant_id == tenant_id,
                FinancialDailyKPI.projection_version == projection_version,
            )
        )
        await db.execute(
            delete(CommunicationDailyKPI).where(
                CommunicationDailyKPI.tenant_id == tenant_id,
                CommunicationDailyKPI.projection_version == projection_version,
            )
        )
        await db.execute(
            delete(AnalyticsEventProcessed).where(AnalyticsEventProcessed.tenant_id == tenant_id)
        )

        # 2. Record start metadata
        for name in ("OPERATIONAL_DAILY_KPI", "FINANCIAL_DAILY_KPI", "COMMUNICATION_DAILY_KPI"):
            meta = await self.analytics_service.get_or_create_metadata(db, tenant_id, name, projection_version)
            meta.rebuild_started_at = now

        # 3. Chronological sort of historical events by occurred_at ASC
        sorted_events = sorted(
            events,
            key=lambda e: e.get("occurred_at") or datetime.min.replace(tzinfo=timezone.utc),
        )

        processed_count = 0
        for evt in sorted_events:
            success = await self.analytics_service.record_event(
                db=db,
                tenant_id=tenant_id,
                event_id=str(evt["event_id"]),
                event_type=evt["event_type"],
                metric_date=evt["metric_date"],
                payload=evt.get("payload", {}),
                projection_version=projection_version,
            )
            if success:
                processed_count += 1

        end_now = datetime.now(timezone.utc)
        for name in ("OPERATIONAL_DAILY_KPI", "FINANCIAL_DAILY_KPI", "COMMUNICATION_DAILY_KPI"):
            meta = await self.analytics_service.get_or_create_metadata(db, tenant_id, name, projection_version)
            meta.rebuild_completed_at = end_now

        if commit:
            await db.commit()

        return {
            "tenant_id": str(tenant_id),
            "projection_version": projection_version,
            "events_processed": processed_count,
            "rebuild_started_at": now.isoformat(),
            "rebuild_completed_at": end_now.isoformat(),
        }
