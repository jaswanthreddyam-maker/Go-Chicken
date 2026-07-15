# ADR 0008: Communication Provider Abstraction (`CommunicationProvider`)

## Status
Accepted (Frozen for PR 8)

## Context
Notification services in enterprise applications frequently couple domain logic directly to vendor APIs (e.g., calling `WhatsAppCloudAPIClient.send_message(...)` inline within event handlers or routers). This makes supporting alternative channels (SMS, Email, Push) impossible without conditional spaghetti code (`if channel == ...`).

## Decision
We establish:
1. **Abstract `CommunicationProvider` Base Interface**: Defines `.channel` and `async def send(recipient, content, metadata)`.
2. **Runtime Provider Registry**: `CommunicationService` dispatches messages through registered providers resolved dynamically by channel name (`WHATSAPP`, `SMS`, `EMAIL`).
3. **Decoupled Business Consumers**: Outbox consumers dispatch messages exclusively through `CommunicationService.send(channel="WHATSAPP", ...)` without direct vendor API dependencies.

## Alternatives Considered
1. **Hardcoded Vendor API Calls in Event Handlers**:
   - *Rejected*: Couples domain consumers directly to external HTTP APIs and vendor SDKs.
2. **Channel Conditional Logic inside `NotificationService`**:
   - *Rejected*: Violates the Open/Closed Principle as adding a channel modifies existing core service logic.
3. **Abstract `CommunicationProvider` & Dynamic Router (`CommunicationService`)**:
   - *Accepted*: Extensible multi-channel platform requiring zero core modifications when adding channels.

## Consequences
- **Positive**: Seamlessly supports multi-channel dispatch (WhatsApp, SMS, Email, Push).
- **Positive**: Mocking communication channels in unit tests is trivial via dummy provider implementations.
- **Negative / Constraint**: Every channel provider must conform to the unified asynchronous `.send()` result interface.

## References
- `COMMUNICATION_SERVICE_DESIGN.md`
