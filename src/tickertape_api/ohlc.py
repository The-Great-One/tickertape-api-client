"""OHLC candle synthesis from Tickertape chart data.

Tickertape's chart endpoints return time-series with ``ts`` (timestamp),
``lp`` (last price), and ``v`` (cumulative volume). This module groups
those points into daily (or custom-frequency) OHLC candles.

The synthesis is purely client-side — no extra API calls are needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class Candle:
    """A single OHLC candle."""

    timestamp: str  # ISO 8601 UTC (date for daily, datetime for intraday)
    open: float
    high: float
    low: float
    close: float
    volume: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp from Tickertape."""
    # Tickertape uses ``2025-06-19T00:00:00.000Z`` format
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _day_key(ts: str) -> str:
    """Extract the date portion (YYYY-MM-DD) from an ISO timestamp."""
    return ts[:10]


def _extract_points(raw: Any) -> list[dict[str, Any]]:
    """Extract the ``points`` list from various Tickertape chart response shapes."""
    if isinstance(raw, list):
        # Indian inter-chart returns a list with one element containing ``points``
        for item in raw:
            if isinstance(item, dict) and "points" in item:
                return item["points"]
        # Fallback: if the list itself is points
        if raw and isinstance(raw[0], dict) and "ts" in raw[0]:
            return raw
    elif isinstance(raw, dict):
        if "points" in raw:
            return raw["points"]
    return []


def synthesize_ohlc(
    raw_chart: Any,
    *,
    frequency: str = "1D",
) -> list[Candle]:
    """Synthesize OHLC candles from Tickertape chart data.

    Parameters:
        raw_chart: The raw response from a Tickertape chart endpoint
            (``stock_inter_chart``, ``stock_intra_chart``, ``us_chart``, etc.).
        frequency: Candle grouping frequency. Supported values:
            ``1D`` (daily, default), ``1W`` (weekly), ``1M`` (monthly).

    Returns:
        A list of :class:`Candle` objects sorted by timestamp.

    For daily candles, intraday points are grouped by calendar date.
    The first point's ``lp`` becomes ``open``, the last becomes ``close``,
    and ``high``/``low`` are the max/min ``lp`` within the group.
    Volume is the difference between the first and last cumulative ``v``
    in the group (Tickertape volumes are cumulative within a session).
    """
    points = _extract_points(raw_chart)
    if not points:
        return []

    if frequency == "1D":
        return _group_daily(points)
    elif frequency == "1W":
        return _group_weekly(points)
    elif frequency == "1M":
        return _group_monthly(points)
    else:
        raise ValueError(f"Unsupported frequency: {frequency!r}. Use '1D', '1W', or '1M'.")


def _group_daily(points: Sequence[dict[str, Any]]) -> list[Candle]:
    """Group points by calendar date into daily OHLC candles."""
    candles: list[Candle] = []
    current_day: str | None = None
    day_points: list[dict[str, Any]] = []

    for pt in points:
        ts = pt.get("ts", "")
        day = _day_key(ts)
        if current_day is not None and day != current_day:
            candles.append(_build_candle(day_points, current_day))
            day_points = []
        current_day = day
        day_points.append(pt)

    if day_points:
        assert current_day is not None
        candles.append(_build_candle(day_points, current_day))

    return candles


def _group_weekly(points: Sequence[dict[str, Any]]) -> list[Candle]:
    """Group points by ISO week into weekly OHLC candles."""
    candles: list[Candle] = []
    current_week: str | None = None
    week_points: list[dict[str, Any]] = []

    for pt in points:
        ts = pt.get("ts", "")
        dt = _parse_ts(ts)
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        if current_week is not None and week_key != current_week:
            label = week_points[0]["ts"][:10]
            candles.append(_build_candle(week_points, label))
            week_points = []
        current_week = week_key
        week_points.append(pt)

    if week_points:
        label = week_points[0]["ts"][:10]
        candles.append(_build_candle(week_points, label))

    return candles


def _group_monthly(points: Sequence[dict[str, Any]]) -> list[Candle]:
    """Group points by calendar month into monthly OHLC candles."""
    candles: list[Candle] = []
    current_month: str | None = None
    month_points: list[dict[str, Any]] = []

    for pt in points:
        ts = pt.get("ts", "")
        month_key = ts[:7]  # YYYY-MM
        if current_month is not None and month_key != current_month:
            label = month_points[0]["ts"][:7]
            candles.append(_build_candle(month_points, label))
            month_points = []
        current_month = month_key
        month_points.append(pt)

    if month_points:
        label = month_points[0]["ts"][:7]
        candles.append(_build_candle(month_points, label))

    return candles


def _build_candle(points: Sequence[dict[str, Any]], label: str) -> Candle:
    """Build a single Candle from a group of price points."""
    prices = [float(pt["lp"]) for pt in points if "lp" in pt]
    if not prices:
        return Candle(label, 0.0, 0.0, 0.0, 0.0, 0.0)

    # Volume: Tickertape volumes are cumulative within a session.
    # For cross-session groupings (weekly/monthly), use sum of daily deltas.
    vols = [pt.get("v", 0) for pt in points]
    if len(vols) >= 2:
        # For daily: delta between last and first cumulative volume
        # For weekly/monthly: sum of within-day deltas
        volume = _calc_volume(vols, points)
    else:
        volume = float(vols[0]) if vols else 0.0

    return Candle(
        timestamp=label,
        open=prices[0],
        high=max(prices),
        low=min(prices),
        close=prices[-1],
        volume=volume,
    )


def _calc_volume(vols: Sequence[Any], points: Sequence[dict[str, Any]]) -> float:
    """Calculate actual volume from cumulative volume points.

    Within a single day, Tickertape's ``v`` is cumulative (monotonically
    increasing). The actual daily volume is ``v_last - v_first``.

    For multi-day groupings (weekly/monthly), we sum the daily deltas.
    """
    total = 0.0
    prev_day: str | None = None
    day_first_v: float | None = None
    day_last_v: float = 0.0

    for pt, v in zip(points, vols):
        day = _day_key(pt.get("ts", ""))
        if prev_day is not None and day != prev_day:
            if day_first_v is not None:
                total += day_last_v - day_first_v
            day_first_v = float(v)
        if day_first_v is None:
            day_first_v = float(v)
        day_last_v = float(v)
        prev_day = day

    if day_first_v is not None:
        total += day_last_v - day_first_v

    return max(total, 0.0)


def ohlc_to_list(candles: Sequence[Candle]) -> list[dict[str, Any]]:
    """Convert a list of Candles to a list of dicts (JSON-serializable)."""
    return [c.as_dict() for c in candles]


def _group_intraday(
    raw_chart: Any, *, interval_minutes: int = 5,
) -> list[Candle]:
    """Group intraday points into fixed-interval OHLC candles.

    Parameters:
        raw_chart: Raw response from an intraday chart endpoint.
        interval_minutes: Candle interval in minutes (default 5).
    """
    points = _extract_points(raw_chart)
    if not points:
        return []

    candles: list[Candle] = []
    current_bucket: str | None = None
    bucket_points: list[dict[str, Any]] = []

    for pt in points:
        ts = pt.get("ts", "")
        dt = _parse_ts(ts)
        # Bucket by interval (floor to nearest N minutes)
        floored_minute = (dt.minute // interval_minutes) * interval_minutes
        bucket = f"{ts[:10]}T{dt.hour:02d}:{floored_minute:02d}"

        if current_bucket is not None and bucket != current_bucket:
            candles.append(_build_candle(bucket_points, current_bucket))
            bucket_points = []
        current_bucket = bucket
        bucket_points.append(pt)

    if bucket_points:
        assert current_bucket is not None
        candles.append(_build_candle(bucket_points, current_bucket))

    return candles


def group_intraday(
    raw_chart: Any, *, interval_minutes: int = 5,
) -> list[Candle]:
    """Group intraday points into fixed-interval OHLC candles.

    Public API for :func:`_group_intraday`.
    """
    return _group_intraday(raw_chart, interval_minutes=interval_minutes)