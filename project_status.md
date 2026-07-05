# Go Chicken - Project Status

**Last Updated:** 2026-07-04 21:16 IST

## Codebase Overview & What We've Built

### 1. Database Infrastructure
- **Status:** Complete (Initial Setup)
- **Details:** 
  - Configured a `docker-compose.yml` to run a `pgvector/pgvector:pg16` container.
  - Automatically runs `schema.sql` on startup.
  - Due to a local conflict on port 5432, the Docker port is mapped to `5435` (`localhost:5435`).
- **Files Modified/Created:** 
  - `docker-compose.yml` (Modified port binding to 5435)

### 2. FastAPI Backend
- **Status:** Complete (WhatsApp Webhooks, Dynamic Pricing API & Auto-Migrations)
- **Details:** 
  - Updated the `.env` file to correctly point to the Docker PostgreSQL instance on port 5435 and added production Meta API credentials (`WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`).
  - Implemented dynamic pricing CRUD endpoints (`routers/pricing.py`) allowing real-time poultry rate updates without server restarts.
  - Added startup auto-migration in `main.py` (`ALTER TABLE orders ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20)`) and ensured all SQLAlchemy models (`models/__init__.py`, created `models/inventory.py`) are loaded at startup.
  - Added root alias routes (`/whatsapp/webhook` and `/whatsapp/webhook/`) in `main.py` and `whatsapp.py` to prevent 307 temporary redirects and resolve Meta webhook verification errors.
  - Hardened WhatsApp processing with **Fast-Fail Ollama Health Check** (`< 1s` timeout in `core/ollama_client.py`) and added **Regex Fallback for GREETING & INQUIRY intents** (`Hi`, `Hello`, `Price`, `Rate`), guaranteeing 100% instant bot responsiveness even when local LLMs are offline.
- **Files Modified/Created:** 
  - `backend/.env` (Updated credentials & DB URL)
  - `backend/main.py` (Added root alias routes & startup auto-migration)
  - `backend/routers/whatsapp.py` (Added trailing slash support, GREETING/INQUIRY regex fallback)
  - `backend/routers/pricing.py` (Created dynamic pricing endpoints)
  - `backend/models/inventory.py` & `models/__init__.py` (Created inventory model & exported all models)
  - `backend/core/ollama_client.py` (Added fast-fail health check with 1s timeout)

### 3. Wholesaler Web Dashboard (Frontend)
- **Status:** Complete (UI, Live Backend API Wiring, Optimistic UI & Netlify Deployment Config)
- **Details:** 
  - Bootstrapped a Next.js project using Tailwind CSS in the `frontend/` directory.
  - Built out the single-page React component dashboard for the "Main Boss".
  - Implemented interactive logic: Real-time clock, Notifications dropdown, "Record Payment" modal, Interactive Khata buttons, Live Search filtering, and an AI Demand Scatter Chart.
  - **Live Backend API Integration:** Replaced static mock arrays with TanStack-style `useEffect` live data hooks fetching from `localhost:8001/api/v1` for `/orders`, `/pricing`, and `/trucks`.
  - **15-Second Auto-Polling & Page Visibility API:** Implemented background auto-refresh every 15s that automatically pauses when the browser tab is inactive/backgrounded to save network load, with immediate refetch upon tab focus.
  - **Optimistic UI & Sanitized Error Rollbacks:** Instant UI updates when toggling order status, updating price rates, or adding trucks. Reverts immediately if the backend fails, displaying sanitized user-friendly alerts without exposing raw stack traces or SQL errors.
  - **Netlify Monorepo Deployment Config:** Created `netlify.toml` in both root (`/`) and `frontend/` directories to automatically configure `base = "frontend"`, `command = "npm run build"`, and enable `@netlify/plugin-nextjs` for seamless cloud hosting.
- **Files Modified/Created:** 
  - `frontend/src/app/page.js` (Fully wired React dashboard with live APIs, polling & optimistic UI)
  - `frontend/.env.local` (Created API URL configuration)
  - `netlify.toml` & `frontend/netlify.toml` (Created Netlify monorepo deployment configuration)

### 4. Tenant Isolation & Security
- **Status:** Complete (Server-Side Tenant Derivation)
- **Details:** 
  - Implemented server-side tenant dependency `get_current_tenant` in `backend/core/auth.py`.
  - Removed client-supplied `tenant_id` query parameters and request body fields across trucks and khata endpoints to eliminate horizontal privilege escalation risks.
  - Added full CRUD unit tests in `backend/tests/test_trucks.py` verifying strict tenant data isolation.
- **Files Modified/Created:** 
  - `backend/core/auth.py` (Created tenant auth dependency)
  - `backend/routers/trucks.py` (Created tenant-isolated fleet router)
  - `backend/api/v1/khata.py` & `backend/schemas/khata.py` (Secured khata transactions)
  - `backend/tests/test_trucks.py` (Created unit test suite for fleet and tenant isolation)

## Architectural Guidelines
- **Service Layer Strategy:** The FastAPI backend serves as both the RESTful API layer and the WhatsApp webhook handler. All orchestration logic lives in Python — no external workflow tools required.
- **WhatsApp Bot (Native FastAPI):** Meta WhatsApp Cloud API webhooks are handled directly by `routers/whatsapp.py`. Incoming messages are validated via Pydantic models, parsed for order intent, and processed in `BackgroundTasks` to meet Meta's fast-response requirement.
- **Resilient AI Pipeline:** Ollama LLM is called via `httpx` with a fast-fail 1s health check (`is_ollama_available`). If offline or low confidence, the handler instantly falls back to robust regex parsing for ORDER, GREETING, and INQUIRY intents.
- **Strict Server-Side Tenant Isolation:** All multi-tenant queries and mutations derive `tenant_id` strictly from authenticated server-side context (`get_current_tenant`), never trusting client parameters.
- **Database Access:** All DB interactions go through SQLAlchemy async sessions via the FastAPI dependency injection system.
- **Local Deployment:** Ngrok is used for local deployment tunneling (`localhost:8001`).

## Pending Tasks
- [x] **WhatsApp Reply Integration:** Implemented using Meta Graph API (`_send_whatsapp_reply`) to send welcome menus, price catalogs, and order confirmations back to retailers.
- [x] **Ollama Intent Classification & Fallback:** Integrated Ollama in `whatsapp.py` to classify messages as ORDER / INQUIRY / GREETING with fast-fail health checks and 100% regex fallback coverage.
- [x] **Netlify Deployment Setup:** Configured monorepo build settings via `netlify.toml` to eliminate 404 errors on cloud deployment.
- [x] **Backend Integration (Phase 1):** Replaced mock data in the Next.js frontend with live `fetch()` calls to the FastAPI backend (`localhost:8001`), implemented optimistic UI rollbacks, and secured endpoints with server-side tenant isolation.
- [x] **Phase 2: WhatsApp Order Confirmation Flow:** Send interactive WhatsApp messages with order summaries (item, qty, rate, total, Khata balance) and confirmation/cancellation buttons. Hardened with atomic SQL updates, sender verification, and full unit test coverage (73 tests passing).
- [ ] **Phase 3: AI Forecaster Engine:** Implement the local Ollama LLM pipeline in the backend to generate demand forecasts and explain reasoning.
- [ ] **Phase 4: Vector Similarity Search:** Collect historical sales embeddings and query them via `pgvector` to populate the AI Demand Cluster scatter chart dynamically.

## Changelog
* **2026-07-04 21:16 IST**: **Direct URL Sub-Route Mapping.** Created Next.js route subdirectories for `/orders`, `/fleet`, `/khata`, and `/ai` mapped to the root dashboard with a `defaultTab` prop. Linked tab toggles to `window.history.pushState` for instant path updates. Eliminates 404 Not Found errors on local refreshes and Netlify deep-links while retaining the SPA performance and background polling loops.
* **2026-07-04 20:53 IST**: **Enterprise B&W Mobile UI Overhaul.** Completed a full monochromatic redesign of the Next.js dashboard using clean borders (`border-[#EBEBEB]`), off-white backgrounds (`#FAFAFA`), and pure black typography (`#111111`). Replaced the mobile sidebar with a fixed, outline-style `BottomNav` bar mapped to instant SPA tab transitions. Wrapped stat blocks in a horizontal swipe snapping grid on mobile. Re-encoded Recharts graphs to minimal black lines with hidden grids. Converted popups to sliding Bottom Sheets for mobile viewports. Fixed pricing update to use `PUT /api/v1/pricing/{item_type}` (resolving 405 errors). Verified successful production build compilation.
* **2026-07-04 20:43 IST**: **Mobile Welcome Splash Screen Animation.** Processed and accelerated `D:\An_animated_chicken_should_loo.mp4` to exactly 2.0 seconds duration (120 FPS), encoded with H.264 (`welcome_chicken.mp4`) for universal mobile browser compatibility. Integrated a mobile-exclusive (`md:hidden`) splash screen overlay in `page.js` that plays the welcome animation on app launch and smoothly fades out after 2 seconds.
* **2026-07-04 20:22 IST**: **Phase 2 Completed — WhatsApp Order Confirmation Flow & Interactive Buttons.** Added interactive button support (`Confirm Order` / `Cancel Order`) via Meta Graph API v21.0. Integrated live Khata balance lookups into order confirmation cards. Hardened concurrency with atomic conditional SQL updates to prevent double-tap race conditions and enforced sender verification. Unified SQLAlchemy models under `models.base.Base`, resolving all ORM mapper conflicts. Verified full backend test suite: **73 unit tests passing (0 failures, 0 warnings)**.
* **2026-07-04 18:35 IST**: **Phase 1 Completed — Live Backend API Wiring & Security Hardening.** Replaced static frontend mock arrays with live endpoints (`/orders`, `/pricing`, `/trucks`). Implemented 15s auto-polling with Page Visibility API pause/resume, manual Refresh button, and optimistic UI updates with sanitized error rollbacks. Hardened backend security by deriving `tenant_id` server-side via `auth.py` and removing client body/query tenant parameters. Added 8 passing unit tests for fleet management and tenant isolation (`test_trucks.py`).
* **2026-07-04 17:45 IST**: **Netlify Monorepo Deployment Configuration & Doc Sync.** Created `netlify.toml` in monorepo root and `frontend/` to fix 404 errors on Netlify deployments. Synchronized `project_status.md` with all recent architecture updates.
* **2026-07-04 16:20 IST**: **WhatsApp Bot Fast-Fail & Regex Greeting Fallback.** Added 1s health check in `core/ollama_client.py` to prevent 30s timeouts when Ollama is offline. Enhanced regex fallback in `whatsapp.py` to support GREETING (`hi`, `hello`) and INQUIRY (`price`, `rate`) intents. Discovered and documented Meta Cloud API Error `#131030` (test recipient phone numbers must be verified in Meta Dashboard).
* **2026-07-04 15:55 IST**: **WhatsApp Webhook Aliases & Database Auto-Migration.** Added `/whatsapp/webhook/` trailing slash alias routes in `main.py` and `whatsapp.py` to fix Meta verification redirect errors. Added startup auto-migration for `phone_number` column in `orders` table and created `models/inventory.py`.
* **2026-07-04 09:48 IST**: **BREAKING: Replaced n8n with native FastAPI WhatsApp webhook handler.** Added `routers/whatsapp.py` (GET/POST webhook endpoints with BackgroundTasks), `schemas/whatsapp.py` (Pydantic models for Meta's nested payload), updated `core/config.py` and `.env` with WhatsApp settings, removed n8n service from `docker-compose.yml`.
* **2026-07-03 01:06 IST**: Documented n8n WhatsApp Bot Architectural Guidelines (FastAPI as pure service layer, n8n for orchestration, Ollama guardrails).
* **2026-07-03 00:20 IST**: Implemented dynamic Truck CRUD Interface and Add Truck modal. Removed static fleet map placeholder.
* **2026-07-03 00:15 IST**: Added `project_status.md` to track project state.
* **2026-07-02**: Initialized Next.js frontend, built Wholesaler Dashboard UI with interactive functionality.
* **2026-07-02**: Initialized Docker Postgres DB (port 5435), established backend connectivity.
