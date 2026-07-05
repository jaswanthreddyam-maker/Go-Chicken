"""Pydantic schema for Ollama intent classification results."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class MessageClassification(BaseModel):
    """Structured output from Ollama's message intent classifier.

    Ollama is prompted to return raw JSON matching this schema.
    If it can't classify, it returns intent="INQUIRY" with confidence=0.

    Example successful classification:
        {"intent": "ORDER", "item": "Live Bird", "quantity_kg": 50.0, "confidence": 0.95}

    Example unknown message:
        {"intent": "INQUIRY", "item": null, "quantity_kg": null, "confidence": 0.0}
    """

    intent: Literal["ORDER", "INQUIRY", "GREETING"] = Field(
        ...,
        description="Classified intent of the WhatsApp message",
    )
    item: Optional[str] = Field(
        None,
        description="Poultry item type: 'Live Bird', 'Dressed', or 'Skinless'",
    )
    quantity_kg: Optional[float] = Field(
        None,
        description="Extracted quantity in kilograms",
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Classification confidence score (0.0 to 1.0)",
    )
