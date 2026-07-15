# ADR 0009: Structured Template Registry for Customer Communication

## Status
Accepted (Frozen for PR 8)

## Context
Hardcoding message strings or string-formatting templates inside individual event handlers spreads customer-facing copy across dozens of files, making localization, compliance review, and multi-channel formatting difficult.

## Decision
We decouple message copy from event consumers using a centralized **`TemplateRegistry`**:
1. Every communication request specifies a symbolic `template_id` (e.g., `ORDER_CONFIRMED`, `INVOICE_GENERATED`, `PAYMENT_RECEIVED`) alongside a `context` dictionary.
2. `CommunicationService` resolves the registered `CommunicationTemplate` for the target channel and formats the payload (`template.render(context)`).

## Alternatives Considered
1. **Hardcoded Message Strings in Event Consumers**:
   - *Rejected*: Difficult to review, maintain, or adapt across different delivery channels.
2. **External Template Microservice / CMS**:
   - *Rejected*: Adds unnecessary network complexity for an internal messaging system.
3. **In-Memory / Database-Backed `TemplateRegistry`**:
   - *Accepted*: Clean separation between event handling triggers and customer copy formatting.

## Consequences
- **Positive**: Centralized customer messaging copy across WhatsApp, SMS, and Email.
- **Positive**: Business logic only passes data context; formatting is handled by the template engine.
- **Negative / Constraint**: Consumers must pass all required context keys expected by the template.

## References
- `COMMUNICATION_SERVICE_DESIGN.md`
