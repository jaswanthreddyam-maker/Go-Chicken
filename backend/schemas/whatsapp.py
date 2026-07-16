"""Pydantic schemas for Meta WhatsApp Cloud API webhook payloads.

Meta's webhook JSON is deeply nested. These models provide strict
type-safety so we never have to blindly dig through raw dicts.

Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components
"""

from typing import Optional
from pydantic import BaseModel, Field


# ── Incoming Message Models ────────────────────────────────────


class WhatsAppProfile(BaseModel):
    """Sender's WhatsApp profile."""
    name: str


class WhatsAppContact(BaseModel):
    """Contact info attached to an incoming message."""
    profile: Optional[WhatsAppProfile] = None
    wa_id: str  # WhatsApp ID (usually the phone number)


class WhatsAppMessage(BaseModel):
    """A single incoming message from a user."""
    from_: str = Field(..., alias="from")  # Sender's phone number
    id: str                                 # Message ID (for read receipts)
    timestamp: str                          # Unix timestamp as string
    type: str                               # "text", "image", "interactive", etc.
    text: Optional[dict] = None             # {"body": "50kg live bird"}
    interactive: Optional[dict] = None      # {"type": "button_reply", "button_reply": {"id": "...", "title": "..."}}


class WhatsAppStatus(BaseModel):
    """Delivery status update for a sent message."""
    id: str
    status: str         # "sent", "delivered", "read", "failed"
    timestamp: str
    recipient_id: str


class WhatsAppMetadata(BaseModel):
    """Metadata about the WhatsApp Business Account."""
    display_phone_number: str
    phone_number_id: str


class WhatsAppValue(BaseModel):
    """The 'value' block inside each change entry."""
    messaging_product: str  # Always "whatsapp"
    metadata: WhatsAppMetadata
    contacts: Optional[list[WhatsAppContact]] = None
    messages: Optional[list[WhatsAppMessage]] = None
    statuses: Optional[list[WhatsAppStatus]] = None


class WhatsAppChange(BaseModel):
    """A single change entry in the webhook payload."""
    field: str  # "messages" for incoming messages
    value: WhatsAppValue


class WhatsAppEntry(BaseModel):
    """Top-level entry — one per WhatsApp Business Account."""
    id: str       # WhatsApp Business Account ID
    changes: list[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    """Root model for the entire Meta webhook POST body.

    Example payload from Meta:
    {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "...", "phone_number_id": "..."},
                    "contacts": [{"profile": {"name": "Retailer"}, "wa_id": "919876543210"}],
                    "messages": [{"from": "919876543210", "id": "wamid.xxx", "timestamp": "...", "type": "text", "text": {"body": "50kg live bird"}}]
                },
                "field": "messages"
            }]
        }]
    }
    """
    object: str  # "whatsapp_business_account"
    entry: list[WhatsAppEntry]
