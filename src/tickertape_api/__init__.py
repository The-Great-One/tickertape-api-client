"""Python client for public Tickertape web endpoints."""

from .client import TickertapeClient
from .exceptions import TickertapeAPIError, TickertapeError, TickertapeHTTPError

__all__ = ["TickertapeAPIError", "TickertapeClient", "TickertapeError", "TickertapeHTTPError"]
__version__ = "0.1.0"
