"""Unit tests for OrderStateMachine and OrderSLAService."""

import pytest
from decimal import Decimal
from uuid import uuid4
from core.order_state_machine import OrderStateMachine, OrderSLAService


def test_can_transition_valid_paths():
    assert OrderStateMachine.can_transition("pending", "confirmed") is True
    assert OrderStateMachine.can_transition("pending", "cancelled") is True
    assert OrderStateMachine.can_transition("confirmed", "loaded") is True
    assert OrderStateMachine.can_transition("confirmed", "cancelled") is True
    assert OrderStateMachine.can_transition("loaded", "out_for_delivery") is True
    assert OrderStateMachine.can_transition("loaded", "cancelled") is True
    assert OrderStateMachine.can_transition("out_for_delivery", "delivered") is True


def test_can_transition_terminal_states_reject():
    assert OrderStateMachine.can_transition("delivered", "cancelled") is False
    assert OrderStateMachine.can_transition("cancelled", "pending") is False
    assert OrderStateMachine.can_transition("delivered", "pending") is False


def test_validate_transition_terminal_state():
    is_valid, msg = OrderStateMachine.validate_transition(
        current_status="delivered",
        target_status="cancelled",
        quantity_kg=Decimal("100.00"),
    )
    assert is_valid is False
    assert "terminal state 'delivered'" in msg


def test_validate_transition_requires_truck_for_load():
    is_valid, msg = OrderStateMachine.validate_transition(
        current_status="confirmed",
        target_status="loaded",
        quantity_kg=Decimal("50.00"),
        truck_id=None,
        payload={},
    )
    assert is_valid is False
    assert "No delivery truck assigned" in msg

    # With truck_id assigned, should succeed
    is_valid, msg = OrderStateMachine.validate_transition(
        current_status="confirmed",
        target_status="loaded",
        quantity_kg=Decimal("50.00"),
        truck_id=uuid4(),
    )
    assert is_valid is True


def test_validate_transition_delivered_weight_conservation():
    # Valid conservation: 96 actual + 4 waste == 100 loaded
    is_valid, msg = OrderStateMachine.validate_transition(
        current_status="out_for_delivery",
        target_status="delivered",
        quantity_kg=Decimal("100.00"),
        payload={"actual_delivered_kg": "96.00", "waste_kg": "4.00"},
    )
    assert is_valid is True

    # Invalid conservation: 90 actual + 4 waste == 94 != 100 loaded
    is_valid, msg = OrderStateMachine.validate_transition(
        current_status="out_for_delivery",
        target_status="delivered",
        quantity_kg=Decimal("100.00"),
        payload={"actual_delivered_kg": "90.00", "waste_kg": "4.00"},
    )
    assert is_valid is False
    assert "Weight conservation violated" in msg


def test_order_sla_service_thresholds():
    assert OrderSLAService.get_sla_threshold_minutes("pending") == 120
    assert OrderSLAService.get_sla_threshold_minutes("confirmed") == 1080
    assert OrderSLAService.get_sla_threshold_minutes("out_for_delivery") == 480
    assert OrderSLAService.get_sla_threshold_minutes("unknown") is None
