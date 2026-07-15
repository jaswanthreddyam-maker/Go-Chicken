# 🔗 n8n WhatsApp Orchestration & Architecture Guide

## Executive Summary: Hackathon Pivot Architecture

As highlighted during our architecture review, **business logic must never sit inside n8n**. Using n8n to directly query databases or bypass core domain services leads to fragmented state, missing audit logs, and inconsistent inventory/khata tracking.

In Go Chicken, our architecture strictly adheres to:

```text
WhatsApp
   ↓
n8n Webhook Node (Conversational & AI Extraction Layer)
   ↓
HTTP Request Node (REST API Call)
   ↓
FastAPI Backend REST APIs (/api/v1/orders, /api/v1/quotes, /api/v1/orders/{id}/status)
   ↓
Domain Services (OrderService, InventoryService, KhataService, PricingService)
   ↓
PostgreSQL / Outbox / Dashboard Live Polling
```

---

## 🛠️ Turnkey Workflow Import (`n8n_whatsapp_orchestration.json`)

We have created an exportable, ready-to-use n8n workflow file located at:
`workflows/n8n_whatsapp_orchestration.json`

### Node Breakdown & Responsibilities

1. **`WhatsApp Webhook In` (Webhook Node)**
   - **Path**: `/webhook/whatsapp` (`POST`)
   - **Purpose**: Receives raw JSON webhooks from Meta WhatsApp Cloud API whenever a retailer sends a text or clicks an interactive button.

2. **`Extract Sender & Message` (Code Node)**
   - **Purpose**: Safely parses Meta's nested `entry[0].changes[0].value.messages[0]` payload.
   - **Output**: Normalizes to `{ sender_phone, message_text, button_id, is_interactive }`.

3. **`Button vs Text?` (Switch Node)**
   - **Route 0 (`is_interactive == true`)**: If the message is an interactive button click (`confirm_order_123` / `cancel_order_123`), routes directly to status update execution.
   - **Route 1 (`is_interactive == false`)**: If the message is a text command (`"50kg live bird"`), routes to our AI Intent Classifier.

4. **`Parse Button Click` + `FastAPI - Update Order Status` (HTTP Request Node)**
   - **Endpoint**: `PATCH http://host.docker.internal:8000/api/v1/orders/{order_id}/status`
   - **Headers**: `X-Tenant-ID: <UUID>` (or falls back automatically to default demo tenant).
   - **Body**: `{ "status": "confirmed" | "cancelled" }`
   - **ACID Action**: Instantly transitions order state, reduces/reserves inventory (`InventoryService.deliver_stock` / `release_stock`), and updates ledger projections without bypassing business logic.

5. **`AI Intent Classifier Node` (Code / LLM Node)**
   - **Purpose**: Analyzes raw natural language (`"Send 50kg broiler right now"`) to classify intent (`ORDER`, `QUOTE`, or `INQUIRY`) and extract `item_type` (`Live Bird`, `Broiler`, `DESI`, `Country Chicken`) and `quantity_kg`.

6. **`FastAPI - Create Order` (HTTP Request Node)**
   - **Endpoint**: `POST http://host.docker.internal:8000/api/v1/orders/`
   - **Body**:
     ```json
     {
       "phone_number": "{{ $json.sender_phone }}",
       "item_type": "{{ $json.item_type }}",
       "quantity_kg": {{ $json.quantity_kg }}
     }
     ```
   - **ACID Action**: FastAPI resolves the retailer account (`UserRole.RETAILER`), locks contract pricing (`PricingService`), creates the immutable `Order` and `OrderTimeline` records, and returns the full `OrderResponse`.

7. **`Format WhatsApp Confirmation` (Code Node)**
   - **Purpose**: Takes the exact `OrderResponse` (`id`, `total_amount`, `unit_price`) and formats a clean WhatsApp message with interactive confirmation buttons (`Confirm Order` / `Cancel Order`).

---

## 🚀 90-Second Demo Execution Flow

To execute the flawless hackathon demo for judges:

1. **Reset Database to Day 1 Clean State**:
   ```bash
   python -m scripts.reset_demo
   ```
2. **Start FastAPI Backend Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
3. **Start Next.js Frontend Dashboard**:
   ```bash
   cd frontend && npm run dev
   ```
4. **Trigger n8n Orchestration**:
   - Send simulated text `"50kg live bird"` via n8n webhook or Postman/cURL to `POST http://localhost:5678/webhook/whatsapp`.
   - Watch the backend immediately generate Order # `QT-YYYY-...` with `order_source: "n8n"`.
   - Click the interactive confirm button (`confirm_order_<id>`).
   - Observe the live Next.js dashboard auto-refresh within 3 seconds, showing updated orders, reduced inventory stock, and recorded Khata ledger transactions.
