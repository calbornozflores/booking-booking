class BookingBookingError(Exception):
    """Base class for all errors raised by this package."""


class ChallengeBlockedError(BookingBookingError):
    """Booking.com's anti-bot challenge (AWS WAF) did not clear in time."""


class ElementNotFoundError(BookingBookingError):
    """An expected page element could not be located.

    Distinct from ChallengeBlockedError: the page loaded real content, but a
    specific element we depend on wasn't there (site markup likely changed).
    """


class NoResultsError(BookingBookingError):
    """The search completed but returned zero properties."""
