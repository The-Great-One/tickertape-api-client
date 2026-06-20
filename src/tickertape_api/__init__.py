"""Python client for public Tickertape web endpoints."""

from .auth_capture import capture_credentials_via_hybrid, get_auth_token
from .client import TickertapeClient
from .exceptions import TickertapeAPIError, TickertapeError, TickertapeHTTPError
from .ohlc import Candle, group_intraday, ohlc_to_list, synthesize_ohlc
from .portfolio_client import PortfolioClient
from .rate_limiter import RateLimiter

__all__ = [
    "Candle",
    "PortfolioClient",
    "RateLimiter",
    "TickertapeAPIError",
    "TickertapeClient",
    "TickertapeError",
    "TickertapeHTTPError",
    "capture_credentials_via_hybrid",
    "get_auth_token",
    "group_intraday",
    "ohlc_to_list",
    "synthesize_ohlc",
]
__version__ = "0.2.0"