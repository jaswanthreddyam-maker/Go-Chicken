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
        raw = 'Sure! Here is the classification:\n{"intent": "INQUIRY", "item": null, "quantity_kg": null, "confidence": 0.72}'
        result = _parse_classification_json(raw)
        assert result is not None
        assert result.intent == "INQUIRY"
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


class TestHandleTextMessageFallback:
    """Test the Ollama → regex fallback pipeline in _handle_text_message.

    NOTE: _log_classification is patched in all tests because it opens
    its own AsyncSessionLocal, separate from the Order creation session.
    """

    @pytest.fixture(autouse=True)
    def mock_ollama_available(self):
        with patch("core.ollama_client.is_ollama_available", new_callable=AsyncMock, return_value=True):
            yield

    @pytest.fixture(autouse=True)
    def mock_whatsapp_replies(self):
        with patch("routers.whatsapp._send_whatsapp_interactive_reply", new_callable=AsyncMock), \
             patch("routers.whatsapp._send_whatsapp_reply", new_callable=AsyncMock):
            yield

    def _setup_mock_db(self, mock_db):
        mock_retailer = MagicMock()
        mock_retailer.id = uuid.uuid4()
        mock_retailer.tenant_id = uuid.uuid4()
        mock_retailer.name = "Test Retailer"

        mock_txn = MagicMock()
        mock_txn.balance_after = Decimal("5000.00")

        def side_effect_execute(*args, **kwargs):
            mock_res = MagicMock()
            mock_res.scalars.return_value.all.return_value = []
            query_str = str(args[0])
            if "pricing" in query_str or "ProductPrice" in query_str or "price" in query_str or "product_prices" in query_str:
                mock_p1 = MagicMock(item_type="Live Bird", price_per_kg=Decimal("180.00"))
                mock_p2 = MagicMock(item_type="Dressed", price_per_kg=Decimal("250.00"))
                mock_p3 = MagicMock(item_type="Skinless", price_per_kg=Decimal("320.00"))
                mock_res.scalars.return_value.all.return_value = [mock_p1, mock_p2, mock_p3]
            elif "users" in query_str or "User" in query_str:
                mock_res.scalar_one_or_none.return_value = mock_retailer
            elif "khata" in query_str or "Khata" in query_str:
                mock_res.scalar_one_or_none.return_value = mock_txn
            else:
                mock_res.scalar_one_or_none.return_value = None
            return mock_res

        mock_db.execute = AsyncMock(side_effect=side_effect_execute)

    @pytest.mark.asyncio
    async def test_ollama_success_creates_order_with_ollama_source(self):
        """When Ollama classifies ORDER with high confidence, order_source = 'ollama'."""
        mock_classification = MessageClassification(
            intent="ORDER",
            item="Dressed",
            quantity_kg=30.0,
            confidence=0.92,
        )

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        self._setup_mock_db(mock_db)

        # Capture what Order was created
        created_orders = []

        def capture_add(order):
            created_orders.append(order)

        mock_db.add = capture_add

        with patch("routers.whatsapp.classify_message", return_value=mock_classification), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock) as mock_log:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="30kg dressed chicken chahiye",
                phone_number_id="12345",
            )

        assert len(created_orders) == 1
        order = created_orders[0]
        assert order.order_source == "ollama"
        assert order.item_type == "Dressed"
        assert order.quantity_kg == Decimal("30.0")

        # Verify classification was logged
        mock_log.assert_called_once()
        log_kwargs = mock_log.call_args
        assert log_kwargs[1]["order_source"] == "ollama"
        assert log_kwargs[1]["intent"] == "ORDER"
        assert log_kwargs[1]["confidence"] == 0.92

    @pytest.mark.asyncio
    async def test_ollama_fails_falls_back_to_regex(self):
        """When Ollama returns None, regex fallback kicks in. order_source = 'regex'."""
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        self._setup_mock_db(mock_db)

        created_orders = []

        def capture_add(order):
            created_orders.append(order)

        mock_db.add = capture_add

        with patch("routers.whatsapp.classify_message", return_value=None), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock) as mock_log:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="50kg live bird",
                phone_number_id="12345",
            )

        assert len(created_orders) == 1
        order = created_orders[0]
        assert order.order_source == "regex"
        assert order.quantity_kg == Decimal("50")
        assert order.item_type == "Live Bird"

        # Verify fallback was logged
        mock_log.assert_called_once()
        assert mock_log.call_args[1]["order_source"] == "regex"

    @pytest.mark.asyncio
    async def test_ollama_low_confidence_falls_back_to_regex(self):
        """When Ollama confidence < threshold, regex takes over."""
        low_confidence_classification = MessageClassification(
            intent="ORDER",
            item="Live Bird",
            quantity_kg=50.0,
            confidence=0.3,  # Below the 0.6 threshold
        )

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        self._setup_mock_db(mock_db)

        created_orders = []

        def capture_add(order):
            created_orders.append(order)

        mock_db.add = capture_add

        with patch("routers.whatsapp.classify_message", return_value=low_confidence_classification), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock) as mock_log:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="50kg skinless",
                phone_number_id="12345",
            )

        assert len(created_orders) == 1
        order = created_orders[0]
        assert order.order_source == "regex"
        assert order.item_type == "Skinless"

        # Low confidence should still be logged with original confidence
        mock_log.assert_called_once()
        assert mock_log.call_args[1]["confidence"] == 0.3
        assert mock_log.call_args[1]["order_source"] == "regex"

    @pytest.mark.asyncio
    async def test_greeting_does_not_create_order(self):
        """When Ollama classifies GREETING, no order is created."""
        greeting_classification = MessageClassification(
            intent="GREETING",
            item=None,
            quantity_kg=None,
            confidence=0.98,
        )

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        created_orders = []

        def capture_add(order):
            created_orders.append(order)

        mock_db.add = capture_add

        with patch("routers.whatsapp.classify_message", return_value=greeting_classification), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock) as mock_log:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="Good morning bhai",
                phone_number_id="12345",
            )

        assert len(created_orders) == 0

        # GREETING should still be logged (early return path)
        mock_log.assert_called_once()
        assert mock_log.call_args[1]["intent"] == "GREETING"
        assert mock_log.call_args[1]["order_source"] == "ollama"

    @pytest.mark.asyncio
    async def test_inquiry_does_not_create_order(self):
        """When Ollama classifies INQUIRY, no order is created."""
        inquiry_classification = MessageClassification(
            intent="INQUIRY",
            item=None,
            quantity_kg=None,
            confidence=0.85,
        )

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        self._setup_mock_db(mock_db)

        created_orders = []

        def capture_add(order):
            created_orders.append(order)

        mock_db.add = capture_add

        with patch("routers.whatsapp.classify_message", return_value=inquiry_classification), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock) as mock_log:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="Aaj ka rate kya hai?",
                phone_number_id="12345",
            )

        assert len(created_orders) == 0

        # INQUIRY should still be logged
        mock_log.assert_called_once()
        assert mock_log.call_args[1]["intent"] == "INQUIRY"

    @pytest.mark.asyncio
    async def test_no_quantity_from_either_method(self):
        """When both Ollama and regex can't parse quantity, no order is created."""
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        self._setup_mock_db(mock_db)

        created_orders = []

        def capture_add(order):
            created_orders.append(order)

        mock_db.add = capture_add

        with patch("routers.whatsapp.classify_message", return_value=None), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock) as mock_log:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="kuch nahi bas bol raha tha",
                phone_number_id="12345",
            )

        assert len(created_orders) == 0

        # Even failed classifications should be logged
        mock_log.assert_called_once()
        assert mock_log.call_args[1]["intent"] is None
        assert mock_log.call_args[1]["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_latency_is_measured(self):
        """Verify latency_ms is captured and passed to classification log."""
        mock_classification = MessageClassification(
            intent="ORDER",
            item="Live Bird",
            quantity_kg=25.0,
            confidence=0.88,
        )

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        self._setup_mock_db(mock_db)

        with patch("routers.whatsapp.classify_message", return_value=mock_classification), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock) as mock_log:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="25kg live bird",
                phone_number_id="12345",
            )

        # latency_ms should be an integer >= 0
        mock_log.assert_called_once()
        latency = mock_log.call_args[1]["latency_ms"]
        assert isinstance(latency, int)
        assert latency >= 0


# ════════════════════════════════════════════════════════════════
# 5. Unit Tests: _log_classification helper
# ════════════════════════════════════════════════════════════════


class TestLogClassification:
    """Test the _log_classification helper that persists to DB."""

    @pytest.mark.asyncio
    async def test_log_persists_to_db(self):
        """Classification log entry is created and committed."""
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        captured_args = {}
        mock_log_cls = MagicMock()

        def capture_constructor(**kwargs):
            captured_args.update(kwargs)
            return mock_log_cls

        with patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp.ClassificationLog", side_effect=capture_constructor):
            from routers.whatsapp import _log_classification
            await _log_classification(
                message="50kg live bird order from Hyderabad",
                intent="ORDER",
                confidence=0.92,
                order_source="ollama",
                latency_ms=450,
            )

        assert captured_args["message_snippet"] == "50kg live bird order from Hyderabad"
        assert captured_args["intent"] == "ORDER"
        assert captured_args["confidence"] == 0.92
        assert captured_args["order_source"] == "ollama"
        assert captured_args["latency_ms"] == 450
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_truncates_long_messages(self):
        """Messages longer than 100 chars are truncated for privacy."""
        long_message = "x" * 200

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        captured_args = {}

        def capture_constructor(**kwargs):
            captured_args.update(kwargs)
            return MagicMock()

        with patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp.ClassificationLog", side_effect=capture_constructor):
            from routers.whatsapp import _log_classification
            await _log_classification(
                message=long_message,
                intent="INQUIRY",
                confidence=0.7,
                order_source="ollama",
                latency_ms=200,
            )

        assert len(captured_args["message_snippet"]) == 100

    @pytest.mark.asyncio
    async def test_log_failure_does_not_crash_pipeline(self):
        """If classification logging fails, it should NOT raise — just warn."""
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock(side_effect=Exception("DB connection lost"))
        mock_db.add = MagicMock()

        with patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp.ClassificationLog", return_value=MagicMock()):
            from routers.whatsapp import _log_classification
            # This should NOT raise even though commit fails
            await _log_classification(
                message="50kg live bird",
                intent="ORDER",
                confidence=0.9,
                order_source="ollama",
                latency_ms=300,
            )
        # If we get here without exception, the test passes


# ════════════════════════════════════════════════════════════════
# 6. Schema Tests: MessageClassification Pydantic model
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
            intent="INQUIRY", item=None, quantity_kg=None, confidence=0.0
        )
        assert mc.intent == "INQUIRY"

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

