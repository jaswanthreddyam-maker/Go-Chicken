# ADR 0005: Outbox Worker Polling & Concurrency Control (`FOR UPDATE SKIP LOCKED`)

## Status
Accepted (Frozen)

## Context
Asynchronous outbox dispatch requires a worker daemon capable of scaling horizontally across multiple pods without duplicate event delivery, row lock contention, or head-of-line blocking.

## Decision
We implement `OutboxWorker` (`backend/core/outbox_worker.py`) using PostgreSQL row-level locks via `SELECT ... FOR UPDATE SKIP LOCKED`. Furthermore, each event in a polled batch is dispatched and committed in an isolated transaction boundary, with exponential backoff (`30s * 2^(retry_count - 1)`) and Dead-Letter Queueing (`status = 'FAILED'`).

## Alternatives Considered
1. **Single-Instance In-Memory Worker Loop**:
   - *Rejected*: Single point of failure and cannot scale horizontally.
2. **Dedicated External Broker (RabbitMQ / Kafka) as Source of Truth**:
   - *Rejected*: Adds infrastructure operational complexity when PostgreSQL natively supports lock-free multi-worker polling via `SKIP LOCKED`.
3. **PostgreSQL `FOR UPDATE SKIP LOCKED` Polling Daemon (`OutboxWorker`)**:
   - *Accepted*: Highly reliable, horizontally scalable, and requires no additional infrastructure.

## Consequences
- **Positive**: Zero lock contention across horizontally scaled worker pods.
- **Positive**: Failure on one event never rolls back successfully processed events in the same batch.
- **Positive**: Worker contains zero domain logic—it only polls, locks, dispatches, and tracks status.
- **Negative / Constraint**: Polling interval introduces minor latency (typically < 2 seconds) compared to push-based message brokers.

## References
- `OUTBOX_WORKER_ARCHITECTURE.md`
