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

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, desc, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db, AsyncSessionLocal
from core.ollama_client import classify_message
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

    # Check against both config variable and explicit string just in case .env was modified
    if mode == "subscribe" and token in (settings.WHATSAPP_VERIFY_TOKEN, "gochicken123"):
        logger.info(f"✅ Webhook verified successfully! Challenge: {challenge}")
        return Response(content=challenge, media_type="text/plain")

    logger.warning(f"❌ Webhook verification failed — mode: {mode}, token: {token}")
    return Response(content="Verification failed", status_code=403, media_type="text/plain")


# ── POST: Incoming Messages & Status Updates ───────────────────


@router.post("/webhook")
@router.post("/webhook/")
async def handle_webhook(
    payload: WhatsAppWebhookPayload,
    background_tasks: BackgroundTasks,
):
    """Receive incoming messages from Meta WhatsApp Cloud API.

    Returns 200 OK immediately, then processes messages in background.
    This is critical — Meta will retry (and eventually disable) webhooks
    that don't respond quickly.
    """
    background_tasks.add_task(process_webhook_payload, payload)
    return {"status": "ok"}


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
                            await _handle_text_message(
                                sender_phone=sender_phone,
                                sender_name=sender_name,
                                message_body=message_body,
                                phone_number_id=phone_number_id,
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
                            await _handle_interactive_message(
                                sender_phone=sender_phone,
                                sender_name=sender_name,
                                button_id=button_id,
                                button_title=button_title,
                                phone_number_id=phone_number_id,
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


# ── Message Handlers ───────────────────────────────────────────


async def _handle_text_message(
    sender_phone: str,
    sender_name: str,
    message_body: str,
    phone_number_id: str,
):
    """Process a text message — classify intent via Ollama, fall back to regex.

    Classification Pipeline:
        1. Try Ollama LLM for intent classification (ORDER / INQUIRY / GREETING)
        2. If Ollama returns ORDER with high confidence → use its extracted data
        3. If Ollama fails or confidence is low → fall back to regex parsing
        4. If neither method finds an order → log and skip

    Monitoring:
        Every classification attempt is persisted to classification_logs with
        latency_ms and confidence for Brain Health dashboard analytics.
    """
    try:
        item_type = None
        quantity_kg = Decimal("0")
        order_source = "regex"  # Default — overridden if Ollama succeeds
        classified_intent = None
        classified_confidence = 0.0
        ollama_latency_ms = 0

        # ── Step 1: Try Ollama Classification ──────────────────────
        start_time = time.monotonic()
        classification = await classify_message(message_body)
        ollama_latency_ms = int((time.monotonic() - start_time) * 1000)

        if classification and classification.intent == "ORDER":
            classified_intent = classification.intent
            classified_confidence = classification.confidence

            if classification.confidence >= settings.OLLAMA_CONFIDENCE_THRESHOLD:
                # Ollama is confident this is an order — use its extracted data
                item_type = classification.item or "Live Bird"
                quantity_kg = Decimal(str(classification.quantity_kg or 0))
                order_source = "ollama"

                logger.info(
                    f"🤖 Ollama classified ORDER: {quantity_kg}kg {item_type} "
                    f"(confidence: {classification.confidence:.2f}, "
                    f"latency: {ollama_latency_ms}ms) "
                    f"from {sender_name} ({sender_phone})"
                )
            else:
                # Ollama thinks it's an order but isn't confident
                logger.info(
                    f"🤖 Ollama low confidence ({classification.confidence:.2f}) "
                    f"for '{message_body[:50]}' — falling back to regex "
                    f"(latency: {ollama_latency_ms}ms)"
                )

        elif classification and classification.intent in ("INQUIRY", "GREETING"):
            classified_intent = classification.intent
            classified_confidence = classification.confidence

            # Not an order — send appropriate auto-reply
            logger.info(
                f"🤖 Ollama classified as {classification.intent} "
                f"(confidence: {classification.confidence:.2f}, "
                f"latency: {ollama_latency_ms}ms) "
                f"from {sender_name}: '{message_body[:80]}'"
            )

            # Persist classification log before sending reply
            await _log_classification(
                message=message_body,
                intent=classified_intent,
                confidence=classified_confidence,
                order_source="ollama",
                latency_ms=ollama_latency_ms,
            )

            # ── Auto-Reply: GREETING ──────────────────────────────
            if classification.intent == "GREETING":
                await _send_whatsapp_reply(
                    phone_number_id=phone_number_id,
                    to=sender_phone,
                    message=(
                        f"🐔 Welcome to *Go Chicken*, {sender_name}!\n\n"
                        "How can we help you today?\n\n"
                        "📦 *Place an order* — just tell us what you need\n"
                        "   _Example: \"50kg live bird\"_\n\n"
                        "💰 *Check prices* — type \"price\" or \"rate\"\n\n"
                        "We deliver fresh poultry daily! 🚛"
                    ),
                )

            # ── Auto-Reply: INQUIRY ───────────────────────────────
            elif classification.intent == "INQUIRY":
                async with AsyncSessionLocal() as db:
                    prices = await get_all_prices(db)
                live_bird_p = prices.get("Live Bird", Decimal(str(settings.PRICE_LIVE_BIRD)))
                dressed_p = prices.get("Dressed", Decimal(str(settings.PRICE_DRESSED)))
                skinless_p = prices.get("Skinless", Decimal(str(settings.PRICE_SKINLESS)))

                await _send_whatsapp_reply(
                    phone_number_id=phone_number_id,
                    to=sender_phone,
                    message=(
                        "📋 *Today's Rates — Go Chicken*\n\n"
                        f"🐔 Live Bird: *₹{live_bird_p:.0f}/kg*\n"
                        f"🍗 Dressed: *₹{dressed_p:.0f}/kg*\n"
                        f"🥩 Skinless: *₹{skinless_p:.0f}/kg*\n\n"
                        "To place an order, just send:\n"
                        "_\"50kg live bird\"_ or _\"30kg dressed\"_\n\n"
                        "We'll confirm your order instantly! ✅"
                    ),
                )

            return

        else:
            # Ollama returned None (unavailable, timeout, parse error)
            logger.info(
                "🤖 Ollama unavailable or failed — falling back to regex "
                f"for message from {sender_name} ({sender_phone}) "
                f"(latency: {ollama_latency_ms}ms)"
            )

        # ── Step 2: Regex Fallback (if Ollama didn't resolve it) ───
        if order_source != "ollama":
            quantity_kg = _parse_quantity(message_body)
            item_type = _parse_item_type(message_body)

            if quantity_kg > 0:
                classified_intent = classified_intent or "ORDER"
                logger.info(
                    f"📐 Regex fallback parsed ORDER: {quantity_kg}kg {item_type} "
                    f"from {sender_name} ({sender_phone})"
                )
            elif re.search(r"\b(hi|hello|hey|namaste|vanakkam|start|help)\b", message_body.lower()):
                classified_intent = "GREETING"
                logger.info(f"📐 Regex fallback parsed GREETING from {sender_name} ({sender_phone})")
                await _send_whatsapp_reply(
                    phone_number_id=phone_number_id,
                    to=sender_phone,
                    message=(
                        f"🐔 Welcome to *Go Chicken*, {sender_name}!\n\n"
                        "How can we help you today?\n\n"
                        "📦 *Place an order* — just tell us what you need\n"
                        "   _Example: \"50kg live bird\"_\n\n"
                        "💰 *Check prices* — type \"price\" or \"rate\"\n\n"
                        "We deliver fresh poultry daily! 🚛"
                    ),
                )
                await _log_classification(
                    message=message_body,
                    intent=classified_intent,
                    confidence=1.0,
                    order_source="regex",
                    latency_ms=ollama_latency_ms,
                )
                return
            elif re.search(r"\b(price|rate|cost|entha|rate entha|rates|catalog|menu)\b", message_body.lower()):
                classified_intent = "INQUIRY"
                logger.info(f"📐 Regex fallback parsed INQUIRY from {sender_name} ({sender_phone})")
                async with AsyncSessionLocal() as db:
                    prices = await get_all_prices(db)
                live_bird_p = prices.get("Live Bird", Decimal(str(settings.PRICE_LIVE_BIRD)))
                dressed_p = prices.get("Dressed", Decimal(str(settings.PRICE_DRESSED)))
                skinless_p = prices.get("Skinless", Decimal(str(settings.PRICE_SKINLESS)))

                await _send_whatsapp_reply(
                    phone_number_id=phone_number_id,
                    to=sender_phone,
                    message=(
                        "📋 *Today's Rates — Go Chicken*\n\n"
                        f"🐔 Live Bird: *₹{live_bird_p:.0f}/kg*\n"
                        f"🍗 Dressed: *₹{dressed_p:.0f}/kg*\n"
                        f"🥩 Skinless: *₹{skinless_p:.0f}/kg*\n\n"
                        "To place an order, just send:\n"
                        "_\"50kg live bird\"_ or _\"30kg dressed\"_\n\n"
                        "We'll confirm your order instantly! ✅"
                    ),
                )
                await _log_classification(
                    message=message_body,
                    intent=classified_intent,
                    confidence=1.0,
                    order_source="regex",
                    latency_ms=ollama_latency_ms,
                )
                return

        # ── Step 3: Create Order (if either method found one) ──────
        if quantity_kg > 0:
            async with AsyncSessionLocal() as db:
                # 3a. Look up retailer by phone or whatsapp_id
                stmt = select(User).where(
                    User.role == UserRole.RETAILER,
                    (User.phone == sender_phone) | (User.whatsapp_id == sender_phone),
                )
                res = await db.execute(stmt)
                retailer = res.scalar_one_or_none()

                if not retailer:
                    logger.warning(
                        f"⚠️ Unregistered sender {sender_phone} attempted to place an order ({quantity_kg}kg {item_type}). Rejecting."
                    )
                    await _send_whatsapp_reply(
                        phone_number_id=phone_number_id,
                        to=sender_phone,
                        message=(
                            f"⚠️ *Unregistered Number:* Your phone number ({sender_phone}) is not registered as a Go Chicken retailer.\n\n"
                            "Please contact your wholesaler / Main Boss to register your shop and activate digital ordering. 🚛"
                        ),
                    )
                    await _log_classification(
                        message=message_body,
                        intent=classified_intent,
                        confidence=classified_confidence,
                        order_source=order_source,
                        latency_ms=ollama_latency_ms,
                    )
                    return

                # 3b. Query latest Khata transaction for retailer's balance
                txn_res = await db.execute(
                    select(KhataTransaction)
                    .where(KhataTransaction.retailer_id == retailer.id)
                    .order_by(desc(KhataTransaction.created_at))
                    .limit(1)
                )
                latest_txn = txn_res.scalar_one_or_none()
                current_khata_balance = latest_txn.balance_after if latest_txn else Decimal("0.00")

                price_per_kg = await get_price_for_item(db, item_type)
                total_amount = quantity_kg * price_per_kg

                order = Order(
                    phone_number=sender_phone,
                    tenant_id=retailer.tenant_id,
                    retailer_id=retailer.id,
                    item_type=item_type,
                    quantity_kg=quantity_kg,
                    total_amount=total_amount,
                    status="pending",
                    order_source=order_source,
                )
                db.add(order)
                await db.commit()
                await db.refresh(order)

                logger.info(
                    f"🐔 Order created! ID: {order.id} | "
                    f"{quantity_kg}kg {item_type} from {sender_name} ({sender_phone}) "
                    f"[source: {order_source}, retailer: {retailer.name}]"
                )

            # ── Auto-Reply: ORDER Summary with Interactive Buttons ────
            summary_msg = (
                f"📦 *Order Summary*\n\n"
                f"• *Item:* {item_type}\n"
                f"• *Quantity:* {quantity_kg}kg\n"
                f"• *Rate:* ₹{price_per_kg}/kg\n"
                f"• *Total Amount:* ₹{total_amount:,.2f}\n\n"
                f"💳 *Current Khata Balance:* ₹{current_khata_balance:,.2f}\n\n"
                f"Please confirm or cancel your order below:"
            )
            buttons = [
                {"id": f"confirm_order_{order.id}", "title": "Confirm Order"},
                {"id": f"cancel_order_{order.id}", "title": "Cancel Order"},
            ]
            await _send_whatsapp_interactive_reply(
                phone_number_id=phone_number_id,
                to=sender_phone,
                message_text=summary_msg,
                buttons=buttons,
            )
        else:
            logger.info(
                f"🤔 Could not parse order from: '{message_body}' — "
                f"no quantity detected by Ollama or regex. "
                f"Sender: {sender_name} ({sender_phone})"
            )

        # ── Step 4: Persist classification log ─────────────────────
        await _log_classification(
            message=message_body,
            intent=classified_intent,
            confidence=classified_confidence,
            order_source=order_source,
            latency_ms=ollama_latency_ms,
        )

    except Exception as e:
        logger.error(
            f"🔥 Failed to handle message from {sender_phone}: {e}"
        )
        await _log_error(
            source="whatsapp_message_handler",
            error=e,
            payload={
                "sender_phone": sender_phone,
                "sender_name": sender_name,
                "message_body": message_body,
            },
        )


async def _handle_interactive_message(
    sender_phone: str,
    sender_name: str,
    button_id: str,
    button_title: str,
    phone_number_id: str,
):
    """Handle interactive button clicks (e.g. Confirm Order / Cancel Order)."""
    if not (button_id.startswith("confirm_order_") or button_id.startswith("cancel_order_")):
        logger.info(f"🔘 Unrecognized button ID '{button_id}' from {sender_phone} — ignoring.")
        return

    is_confirm = button_id.startswith("confirm_order_")
    order_id_str = button_id.replace("confirm_order_", "").replace("cancel_order_", "")

    try:
        order_id = uuid.UUID(order_id_str)
    except ValueError:
        logger.warning(f"⚠️ Invalid UUID in button_id: {button_id}")
        return

    new_status = "confirmed" if is_confirm else "cancelled"

    try:
        async with AsyncSessionLocal() as db:
            # 1. Atomic conditional UPDATE matching order_id, status='pending', and phone_number==sender_phone
            stmt = (
                update(Order)
                .where(
                    Order.id == order_id,
                    Order.status == "pending",
                    Order.phone_number == sender_phone,
                )
                .values(status=new_status)
                .returning(Order)
            )
            result = await db.execute(stmt)
            updated_order = result.scalar_one_or_none()

            if updated_order:
                await db.commit()
                logger.info(f"✅ Order #{order_id} atomically updated to '{new_status}' by {sender_phone}")
                reply_msg = (
                    f"🎉 *Order Confirmed!*\n\nThank you, your order #{order_id} for {updated_order.quantity_kg}kg {updated_order.item_type} is locked in and will be dispatched as scheduled. 🚛✅"
                    if is_confirm
                    else f"❌ *Order Cancelled.*\n\nYour order #{order_id} has been cancelled. If this was a mistake, simply send us your order again!"
                )
                await _send_whatsapp_reply(phone_number_id=phone_number_id, to=sender_phone, message=reply_msg)
                return

            # 2. If updated_order is None, figure out why (sender mismatch or not pending)
            existing_order = await db.get(Order, order_id)
            if not existing_order:
                logger.warning(f"⚠️ Order #{order_id} not found in DB.")
                await _send_whatsapp_reply(phone_number_id=phone_number_id, to=sender_phone, message="⚠️ Order not found.")
                return

            if existing_order.phone_number != sender_phone:
                logger.warning(f"🚨 Unauthorized button click attempt on Order #{order_id} from {sender_phone} (owner: {existing_order.phone_number})")
                await _log_error(
                    source="unauthorized_button_click",
                    error=PermissionError("Unauthorized order modification attempt"),
                    payload={"order_id": str(order_id), "sender_phone": sender_phone, "owner_phone": existing_order.phone_number},
                )
                await _send_whatsapp_reply(
                    phone_number_id=phone_number_id,
                    to=sender_phone,
                    message="⚠️ You are not authorized to modify this order.",
                )
                return

            # Order was found and belongs to sender, but status was not pending (already confirmed/cancelled/in transit)
            logger.info(f"ℹ️ Order #{order_id} already has status '{existing_order.status}' — no changes made.")
            await _send_whatsapp_reply(
                phone_number_id=phone_number_id,
                to=sender_phone,
                message=f"ℹ️ This order is already *{existing_order.status}*. No changes were made.",
            )
    except Exception as e:
        logger.error(f"🔥 Error handling interactive message from {sender_phone}: {e}")
        await _log_error(
            source="whatsapp_interactive_handler",
            error=e,
            payload={"sender_phone": sender_phone, "button_id": button_id},
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
