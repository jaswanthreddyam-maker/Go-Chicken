"""PR 6 Outbox Worker Pipeline — Reliable Event Dispatcher & Plug-in Handler Registry."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from core.outbox_service import OutboxService
from models.outbox import IntegrationOutbox

logger = logging.getLogger("gochicken.outbox_worker")


@dataclass(frozen=True)
class IntegrationEvent:
    """Standard transport envelope passed to all consumer handlers."""
    event_id: UUID
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    tenant_id: UUID
    occurred_at: datetime
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None


class EventHandler(ABC):
    """Abstract interface for all outbox event consumers."""

    @abstractmethod
    async def handle(self, event: IntegrationEvent) -> None:
        """Execute domain side effects for the given outbox event envelope."""
        pass


@dataclass(frozen=True)
class ConsumerRegistration:
    """Declares operational capabilities and profile for a registered consumer."""
    event_type: str
    handler: EventHandler
    max_concurrency: int = 4
    timeout_seconds: float = 30.0
    retryable: bool = True


class HandlerRegistry:
    """Dynamic event handler registry decoupling the polling engine from consumers."""

    def __init__(self):
        self._registrations: Dict[str, ConsumerRegistration] = {}

    def register(
        self,
        event_type: str,
        handler: EventHandler,
        max_concurrency: int = 4,
        timeout_seconds: float = 30.0,
        retryable: bool = True,
    ) -> None:
        """Register an event handler for a given event type."""
        self._registrations[event_type] = ConsumerRegistration(
            event_type=event_type,
            handler=handler,
            max_concurrency=max_concurrency,
            timeout_seconds=timeout_seconds,
            retryable=retryable,
        )

    def resolve(self, event_type: str) -> Optional[ConsumerRegistration]:
        """Resolve a consumer registration by event type."""
        return self._registrations.get(event_type)

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._registrations.clear()


@dataclass
class OutboxWorkerMetrics:
    """Tracks real-time queue and worker daemon health metrics."""
    # Queue metrics
    pending_total: int = 0
    processed_total: int = 0
    failed_total: int = 0
    retry_total: int = 0
    dead_letter_total: int = 0
    oldest_pending_seconds: float = 0.0
    processing_duration_seconds: List[float] = field(default_factory=list)

    # Worker daemon metrics
    worker_running: int = 0
    worker_last_poll_timestamp: float = 0.0
    worker_batches_processed_total: int = 0
    worker_active_handlers: int = 0


class OutboxWorker:
    """Autonomous outbox polling daemon with row locking, backoff, and plug-in dispatch."""

    def __init__(
        self,
        registry: HandlerRegistry,
        poll_interval_seconds: float = 2.0,
        batch_size: int = 100,
        shutdown_grace_period_seconds: float = 15.0,
        metrics: Optional[OutboxWorkerMetrics] = None,
    ):
        self.registry = registry
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.shutdown_grace_period_seconds = shutdown_grace_period_seconds
        self.metrics = metrics or OutboxWorkerMetrics()
        self.is_running = False
        self._shutdown_requested = False

    async def start(self, session_factory: Callable[[], AsyncSession]) -> None:
        """Start the outbox polling daemon loop."""
        self.is_running = True
        self.metrics.worker_running = 1
        logger.info("[OUTBOX WORKER] Starting outbox polling daemon.")

        try:
            while not self._shutdown_requested:
                async with session_factory() as db:
                    await self.process_batch(db)
                await asyncio.sleep(self.poll_interval_seconds)
        finally:
            await self.shutdown()

    async def stop(self) -> None:
        """Request graceful shutdown of the worker."""
        logger.info("[OUTBOX WORKER] Shutdown requested. Stopping polling.")
        self._shutdown_requested = True
        self.is_running = False

    async def shutdown(self) -> None:
        """Drain active handlers and clean up worker state."""
        deadline = time.time() + self.shutdown_grace_period_seconds
        while self.metrics.worker_active_handlers > 0 and time.time() < deadline:
            await asyncio.sleep(0.1)
        self.is_running = False
        self.metrics.worker_running = 0
        logger.info("[OUTBOX WORKER] Worker daemon shutdown cleanly.")

    async def process_batch(self, db: AsyncSession) -> int:
        """Poll and dispatch a single batch of pending outbox events with row locking."""
        self.metrics.worker_last_poll_timestamp = time.time()

        events = await OutboxService.get_pending_events(
            db=db,
            limit=self.batch_size,
            for_update=True,
        )

        if not events:
            return 0

        processed_in_batch = 0

        for entry in events:
            envelope = IntegrationEvent(
                event_id=entry.event_id,
                event_type=entry.event_type,
                aggregate_type=entry.aggregate_type,
                aggregate_id=entry.aggregate_id,
                tenant_id=entry.tenant_id,
                occurred_at=entry.created_at,
                payload=entry.payload or {},
                correlation_id=entry.correlation_id,
                causation_id=entry.causation_id,
            )

            registration = self.registry.resolve(entry.event_type)
            if not registration:
                logger.warning(
                    f"[OUTBOX WORKER] No handler registered for event type '{entry.event_type}'. Skipping dispatch."
                )
                continue

            self.metrics.worker_active_handlers += 1
            start_time = time.time()

            try:
                await asyncio.wait_for(
                    registration.handler.handle(envelope),
                    timeout=registration.timeout_seconds,
                )
                duration = time.time() - start_time
                self.metrics.processing_duration_seconds.append(duration)
                self.metrics.processed_total += 1
                await OutboxService.mark_processed(db, entry, commit=True)
                processed_in_batch += 1
            except Exception as exc:
                duration = time.time() - start_time
                self.metrics.failed_total += 1
                await OutboxService.mark_failed(db, entry, error=str(exc), commit=True)

                if entry.status == "FAILED":
                    self.metrics.dead_letter_total += 1
                else:
                    self.metrics.retry_total += 1
            finally:
                self.metrics.worker_active_handlers -= 1

        self.metrics.worker_batches_processed_total += 1
        return processed_in_batch
