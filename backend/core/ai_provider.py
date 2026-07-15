"""AI Provider abstraction.

Wraps the existing Ollama client and the new Groq client behind a unified interface.
Which provider is used is controlled by the AI_PROVIDER environment variable.
"""

import logging
from core.config import get_settings
from schemas.classification import MessageClassification

# Import providers
from core import ollama_client
from core import groq_provider

logger = logging.getLogger("go_chicken.ai_provider")
settings = get_settings()

async def classify_message(message: str) -> MessageClassification | None:
    """Classify a message using the configured AI provider."""
    provider = settings.AI_PROVIDER.lower().strip()
    
    if provider == "groq":
        return await groq_provider.classify_message(message)
    elif provider == "ollama":
        return await ollama_client.classify_message(message)
    else:
        logger.error(f"Unknown AI_PROVIDER '{provider}'. Falling back to Ollama.")
        return await ollama_client.classify_message(message)
