"""Order State Machine & SLA Service — pure domain transition validation and SLA monitoring."""

import logging
from decimal import Decimal
from typing import Optional, Tuple, Set, Dict
from uuid import UUID

logger = logging.getLogger("go_chicken.order_state_machine")


class OrderStateMachine:
    """Pure domain transition and invariant validator for Order lifecycle."""

    TERMINAL_STATES: Set[str] = {"delivered", "cancelled"}

    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"loaded", "cancelled"},
        "loaded": {"out_for_delivery", "cancelled"},
        "out_for_delivery": {"delivered"},
        "delivered": set(),
        "cancelled": set(),
    }

    @classmethod
    def can_transition(cls, current_status: str, target_status: str) -> bool:
        """Check if target_status is a valid destination from current_status."""
        clean_current = (current_status or "").strip().lower()
        clean_target = (target_status or "").strip().lower()
        return clean_target in cls.VALID_TRANSITIONS.get(clean_current, set())

    @classmethod
    def validate_transition(
        cls,
        current_status: str,
        target_status: str,
        quantity_kg: Decimal,
        truck_id: Optional[UUID] = None,
        payload: Optional[dict] = None,
    ) -> Tuple[bool, str]:
        """Validate domain invariants before permitting order status mutation.

        Returns:
            (is_valid, message)
        """
        payload = payload or {}
        clean_current = (current_status or "").strip().lower()
        clean_target = (target_status or "").strip().lower()

        # Terminal state check
        if clean_current in cls.TERMINAL_STATES:
            return (
                False,
                f"Order is in terminal state '{clean_current}' and cannot be modified.",
            )

        # Transition matrix check
        if not cls.can_transition(clean_current, clean_target):
            return (
                False,
                f"Invalid transition from '{clean_current}' to '{clean_target}'.",
            )

        # Invariant 1: Mandatory Truck Assignment for loaded / out_for_delivery
        effective_truck_id = payload.get("truck_id") or truck_id
        if clean_target in ("loaded", "out_for_delivery"):
            if not effective_truck_id:
                return (
                    False,
                    f"Cannot transition to '{clean_target}': No delivery truck assigned.",
                )

        # Invariant 2: Delivered Weight Conservation
        if clean_target == "delivered":
            try:
                actual_kg = Decimal(str(payload.get("actual_delivered_kg", 0)))
                waste_kg = Decimal(str(payload.get("waste_kg", 0)))
            except (ValueError, TypeError):
                return False, "Invalid decimal format for delivered or waste weight."

            if actual_kg <= 0:
                return False, "Delivered weight must be positive."

            if actual_kg + waste_kg != Decimal(str(quantity_kg)):
                return (
                    False,
                    f"Weight conservation violated: Actual ({actual_kg}) + Waste ({waste_kg}) != Loaded ({quantity_kg}).",
                )

        return True, "Valid transition."


class OrderSLAService:
    """SLA threshold monitor for unconfirmed or delayed wholesale orders."""

    SLA_THRESHOLDS_MINUTES: Dict[str, int] = {
        "pending": 120,          # 2 hours unconfirmed
        "confirmed": 18 * 60,    # 18 hours unloaded
        "out_for_delivery": 480, # 8 hours in transit
    }

    @classmethod
    def get_sla_threshold_minutes(cls, status: str) -> Optional[int]:
        """Get SLA warning threshold in minutes for a given status."""
        return cls.SLA_THRESHOLDS_MINUTES.get((status or "").strip().lower())
