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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request, BackgroundTasks
from schemas.whatsapp import WhatsAppWebhookPayload

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


@app.on_event("startup")
async def startup():
    # In serverless environments (e.g. Vercel) or when DB is offline, prevent cold start hangs/crashes
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logging.warning(f"Could not connect to database on startup (table auto-creation skipped): {e}")

@app.get("/")
async def root():
    return {"message": "Go Chicken Supply Chain Engine is running smoothly!"}
