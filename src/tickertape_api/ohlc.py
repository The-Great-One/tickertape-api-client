"""OHLC candle synthesis from Tickertape chart data.

Tickertape's chart endpoints return time-series with ``ts`` (timestamp),
``lp`` (last price), and ``v`` (cumulative volume). This module groups
those points into daily (or custom-frequency) OHLC candles.

The synthesis is purely client-side — no extra API calls are needed.

Stock-split handling
--------------------
Tickertape's inter-day charts (1y, 5y, max) are usually split-adjusted.
However, intraday data (``1w`` duration) and some edge cases can contain
unadjusted prices around a split date. When a stock splits (e.g. 10:1),
the price drops from ₹40 to ₹4 overnight. Without adjustment, the OHLC
synthesis produces a broken candle with open=40, close=4, high=40, low=4.

This module detects split-like discontinuities and adjusts pre-split
prices by the split ratio before building candles. Detected splits are
returned as metadata so callers can verify the adjustment.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


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


@dataclass(frozen=True, slots=True)
class SplitEvent:
    """A detected stock split."""

    date: str  # ISO date (YYYY-MM-DD) when the split took effect
    ratio: float  # New shares per old share (e.g. 5.0 for a 1:5 split)
    old_price: float  # Price just before the split
    new_price: float  # Price just after the split
    timestamp: str = ""  # Full ISO timestamp of the first post-split point

    def as_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "ratio": self.ratio,
            "old_price": self.old_price,
            "new_price": self.new_price,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class OHLCResult:
    """Result of OHLC synthesis with optional split metadata."""

    candles: list[Candle]
    splits: list[SplitEvent] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "candles": [c.as_dict() for c in self.candles],
            "splits": [s.as_dict() for s in self.splits],
        }


# ---- split detection -------------------------------------------------------

# Common split ratios (new shares per old share). We detect these by
# checking if the price ratio between consecutive points is close to one
# of these values. The tolerance accounts for normal intraday volatility.
_SPLIT_RATIOS: tuple[float, ...] = (2.0, 3.0, 4.0, 5.0, 10.0, 1.5, 1.25, 7.0)
_SPLIT_TOLERANCE: float = 0.20  # 20% tolerance — weekly data has price movement between points
_MIN_PRICE_DROP: float = 0.30  # price must drop by at least 70% (ratio >= ~1.43)


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp from Tickertape."""
    # Tickertape uses ``2025-06-19T00:00:00.000Z`` format
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _day_key(ts: str) -> str:
    """Extract the date portion (YYYY-MM-DD) from an ISO timestamp."""
    return ts[:10]


def _extract_points(raw: Any) -> list[dict[str, Any]]:
    """Extract the ``points`` list from various Tickertape chart response shapes."""
    result: list[dict[str, Any]] = []
    if isinstance(raw, list):
        # Indian inter-chart returns a list with one element containing ``points``
        for item in raw:
            if isinstance(item, dict) and "points" in item:
                result = item["points"]
                break
        else:
            # Fallback: if the list itself is points
            if raw and isinstance(raw[0], dict) and "ts" in raw[0]:
                result = raw
    elif isinstance(raw, dict) and "points" in raw:
        result = raw["points"]
    return result


def detect_splits(
    points: Sequence[dict[str, Any]],
    *,
    min_ratio: float = 1.44,
    tolerance: float = _SPLIT_TOLERANCE,
) -> list[SplitEvent]:
    """Detect stock splits in a price point series.

    A split is detected when the price drops by a factor close to a common
    split ratio (2:1, 3:1, 5:1, 10:1, etc.) between two consecutive points.

    Parameters:
        points: Price points with ``ts`` and ``lp`` keys.
        min_ratio: Minimum price ratio to consider as a potential split.
        tolerance: How close the ratio must be to a clean split ratio.

    Returns:
        List of detected :class:`SplitEvent` objects, sorted chronologically.
    """
    if len(points) < 2:
        return []

    splits: list[SplitEvent] = []
    prev_price: float | None = None

    for pt in points:
        lp = pt.get("lp")
        if lp is None:
            continue
        curr_price = float(lp)
        ts = pt.get("ts", "")

        if prev_price is not None and prev_price > 0 and curr_price > 0:
            ratio = prev_price / curr_price
            if ratio >= min_ratio:
                # Check if ratio is close to a known split ratio
                for split_ratio in _SPLIT_RATIOS:
                    if abs(ratio - split_ratio) / split_ratio <= tolerance:
                        splits.append(
                            SplitEvent(
                                date=_day_key(ts),
                                ratio=split_ratio,
                                old_price=prev_price,
                                new_price=curr_price,
                                timestamp=ts,
                            )
                        )
                        break

        prev_price = curr_price

    return splits


def adjust_points_for_splits(
    points: list[dict[str, Any]],
    splits: list[SplitEvent],
) -> list[dict[str, Any]]:
    """Adjust pre-split prices by applying split ratios backward.

    For each detected split, all prices BEFORE the split timestamp are divided
    by the split ratio. This makes the entire series comparable on a
    post-split basis.

    Volume is multiplied by the split ratio (more shares after split =
    proportionally higher volume on a per-share basis pre-split).

    The adjustment is applied on copies — the original points are not modified.

    Parameters:
        points: Raw price points from Tickertape.
        splits: Detected split events.

    Returns:
        New list of points with adjusted ``lp`` and ``v`` values.
    """
    if not splits:
        return [dict(pt) for pt in points]  # return copies

    # Sort splits by timestamp (earliest first)
    sorted_splits = sorted(splits, key=lambda s: s.timestamp or s.date)

    adjusted: list[dict[str, Any]] = []

    for pt in points:
        ts = pt.get("ts", "")
        lp = pt.get("lp")
        v = pt.get("v")

        # Compute cumulative factor: product of all split ratios that
        # occurred AFTER this point's timestamp.
        # Use timestamp for precise comparison (handles intraday splits).
        # If split has no timestamp, fall back to date comparison.
        factor = 1.0
        for sp in sorted_splits:
            split_key = sp.timestamp or sp.date
            if ts < split_key:
                factor *= sp.ratio

        new_pt = dict(pt)
        if lp is not None and factor != 1.0:
            new_pt["lp"] = float(lp) / factor
        if v is not None and factor != 1.0:
            new_pt["v"] = float(v) * factor

        adjusted.append(new_pt)

    return adjusted


def synthesize_ohlc(
    raw_chart: Any,
    *,
    frequency: str = "1D",
    adjust_splits: bool = True,
) -> list[Candle]:
    """Synthesize OHLC candles from Tickertape chart data.

    Parameters:
        raw_chart: The raw response from a Tickertape chart endpoint
            (``stock_inter_chart``, ``stock_intra_chart``, ``us_chart``, etc.).
        frequency: Candle grouping frequency. Supported values:
            ``1D`` (daily, default), ``1W`` (weekly), ``1M`` (monthly).
        adjust_splits: If True (default), detect stock splits in the
            price data and adjust pre-split prices before building candles.

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

    # Detect and adjust for stock splits
    split_events: list[SplitEvent] = []
    if adjust_splits:
        split_events = detect_splits(points)
        if split_events:
            points = adjust_points_for_splits(points, split_events)

    if frequency == "1D":
        return _group_daily(points)
    elif frequency == "1W":
        return _group_weekly(points)
    elif frequency == "1M":
        return _group_monthly(points)
    else:
        raise ValueError(f"Unsupported frequency: {frequency!r}. Use '1D', '1W', or '1M'.")


def synthesize_ohlc_with_splits(
    raw_chart: Any,
    *,
    frequency: str = "1D",
    adjust_splits: bool = True,
) -> OHLCResult:
    """Synthesize OHLC candles and return split metadata.

    Like :func:`synthesize_ohlc` but returns an :class:`OHLCResult` that
    includes detected split events alongside the candles.

    Parameters:
        raw_chart: The raw response from a Tickertape chart endpoint.
        frequency: Candle grouping frequency (``1D``, ``1W``, ``1M``).
        adjust_splits: If True, adjust pre-split prices before building candles.

    Returns:
        An :class:`OHLCResult` with candles and detected splits.
    """
    points = _extract_points(raw_chart)
    if not points:
        return OHLCResult(candles=[], splits=[])

    split_events: list[SplitEvent] = []
    if adjust_splits:
        split_events = detect_splits(points)
        if split_events:
            points = adjust_points_for_splits(points, split_events)

    if frequency == "1D":
        candles = _group_daily(points)
    elif frequency == "1W":
        candles = _group_weekly(points)
    elif frequency == "1M":
        candles = _group_monthly(points)
    else:
        raise ValueError(f"Unsupported frequency: {frequency!r}. Use '1D', '1W', or '1M'.")

    return OHLCResult(candles=candles, splits=split_events)


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
    # For daily: delta between last and first cumulative volume
    # For weekly/monthly: sum of within-day deltas
    volume = _calc_volume(vols, points) if len(vols) >= 2 else (float(vols[0]) if vols else 0.0)

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
    adjust_splits: bool = True,
) -> list[Candle]:
    """Group intraday points into fixed-interval OHLC candles.

    Parameters:
        raw_chart: Raw response from an intraday chart endpoint.
        interval_minutes: Candle interval in minutes (default 5).
        adjust_splits: If True, detect and adjust for stock splits.
    """
    points = _extract_points(raw_chart)
    if not points:
        return []

    # Detect and adjust for stock splits
    if adjust_splits:
        split_events = detect_splits(points)
        if split_events:
            points = adjust_points_for_splits(points, split_events)

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
    adjust_splits: bool = True,
) -> list[Candle]:
    """Group intraday points into fixed-interval OHLC candles.

    Public API for :func:`_group_intraday`.

    Parameters:
        raw_chart: Raw response from an intraday chart endpoint.
        interval_minutes: Candle interval in minutes (default 5).
        adjust_splits: If True (default), detect and adjust for stock splits.
    """
    return _group_intraday(raw_chart, interval_minutes=interval_minutes, adjust_splits=adjust_splits)