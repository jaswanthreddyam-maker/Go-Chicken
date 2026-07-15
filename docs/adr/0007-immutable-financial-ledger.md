# ADR 0007: Immutable Financial Ledger & Separate Rebuildable Balance Projection

## Status
Accepted (Frozen for PR 7)

## Context
Traditional invoicing systems often mutate invoice balances or update a single `customer.balance` column directly during payment receipt. This leads to untraceable accounting discrepancies, concurrency race conditions, and an inability to audit financial history.

## Decision
We establish:
1. **Append-Only Immutable Ledger (`KhataLedger`)**: The sole financial source of truth. Every transaction (`INVOICE`, `PAYMENT`, `CREDIT_NOTE`, `DEBIT_NOTE`, `ADJUSTMENT`, `REVERSAL`) is strictly append-only. Existing entries are never updated or deleted.
2. **Rebuildable Read Projection (`CustomerBalanceProjection`)**: Stores cached balances for low-latency queries. It is strictly a projection that can be deterministically rebuilt at any time from `SUM(KhataLedger)`.
3. **Strict `Decimal` Precision**: Floating-point arithmetic (`float`) is banned across all financial models and calculations.

## Alternatives Considered
1. **Mutable Invoices (`UPDATE invoices SET amount_paid = ...`)**:
   - *Rejected*: Destroys historical audit trail and complicates multi-payment reconciliation.
2. **In-Place Running Balance Columns Only**:
   - *Rejected*: Subject to concurrency race conditions and drift over time.
3. **Immutable `KhataLedger` + Rebuildable `CustomerBalanceProjection`**:
   - *Accepted*: Guarantees auditability, concurrency safety, and deterministic accounting parity.

## Consequences
- **Positive**: Complete financial audit trail with zero loss of accounting history.
- **Positive**: Erroneous postings can be corrected cleanly via non-destructive `REVERSAL` entries.
- **Negative / Constraint**: Balance projections must be kept synchronized with ledger appends within the same database transaction.

## References
- `KHATA_SERVICE_DESIGN.md`
