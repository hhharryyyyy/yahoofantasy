"""Custom exceptions for Yahoo Fantasy API operations."""


class YahooFantasyError(Exception):
    """Base exception for Yahoo Fantasy API errors."""

    def __init__(self, message, code=None, raw_response=None):
        super().__init__(message)
        self.code = code
        self.raw_response = raw_response


class RosterError(YahooFantasyError):
    """Errors related to roster operations."""

    pass


class TransactionError(YahooFantasyError):
    """Errors related to transactions (add/drop/waiver)."""

    pass


class InvalidPositionError(RosterError):
    """Player cannot be placed in the specified position."""

    pass


class RosterFullError(TransactionError):
    """Cannot add player - roster is full."""

    pass


class PlayerNotAvailableError(TransactionError):
    """Player is not available (already owned, on waivers, etc.)."""

    pass


class InsufficientFAABError(TransactionError):
    """FAAB bid exceeds available budget."""

    pass


class WaiverPriorityError(TransactionError):
    """Waiver claim failed due to priority."""

    pass


class InsufficientScopeError(YahooFantasyError):
    """OAuth token does not have write permissions.

    Re-run 'yahoofantasy login' and ensure your Yahoo app
    has the 'Fantasy Sports' permission with read/write access.
    """

    pass
