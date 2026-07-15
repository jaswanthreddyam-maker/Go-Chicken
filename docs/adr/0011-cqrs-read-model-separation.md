# ADR 0011: CQRS Read Model Separation for Analytical Workloads

## Status
Accepted (Frozen for PR 9)

## Context
High-frequency transactional write workloads (`OrderService`, `KhataService`, `InventoryService`) have competing database tuning and indexing requirements compared to heavy analytical read workloads (`SUM`, `COUNT`, multi-day aggregations). Running analytical queries directly against transactional tables degrades ACID write latency and risks table locks.

## Decision
We enforce strict **Command Query Responsibility Segregation (CQRS)** for analytics:
1. **Dedicated Read-Only Projections**: Analytical queries from dashboards and reports must read exclusively from projection tables (`OperationalDailyKPI`, `FinancialDailyKPI`, `CommunicationDailyKPI`).
2. **Prohibition of Direct Aggregate Queries**: Analytics endpoints are banned from executing analytical aggregations against Layer 1 transactional tables (`orders`, `khata_ledger`, `inventory_items`).
3. **Asynchronous Population**: Projections are populated asynchronously via Layer 3 domain event consumers.

## Alternatives Considered
1. **Shared Database Views Over Transactional Tables**:
   - *Rejected*: Still executes queries against live operational tables under heavy read volume.
2. **Dedicated CQRS Read Projections**:
   - *Accepted*: Complete isolation of analytical read workloads from transactional write workloads.

## Consequences
- **Positive**: Zero analytical query overhead on transactional core tables.
- **Positive**: Projections can be indexed specifically for dashboard query patterns.
- **Negative / Constraint**: Projections reflect eventual consistency based on outbox consumer processing latency.

## References
- `ANALYTICS_SERVICE_DESIGN.md`
