"""WhatsApp Cloud API Webhook Router — replaces n8n for webhook handling.

Handles:
  GET  /api/v1/whatsapp/webhook  → Meta verification challenge-response
  POST /api/v1/whatsapp/webhook  → Incoming messages & status updates

Meta requires a 200 OK within ~15 seconds, so all heavy processing
(Ollama, DB writes, reply sending) is dispatched via BackgroundTasks.
"""

import logging
import re
import time
import traceback
import uuid
from decimal import Decimal
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, desc, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db, AsyncSessionLocal
from core.ai_provider import classify_message
from core.pricing_service import get_all_prices, get_price_for_item
from models.classification_log import ClassificationLog
from models.order import Order
from models.error_log import ErrorLog
from models.user import User, UserRole
from models.khata import KhataTransaction
from schemas.whatsapp import WhatsAppWebhookPayload

logger = logging.getLogger("go_chicken.whatsapp")

router = APIRouter(
    prefix="/api/v1/whatsapp",
    tags=["WhatsApp Webhook"],
)

settings = get_settings()


# ── GET: Meta Webhook Verification ─────────────────────────────


@router.get("/webhook")
@router.get("/webhook/")
async def verify_webhook(request: Request):
    """Meta sends a GET request to verify the webhook URL.

    Query params from Meta:
        hub.mode        — should be "subscribe"
        hub.verify_token — must match our WHATSAPP_VERIFY_TOKEN
        hub.challenge   — the string we must echo back
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    import hmac
    if mode == "subscribe" and hmac.compare_digest(token or "", settings.WHATSAPP_VERIFY_TOKEN):
        logger.info(f"✅ Webhook verified successfully! Challenge: {challenge}")
        return Response(content=challenge, media_type="text/plain")

    logger.warning(f"❌ Webhook verification failed — mode: {mode}, token: {token}")
    return Response(content="Verification failed", status_code=403, media_type="text/plain")


# ── POST: Incoming Messages & Status Updates ───────────────────


@router.post("/webhook")
@router.post("/webhook/")
async def process_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        raw_body = await request.json()
        logger.info(f"RAW WEBHOOK PAYLOAD: {raw_body}")
        payload = WhatsAppWebhookPayload(**raw_body)
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return Response(content="Bad Request", status_code=400)
    
    background_tasks.add_task(process_webhook_payload, payload)
    return Response(content="EVENT_RECEIVED", media_type="text/plain")


# ── Background Processing ──────────────────────────────────────


async def process_webhook_payload(payload: WhatsAppWebhookPayload):
    """Process the webhook payload in the background.

    Extracts messages from Meta's nested structure and handles each one.
    Uses its own DB session since BackgroundTasks run outside the
    request lifecycle.

    IMPORTANT: This entire function is wrapped in try-except because
    BackgroundTasks silently swallow exceptions. Any failure is persisted
    to the error_logs table for debugging.
    """
    try:
        for entry in payload.entry:
            for change in entry.changes:
                if change.field != "messages":
                    continue

                value = change.value
                phone_number_id = value.metadata.phone_number_id

                # Handle status updates (delivered, read, etc.)
                if value.statuses:
                    for status in value.statuses:
                        logger.info(
                            f"📨 Message {status.id} → {status.status} "
                            f"(to: {status.recipient_id})"
                        )

                # Handle incoming messages
                if value.messages:
                    for message in value.messages:
                        sender_phone = message.from_
                        sender_name = _get_sender_name(value.contacts, sender_phone)

                        if message.type == "text" and message.text:
                            message_body = message.text.get("body", "")
                            logger.info(
                                f"💬 Message from {sender_name} ({sender_phone}): "
                                f"{message_body}"
                            )
                            await _process_message(
                                sender_phone=sender_phone,
                                sender_name=sender_name,
                                phone_number_id=phone_number_id,
                                text=message_body
                            )
                        elif message.type == "interactive":
                            if not message.interactive or not isinstance(message.interactive, dict):
                                logger.warning(
                                    f"⚠️ Malformed interactive payload from {sender_name} ({sender_phone})"
                                )
                                continue
                            button_reply = message.interactive.get("button_reply", {})
                            button_id = button_reply.get("id", "")
                            button_title = button_reply.get("title", "")
                            logger.info(
                                f"🔘 Button click from {sender_name} ({sender_phone}): "
                                f"ID='{button_id}' Title='{button_title}'"
                            )
                            await _process_message(
                                sender_phone=sender_phone,
                                sender_name=sender_name,
                                phone_number_id=phone_number_id,
                                button_id=button_id,
                                text=button_title
                            )
                        elif message.type == "location" and message.location:
                            lat = message.location.get("latitude")
                            lon = message.location.get("longitude")
                            logger.info(f"📍 Location from {sender_name} ({sender_phone}): {lat}, {lon}")
                            await _process_message(
                                sender_phone=sender_phone,
                                sender_name=sender_name,
                                phone_number_id=phone_number_id,
                                latitude=lat,
                                longitude=lon
                            )
                        else:
                            logger.info(
                                f"📎 Non-text message ({message.type}) from "
                                f"{sender_name} ({sender_phone}) — skipping for now."
                            )
    except Exception as e:
        logger.error(f"🔥 Background webhook processing failed: {e}")
        await _log_error(
            source="whatsapp_webhook",
            error=e,
            payload=payload.model_dump(by_alias=True),
        )


# ── Unified Message Handler ────────────────────────────────────────

async def _process_message(
    sender_phone: str,
    sender_name: str,
    phone_number_id: str,
    text: str | None = None,
    button_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None
):
    try:
        from core.conversation_service import ConversationService, WhatsAppMessage
        wa_msg = WhatsAppMessage(
            sender_phone=sender_phone,
            sender_name=sender_name,
            text=text,
            button_id=button_id,
            latitude=latitude,
            longitude=longitude
        )
        
        async with AsyncSessionLocal() as db:
            # 1. Look up User
            result = await db.execute(
                select(User).where(
                    User.role == UserRole.RETAILER,
                    (User.phone_number == sender_phone) | (User.whatsapp_id == sender_phone)
                )
            )
            user = result.scalars().first()
            
            # 2. Process via ConversationService
            actions = await ConversationService.process(db, wa_msg, user)
            
            # 3. Execute resulting actions
            if actions:
                await _execute_actions(phone_number_id, sender_phone, actions)
                
    except Exception as e:
        logger.error(f"🔥 Error processing turn for {sender_phone}: {e}", exc_info=True)
        await _log_error(
            source="whatsapp_process_turn",
            error=e,
            payload={"sender_phone": sender_phone, "text": text, "button": button_id},
        )

async def _execute_actions(phone_number_id: str, to: str, actions: list[dict]):
    """Execute generic actions returned by ConversationService."""
    for action in actions:
        if action["type"] == "text":
            await _send_whatsapp_reply(phone_number_id, to, action["text"])
        elif action["type"] == "interactive":
            await _send_whatsapp_interactive_reply(
                phone_number_id, to, action["text"], action.get("buttons", [])
            )


# ── Classification Logging ─────────────────────────────────────


async def _log_classification(
    message: str,
    intent: str | None,
    confidence: float,
    order_source: str,
    latency_ms: int,
):
    """Persist a classification attempt to the classification_logs table.

    Every message that goes through the pipeline gets logged here,
    regardless of outcome. This powers the Brain Health analytics.

    The message is truncated to 100 chars to avoid storing full
    customer messages (privacy) while keeping enough context for
    pattern analysis.
    """
    try:
        async with AsyncSessionLocal() as db:
            log_entry = ClassificationLog(
                message_snippet=message[:100],
                intent=intent,
                confidence=confidence,
                order_source=order_source,
                latency_ms=latency_ms,
            )
            db.add(log_entry)
            await db.commit()
    except Exception as e:
        # Classification logging should never crash the main pipeline
        logger.warning(f"📊 Failed to persist classification log: {e}")


# ── Error Logging ──────────────────────────────────────────────


async def _log_error(source: str, error: Exception, payload: dict = None):
    """Persist a background task error to the error_logs table.

    BackgroundTasks silently swallow exceptions — this ensures every
    failure is captured with full context for post-mortem debugging.
    """
    try:
        async with AsyncSessionLocal() as db:
            error_log = ErrorLog(
                source=source,
                error_type=type(error).__name__,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                payload=payload,
            )
            db.add(error_log)
            await db.commit()
            logger.info(f"📝 Error logged to DB: {source} — {type(error).__name__}")
    except Exception as log_err:
        # Last resort — if even error logging fails, at least print it
        logger.critical(
            f"🚨 DOUBLE FAULT: Failed to log error to DB! "
            f"Original error: {error} | Logging error: {log_err}"
        )


# ── Helper Functions ───────────────────────────────────────────


def _get_sender_name(contacts, phone: str) -> str:
    """Look up the sender's profile name from the contacts list."""
    if contacts:
        for contact in contacts:
            if contact.wa_id == phone:
                return contact.profile.name
    return "Unknown"


def _parse_quantity(message: str) -> Decimal:
    """Extract numeric kg from a message like '50kg live bird'."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*kg", message, re.IGNORECASE)
    if match:
        return Decimal(match.group(1))
    return Decimal("0")


def _parse_item_type(message: str) -> str:
    """Extract item type from a message. Defaults to 'Live Bird'."""
    message_lower = message.lower()
    if "dressed" in message_lower:
        return "Dressed"
    if "skinless" in message_lower:
        return "Skinless"
    return "Live Bird"


def _get_price_per_kg(item_type: str) -> Decimal:
    """Get the price per kg for an item type from config.

    Prices are configurable via environment variables:
      PRICE_LIVE_BIRD=180.00
      PRICE_DRESSED=250.00
      PRICE_SKINLESS=320.00
    """
    prices = {
        "Live Bird": Decimal(str(settings.PRICE_LIVE_BIRD)),
        "Dressed": Decimal(str(settings.PRICE_DRESSED)),
        "Skinless": Decimal(str(settings.PRICE_SKINLESS)),
    }
    return prices.get(item_type, Decimal(str(settings.PRICE_LIVE_BIRD)))


# ── WhatsApp Reply Sender ──────────────────────────────────────


async def _send_whatsapp_reply(
    phone_number_id: str,
    to: str,
    message: str,
):
    """Send a text message reply via Meta WhatsApp Cloud API.

    Uses the Graph API v21.0 endpoint:
      POST https://graph.facebook.com/v21.0/{phone_number_id}/messages

    Auth: Bearer token from WHATSAPP_API_TOKEN in config/.env.

    IMPORTANT: This function never raises exceptions. If Meta's API
    is down or the token is invalid, the failure is logged but the
    calling pipeline (order creation, etc.) continues unaffected.
    """
    if not settings.WHATSAPP_API_TOKEN or settings.WHATSAPP_API_TOKEN == "your_meta_graph_api_token_here":
        logger.warning(
            "📤 WhatsApp reply skipped — WHATSAPP_API_TOKEN not configured. "
            f"Would have sent to {to}: '{message[:60]}...'"
        )
        return

    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": message},
                },
                timeout=15.0,
            )
            response.raise_for_status()

            logger.info(
                f"📤 WhatsApp reply sent to {to}: '{message[:60]}...'"
            )

    except httpx.HTTPStatusError as e:
        logger.error(
            f"📤 WhatsApp reply failed (HTTP {e.response.status_code}): "
            f"{e.response.text[:200]}"
        )
    except httpx.TimeoutException:
        logger.error(
            f"📤 WhatsApp reply timed out sending to {to}"
        )
    except Exception as e:
        logger.error(
            f"📤 WhatsApp reply failed: {type(e).__name__}: {e}"
        )


async def _send_whatsapp_interactive_reply(
    phone_number_id: str,
    to: str,
    message_text: str,
    buttons: list[dict[str, str]],
):
    """Send an interactive button reply via Meta WhatsApp Cloud API.

    buttons format: [{"id": "btn_1", "title": "Confirm Order"}, ...]
    """
    if not settings.WHATSAPP_API_TOKEN or settings.WHATSAPP_API_TOKEN == "your_meta_graph_api_token_here":
        logger.warning(
            "📤 WhatsApp interactive reply skipped — WHATSAPP_API_TOKEN not configured. "
            f"Would have sent to {to}: '{message_text[:60]}...' with buttons {buttons}"
        )
        return

    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"

    formatted_buttons = [
        {
            "type": "reply",
            "reply": {
                "id": btn["id"],
                "title": btn["title"][:20],  # Enforce Meta's 20-char limit
            },
        }
        for btn in buttons[:3]  # Meta allows max 3 buttons per interactive message
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": message_text},
            "action": {"buttons": formatted_buttons},
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()
            logger.info(f"📤 WhatsApp interactive reply sent to {to}: '{message_text[:60]}...'")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"📤 WhatsApp interactive reply failed (HTTP {e.response.status_code}): "
            f"{e.response.text[:200]}"
        )
    except httpx.TimeoutException:
        logger.error(f"📤 WhatsApp interactive reply timed out sending to {to}")
    except Exception as e:
        logger.error(f"📤 WhatsApp interactive reply failed: {type(e).__name__}: {e}")
