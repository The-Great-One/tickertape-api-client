"""Exceptions raised by tickertape-api-client."""

from __future__ import annotations

from typing import Any


class TickertapeError(Exception):
    """Base exception for all client errors."""


class TickertapeHTTPError(TickertapeError):
    """Raised when Tickertape returns a non-2xx HTTP response."""

    def __init__(self, status_code: int, message: str, payload: Any | None = None) -> None:
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Tickertape HTTP {status_code}: {message}")


class TickertapeAPIError(TickertapeError):
    """Raised when a 2xx response contains success=false."""

    def __init__(self, message: str, payload: Any | None = None) -> None:
        self.payload = payload
        super().__init__(message)
