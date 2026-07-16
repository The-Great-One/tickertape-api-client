"""Tests for stock-split detection and adjustment in OHLC synthesis."""

import pytest

from tickertape_api.ohlc import (
    Candle,
    OHLCResult,
    SplitEvent,
    adjust_points_for_splits,
    detect_splits,
    synthesize_ohlc,
    synthesize_ohlc_with_splits,
    group_intraday,
)


# ---- detect_splits ---------------------------------------------------------

def test_detect_splits_finds_simple_10_to_1_split():
    """A price drop from 40 to 4 should be detected as a 10:1 split."""
    points = [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 40.0, "v": 1000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 4.0, "v": 10000},
    ]
    splits = detect_splits(points)
    assert len(splits) == 1
    assert splits[0].ratio == 10.0
    assert splits[0].old_price == 40.0
    assert splits[0].new_price == 4.0
    assert splits[0].date == "2025-01-14"


def test_detect_splits_finds_5_to_1_split():
    """A price drop from 2000 to 400 should be detected as a 5:1 split."""
    points = [
        {"ts": "2021-10-27T00:00:00.000Z", "lp": 2000.0, "v": 500},
        {"ts": "2021-10-28T00:00:00.000Z", "lp": 400.0, "v": 2500},
    ]
    splits = detect_splits(points)
    assert len(splits) == 1
    assert splits[0].ratio == 5.0
    assert splits[0].date == "2021-10-28"


def test_detect_splits_finds_2_to_1_split():
    """A price drop from 100 to 50 should be detected as a 2:1 split."""
    points = [
        {"ts": "2025-03-15T00:00:00.000Z", "lp": 100.0, "v": 1000},
        {"ts": "2025-03-16T00:00:00.000Z", "lp": 50.0, "v": 2000},
    ]
    splits = detect_splits(points)
    assert len(splits) == 1
    assert splits[0].ratio == 2.0


def test_detect_splits_ignores_normal_price_moves():
    """A 5% daily price drop should NOT be detected as a split."""
    points = [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 100.0, "v": 1000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 95.0, "v": 1200},
    ]
    splits = detect_splits(points)
    assert len(splits) == 0


def test_detect_splits_ignores_30_percent_drop():
    """A 30% drop (e.g. bad earnings) should not be a split."""
    points = [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 100.0, "v": 1000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 70.0, "v": 2000},
    ]
    splits = detect_splits(points)
    assert len(splits) == 0


def test_detect_splits_handles_multiple_splits():
    """Two splits in the series should both be detected."""
    points = [
        {"ts": "2020-01-01T00:00:00.000Z", "lp": 1000.0, "v": 100},
        {"ts": "2020-06-01T00:00:00.000Z", "lp": 100.0, "v": 1000},  # 10:1 split
        {"ts": "2021-01-01T00:00:00.000Z", "lp": 200.0, "v": 2000},
        {"ts": "2021-06-01T00:00:00.000Z", "lp": 100.0, "v": 4000},  # 2:1 split
    ]
    splits = detect_splits(points)
    assert len(splits) == 2
    assert splits[0].ratio == 10.0
    assert splits[1].ratio == 2.0


def test_detect_splits_empty_points():
    """Empty points list should return no splits."""
    assert detect_splits([]) == []


def test_detect_splits_single_point():
    """Single point should return no splits."""
    points = [{"ts": "2025-01-13T00:00:00.000Z", "lp": 40.0, "v": 1000}]
    assert detect_splits(points) == []


def test_detect_splits_tolerates_small_variance():
    """A 10:1 split with slight price variance should still be detected.

    Pre-split close 40.5, post-split open 4.1 → ratio 9.88, within 8% of 10.
    """
    points = [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 40.5, "v": 1000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 4.1, "v": 10000},
    ]
    splits = detect_splits(points)
    assert len(splits) == 1
    assert splits[0].ratio == 10.0


# ---- adjust_points_for_splits ----------------------------------------------

def test_adjust_points_basic_10_to_1_split():
    """Pre-split prices should be divided by the split ratio."""
    points = [
        {"ts": "2025-01-12T00:00:00.000Z", "lp": 40.0, "v": 1000},
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 41.0, "v": 2000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 4.0, "v": 10000},
        {"ts": "2025-01-15T00:00:00.000Z", "lp": 4.2, "v": 12000},
    ]
    splits = detect_splits(points)
    assert len(splits) == 1

    adjusted = adjust_points_for_splits(points, splits)
    # Pre-split prices should be divided by 10
    assert adjusted[0]["lp"] == pytest.approx(4.0)
    assert adjusted[1]["lp"] == pytest.approx(4.1)
    # Post-split prices should be unchanged
    assert adjusted[2]["lp"] == pytest.approx(4.0)
    assert adjusted[3]["lp"] == pytest.approx(4.2)
    # Volume should be multiplied by 10 for pre-split
    assert adjusted[0]["v"] == pytest.approx(10000)
    assert adjusted[2]["v"] == pytest.approx(10000)


def test_adjust_points_no_splits_returns_copies():
    """With no splits, points should be returned as copies."""
    points = [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 40.0, "v": 1000},
    ]
    adjusted = adjust_points_for_splits(points, [])
    assert adjusted[0]["lp"] == 40.0
    # Verify it's a copy, not the same object
    adjusted[0]["lp"] = 999
    assert points[0]["lp"] == 40.0


def test_adjust_points_multiple_splits():
    """Multiple splits should compound the adjustment."""
    points = [
        {"ts": "2020-01-01T00:00:00.000Z", "lp": 1000.0, "v": 100},
        {"ts": "2020-06-01T00:00:00.000Z", "lp": 100.0, "v": 1000},  # 10:1
        {"ts": "2021-06-01T00:00:00.000Z", "lp": 100.0, "v": 1000},  # 2:1
        {"ts": "2022-01-01T00:00:00.000Z", "lp": 50.0, "v": 4000},
    ]
    splits = detect_splits(points)
    assert len(splits) == 2

    adjusted = adjust_points_for_splits(points, splits)
    # First point: before both splits → divide by 10*2=20
    assert adjusted[0]["lp"] == pytest.approx(50.0)
    # Second point: after 10:1 but before 2:1 → divide by 2
    assert adjusted[1]["lp"] == pytest.approx(50.0)
    # Third point: after 10:1 but before 2:1 → divide by 2
    assert adjusted[2]["lp"] == pytest.approx(50.0)
    # Fourth point: after both splits → no adjustment
    assert adjusted[3]["lp"] == pytest.approx(50.0)


# ---- synthesize_ohlc with split adjustment --------------------------------

def test_synthesize_ohlc_adjusts_split_in_daily_candles():
    """Daily OHLC should not show a broken candle across a split date."""
    # Simulate: day 1 closes at 40, day 2 (split) opens at 4
    raw = [{"points": [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 40.0, "v": 1000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 4.0, "v": 10000},
        {"ts": "2025-01-15T00:00:00.000Z", "lp": 4.2, "v": 12000},
    ]}]

    # Without adjustment (old behavior)
    candles_raw = synthesize_ohlc(raw, adjust_splits=False)
    assert candles_raw[0].close == 40.0
    assert candles_raw[1].open == 4.0  # broken: looks like a 90% drop

    # With adjustment (new behavior)
    candles_adj = synthesize_ohlc(raw, adjust_splits=True)
    assert candles_adj[0].close == pytest.approx(4.0)  # adjusted to post-split
    assert candles_adj[0].open == pytest.approx(4.0)
    assert candles_adj[1].open == pytest.approx(4.0)  # smooth transition
    assert candles_adj[2].open == pytest.approx(4.2)


def test_synthesize_ohlc_with_splits_returns_metadata():
    """synthesize_ohlc_with_splits should return both candles and split info."""
    raw = [{"points": [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 40.0, "v": 1000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 4.0, "v": 10000},
    ]}]

    result = synthesize_ohlc_with_splits(raw, frequency="1D")
    assert isinstance(result, OHLCResult)
    assert len(result.splits) == 1
    assert result.splits[0].ratio == 10.0
    assert len(result.candles) == 2
    # Both candles should be on the same price scale
    assert result.candles[0].close == pytest.approx(4.0)
    assert result.candles[1].open == pytest.approx(4.0)


def test_synthesize_ohlc_no_false_positives_on_normal_data():
    """Normal price data with volatility should not trigger split adjustment."""
    raw = [{"points": [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 100.0, "v": 1000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 95.0, "v": 1200},
        {"ts": "2025-01-15T00:00:00.000Z", "lp": 97.0, "v": 1100},
        {"ts": "2025-01-16T00:00:00.000Z", "lp": 93.0, "v": 1300},
    ]}]

    result = synthesize_ohlc_with_splits(raw, frequency="1D")
    assert len(result.splits) == 0
    # Prices should be unchanged
    assert result.candles[0].close == 100.0
    assert result.candles[1].open == 95.0


def test_synthesize_ohlc_intraday_split_adjustment():
    """Intraday data spanning a split should be adjusted before grouping."""
    # Simulate intraday data where a 10:1 split happens mid-day
    raw = [{"points": [
        # Pre-split: 09:15-09:30 at ~40
        {"ts": "2025-01-14T03:45:00.000Z", "lp": 40.0, "v": 500},
        {"ts": "2025-01-14T03:50:00.000Z", "lp": 40.5, "v": 1000},
        {"ts": "2025-01-14T03:55:00.000Z", "lp": 41.0, "v": 1500},
        # Post-split: 09:30 onwards at ~4
        {"ts": "2025-01-14T04:00:00.000Z", "lp": 4.0, "v": 5000},
        {"ts": "2025-01-14T04:05:00.000Z", "lp": 4.1, "v": 8000},
        {"ts": "2025-01-14T04:10:00.000Z", "lp": 4.05, "v": 11000},
    ]}]

    # Without adjustment: the daily candle would have open=40, close=4.05, high=41, low=4
    candles_raw = synthesize_ohlc(raw, frequency="1D", adjust_splits=False)
    assert len(candles_raw) == 1
    assert candles_raw[0].open == 40.0
    assert candles_raw[0].close == 4.05  # broken
    assert candles_raw[0].high == 41.0
    assert candles_raw[0].low == 4.0

    # With adjustment: pre-split prices divided by 10
    candles_adj = synthesize_ohlc(raw, frequency="1D", adjust_splits=True)
    assert len(candles_adj) == 1
    assert candles_adj[0].open == pytest.approx(4.0)  # 40/10
    assert candles_adj[0].close == pytest.approx(4.05)
    assert candles_adj[0].high == pytest.approx(4.1)  # 41/10
    assert candles_adj[0].low == pytest.approx(4.0)


def test_group_intraday_with_split():
    """group_intraday should also adjust for splits."""
    raw = [{"points": [
        {"ts": "2025-01-14T03:45:00.000Z", "lp": 40.0, "v": 500},
        {"ts": "2025-01-14T03:50:00.000Z", "lp": 40.5, "v": 1000},
        {"ts": "2025-01-14T04:00:00.000Z", "lp": 4.0, "v": 5000},
        {"ts": "2025-01-14T04:05:00.000Z", "lp": 4.1, "v": 8000},
    ]}]

    candles = group_intraday(raw, interval_minutes=5, adjust_splits=True)
    # All candles should be on the same (post-split) price scale
    for c in candles:
        assert c.open < 10.0  # all prices should be in the 4.x range
        assert c.close < 10.0
        assert c.high < 10.0
        assert c.low < 10.0


def test_synthesize_ohlc_preserves_no_split_data():
    """Data with no splits should be identical with or without adjust_splits."""
    raw = [{"points": [
        {"ts": "2025-01-13T00:00:00.000Z", "lp": 100.0, "v": 1000},
        {"ts": "2025-01-14T00:00:00.000Z", "lp": 102.0, "v": 2000},
        {"ts": "2025-01-15T00:00:00.000Z", "lp": 101.0, "v": 1500},
    ]}]

    candles_default = synthesize_ohlc(raw, frequency="1D")
    candles_no_adj = synthesize_ohlc(raw, frequency="1D", adjust_splits=False)

    assert len(candles_default) == len(candles_no_adj)
    for c1, c2 in zip(candles_default, candles_no_adj):
        assert c1.open == c2.open
        assert c1.close == c2.close
        assert c1.high == c2.high
        assert c1.low == c2.low


def test_split_event_as_dict():
    """SplitEvent should serialize to dict correctly."""
    split = SplitEvent(date="2025-01-14", ratio=10.0, old_price=40.0, new_price=4.0, timestamp="2025-01-14T00:00:00.000Z")
    d = split.as_dict()
    assert d == {"date": "2025-01-14", "ratio": 10.0, "old_price": 40.0, "new_price": 4.0, "timestamp": "2025-01-14T00:00:00.000Z"}


def test_ohlc_result_as_dict():
    """OHLCResult should serialize to dict with candles and splits."""
    result = OHLCResult(
        candles=[Candle("2025-01-14", 4.0, 4.1, 4.0, 4.05, 10000)],
        splits=[SplitEvent("2025-01-14", 10.0, 40.0, 4.0, "2025-01-14T00:00:00.000Z")],
    )
    d = result.as_dict()
    assert "candles" in d
    assert "splits" in d
    assert len(d["candles"]) == 1
    assert len(d["splits"]) == 1
    assert d["splits"][0]["ratio"] == 10.0