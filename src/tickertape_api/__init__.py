"""Python client for public Tickertape web endpoints."""

from .auth_capture import capture_credentials_via_hybrid, get_auth_token
from .client import TickertapeClient
from .credentials_store import list_accounts, read_credentials_file
from .exceptions import TickertapeAPIError, TickertapeError, TickertapeHTTPError
from .ohlc import (
    Candle,
    OHLCResult,
    SplitEvent,
    adjust_points_for_splits,
    detect_splits,
    group_intraday,
    ohlc_to_list,
    synthesize_ohlc,
    synthesize_ohlc_with_splits,
)
from .portfolio_client import PortfolioClient
from .rate_limiter import RateLimiter

__all__ = [
    "Candle",
    "OHLCResult",
    "PortfolioClient",
    "RateLimiter",
    "SplitEvent",
    "TickertapeAPIError",
    "TickertapeClient",
    "TickertapeError",
    "TickertapeHTTPError",
    "adjust_points_for_splits",
    "capture_credentials_via_hybrid",
    "detect_splits",
    "get_auth_token",
    "group_intraday",
    "list_accounts",
    "ohlc_to_list",
    "read_credentials_file",
    "synthesize_ohlc",
    "synthesize_ohlc_with_splits",
]
__version__ = "0.2.1"