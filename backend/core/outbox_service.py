"""Enterprise OutboxService — Transactional outbox writer and asynchronous event dispatch helper."""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.outbox import IntegrationOutbox

logger = logging.getLogger("go_chicken.outbox_service")


class OutboxService:
    """Manages transactional outbox persistence and worker state transitions."""

    @classmethod
    async def record_events(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        aggregate_type: str,
        aggregate_id: UUID,
        event_types: List[str],
        payload: Dict[str, Any],
        commit: bool = False,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ) -> List[IntegrationOutbox]:
        """Write integration events to the outbox table within the active ACID transaction."""
        outbox_entries: List[IntegrationOutbox] = []
        import uuid
        for evt_type in event_types:
            entry = IntegrationOutbox(
                event_id=uuid.uuid4(),
                tenant_id=tenant_id,
                event_type=evt_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                correlation_id=correlation_id or str(aggregate_id),
                causation_id=causation_id,
                payload=payload or {},
                status="PENDING",
            )
            db.add(entry)
            outbox_entries.append(entry)
            logger.info(
                f"[OUTBOX WRITING] Recorded {evt_type} (event_id={entry.event_id}) for {aggregate_type} {aggregate_id}"
            )

        if commit:
            await db.commit()
            for entry in outbox_entries:
                await db.refresh(entry)

        return outbox_entries

    @classmethod
    async def get_pending_events(
        cls,
        db: AsyncSession,
        limit: int = 50,
        for_update: bool = True,
    ) -> List[IntegrationOutbox]:
        """Fetch pending outbox events ready for asynchronous delivery."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(IntegrationOutbox)
            .where(
                IntegrationOutbox.status == "PENDING",
                IntegrationOutbox.retry_count < IntegrationOutbox.max_retries,
                (IntegrationOutbox.next_retry_at.is_(None)) | (IntegrationOutbox.next_retry_at <= now),
            )
            .order_by(IntegrationOutbox.created_at.asc())
            .limit(limit)
        )
        if for_update:
            stmt = stmt.with_for_update(skip_locked=True)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def mark_processed(
        cls,
        db: AsyncSession,
        event: IntegrationOutbox,
        commit: bool = True,
    ) -> None:
        """Mark an outbox event as successfully delivered."""
        event.status = "PROCESSED"
        event.processed_at = datetime.now(timezone.utc)
        logger.info(f"[OUTBOX PROCESSED] Event {event.id} ({event.event_type}) delivered successfully.")
        if commit:
            await db.commit()

    @classmethod
    async def mark_failed(
        cls,
        db: AsyncSession,
        event: IntegrationOutbox,
        error: str,
        commit: bool = True,
    ) -> None:
        """Increment retry count on failure and calculate exponential backoff next_retry_at."""
        from datetime import timedelta
        event.retry_count += 1
        event.last_error = str(error)[:500]
        if event.retry_count >= event.max_retries:
            event.status = "FAILED"
            event.next_retry_at = None
            logger.error(
                f"[OUTBOX DEAD LETTER] Event {event.id} ({event.event_type}) permanently failed after {event.retry_count} retries: {error}"
            )
        else:
            # Exponential backoff: 30s * 2^(retry_count-1) -> 30s, 60s, 120s, 240s...
            backoff_sec = 30 * (2 ** (event.retry_count - 1))
            event.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_sec)
            logger.warning(
                f"[OUTBOX RETRY] Event {event.id} ({event.event_type}) failed (attempt {event.retry_count}/{event.max_retries}), next retry in {backoff_sec}s: {error}"
            )
        if commit:
            await db.commit()
