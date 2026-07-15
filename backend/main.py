import sys
import os

# Ensure the backend directory is in sys.path so modules like 'core', 'models', and 'routers' can be resolved in serverless environments (e.g., Vercel).
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import logging
from fastapi import FastAPI
from core.database import engine, Base
import models  # Import all models to ensure they are attached to Base.metadata
from routers import orders, whatsapp, analytics, pricing, trucks, profile, auth, inventory, quotes, events  # Import routers
from api.v1 import khata as khata_v1  # Import Khata ledger router
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

# Configure logging so webhook debug output is visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("go_chicken.main")

app = FastAPI(
    title="Go Chicken API",
    version="0.1.0"
)

# Allow CORS for Next.js / frontend dashboard
from core.config import get_settings
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "https://go-chicken-steel.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class HSTSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(HSTSMiddleware)

from fastapi import Request, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from schemas.whatsapp import WhatsAppWebhookPayload
from schemas.auth import SignupRequest, LoginRequest
from routers.auth import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Connect routers to the main app
app.include_router(orders.router)
app.include_router(whatsapp.router)
app.include_router(analytics.router)
app.include_router(pricing.router)
app.include_router(quotes.router)
app.include_router(trucks.router)
app.include_router(profile.router)
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(khata_v1.router, prefix="/api/v1/khata", tags=["Khata Ledger"])
app.include_router(events.router, prefix="/api/v1")


# Root alias routes in case Meta webhook is configured without /api/v1 prefix
@app.get("/whatsapp/webhook")
@app.get("/whatsapp/webhook/")
async def root_verify_webhook(request: Request):
    return await whatsapp.verify_webhook(request)


@app.post("/whatsapp/webhook")
@app.post("/whatsapp/webhook/")
async def root_handle_webhook(payload: WhatsAppWebhookPayload, background_tasks: BackgroundTasks):
    return await whatsapp.handle_webhook(payload, background_tasks)


# Root alias routes for Google OAuth and Auth in case frontend or direct link is missing /api/v1 prefix
@app.get("/auth/google/login")
@app.get("/auth/google/login/")
async def root_google_login(request: Request):
    return await auth.google_login(request)


@app.get("/auth/google/callback")
@app.get("/auth/google/callback/")
async def root_google_callback(request: Request, code: str = None, error: str = None, state: str = None, db: AsyncSession = Depends(get_db)):
    return await auth.google_callback(request, code, error, state, db)


@app.post("/auth/signup")
@app.post("/auth/signup/")
async def root_signup(request: Request, body: SignupRequest, db: AsyncSession = Depends(get_db)):
    return await auth.signup(request, body, db)


@app.post("/auth/login")
@app.post("/auth/login/")
async def root_login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth.login(request, body, db)


@app.on_event("startup")
async def startup():
    logger.info("Starting up Go Chicken API...")
    # 1. Critical configuration check
    if not settings.JWT_SECRET:
        logger.critical("JWT_SECRET is missing! Backend refusing to start.")
        sys.exit(1)
        
    # 2. Database check
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection: OK")
    except Exception as e:
        logger.critical(f"Database connection failed! {e}")
        sys.exit(1)
        
    # 3. Optional Services warning
    if settings.AI_PROVIDER.lower() == "groq" and not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is missing! AI extraction will fail.")
    if not settings.WHATSAPP_VERIFY_TOKEN or not settings.WHATSAPP_API_TOKEN:
        logger.warning("WhatsApp tokens are missing! Meta webhook will fail.")
        
    logger.info("Startup validation complete.")

@app.get("/")
async def root():
    return {"message": "Go Chicken Supply Chain Engine is running smoothly!"}

@app.get("/health")
async def health_check():
    from fastapi.responses import JSONResponse
    checks = {
        "database": "unhealthy",
        "supabase": "healthy" if "supabase" in settings.DATABASE_URL else "N/A",
        "ai": "healthy" if settings.AI_PROVIDER else "unconfigured",
        "meta": "configured" if settings.WHATSAPP_VERIFY_TOKEN else "unconfigured",
        "n8n": "configured" if hasattr(settings, 'N8N_WEBHOOK_SECRET') else "unconfigured"
    }
    
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
        return {"status": "healthy", "checks": checks, "version": settings.APP_VERSION}
    except Exception as e:
        checks["database"] = "unhealthy"
        return JSONResponse(status_code=503, content={"status": "unhealthy", "checks": checks, "version": settings.APP_VERSION})

@app.get("/ready")
async def ready_probe():
    """Kubernetes-style readiness probe."""
    return {"status": "ready"}

@app.get("/system/info")
async def system_info():
    """System info for debugging. Hidden unless DEMO_MODE is true."""
    from fastapi import HTTPException
    if not getattr(settings, 'DEMO_MODE', False):
        raise HTTPException(status_code=403, detail="System info is disabled outside demo mode.")
        
    return {
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "ai_provider": getattr(settings, 'AI_PROVIDER', 'unknown'),
        "database": "supabase" if "supabase" in settings.DATABASE_URL else "local",
        "build": "2026-07-16",
        "version": settings.APP_VERSION
    }
