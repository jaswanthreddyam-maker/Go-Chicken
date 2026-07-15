"""PR 8 Abstract Communication Provider Interface & Implementations (ADR 0008)."""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


class UnsupportedChannelError(Exception):
    """Raised when attempting to dispatch via an unregistered or unsupported communication channel."""
    pass


@dataclass(frozen=True)
class ProviderDeliveryResult:
    """Standardized delivery result returned by any CommunicationProvider."""
    success: bool
    status: str  # QUEUED, SENT, DELIVERED, FAILED
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None


class CommunicationProvider(ABC):
    """Abstract interface for all multi-channel communication providers."""

    @property
    @abstractmethod
    def channel(self) -> str:
        """Return canonical channel identifier (e.g., 'WHATSAPP', 'SMS')."""
        pass

    @abstractmethod
    async def send(
        self,
        recipient: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> ProviderDeliveryResult:
        """Dispatch message payload asynchronously via vendor API."""
        pass


class WhatsAppProvider(CommunicationProvider):
    """Meta Cloud API / WhatsApp provider implementation."""

    def __init__(self, fail_simulation: bool = False, error_msg: Optional[str] = None) -> None:
        self.fail_simulation = fail_simulation
        self.error_msg = error_msg
        self.sent_messages: list[Dict[str, Any]] = []

    @property
    def channel(self) -> str:
        return "WHATSAPP"

    async def send(
        self,
        recipient: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> ProviderDeliveryResult:
        if self.fail_simulation:
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message=self.error_msg or "WhatsApp Cloud API Network Timeout",
            )

        msg_id = f"wa-{uuid.uuid4()}"
        self.sent_messages.append({
            "recipient": recipient,
            "content": content,
            "metadata": metadata,
            "message_id": msg_id,
        })
        return ProviderDeliveryResult(
            success=True,
            status="SENT",
            provider_message_id=msg_id,
        )


class SMSProvider(CommunicationProvider):
    """SMS channel provider implementation."""

    def __init__(self, fail_simulation: bool = False) -> None:
        self.fail_simulation = fail_simulation
        self.sent_messages: list[Dict[str, Any]] = []

    @property
    def channel(self) -> str:
        return "SMS"

    async def send(
        self,
        recipient: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> ProviderDeliveryResult:
        if self.fail_simulation:
            return ProviderDeliveryResult(
                success=False,
                status="FAILED",
                error_message="SMS Gateway Rejection",
            )

        msg_id = f"sms-{uuid.uuid4()}"
        self.sent_messages.append({
            "recipient": recipient,
            "content": content,
            "metadata": metadata,
            "message_id": msg_id,
        })
        return ProviderDeliveryResult(
            success=True,
            status="SENT",
            provider_message_id=msg_id,
        )


class ProviderRegistry:
    """Registry mapping channel names to runtime provider implementations."""

    def __init__(self) -> None:
        self._providers: Dict[str, CommunicationProvider] = {}

    def register(self, provider: CommunicationProvider) -> None:
        self._providers[provider.channel.upper()] = provider

    def resolve(self, channel: str) -> CommunicationProvider:
        chan_key = channel.upper()
        if chan_key not in self._providers:
            raise UnsupportedChannelError(f"Unsupported or unregistered communication channel '{channel}'")
        return self._providers[chan_key]
