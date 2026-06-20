"""Python client for public Tickertape web endpoints."""

from .auth_capture import capture_credentials_via_hybrid, get_auth_token
from .client import TickertapeClient
from .exceptions import TickertapeAPIError, TickertapeError, TickertapeHTTPError
from .portfolio_client import PortfolioClient

__all__ = [
    "PortfolioClient",
    "TickertapeAPIError",
    "TickertapeClient",
    "TickertapeError",
    "TickertapeHTTPError",
    "capture_credentials_via_hybrid",
    "get_auth_token",
]
__version__ = "0.1.0"
