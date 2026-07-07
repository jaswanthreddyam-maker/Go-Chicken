"""Ollama service-layer client for intent classification.

This is a REUSABLE service client designed for BackgroundTasks.
Unlike the HTTP endpoint helpers in api/v1/ai.py, this module:
  - Returns None on failure instead of raising HTTPException
  - Never crashes the calling background task
  - Logs all failures for debugging

Usage:
    from core.ollama_client import classify_message, is_ollama_available

    result = await classify_message("50kg live bird")
    if result and result.intent == "ORDER":
        # Process order using result.item, result.quantity_kg
    else:
        # Fall back to regex parsing
"""

import json
import logging
import re

import httpx
from pydantic import ValidationError

from core.config import get_settings
from schemas.classification import MessageClassification

logger = logging.getLogger("go_chicken.ollama")
settings = get_settings()

# ── System Prompt ──────────────────────────────────────────────
# Hardened to prevent Mistral/LLaMA from adding chitchat.
# The "Do not add any text" instruction is critical — without it,
# models love to prepend "Sure! Here is the classification:" which
# breaks JSON parsing.

CLASSIFY_SYSTEM_PROMPT = (
    "You are an automated poultry order processor for a chicken supply chain business. "
    "Respond ONLY with raw JSON. Do not add any text, markdown, code fences, or explanation "
    "outside the JSON object.\n\n"
    "Classify the WhatsApp message into one of these intents:\n"
    "- ORDER: Customer wants to place an order for poultry (e.g., '50kg live bird', '30kg dressed chicken')\n"
    "- INQUIRY: Customer is asking a question about price, availability, delivery, etc.\n"
    "- GREETING: Customer is saying hello, hi, good morning, etc.\n\n"
    "For ORDER intent, extract the item type (Live Bird, Dressed, or Skinless) and quantity in kg.\n"
    "For other intents, set item and quantity_kg to null.\n\n"
    "If you cannot classify the message, return intent as 'INQUIRY' and confidence as 0.\n\n"
    "Response format (JSON ONLY, nothing else):\n"
    '{"intent": "ORDER|INQUIRY|GREETING", "item": "Live Bird|Dressed|Skinless|null", '
    '"quantity_kg": <number|null>, "confidence": <0.0-1.0>}'
)


# ── Public API ─────────────────────────────────────────────────


async def classify_message(message: str) -> MessageClassification | None:
    """Classify a WhatsApp message using local Ollama LLM.

    Args:
        message: Raw WhatsApp message text (e.g., "50kg live bird")

    Returns:
        MessageClassification on success, None on any failure.
        Never raises exceptions — safe for BackgroundTasks.

    Failure modes (all return None):
        - Ollama is not running
        - Ollama times out (>30s)
        - Model returns non-JSON text
        - JSON doesn't match Pydantic schema
    """
    try:
        if not await is_ollama_available():
            logger.warning(
                "🤖 Ollama is not running — falling back to regex immediately. "
                f"Expected at: {settings.OLLAMA_BASE_URL}"
            )
            return None

        safe_message = _sanitize_for_llm(message)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_CHAT_MODEL,
                    "prompt": f'Classify this WhatsApp message:\n"{safe_message}"',
                    "system": CLASSIFY_SYSTEM_PROMPT,
                    "stream": False,
                    # Lower temperature for more deterministic classification
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 150,  # Classification JSON is short
                    },
                },
                timeout=30.0,
            )
            response.raise_for_status()

        data = response.json()
        response_text = data.get("response", "").strip()

        if not response_text:
            logger.warning("🤖 Ollama returned empty response")
            return None

        # Parse the JSON from Ollama's response
        classification = _parse_classification_json(response_text)

        if classification:
            logger.info(
                f"🤖 Ollama classified: intent={classification.intent} "
                f"item={classification.item} qty={classification.quantity_kg}kg "
                f"confidence={classification.confidence:.2f}"
            )

        return classification

    except httpx.ConnectError:
        logger.warning(
            "🤖 Ollama is not running — cannot classify message. "
            f"Expected at: {settings.OLLAMA_BASE_URL}"
        )
        return None

    except httpx.TimeoutException:
        logger.warning(
            f"🤖 Ollama timed out classifying: '{message[:50]}...' "
            "Consider using a lighter model (llama3, gemma2)."
        )
        return None

    except httpx.HTTPStatusError as e:
        logger.warning(f"🤖 Ollama HTTP error: {e.response.status_code} — {e}")
        return None

    except Exception as e:
        logger.error(f"🤖 Unexpected Ollama error: {type(e).__name__}: {e}")
        return None


async def is_ollama_available() -> bool:
    """Quick health check — is Ollama running and reachable?

    Calls GET /api/tags which lists available models.
    Uses a short 1.0s timeout so it doesn't block.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=1.0,
            )
            return response.status_code == 200
    except Exception:
        return False


# ── Internal Helpers ───────────────────────────────────────────


def _sanitize_for_llm(text: str, max_len: int = 200) -> str:
    """Strip control characters and truncate for LLM safety to prevent prompt injection."""
    import unicodedata
    cleaned = "".join(
        c for c in text[:max_len]
        if unicodedata.category(c)[0] != "C"  # Remove control chars
    )
    # Remove common injection patterns
    cleaned = re.sub(r"(?i)(ignore|forget|disregard).*(previous|above|prior).*instructions?", "[filtered]", cleaned)
    return cleaned


def _parse_classification_json(text: str) -> MessageClassification | None:
    """Extract and validate JSON from Ollama's response.

    Handles common LLM quirks:
    - Wrapping JSON in markdown code fences (```json ... ```)
    - Prepending/appending extra text ("Sure! Here is..." etc.)
    - Trailing commas or minor JSON issues
    """
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = text.strip("`").strip()

    # Try to find JSON object in the response
    json_match = re.search(r"\{[^{}]*\}", text)
    if not json_match:
        logger.warning(
            f"🤖 Could not find JSON in Ollama response: '{text[:100]}...'"
        )
        return None

    json_str = json_match.group()

    try:
        raw_data = json.loads(json_str)
        classification = MessageClassification(**raw_data)
        return classification

    except json.JSONDecodeError as e:
        logger.warning(
            f"🤖 Invalid JSON from Ollama: {e} — raw: '{json_str[:100]}'"
        )
        return None

    except ValidationError as e:
        logger.warning(
            f"🤖 Ollama JSON doesn't match schema: {e} — raw: '{json_str[:100]}'"
        )
        return None
