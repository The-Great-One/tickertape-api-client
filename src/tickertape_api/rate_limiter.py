"""Rate limiter for Tickertape API requests.

Implements a sliding-window rate limiter that respects configurable
requests-per-second and burst limits. Designed to be thread-safe and
zero-dependency.
"""

from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    """Sliding-window rate limiter.

    Parameters:
        max_calls: Maximum number of calls allowed within ``period`` seconds.
        period: Time window in seconds.
    """

    def __init__(self, max_calls: float = 5.0, period: float = 1.0) -> None:
        if max_calls <= 0:
            raise ValueError("max_calls must be positive")
        if period <= 0:
            raise ValueError("period must be positive")
        self._max_calls = max_calls
        self._period = period
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a request slot is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                # Evict timestamps older than the window
                cutoff = now - self._period
                while self._timestamps and self._timestamps[0] <= cutoff:
                    self._timestamps.popleft()
                if len(self._timestamps) < self._max_calls:
                    self._timestamps.append(now)
                    return
                # Calculate sleep time until the oldest timestamp exits the window
                sleep_for = self._timestamps[0] + self._period - now
            if sleep_for > 0:
                time.sleep(sleep_for)

    def try_acquire(self) -> bool:
        """Non-blocking acquire. Returns True if a slot was taken, False otherwise."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - self._period
            while self._timestamps and self._timestamps[0] <= cutoff:
                self._timestamps.popleft()
            if len(self._timestamps) < self._max_calls:
                self._timestamps.append(now)
                return True
            return False

    @property
    def max_calls(self) -> float:
        return self._max_calls

    @property
    def period(self) -> float:
        return self._period