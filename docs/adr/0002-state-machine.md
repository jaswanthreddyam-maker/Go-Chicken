# ADR 0001: OrderService as the Central Domain Orchestrator

## Status
Accepted (Frozen)

## Context
In early iterations, API and WhatsApp webhook routers executed direct database mutations across `Order`, `InventoryItem`, and `Khata` models. This caused duplicated validation logic, inconsistent state transitions, and high vulnerability to partial transaction failures.

## Decision
We establish `OrderService` (`backend/core/order_service.py`) as the sole domain orchestrator for all order lifecycle operations. API routers and webhook handlers must remain completely thin adapters (`Router -> OrderService`). No API endpoint or webhook handler is permitted to invoke `InventoryService`, `TruckService`, or database mutations directly.

## Consequences
- **Positive**: All order lifecycle operations flow through a single, consistent execution path (`_execute_transition`).
- **Positive**: Enforcement of tenant scoping, ACID boundaries, and audit logging is centralized.
- **Negative / Constraint**: Every new order lifecycle capability must integrate through `OrderService` rather than ad-hoc router queries.
