"""Groq service-layer client for intent classification.

This is a fast, cloud-based alternative to the local Ollama LLM.
It uses Llama 3 on Groq's LPUs for near-instant JSON classification.
"""

import json
import logging
import httpx
from core.config import get_settings
from schemas.classification import MessageClassification
from core.ollama_client import CLASSIFY_SYSTEM_PROMPT, _sanitize_for_llm

logger = logging.getLogger("go_chicken.groq")
settings = get_settings()

async def classify_message(message: str) -> MessageClassification | None:
    """Classify a WhatsApp message using Groq Cloud API."""
    if not settings.GROQ_API_KEY:
        logger.error("🤖 GROQ_API_KEY is not set. Cannot use Groq Provider.")
        return None

    safe_message = _sanitize_for_llm(message)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-8b-8192",  # Fast and extremely cheap/free
                    "messages": [
                        {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                        {"role": "user", "content": f'Classify this WhatsApp message:\n"{safe_message}"'}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.0
                },
                timeout=10.0
            )

        if response.status_code != 200:
            logger.error(f"Groq API error: {response.text}")
            return None
            
        data = response.json()
        raw_json = data["choices"][0]["message"]["content"]
        
        parsed = json.loads(raw_json)
        return MessageClassification(**parsed)

    except json.JSONDecodeError as e:
        logger.error(f"Groq returned invalid JSON: {e} - Raw: {raw_json}")
        return None
    except Exception as e:
        logger.error(f"Groq classification failed: {e}")
        return None
