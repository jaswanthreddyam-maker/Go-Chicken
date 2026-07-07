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
from routers import orders, whatsapp, analytics, pricing, trucks, profile, auth  # Import routers
from api.v1 import khata as khata_v1  # Import Khata ledger router
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

# Configure logging so webhook debug output is visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

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
app.include_router(trucks.router)
app.include_router(profile.router)
app.include_router(auth.router)
app.include_router(khata_v1.router, prefix="/api/v1/khata", tags=["Khata Ledger"])


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
    # Table auto-creation removed in favor of Alembic migrations.
    # Please use `alembic upgrade head` to manage the schema.
    pass

@app.get("/")
async def root():
    return {"message": "Go Chicken Supply Chain Engine is running smoothly!"}

@app.get("/health")
async def health_check():
    from fastapi.responses import JSONResponse
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "db": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "db": "disconnected"})
