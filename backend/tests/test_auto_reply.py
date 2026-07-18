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


