"""Tests for Ollama classification service and WhatsApp fallback logic.

Tests cover:
  1. ollama_client.py — classify_message() and _parse_classification_json()
  2. whatsapp.py — _handle_text_message() with Ollama → regex fallback
"""

import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import uuid
import models

from core.ollama_client import classify_message, _parse_classification_json
from schemas.classification import MessageClassification


# ════════════════════════════════════════════════════════════════
# 1. Unit Tests: _parse_classification_json (internal JSON parser)
# ════════════════════════════════════════════════════════════════


class TestParseClassificationJson:
    """Test the JSON extraction from various LLM response formats."""

    def test_clean_json(self):
        """Model returns perfect JSON — happy path."""
        raw = '{"intent": "ORDER", "item": "Live Bird", "quantity_kg": 50.0, "confidence": 0.95}'
        result = _parse_classification_json(raw)
        assert result is not None
        assert result.intent == "ORDER"
        assert result.item == "Live Bird"
        assert result.quantity_kg == 50.0
        assert result.confidence == 0.95

    def test_json_with_markdown_fences(self):
        """Model wraps JSON in ```json ... ``` — common LLM quirk."""
        raw = '```json\n{"intent": "ORDER", "item": "Dressed", "quantity_kg": 30.0, "confidence": 0.88}\n```'
        result = _parse_classification_json(raw)
        assert result is not None
        assert result.intent == "ORDER"
        assert result.item == "Dressed"
        assert result.quantity_kg == 30.0

    def test_json_with_preamble(self):
        """Model adds chatty preamble before JSON — 'Sure! Here is...'"""
        raw = 'Sure! Here is the classification:\n{"intent": "PRICE_INQUIRY", "item": null, "quantity_kg": null, "confidence": 0.72}'
        result = _parse_classification_json(raw)
        assert result is not None
        assert result.intent == "PRICE_INQUIRY"
        assert result.item is None
        assert result.quantity_kg is None

    def test_greeting_classification(self):
        """Model classifies a greeting correctly."""
        raw = '{"intent": "GREETING", "item": null, "quantity_kg": null, "confidence": 0.99}'
        result = _parse_classification_json(raw)
        assert result is not None
        assert result.intent == "GREETING"
        assert result.confidence == 0.99

    def test_empty_response(self):
        """Model returns empty string — should return None."""
        result = _parse_classification_json("")
        assert result is None

    def test_no_json_at_all(self):
        """Model returns pure text with no JSON — should return None."""
        result = _parse_classification_json("I'm sorry, I cannot process that message.")
        assert result is None

    def test_invalid_json(self):
        """Model returns malformed JSON — should return None."""
        result = _parse_classification_json('{"intent": "ORDER", "item": }')
        assert result is None

    def test_wrong_schema(self):
        """Model returns valid JSON but wrong keys — Pydantic should reject."""
        raw = '{"type": "order", "product": "chicken", "kg": 50}'
        result = _parse_classification_json(raw)
        # This should fail Pydantic validation because 'intent' is required
        assert result is None

    def test_invalid_intent_value(self):
        """Model returns an intent not in the Literal — Pydantic should reject."""
        raw = '{"intent": "COMPLAINT", "item": null, "quantity_kg": null, "confidence": 0.5}'
        result = _parse_classification_json(raw)
        assert result is None

    def test_confidence_out_of_range(self):
        """Model returns confidence > 1.0 — Pydantic should reject."""
        raw = '{"intent": "ORDER", "item": "Live Bird", "quantity_kg": 50, "confidence": 1.5}'
        result = _parse_classification_json(raw)
        assert result is None

    def test_json_with_backticks_only(self):
        """Model wraps in plain backticks (no json label)."""
        raw = '```\n{"intent": "ORDER", "item": "Skinless", "quantity_kg": 25.0, "confidence": 0.91}\n```'
        result = _parse_classification_json(raw)
        assert result is not None
        assert result.item == "Skinless"


# ════════════════════════════════════════════════════════════════
# 2. Unit Tests: classify_message() — full Ollama HTTP flow
# ════════════════════════════════════════════════════════════════


class TestClassifyMessage:
    """Test classify_message with mocked httpx responses."""

    @pytest.fixture(autouse=True)
    def mock_ollama_available(self):
        with patch("core.ollama_client.is_ollama_available", new_callable=AsyncMock, return_value=True):
            yield

    @pytest.mark.asyncio
    async def test_successful_classification(self):
        """Ollama returns a valid ORDER classification."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"intent": "ORDER", "item": "Live Bird", "quantity_kg": 50.0, "confidence": 0.95}'
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await classify_message("50kg live bird chahiye")

        assert result is not None
        assert result.intent == "ORDER"
        assert result.item == "Live Bird"
        assert result.quantity_kg == 50.0
        assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_ollama_connection_error(self):
        """Ollama is not running — should return None, not crash."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await classify_message("50kg live bird")

        assert result is None

    @pytest.mark.asyncio
    async def test_ollama_timeout(self):
        """Ollama takes too long — should return None, not crash."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await classify_message("30kg dressed chicken")

        assert result is None

    @pytest.mark.asyncio
    async def test_ollama_http_error(self):
        """Ollama returns 500 — should return None, not crash."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await classify_message("50kg live bird")

        assert result is None

    @pytest.mark.asyncio
    async def test_ollama_empty_response(self):
        """Ollama returns empty response text — should return None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": ""}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await classify_message("hello")

        assert result is None

    @pytest.mark.asyncio
    async def test_ollama_garbage_response(self):
        """Ollama returns non-JSON garbage — should return None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "I'm a helpful AI assistant and I'd be happy to help you!"
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.ollama_client.httpx.AsyncClient", return_value=mock_client):
            result = await classify_message("tell me about chicken")

        assert result is None


# ════════════════════════════════════════════════════════════════
# 3. Unit Tests: Regex parsers (_parse_quantity, _parse_item_type)
# ════════════════════════════════════════════════════════════════


class TestRegexParsers:
    """Test the regex fallback parsers in whatsapp.py."""

    def test_parse_quantity_simple(self):
        from routers.whatsapp import _parse_quantity
        assert _parse_quantity("50kg live bird") == Decimal("50")

    def test_parse_quantity_with_decimal(self):
        from routers.whatsapp import _parse_quantity
        assert _parse_quantity("25.5kg dressed") == Decimal("25.5")

    def test_parse_quantity_with_space(self):
        from routers.whatsapp import _parse_quantity
        assert _parse_quantity("30 kg chicken") == Decimal("30")

    def test_parse_quantity_no_match(self):
        from routers.whatsapp import _parse_quantity
        assert _parse_quantity("hello, what's the price?") == Decimal("0")

    def test_parse_quantity_uppercase(self):
        from routers.whatsapp import _parse_quantity
        assert _parse_quantity("50KG LIVE BIRD") == Decimal("50")

    def test_parse_item_type_live_bird(self):
        from routers.whatsapp import _parse_item_type
        assert _parse_item_type("50kg live bird") == "Live Bird"

    def test_parse_item_type_dressed(self):
        from routers.whatsapp import _parse_item_type
        assert _parse_item_type("30kg dressed chicken") == "Dressed"

    def test_parse_item_type_skinless(self):
        from routers.whatsapp import _parse_item_type
        assert _parse_item_type("20kg skinless") == "Skinless"

    def test_parse_item_type_default(self):
        from routers.whatsapp import _parse_item_type
        assert _parse_item_type("50kg") == "Live Bird"


# ════════════════════════════════════════════════════════════════
# 4. Integration Tests: _handle_text_message fallback pipeline
# ════════════════════════════════════════════════════════════════


class TestMessageClassificationSchema:
    """Test the Pydantic schema validation directly."""

    def test_valid_order(self):
        mc = MessageClassification(
            intent="ORDER", item="Live Bird", quantity_kg=50.0, confidence=0.95
        )
        assert mc.intent == "ORDER"

    def test_valid_inquiry(self):
        mc = MessageClassification(
            intent="PRICE_INQUIRY", item=None, quantity_kg=None, confidence=0.0
        )
        assert mc.intent == "PRICE_INQUIRY"

    def test_invalid_intent_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MessageClassification(
                intent="COMPLAINT", item=None, quantity_kg=None, confidence=0.5
            )

    def test_confidence_too_high_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MessageClassification(
                intent="ORDER", item="Live Bird", quantity_kg=50, confidence=1.5
            )

    def test_confidence_negative_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MessageClassification(
                intent="ORDER", item="Live Bird", quantity_kg=50, confidence=-0.1
            )

    def test_defaults(self):
        mc = MessageClassification(intent="GREETING")
        assert mc.item is None
        assert mc.quantity_kg is None
        assert mc.confidence == 0.0


# ════════════════════════════════════════════════════════════════
# 7. Schema Tests: Analytics Pydantic models
# ════════════════════════════════════════════════════════════════


class TestAnalyticsSchemas:
    """Test the analytics response schemas."""

    def test_source_breakdown_defaults(self):
        from schemas.analytics import SourceBreakdown
        sb = SourceBreakdown()
        assert sb.ollama_count == 0
        assert sb.regex_count == 0
        assert sb.total == 0
        assert sb.ollama_hit_rate_pct == 0.0

    def test_source_breakdown_with_data(self):
        from schemas.analytics import SourceBreakdown
        sb = SourceBreakdown(
            ollama_count=75, regex_count=25, total=100, ollama_hit_rate_pct=75.0
        )
        assert sb.ollama_hit_rate_pct == 75.0

    def test_confidence_stats_defaults(self):
        from schemas.analytics import ConfidenceStats
        cs = ConfidenceStats()
        assert cs.avg_confidence == 0.0
        assert cs.low_confidence_count == 0

    def test_latency_stats_defaults(self):
        from schemas.analytics import LatencyStats
        ls = LatencyStats()
        assert ls.avg_ms == 0.0
        assert ls.p50_ms == 0.0
        assert ls.p95_ms == 0.0

    def test_full_classification_stats(self):
        from schemas.analytics import (
            ClassificationStats, SourceBreakdown,
            ConfidenceStats, LatencyStats, IntentBreakdown,
        )
        stats = ClassificationStats(
            source_breakdown=SourceBreakdown(
                ollama_count=80, regex_count=20, total=100, ollama_hit_rate_pct=80.0
            ),
            confidence_stats=ConfidenceStats(
                avg_confidence=0.85, min_confidence=0.3, max_confidence=0.99,
                low_confidence_count=5,
            ),
            latency_stats=LatencyStats(
                avg_ms=320.5, p50_ms=280.0, p95_ms=890.0, max_ms=1200.0
            ),
            intent_breakdown=IntentBreakdown(
                order_count=60, inquiry_count=25, greeting_count=10, failed_count=5
            ),
            current_threshold=0.6,
        )
        assert stats.source_breakdown.ollama_hit_rate_pct == 80.0
        assert stats.latency_stats.p95_ms == 890.0
        assert stats.current_threshold == 0.6

