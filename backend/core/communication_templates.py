"""PR 8 Centralized Template Registry & Strict Rendering Engine (ADR 0009)."""

import string
from dataclasses import dataclass
from typing import Dict, Any, Optional


class TemplateRenderingError(Exception):
    """Raised when rendering a template fails due to missing context variables or invalid syntax."""
    pass


@dataclass(frozen=True)
class CommunicationTemplate:
    """Immutable template definition for a specific communication channel."""
    template_id: str
    channel: str
    body_template: str
    subject_template: Optional[str] = None

    def render(self, context: Dict[str, Any]) -> str:
        """Render template body with context, raising TemplateRenderingError if variables are missing."""
        formatter = string.Formatter()
        required_keys = {
            field_name
            for _, field_name, _, _ in formatter.parse(self.body_template)
            if field_name is not None
        }

        missing_keys = required_keys - context.keys()
        if missing_keys:
            raise TemplateRenderingError(
                f"Missing required context variables for template '{self.template_id}' ({self.channel}): {sorted(missing_keys)}"
            )

        try:
            return self.body_template.format_map(context)
        except Exception as e:
            raise TemplateRenderingError(f"Error rendering template '{self.template_id}': {e}") from e


class TemplateRegistry:
    """Registry managing structured templates decoupled from domain event consumers."""

    def __init__(self) -> None:
        self._templates: Dict[tuple[str, str], CommunicationTemplate] = {}

    def register(self, template: CommunicationTemplate) -> None:
        key = (template.template_id.upper(), template.channel.upper())
        self._templates[key] = template

    def resolve(self, template_id: str, channel: str = "WHATSAPP") -> CommunicationTemplate:
        key = (template_id.upper(), channel.upper())
        if key not in self._templates:
            raise KeyError(f"Template '{template_id}' not found for channel '{channel}'")
        return self._templates[key]


# Global default template registry instance populated with Go Chicken enterprise templates
default_template_registry = TemplateRegistry()

# 1. ORDER_CONFIRMED
default_template_registry.register(
    CommunicationTemplate(
        template_id="ORDER_CONFIRMED",
        channel="WHATSAPP",
        body_template="Chicken order #{order_number} confirmed! Qty: {quantity_kg}kg at ₹{unit_price}/kg. Total: ₹{total_amount}.",
    )
)
default_template_registry.register(
    CommunicationTemplate(
        template_id="ORDER_CONFIRMED",
        channel="SMS",
        body_template="Order #{order_number} confirmed ({quantity_kg}kg, Total ₹{total_amount}).",
    )
)

# 2. ORDER_LOADED
default_template_registry.register(
    CommunicationTemplate(
        template_id="ORDER_LOADED",
        channel="WHATSAPP",
        body_template="Order #{order_number} has been loaded onto transport truck {truck_id}. Dispatching soon.",
    )
)

# 3. ORDER_OUT_FOR_DELIVERY
default_template_registry.register(
    CommunicationTemplate(
        template_id="ORDER_OUT_FOR_DELIVERY",
        channel="WHATSAPP",
        body_template="Truck {truck_id} is en route with order #{order_number} ({quantity_kg}kg). ETA: {eta}.",
    )
)

# 4. ORDER_DELIVERED
default_template_registry.register(
    CommunicationTemplate(
        template_id="ORDER_DELIVERED",
        channel="WHATSAPP",
        body_template="Order #{order_number} delivered successfully! Delivered qty: {delivered_kg}kg.",
    )
)

# 5. INVOICE_GENERATED
default_template_registry.register(
    CommunicationTemplate(
        template_id="INVOICE_GENERATED",
        channel="WHATSAPP",
        body_template="Invoice generated for Order #{order_number}. Total amount payable: ₹{total_amount}. Khata ledger updated.",
    )
)

# 6. PAYMENT_RECEIVED
default_template_registry.register(
    CommunicationTemplate(
        template_id="PAYMENT_RECEIVED",
        channel="WHATSAPP",
        body_template="Payment received: ₹{payment_amount}. Outstanding balance remaining: ₹{outstanding_balance}.",
    )
)

# 7. PAYMENT_OVERDUE
default_template_registry.register(
    CommunicationTemplate(
        template_id="PAYMENT_OVERDUE",
        channel="WHATSAPP",
        body_template="URGENT: Outstanding balance of ₹{outstanding_balance} is overdue. Please settle to avoid supply hold.",
    )
)
