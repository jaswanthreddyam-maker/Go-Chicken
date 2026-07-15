# ADR 0012: Immutable Quote Snapshots

## Status
Proposed (Draft for PR 10)

## Context
In B2B enterprise supply chains, wholesale unit prices fluctuate frequently. If orders reference mutable `price_book` rows or calculate totals dynamically at invoice time, quotes accepted by customers can drift from the final invoice, leading to billing disputes and audit failures.

## Decision
We establish **Immutable Quote Snapshots**:
1. Upon quote generation, `QuoteService` calculates and freezes all line-item unit prices, tier discounts, zone surcharges, and total amounts inside `Quote` and `QuoteItem` records.
2. Subsequent modifications to `PriceBook` or wholesale rates have **zero effect** on existing quotes.
3. When converted to an order, `QuoteService.convert_to_order()` publishes `QuoteConvertedIntegrationEvent` containing the exact snapshotted pricing to `OrderService`.

## Alternatives Considered
1. **Dynamic Price Lookup at Invoice/Order Time**:
   - *Rejected*: Causes price drift between customer quote agreement and invoice generation.
2. **Immutable Quote Snapshots (`Quote` + `QuoteItem`)**:
   - *Accepted*: Guarantees financial contract fidelity and complete auditability.

## Consequences
- **Positive**: Exact financial parity between quote agreement and generated order/invoice.
- **Positive**: Quotes carry an explicit validity window (`expires_at`).
- **Negative / Constraint**: Expired quotes cannot be retroactively converted; a new quote must be generated.

## References
- `PRICING_QUOTE_SERVICE_DESIGN.md`
