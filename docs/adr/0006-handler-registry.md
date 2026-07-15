# ADR 0006: Dynamic Handler Registry & Typed IntegrationEvent Envelope

## Status
Accepted (Frozen)

## Context
Coupling outbox polling daemons directly to specific consumer service classes or raw database ORM instances degrades maintainability and prevents independent consumer evolution.

## Decision
We decouple outbox consumers using:
1. **`IntegrationEvent` Envelope**: An immutable transport dataclass carrying `event_id`, `event_type`, `aggregate_type`, `aggregate_id`, `tenant_id`, `occurred_at`, `payload`, `correlation_id`, and `causation_id`.
2. **`HandlerRegistry`**: A dynamic runtime registry (`registry.register(...)` and `registry.resolve(...)`). Downstream subsystems register typed `EventHandler` implementations at application startup.

## Alternatives Considered
1. **Hardcoded `if/elif event.event_type == ...` in Polling Loop**:
   - *Rejected*: Violates Open/Closed Principle; every new consumer requires modifying infrastructure worker code.
2. **Passing Raw ORM `IntegrationOutbox` Rows to Handlers**:
   - *Rejected*: Couples consumer domain logic directly to database storage schemas.
3. **Dynamic `HandlerRegistry` with `IntegrationEvent` Envelope**:
   - *Accepted*: Complete decoupling of polling infrastructure from consumer domain services.

## Consequences
- **Positive**: Adding new consumers (`KhataService`, `NotificationService`, `AnalyticsService`) requires zero code changes to `OutboxWorker`.
- **Positive**: Consumers remain 100% independent of persistence ORM models.
- **Positive**: Distributed tracing across asynchronous consumer pipelines is natively supported via `correlation_id` and `causation_id`.

## References
- `OUTBOX_WORKER_ARCHITECTURE.md`
- `DOMAIN_EVENTS.md`
