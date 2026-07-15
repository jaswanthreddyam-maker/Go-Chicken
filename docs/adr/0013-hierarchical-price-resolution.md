# ADR 0013: Deterministic Hierarchical Price Resolution

## Status
Proposed (Draft for PR 10)

## Context
Pricing logic in commercial supply chains often degenerates into convoluted `if/else` conditional scripts checking customer codes, regions, volume tiers, and promotional overrides.

## Decision
We enforce a **Deterministic Hierarchical Price Resolution Engine (`PricingService`)** evaluating prices in strict precedence order:
1. **Customer Contract Override**: Specific negotiated SKU price for a customer (`CustomerPriceOverride`).
2. **Volume / Tier Price Book**: Tiered wholesale rate based on ordered weight (`PriceBookEntry.min_quantity_kg`).
3. **Delivery Zone Surcharge**: Additive or multiplier surcharge based on route distance (`DeliveryZoneSurcharge`).
4. **Base Wholesale Price Book**: Tenant default wholesale rate.

All calculations strictly use Python `Decimal` with rounding enforced to 2 decimal places.

## Alternatives Considered
1. **Hardcoded Conditional Pricing Rules in Routers**:
   - *Rejected*: Unmaintainable and impossible to audit or test systematically.
2. **Hierarchical Price Resolution Engine (`PricingService`)**:
   - *Accepted*: Clean, modular, and deterministic evaluation hierarchy.

## Consequences
- **Positive**: Clear, predictable pricing precedence hierarchy.
- **Positive**: Fully testable pricing rules decoupled from order orchestration.
- **Negative / Constraint**: Every price evaluation requires inspecting the precedence chain.

## References
- `PRICING_QUOTE_SERVICE_DESIGN.md`
