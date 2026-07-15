# ADR 0004: Transactional Outbox Pattern for Reliable Event Delivery

## Status
Accepted (Frozen)

## Context
Directly invoking asynchronous notifications or publishing to an external message bus immediately after committing a database transaction creates dual-write vulnerabilities. If the process crashes after `db.commit()` but before message dispatch, downstream subsystems (`Khata`, `Notifications`, `Analytics`) lose critical business events forever.

## Decision
We adopt the **Transactional Outbox Pattern** (`backend/models/outbox.py`). Integration events (`OrderConfirmed`, `OrderDelivered`, `OrderInvoiceGenerated`) are inserted into the `integration_outbox` table within the same ACID transaction boundary as domain state mutations.

## Alternatives Considered
1. **Publish Directly After Commit**:
   - *Rejected*: Dual-write vulnerability; events are permanently lost if crash occurs between commit and publish.
2. **Publish Before Commit**:
   - *Rejected*: Can publish false events if the database transaction rolls back.
3. **Transactional Outbox Pattern**:
   - *Accepted*: Guarantees At-Least-Once delivery by coupling event persistence directly to domain transaction commit.

## Consequences
- **Positive**: Guaranteed At-Least-Once event delivery even if the application server or network crashes immediately after commit.
- **Positive**: Complete auditability of pending, processed, and failed integration events.
- **Negative / Constraint**: Consumers must be idempotent to tolerate potential retries on delivery failure.

## References
- `DOMAIN_EVENTS.md`
- `OUTBOX_WORKER_ARCHITECTURE.md`
