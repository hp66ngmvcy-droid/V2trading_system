"""Tests for new functions in generate_daily_brief.py."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.generate_daily_brief import (
    _double_touch_alerts,
    _ema200,
    _ic_markets_server_utc_offset_hours,
    _iv_walls,
    _multi_day_levels,
    _scenario_maps,
    _session_vwap,
    _timeframe_structure,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_bars(n_days: int = 7, base_price: float = 4300.0, seed: int = 42) -> pd.DataFrame:
    """Synthetic M15 bars over n_days business days."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2026-09-15", periods=n_days)
    rows = []
    price = base_price
    for d in dates:
        for h in range(0, 24):
            for m in (0, 15, 30, 45):
                ts = pd.Timestamp(d.year, d.month, d.day, h, m, tzinfo=pd.Timestamp("now", tz="UTC").tzinfo)
                o = price + rng.uniform(-1, 1)
                c = o + rng.uniform(-2, 2)
                hi = max(o, c) + abs(rng.uniform(0, 1))
                lo = min(o, c) - abs(rng.uniform(0, 1))
                rows.append({"timestamp": ts, "open": o, "high": hi, "low": lo, "close": c})
                price = c
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


@pytest.fixture()
def bars() -> pd.DataFrame:
    return _make_bars(n_days=7)


@pytest.fixture()
def today_str(bars) -> str:
    dates = sorted(set(bars["timestamp"].dt.date))
    return str(dates[-1])


# ---------------------------------------------------------------------------
# IC Markets server offset
# ---------------------------------------------------------------------------

class TestIcMarketsServerOffset:
    def test_returns_winter_offset(self):
        assert _ic_markets_server_utc_offset_hours("2026-01-15") == 2

    def test_returns_summer_dst_offset(self):
        assert _ic_markets_server_utc_offset_hours("2026-09-30") == 3


# ---------------------------------------------------------------------------
# _ema200
# ---------------------------------------------------------------------------

class TestEma200:
    def test_returns_float_with_enough_bars(self, bars):
        result = _ema200(bars)
        assert result is None or isinstance(result, float)

    def test_returns_none_with_too_few_bars(self):
        tiny = _make_bars(n_days=1)  # ~96 bars, < 200
        assert _ema200(tiny) is None

    def test_returns_float_with_200_plus_bars(self):
        big = _make_bars(n_days=4)   # 4 × 96 = 384 bars
        result = _ema200(big)
        assert isinstance(result, float)

    def test_ema_within_price_range(self):
        big = _make_bars(n_days=4)
        result = _ema200(big)
        lo = float(big["low"].min())
        hi = float(big["high"].max())
        assert lo <= result <= hi


# ---------------------------------------------------------------------------
# _session_vwap
# ---------------------------------------------------------------------------

class TestSessionVwap:
    def test_returns_dict(self, bars, today_str):
        v = _session_vwap(bars, today_str)
        assert isinstance(v, dict)

    def test_keys_present_when_data_available(self, bars, today_str):
        # Inject today bars by shifting last day of fixture to today_str
        b = bars.copy()
        dates = sorted(set(b["timestamp"].dt.date))
        last_d = dates[-1]
        delta = pd.Timestamp(today_str).date() - last_d
        b["timestamp"] = b["timestamp"] + pd.Timedelta(days=delta.days)
        v = _session_vwap(b, today_str)
        assert "asia_vwap" in v
        assert "london_vwap" in v
        assert "ny_vwap" in v

    def test_empty_bars_returns_empty(self):
        empty = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        empty["timestamp"] = pd.to_datetime(empty["timestamp"], utc=True)
        assert _session_vwap(empty, "2026-09-29") == {}

    def test_vwap_within_price_range(self, bars, today_str):
        b = bars.copy()
        dates = sorted(set(b["timestamp"].dt.date))
        last_d = dates[-1]
        delta = pd.Timestamp(today_str).date() - last_d
        b["timestamp"] = b["timestamp"] + pd.Timedelta(days=delta.days)
        v = _session_vwap(b, today_str)
        lo = float(b[b["timestamp"].dt.date.astype(str) == today_str]["low"].min())
        hi = float(b[b["timestamp"].dt.date.astype(str) == today_str]["high"].max())
        for key, val in v.items():
            if val is not None:
                assert lo <= val <= hi, f"{key}={val} outside [{lo},{hi}]"

    def test_server_offset_uses_corrected_utc_anchor(self):
        today = "2026-01-06"
        bars = pd.DataFrame(
            [
                {
                    "timestamp": pd.Timestamp(f"{today} 08:00", tz="UTC"),
                    "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0,
                    "volume": 1.0,
                },
                {
                    "timestamp": pd.Timestamp(f"{today} 10:00", tz="UTC"),
                    "open": 200.0, "high": 200.0, "low": 200.0, "close": 200.0,
                    "volume": 1.0,
                },
            ]
        )

        uncorrected = _session_vwap(bars, today, server_utc_offset_hours=0)
        corrected = _session_vwap(bars, today, server_utc_offset_hours=2)

        assert uncorrected["london_vwap"] == 150.0
        assert corrected["london_vwap"] == 200.0


# ---------------------------------------------------------------------------
# _double_touch_alerts
# ---------------------------------------------------------------------------

def _make_touch_bars(today_str: str, highs: list[float], lows: list[float]) -> pd.DataFrame:
    """Minimal bars for a single day with specified high/low per bar."""
    rows = []
    base_ts = pd.Timestamp(today_str, tz="UTC")
    for i, (h, l) in enumerate(zip(highs, lows)):
        mid = (h + l) / 2
        rows.append({
            "timestamp": base_ts + pd.Timedelta(minutes=15 * i),
            "open": mid, "high": h, "low": l, "close": mid,
            "volume": 100.0,
        })
    return pd.DataFrame(rows)


class TestDoubleTouchAlerts:
    def test_no_alert_single_touch(self):
        today = "2026-09-29"
        bars = _make_touch_bars(today, [4310.0, 4280.0, 4260.0], [4290.0, 4260.0, 4240.0])
        alerts = _double_touch_alerts(bars, today, {"PDH": 4310.0}, {}, atr=20.0)
        # Only one bar touches 4310 → no double top
        assert len(alerts) == 0

    def test_double_top_detected(self):
        today = "2026-09-29"
        # Two bars both approach PDH=4310 within tol=3 (ATR=20 × 0.15)
        bars = _make_touch_bars(today,
            [4309.0, 4280.0, 4308.0, 4270.0],
            [4290.0, 4260.0, 4290.0, 4250.0])
        alerts = _double_touch_alerts(bars, today, {"PDH": 4310.0}, {}, atr=20.0)
        assert len(alerts) == 1
        assert alerts[0]["touch_type"] == "double_top"
        assert alerts[0]["level_name"] == "PDH"

    def test_double_bottom_detected(self):
        today = "2026-09-29"
        # Two bars both approach PDL=4250 within tol=3
        bars = _make_touch_bars(today,
            [4310.0, 4280.0, 4310.0, 4280.0],
            [4290.0, 4251.0, 4290.0, 4252.0])
        alerts = _double_touch_alerts(bars, today, {}, {"PDL": 4250.0}, atr=20.0)
        assert len(alerts) == 1
        assert alerts[0]["touch_type"] == "double_bottom"

    def test_touch_count_in_alert(self):
        today = "2026-09-29"
        bars = _make_touch_bars(today,
            [4309.0, 4308.0, 4307.0, 4260.0],
            [4290.0, 4290.0, 4290.0, 4240.0])
        alerts = _double_touch_alerts(bars, today, {"PDH": 4310.0}, {}, atr=20.0)
        assert alerts[0]["touch_count"] == 3

    def test_empty_bars_returns_empty(self):
        empty = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        empty["timestamp"] = pd.to_datetime(empty["timestamp"], utc=True)
        assert _double_touch_alerts(empty, "2026-09-29", {"PDH": 4310.0}, {}, atr=20.0) == []

    def test_no_levels_returns_empty(self, bars, today_str):
        assert _double_touch_alerts(bars, today_str, {}, {}, atr=20.0) == []

    def test_alert_has_required_keys(self):
        today = "2026-09-29"
        bars = _make_touch_bars(today,
            [4309.0, 4280.0, 4308.0, 4270.0],
            [4290.0, 4260.0, 4290.0, 4250.0])
        alerts = _double_touch_alerts(bars, today, {"PDH": 4310.0}, {}, atr=20.0)
        required = {"level_name", "level_price", "touch_type", "touch_count",
                    "last_touch_time", "signal"}
        assert required <= set(alerts[0].keys())

    def test_server_offset_reports_corrected_touch_time(self):
        today = "2026-01-06"
        bars = _make_touch_bars(today, [4309.0, 4308.0], [4290.0, 4290.0])
        bars["timestamp"] = bars["timestamp"] + pd.Timedelta(hours=2)

        alerts = _double_touch_alerts(
            bars,
            today,
            {"PDH": 4310.0},
            {},
            atr=20.0,
            server_utc_offset_hours=2,
        )

        assert alerts[0]["last_touch_time"].startswith(f"{today} 00:15:00")

    def test_hierarchy_pdh_beats_pm_high(self):
        today = "2026-09-29"
        # Both PDH and PM_HIGH at same level — both get detected if both touched
        bars = _make_touch_bars(today,
            [4309.0, 4308.0, 4260.0, 4260.0],
            [4290.0, 4290.0, 4240.0, 4240.0])
        alerts = _double_touch_alerts(
            bars, today,
            {"PDH": 4310.0, "PM_HIGH": 4305.0}, {}, atr=20.0)
        names = {a["level_name"] for a in alerts}
        assert "PDH" in names


# ---------------------------------------------------------------------------
# _iv_walls
# ---------------------------------------------------------------------------

class TestIvWalls:
    def test_keys_present(self):
        w = _iv_walls(84000.0, 50.0)
        for k in ("iv_pct", "iv_expected_move_daily", "iv_high_90",
                  "iv_low_90", "iv_high_68", "iv_low_68"):
            assert k in w

    def test_90_pct_wider_than_68_pct(self):
        w = _iv_walls(84000.0, 50.0)
        assert w["iv_high_90"] > w["iv_high_68"]
        assert w["iv_low_90"]  < w["iv_low_68"]

    def test_walls_symmetric_around_price(self):
        price = 84000.0
        w = _iv_walls(price, 50.0)
        em = w["iv_expected_move_daily"]
        assert abs((w["iv_high_68"] - price) - em) < 0.1
        assert abs((price - w["iv_low_68"]) - em) < 0.1

    def test_90_pct_multiplier_approx_1645(self):
        price = 84000.0
        w = _iv_walls(price, 50.0)
        em = w["iv_expected_move_daily"]
        spread_90 = w["iv_high_90"] - price
        assert abs(spread_90 / em - 1.645) < 0.01

    def test_known_value_btc(self):
        # BTC $84k, IV 50%: daily_em = 84000 × 0.50 × sqrt(1/252) ≈ 2645
        import math
        expected_em = round(84000 * 0.50 * math.sqrt(1 / 252), 2)
        w = _iv_walls(84000.0, 50.0)
        assert abs(w["iv_expected_move_daily"] - expected_em) < 1.0

    def test_known_value_xau(self):
        # XAU $4150, IV 14%: daily_em ≈ 4150 × 0.14 × sqrt(1/252) ≈ 36.6
        import math
        expected_em = round(4150 * 0.14 * math.sqrt(1 / 252), 2)
        w = _iv_walls(4150.0, 14.0)
        assert abs(w["iv_expected_move_daily"] - expected_em) < 1.0

    def test_higher_iv_gives_wider_walls(self):
        low_iv  = _iv_walls(84000.0, 30.0)
        high_iv = _iv_walls(84000.0, 70.0)
        assert high_iv["iv_high_90"] > low_iv["iv_high_90"]
        assert high_iv["iv_low_90"]  < low_iv["iv_low_90"]

    def test_iv_pct_stored_correctly(self):
        w = _iv_walls(84000.0, 42.5)
        assert w["iv_pct"] == 42.5


# ---------------------------------------------------------------------------
# _multi_day_levels
# ---------------------------------------------------------------------------

class TestMultiDayLevels:
    def test_keys_present(self, bars, today_str):
        md = _multi_day_levels(bars, today_str)
        for k in ("prev_day", "prev_3d_high", "prev_3d_low", "prev_5d_high",
                  "prev_5d_low", "week_high", "week_low", "recent_days"):
            assert k in md, f"missing key: {k}"

    def test_prev_day_keys(self, bars, today_str):
        md = _multi_day_levels(bars, today_str)
        pd_ = md["prev_day"]
        for k in ("date", "open", "high", "low", "close"):
            assert k in pd_

    def test_prev_day_not_today(self, bars, today_str):
        md = _multi_day_levels(bars, today_str)
        assert md["prev_day"]["date"] < today_str

    def test_prev_day_high_ge_low(self, bars, today_str):
        md = _multi_day_levels(bars, today_str)
        assert md["prev_day"]["high"] >= md["prev_day"]["low"]

    def test_3d_range_within_5d_range(self, bars, today_str):
        md = _multi_day_levels(bars, today_str)
        assert md["prev_3d_high"] <= md["prev_5d_high"]
        assert md["prev_3d_low"]  >= md["prev_5d_low"]

    def test_week_high_ge_week_low(self, bars, today_str):
        md = _multi_day_levels(bars, today_str)
        if md["week_high"] is not None and md["week_low"] is not None:
            assert md["week_high"] >= md["week_low"]

    def test_empty_bars_returns_empty(self):
        empty = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close"])
        empty["timestamp"] = pd.to_datetime(empty["timestamp"], utc=True)
        assert _multi_day_levels(empty, "2026-09-29") == {}

    def test_no_bars_before_today(self, bars):
        earliest = str(sorted(set(bars["timestamp"].dt.date))[0])
        assert _multi_day_levels(bars, earliest) == {}

    def test_recent_days_count(self, bars, today_str):
        md = _multi_day_levels(bars, today_str, n_days=3)
        assert len(md["recent_days"]) <= 3


# ---------------------------------------------------------------------------
# _timeframe_structure
# ---------------------------------------------------------------------------

class TestTimeframeStructure:
    def test_keys_present(self, bars):
        tfs = _timeframe_structure(bars)
        assert "h1_structure" in tfs
        assert "m15_pattern" in tfs
        assert "combined_verdict" in tfs

    def test_h1_structure_valid_values(self, bars):
        tfs = _timeframe_structure(bars)
        assert tfs["h1_structure"] in ("BULLISH", "BEARISH", "NEUTRAL")

    def test_m15_pattern_valid_values(self, bars):
        tfs = _timeframe_structure(bars)
        assert tfs["m15_pattern"] in ("RANGE", "BREAKOUT", "REJECTION", "CONTINUATION")

    def test_combined_verdict_string(self, bars):
        tfs = _timeframe_structure(bars)
        assert isinstance(tfs["combined_verdict"], str)

    def test_short_bars_does_not_crash(self):
        """Fewer than 10 1H bars should default to NEUTRAL."""
        minimal = _make_bars(n_days=1)
        tfs = _timeframe_structure(minimal)
        assert tfs["h1_structure"] in ("BULLISH", "BEARISH", "NEUTRAL")


# ---------------------------------------------------------------------------
# _scenario_maps
# ---------------------------------------------------------------------------

SELL_SETUP = {
    "zone_high": 4320.0, "zone_low": 4310.0,
    "stop": 4330.0, "t1": 4280.0, "t2": 4260.0,
    "rr_t1": 2.5, "risk_pts": 15,
}
BUY_SETUP = {
    "zone_high": 4270.0, "zone_low": 4260.0,
    "stop": 4250.0, "t1": 4300.0, "t2": 4320.0,
    "rr_t1": 2.0, "risk_pts": 15,
}
MULTI_DAY = {
    "prev_day": {"high": 4340.0, "low": 4280.0, "open": 4300.0, "close": 4330.0, "date": "2026-09-25"},
    "prev_3d_high": 4350.0, "prev_3d_low": 4260.0,
    "prev_5d_high": 4360.0, "prev_5d_low": 4250.0,
    "week_high": 4355.0, "week_low": 4255.0,
    "recent_days": [],
}


class TestScenarioMaps:
    def test_returns_four_scenarios(self):
        scenes = _scenario_maps(4295.0, MULTI_DAY, SELL_SETUP, BUY_SETUP, 10.0)
        assert len(scenes) == 4

    def test_scenario_names(self):
        scenes = _scenario_maps(4295.0, MULTI_DAY, SELL_SETUP, BUY_SETUP, 10.0)
        names = {s["name"] for s in scenes}
        assert names == {"SELL_RETEST", "BUY_EXHAUST", "BREAKDOWN_CONT", "BREAKOUT_CONT"}

    def test_sell_retest_entry_zone(self):
        scenes = {s["name"]: s for s in _scenario_maps(4295.0, MULTI_DAY, SELL_SETUP, BUY_SETUP, 10.0)}
        s = scenes["SELL_RETEST"]
        assert s["entry"][0] == SELL_SETUP["zone_low"]
        assert s["entry"][1] == SELL_SETUP["zone_high"]

    def test_buy_exhaust_entry_zone(self):
        scenes = {s["name"]: s for s in _scenario_maps(4295.0, MULTI_DAY, SELL_SETUP, BUY_SETUP, 10.0)}
        b = scenes["BUY_EXHAUST"]
        assert b["entry"][0] == BUY_SETUP["zone_low"]
        assert b["entry"][1] == BUY_SETUP["zone_high"]

    def test_breakdown_entry_below_prev_day_low(self):
        scenes = {s["name"]: s for s in _scenario_maps(4295.0, MULTI_DAY, SELL_SETUP, BUY_SETUP, 10.0)}
        bd = scenes["BREAKDOWN_CONT"]
        pd_low = MULTI_DAY["prev_day"]["low"]
        assert bd["entry"][1] < pd_low

    def test_breakout_entry_above_prev_day_high(self):
        scenes = {s["name"]: s for s in _scenario_maps(4295.0, MULTI_DAY, SELL_SETUP, BUY_SETUP, 10.0)}
        bk = scenes["BREAKOUT_CONT"]
        pd_high = MULTI_DAY["prev_day"]["high"]
        assert bk["entry"][0] > pd_high

    def test_rr_t1_positive(self):
        scenes = _scenario_maps(4295.0, MULTI_DAY, SELL_SETUP, BUY_SETUP, 10.0)
        for s in scenes:
            assert s["rr_t1"] > 0, f"{s['name']} has rr_t1 <= 0"

    def test_no_prev_day_returns_two_scenarios(self):
        md_no_pd = {**MULTI_DAY, "prev_day": {}}
        scenes = _scenario_maps(4295.0, md_no_pd, SELL_SETUP, BUY_SETUP, 10.0)
        names = {s["name"] for s in scenes}
        assert "BREAKDOWN_CONT" not in names
        assert "BREAKOUT_CONT" not in names

    def test_each_scenario_has_required_keys(self):
        required = {"name", "condition", "entry", "stop", "t1", "t2",
                    "rr_t1", "rr_t2", "risk_pts", "confidence_base", "invalidation"}
        scenes = _scenario_maps(4295.0, MULTI_DAY, SELL_SETUP, BUY_SETUP, 10.0)
        for s in scenes:
            missing = required - s.keys()
            assert not missing, f"{s['name']} missing keys: {missing}"
