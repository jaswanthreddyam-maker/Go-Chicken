"""Enterprise Domain Exceptions — explicit error hierarchy for domain invariants and operations."""


class GoChickenDomainError(Exception):
    """Base class for all Go Chicken domain exceptions."""
    pass


class InsufficientInventoryError(GoChickenDomainError):
    """Raised when an operation requests more stock than available."""
    pass


class InvalidTransitionError(GoChickenDomainError):
    """Raised when an order status transition violates state machine rules."""
    pass


class OrderAlreadyConfirmedError(GoChickenDomainError):
    """Raised when attempting to confirm an order that is already confirmed."""
    pass


class TerminalOrderError(GoChickenDomainError):
    """Raised when attempting to mutate an order in a terminal state (DELIVERED / CANCELLED)."""
    pass


class TruckCapacityExceededError(GoChickenDomainError):
    """Raised when loading an order onto a truck exceeds its maximum payload capacity."""
    pass
