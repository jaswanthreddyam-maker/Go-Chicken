"""Tests for WhatsApp auto-reply system and pricing logic.

Tests cover:
  1. _send_whatsapp_reply() — Meta Graph API message sending
  2. _get_price_per_kg() — config-based pricing lookup
  3. Intent-based auto-replies — GREETING, INQUIRY, ORDER confirmation
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import httpx
import pytest
import models
from schemas.classification import MessageClassification


# ════════════════════════════════════════════════════════════════
# 1. Unit Tests: _get_price_per_kg
# ════════════════════════════════════════════════════════════════


class TestGetPricePerKg:
    """Test config-based pricing lookup."""

    def test_live_bird_price(self):
        from routers.whatsapp import _get_price_per_kg
        price = _get_price_per_kg("Live Bird")
        assert price == Decimal("180.0")

    def test_dressed_price(self):
        from routers.whatsapp import _get_price_per_kg
        price = _get_price_per_kg("Dressed")
        assert price == Decimal("250.0")

    def test_skinless_price(self):
        from routers.whatsapp import _get_price_per_kg
        price = _get_price_per_kg("Skinless")
        assert price == Decimal("320.0")

    def test_unknown_item_defaults_to_live_bird(self):
        from routers.whatsapp import _get_price_per_kg
        price = _get_price_per_kg("Unknown Item")
        assert price == Decimal("180.0")


# ════════════════════════════════════════════════════════════════
# 2. Unit Tests: _send_whatsapp_reply
# ════════════════════════════════════════════════════════════════


class TestSendWhatsAppReply:
    """Test the Meta Graph API message sender."""

    @pytest.mark.asyncio
    async def test_skips_when_token_not_configured(self):
        """When WHATSAPP_API_TOKEN is placeholder, skip silently."""
        with patch("routers.whatsapp.settings") as mock_settings:
            mock_settings.WHATSAPP_API_TOKEN = "your_meta_graph_api_token_here"

            from routers.whatsapp import _send_whatsapp_reply
            # Should not raise, just log a warning
            await _send_whatsapp_reply(
                phone_number_id="12345",
                to="+919876543210",
                message="Test message",
            )
            # If we got here without error, the test passes

    @pytest.mark.asyncio
    async def test_skips_when_token_empty(self):
        """When WHATSAPP_API_TOKEN is empty string, skip silently."""
        with patch("routers.whatsapp.settings") as mock_settings:
            mock_settings.WHATSAPP_API_TOKEN = ""

            from routers.whatsapp import _send_whatsapp_reply
            await _send_whatsapp_reply(
                phone_number_id="12345",
                to="+919876543210",
                message="Test message",
            )

    @pytest.mark.asyncio
    async def test_sends_correct_payload_to_meta_api(self):
        """When token is configured, send correct JSON to Graph API."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("routers.whatsapp.settings") as mock_settings, \
             patch("routers.whatsapp.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WHATSAPP_API_TOKEN = "real_token_here"

            from routers.whatsapp import _send_whatsapp_reply
            await _send_whatsapp_reply(
                phone_number_id="12345",
                to="+919876543210",
                message="Hello from Go Chicken!",
            )

        # Verify the API call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args

        # Check URL
        assert "graph.facebook.com" in call_args[0][0]
        assert "12345" in call_args[0][0]

        # Check headers
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer real_token_here"

        # Check payload
        payload = call_args[1]["json"]
        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == "+919876543210"
        assert payload["type"] == "text"
        assert payload["text"]["body"] == "Hello from Go Chicken!"

    @pytest.mark.asyncio
    async def test_handles_http_error_gracefully(self):
        """Meta API returns 401 — should log error, not crash."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid OAuth access token"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("routers.whatsapp.settings") as mock_settings, \
             patch("routers.whatsapp.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WHATSAPP_API_TOKEN = "expired_token"

            from routers.whatsapp import _send_whatsapp_reply
            # Should NOT raise
            await _send_whatsapp_reply(
                phone_number_id="12345",
                to="+919876543210",
                message="Test",
            )

    @pytest.mark.asyncio
    async def test_handles_timeout_gracefully(self):
        """Meta API times out — should log error, not crash."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("routers.whatsapp.settings") as mock_settings, \
             patch("routers.whatsapp.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WHATSAPP_API_TOKEN = "valid_token"

            from routers.whatsapp import _send_whatsapp_reply
            await _send_whatsapp_reply(
                phone_number_id="12345",
                to="+919876543210",
                message="Test",
            )


# ════════════════════════════════════════════════════════════════
# 3. Integration Tests: Auto-reply in the pipeline
# ════════════════════════════════════════════════════════════════


class TestAutoReplies:
    """Test that the correct auto-reply is sent for each intent."""

    @pytest.mark.asyncio
    async def test_greeting_sends_welcome_message(self):
        """GREETING intent should trigger a welcome reply."""
        greeting_classification = MessageClassification(
            intent="GREETING", item=None, quantity_kg=None, confidence=0.98,
        )

        with patch("routers.whatsapp.classify_message", return_value=greeting_classification), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock), \
             patch("routers.whatsapp._send_whatsapp_reply", new_callable=AsyncMock) as mock_reply:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Ramesh",
                message_body="Good morning",
                phone_number_id="12345",
            )

        mock_reply.assert_called_once()
        call_kwargs = mock_reply.call_args[1]
        assert call_kwargs["to"] == "+919876543210"
        assert call_kwargs["phone_number_id"] == "12345"
        assert "Welcome" in call_kwargs["message"]
        assert "Ramesh" in call_kwargs["message"]
        assert "Go Chicken" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_inquiry_sends_pricing(self):
        """INQUIRY intent should send current pricing."""
        inquiry_classification = MessageClassification(
            intent="INQUIRY", item=None, quantity_kg=None, confidence=0.85,
        )
        mock_prices = {"Live Bird": Decimal("180"), "Dressed": Decimal("250"), "Skinless": Decimal("320")}

        with patch("routers.whatsapp.classify_message", return_value=inquiry_classification), \
             patch("routers.whatsapp.get_all_prices", new_callable=AsyncMock, return_value=mock_prices), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock), \
             patch("routers.whatsapp._send_whatsapp_reply", new_callable=AsyncMock) as mock_reply:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="Aaj ka rate kya hai?",
                phone_number_id="12345",
            )

        mock_reply.assert_called_once()
        reply_msg = mock_reply.call_args[1]["message"]
        assert "Live Bird" in reply_msg
        assert "Dressed" in reply_msg
        assert "Skinless" in reply_msg
        assert "₹180" in reply_msg
        assert "₹250" in reply_msg
        assert "₹320" in reply_msg

    @pytest.mark.asyncio
    async def test_order_sends_confirmation(self):
        """ORDER intent should send confirmation with item details and total."""
        order_classification = MessageClassification(
            intent="ORDER", item="Dressed", quantity_kg=30.0, confidence=0.92,
        )

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        mock_retailer = MagicMock()
        mock_retailer.id = uuid.uuid4()
        mock_retailer.tenant_id = uuid.uuid4()
        mock_retailer.name = "Test Retailer"

        mock_txn = MagicMock()
        mock_txn.balance_after = Decimal("12450.00")

        def side_effect_execute(*args, **kwargs):
            mock_res = MagicMock()
            query_str = str(args[0])
            if "users" in query_str or "User" in query_str:
                mock_res.scalar_one_or_none.return_value = mock_retailer
            elif "khata" in query_str or "Khata" in query_str:
                mock_res.scalar_one_or_none.return_value = mock_txn
            else:
                mock_res.scalar_one_or_none.return_value = None
            return mock_res

        mock_db.execute = AsyncMock(side_effect=side_effect_execute)

        with patch("routers.whatsapp.classify_message", return_value=order_classification), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock), \
             patch("routers.whatsapp._send_whatsapp_interactive_reply", new_callable=AsyncMock) as mock_reply:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="30kg dressed chicken",
                phone_number_id="12345",
            )

        mock_reply.assert_called_once()
        message_text = mock_reply.call_args[1]["message_text"]
        buttons = mock_reply.call_args[1]["buttons"]
        assert "Order Summary" in message_text
        assert "Dressed" in message_text
        assert "30" in message_text
        assert "₹250" in message_text   # price_per_kg for Dressed
        assert "₹7,500" in message_text or "7500" in message_text
        assert len(buttons) == 2
        assert buttons[0]["title"] == "Confirm Order"

    @pytest.mark.asyncio
    async def test_regex_fallback_order_also_sends_confirmation(self):
        """Regex-parsed order should also get a confirmation reply."""
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        mock_retailer = MagicMock()
        mock_retailer.id = uuid.uuid4()
        mock_retailer.tenant_id = uuid.uuid4()
        mock_retailer.name = "Test Retailer"

        mock_txn = MagicMock()
        mock_txn.balance_after = Decimal("5000.00")

        def side_effect_execute(*args, **kwargs):
            mock_res = MagicMock()
            query_str = str(args[0])
            if "users" in query_str or "User" in query_str:
                mock_res.scalar_one_or_none.return_value = mock_retailer
            elif "khata" in query_str or "Khata" in query_str:
                mock_res.scalar_one_or_none.return_value = mock_txn
            else:
                mock_res.scalar_one_or_none.return_value = None
            return mock_res

        mock_db.execute = AsyncMock(side_effect=side_effect_execute)

        with patch("routers.whatsapp.classify_message", return_value=None), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=mock_db), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock), \
             patch("routers.whatsapp._send_whatsapp_interactive_reply", new_callable=AsyncMock) as mock_reply:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="50kg skinless",
                phone_number_id="12345",
            )

        mock_reply.assert_called_once()
        message_text = mock_reply.call_args[1]["message_text"]
        assert "Order Summary" in message_text
        assert "Skinless" in message_text
        assert "50" in message_text
        assert "₹320" in message_text    # price_per_kg for Skinless
        assert "₹16,000" in message_text or "16000" in message_text

    @pytest.mark.asyncio
    async def test_unclassified_message_no_reply(self):
        """When neither Ollama nor regex can parse, no reply is sent."""
        with patch("routers.whatsapp.classify_message", return_value=None), \
             patch("routers.whatsapp.AsyncSessionLocal", return_value=MagicMock()), \
             patch("routers.whatsapp._log_classification", new_callable=AsyncMock), \
             patch("routers.whatsapp._send_whatsapp_reply", new_callable=AsyncMock) as mock_reply:
            from routers.whatsapp import _handle_text_message
            await _handle_text_message(
                sender_phone="+919876543210",
                sender_name="Test User",
                message_body="random gibberish",
                phone_number_id="12345",
            )

        mock_reply.assert_not_called()
