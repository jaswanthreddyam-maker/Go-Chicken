"""PR 10 Quote Approval Pure Functional State Machine."""

class InvalidQuoteTransitionError(Exception):
    """Raised when an illegal quote state transition is attempted."""
    pass


class QuoteStateMachine:
    """Pure functional state machine governing quote approval and order conversion lifecycles."""

    VALID_TRANSITIONS = {
        "DRAFT": {"PENDING_APPROVAL", "APPROVED"},
        "PENDING_APPROVAL": {"APPROVED", "REJECTED"},
        "APPROVED": {"CONVERTED", "EXPIRED"},
        "REJECTED": set(),
        "CONVERTED": set(),
        "EXPIRED": set(),
    }

    @classmethod
    def validate_transition(cls, current_state: str, target_state: str) -> None:
        curr = current_state.upper()
        targ = target_state.upper()

        allowed = cls.VALID_TRANSITIONS.get(curr, set())
        if targ not in allowed:
            raise InvalidQuoteTransitionError(
                f"Invalid quote state transition from '{curr}' to '{targ}'. Allowed targets: {sorted(allowed)}"
            )
