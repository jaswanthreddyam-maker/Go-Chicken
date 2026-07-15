# ADR 0010: Rebuildable Analytics Projections (`AnalyticsRebuilder`)

## Status
Accepted (Frozen for PR 9)

## Context
Analytical dashboards and data warehouses in traditional applications often become tangled with operational tables or accumulate ad-hoc state that cannot be reproduced if corrupted. Furthermore, schema evolutions in dashboards can break when historical data was written in an old format.

## Decision
We establish:
1. **Analytics Owns No Business Truth**: Analytics tables are strictly disposable read-only projections derived from immutable domain events (`OrderConfirmedIntegrationEvent`, `OrderInvoiceGenerated`, etc.).
2. **Deterministic Rebuild Engine (`AnalyticsRebuilder`)**: Any or all analytics tables can be wiped and fully reconstructed at any time by replaying historical outbox / domain events.
3. **Equivalence Invariant**: Incremental real-time projection updates must produce identical results to a full historical replay (`Incremental == Full Rebuild`).

## Alternatives Considered
1. **Analytics Tables as Source of Truth for Reporting**:
   - *Rejected*: Creates irreversible drift and untraceable reporting discrepancies.
2. **Ad-Hoc SQL Aggregations Directly Over Operational Tables**:
   - *Rejected*: Causes severe database locking and degrades transactional core throughput.
3. **Disposable Rebuildable Projections (`AnalyticsService` + `AnalyticsRebuilder`)**:
   - *Accepted*: Guarantees deterministic reporting and zero risk to historical data integrity.

## Consequences
- **Positive**: Complete analytical flexibility—new dashboards can be retroactively populated from historical events.
- **Positive**: Zero risk of permanent reporting corruption.
- **Negative / Constraint**: Rebuilding large event histories requires sequential replay execution time.

## References
- `ANALYTICS_SERVICE_DESIGN.md`
