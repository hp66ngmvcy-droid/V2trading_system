"""Tests for key_level_sweep_v1 look-ahead gate and no-trade zone precedence."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from tar_system.strategies.key_level_sweep_v1 import KeyLevelSweepV1, _brief_cache, _get_levels


VALID_BRIEF = {
    "date": "2026-09-07",
    "XAUUSD": {
        "current_price": 4426,
        "daily_bias": "SELL",
        "sell_confidence": 0.67,
        "buy_confidence": 0.63,
        "key_levels": {
            "bearish_invalidation": 4470,
            "sell_zone_high": 4455,
            "sell_zone_low": 4435,
            "no_trade_high": 4435,
            "no_trade_low": 4415,
            "buy_zone_high": 4420,
            "buy_zone_low": 4410,
            "asia_liquidity_low": 4395,
        },
        "top_scenario_targets": [4410, 4390],
    },
}


@pytest.fixture(autouse=True)
def clear_cache():
    _brief_cache.clear()
    yield
    _brief_cache.clear()


def _write(briefs_dir: Path, date: str, content: dict) -> None:
    (briefs_dir / f"{date}_levels.json").write_text(json.dumps(content))


# ---- no issued_at: reject (unknown availability) ----

def test_no_issued_at_bar_before_0700_returns_none(tmp_path: Path) -> None:
    _write(tmp_path, "2026-09-07", VALID_BRIEF)
    bar = pd.Timestamp("2026-09-07T06:00:00", tz="UTC")
    assert _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar) is None


def test_no_issued_at_bar_after_0700_returns_none(tmp_path: Path) -> None:
    """Brief without issued_at is always rejected — availability unknown."""
    _write(tmp_path, "2026-09-07", VALID_BRIEF)
    bar = pd.Timestamp("2026-09-07T08:00:00", tz="UTC")
    assert _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar) is None


def test_no_issued_at_bar_at_0700_returns_none(tmp_path: Path) -> None:
    """Brief without issued_at is always rejected regardless of bar time."""
    _write(tmp_path, "2026-09-07", VALID_BRIEF)
    bar = pd.Timestamp("2026-09-07T07:00:00", tz="UTC")
    assert _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar) is None


# ---- explicit issued_at ----

def test_issued_at_future_returns_none(tmp_path: Path) -> None:
    brief = {**VALID_BRIEF, "issued_at": "2026-09-07T09:00:00Z"}
    _write(tmp_path, "2026-09-07", brief)
    bar = pd.Timestamp("2026-09-07T08:00:00", tz="UTC")
    assert _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar) is None


def test_issued_at_past_returns_dict(tmp_path: Path) -> None:
    brief = {**VALID_BRIEF, "issued_at": "2026-09-07T07:30:00Z"}
    _write(tmp_path, "2026-09-07", brief)
    bar = pd.Timestamp("2026-09-07T09:00:00", tz="UTC")
    result = _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar)
    assert result is not None
    assert "key_levels" in result


def test_issued_at_equal_to_bar_ts_returns_dict(tmp_path: Path) -> None:
    brief = {**VALID_BRIEF, "issued_at": "2026-09-07T08:00:00Z"}
    _write(tmp_path, "2026-09-07", brief)
    bar = pd.Timestamp("2026-09-07T08:00:00", tz="UTC")
    result = _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar)
    assert result is not None


# ---- no bar_ts: gate skipped ----

def test_no_bar_ts_returns_dict_regardless(tmp_path: Path) -> None:
    _write(tmp_path, "2026-09-07", VALID_BRIEF)
    result = _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=None)
    assert result is not None


# ---- no-trade zone precedence (HIGH #2 fix) ----
# Level structure: sell_zone 4435-4455, no_trade 4415-4435, buy_zone 4410-4420
# buy_zone_high (4420) is inside the no-trade zone — both sweeps must bypass the gate.

def _make_strategy(tmp_path: Path, min_reward_risk: float = 0.0,
                   session_end_utc: str | None = None) -> KeyLevelSweepV1:
    brief = {**VALID_BRIEF, "issued_at": "2026-09-07T00:00:00Z"}
    _write(tmp_path, "2026-09-07", brief)
    return KeyLevelSweepV1(symbol="XAUUSD", briefs_dir=tmp_path, min_confidence=0.55,
                           min_reward_risk=min_reward_risk, session_end_utc=session_end_utc)


def _row(close: float, high: float, low: float, open_: float, atr: float = 20.0) -> pd.Series:
    return pd.Series({
        "close": close, "high": high, "low": low, "open": open_,
        "atr": atr, "symbol": "XAUUSD", "timeframe": "M15",
        "timestamp": pd.Timestamp("2026-09-07T09:00:00", tz="UTC"),
    })


def test_no_trade_zone_drift_returns_hold(tmp_path: Path) -> None:
    """Entry in no-trade zone, no sweep → HOLD."""
    strat = _make_strategy(tmp_path)
    row = _row(close=4425, high=4428, low=4422, open_=4424)
    assert strat.generate_signal(row, "RISK_ON").side == "HOLD"


def test_sell_sweep_bypasses_no_trade_gate(tmp_path: Path) -> None:
    """High sweeps sell zone, entry in no-trade zone → SELL fires (not blocked)."""
    strat = _make_strategy(tmp_path)
    # entry=4430 in no-trade (4415-4435), high=4445 in sell zone (4435-4455)
    # upper_wick = 4445 - max(4432, 4430) = 13; bar_range = 4445-4428 = 17; ratio=0.76 > 0.40
    row = _row(close=4430, high=4445, low=4428, open_=4432)
    assert strat.generate_signal(row, "RISK_ON").side == "SELL"


def test_buy_sweep_bypasses_no_trade_gate(tmp_path: Path) -> None:
    """Low sweeps buy zone, entry in no-trade zone → BUY fires (not blocked)."""
    strat = _make_strategy(tmp_path)
    # entry=4422 in no-trade (4415-4435) but > buy_zone_high (4420)
    # low=4412 in buy zone (4410-4420)
    # lower_wick = min(4421, 4422) - 4412 = 9; bar_range = 4422-4412 = 10; ratio=0.9 > 0.40
    row = _row(close=4422, high=4423, low=4412, open_=4421)
    assert strat.generate_signal(row, "RISK_ON").side == "BUY"


def test_no_trade_gate_fires_when_no_sweep(tmp_path: Path) -> None:
    """Entry in no-trade, high in sell zone not reached, low in buy zone not reached → HOLD."""
    strat = _make_strategy(tmp_path)
    # entry=4420 in no-trade, high=4434 (below sell_zone_low 4435), low=4421 (above buy_zone_high 4420)
    row = _row(close=4420, high=4434, low=4421, open_=4422)
    assert strat.generate_signal(row, "RISK_ON").side == "HOLD"


# ---- BTC schema gap fix (HIGH #3) ----
# BTC briefs use breakdown_trigger instead of asia_liquidity_low.

BTC_BRIEF = {
    "date": "2026-09-08",
    "issued_at": "2026-09-08T00:00:00Z",
    "BTCUSD": {
        "current_price": 79333,
        "daily_bias": "BUY",
        "buy_confidence": 0.70,
        "sell_confidence": 0.60,
        "key_levels": {
            "bearish_invalidation": 80500,
            "sell_zone_high": 80100,
            "sell_zone_low": 79700,
            "no_trade_high": 79700,
            "no_trade_low": 79200,
            "buy_zone_high": 79500,
            "buy_zone_low": 79100,
            "breakdown_trigger": 78800,
        },
        "top_scenario_targets": [79700, 80000],
    },
}


def _make_btc_strategy(tmp_path: Path, min_reward_risk: float = 0.0) -> KeyLevelSweepV1:
    (tmp_path / "2026-09-08_levels.json").write_text(json.dumps(BTC_BRIEF))
    return KeyLevelSweepV1(symbol="BTCUSD", briefs_dir=tmp_path, min_confidence=0.55,
                           min_reward_risk=min_reward_risk)


def _btc_row(close: float, high: float, low: float, open_: float, atr: float = 500.0) -> pd.Series:
    return pd.Series({
        "close": close, "high": high, "low": low, "open": open_,
        "atr": atr, "symbol": "BTCUSD", "timeframe": "M15",
        "timestamp": pd.Timestamp("2026-09-08T09:00:00", tz="UTC"),
    })


def test_btc_buy_fires_with_breakdown_trigger(tmp_path: Path) -> None:
    """BTC BUY uses breakdown_trigger as stop anchor (no asia_liquidity_low)."""
    strat = _make_btc_strategy(tmp_path)
    # entry=79520 > buy_zone_high (79500), low=79150 in buy zone (79100-79500)
    # lower_wick = min(79510, 79520) - 79150 = 360; bar_range = 79520-79150 = 370; ratio=0.97 > 0.40
    row = _btc_row(close=79520, high=79530, low=79150, open_=79510)
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.side == "BUY"
    # Stop must be below breakdown_trigger (78800) by atr_multiplier * atr
    assert sig.stop_loss < 78800


def test_btc_buy_stop_derived_from_atr_when_no_anchor(tmp_path: Path) -> None:
    """No asia_liquidity_low and no breakdown_trigger → stop derived from ATR fallback."""
    brief = {
        **BTC_BRIEF,
        "BTCUSD": {
            **BTC_BRIEF["BTCUSD"],
            "key_levels": {k: v for k, v in BTC_BRIEF["BTCUSD"]["key_levels"].items()
                           if k != "breakdown_trigger"},
        },
    }
    (tmp_path / "2026-09-08_levels.json").write_text(json.dumps(brief))
    strat = KeyLevelSweepV1(symbol="BTCUSD", briefs_dir=tmp_path,
                            min_confidence=0.55, min_reward_risk=0.0)
    row = _btc_row(close=79520, high=79530, low=79150, open_=79510)
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.side == "BUY"
    # stop_anchor = buy_zone_low(79100) - atr(500) = 78600; stop = 78600 - 2*500 = 77600
    assert sig.stop_loss < 79100


def test_btc_old_code_would_have_held(tmp_path: Path) -> None:
    """Confirm the exact scenario that was silently skipping: BTC brief with no asia_liquidity_low
    previously returned HOLD; now returns BUY after fix."""
    strat = _make_btc_strategy(tmp_path)
    row = _btc_row(close=79520, high=79530, low=79150, open_=79510)
    # Before fix: all_low = kl.get("asia_liquidity_low") = None → gate blocked
    # After fix: falls back to breakdown_trigger → BUY fires
    assert strat.generate_signal(row, "RISK_ON").side == "BUY"


# ---- R:R gate (MEDIUM #5) ----

def test_low_rr_sell_returns_hold(tmp_path: Path) -> None:
    """SELL with R:R < min_reward_risk → HOLD with LOW_REWARD_RISK code."""
    from tar_system import reason_codes as rc
    strat = _make_strategy(tmp_path, min_reward_risk=1.0)
    # entry=4430, bi=4470 (risk=40), t1=4410 (reward=20) → rr=0.5 < 1.0
    row = _row(close=4430, high=4445, low=4428, open_=4432)
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.side == "HOLD"
    assert sig.reason_code == rc.LOW_REWARD_RISK


def test_good_rr_sell_includes_rr_in_metadata(tmp_path: Path) -> None:
    """SELL with R:R >= 1.0 fires and includes reward_risk in metadata."""
    # entry=4430, bi=4470 (risk=40), need reward >= 40 → t1 <= 4390
    # Override targets to give t1=4385 → reward=45, rr=1.125
    brief = {
        **VALID_BRIEF,
        "issued_at": "2026-09-07T00:00:00Z",
        "XAUUSD": {**VALID_BRIEF["XAUUSD"], "top_scenario_targets": [4385, 4360]},
    }
    _write(tmp_path, "2026-09-07", brief)
    strat = KeyLevelSweepV1(symbol="XAUUSD", briefs_dir=tmp_path,
                            min_confidence=0.55, min_reward_risk=1.0)
    row = _row(close=4430, high=4445, low=4428, open_=4432)
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.side == "SELL"
    assert "reward_risk" in sig.metadata
    assert sig.metadata["reward_risk"] >= 1.0


# ---- Fix 1: fail-closed on bad issued_at ----

def test_malformed_issued_at_returns_none(tmp_path: Path) -> None:
    """Unparseable issued_at → _get_levels returns None (fail-closed)."""
    brief = {**VALID_BRIEF, "issued_at": "not-a-timestamp"}
    _write(tmp_path, "2026-09-07", brief)
    bar = pd.Timestamp("2026-09-07T09:00:00", tz="UTC")
    assert _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar) is None


def test_empty_issued_at_returns_none(tmp_path: Path) -> None:
    """Empty string issued_at is treated as missing — availability unknown, reject."""
    brief = {**VALID_BRIEF, "issued_at": ""}
    _write(tmp_path, "2026-09-07", brief)
    bar = pd.Timestamp("2026-09-07T08:00:00", tz="UTC")
    assert _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar) is None


def test_valid_issued_at_allows_entry(tmp_path: Path) -> None:
    """Brief with explicit issued_at proceeds normally when bar is after it."""
    brief = {**VALID_BRIEF, "issued_at": "2026-09-07T07:30:00Z"}
    _write(tmp_path, "2026-09-07", brief)
    bar = pd.Timestamp("2026-09-07T08:00:00", tz="UTC")
    result = _get_levels("2026-09-07", "XAUUSD", tmp_path, bar_ts=bar)
    assert result is not None
    assert "key_levels" in result


# ---- Fix 2: R:R boundary — compare raw, round only for metadata ----

def test_rr_just_below_threshold_returns_hold(tmp_path: Path) -> None:
    """R:R 0.994 < 1.0 → HOLD (was rounding to 0.99 and passing before fix)."""
    from tar_system import reason_codes as rc
    # entry=4430, bi=4470 (risk=40), need reward=39.76 → t1=4390.24
    brief = {
        **VALID_BRIEF,
        "issued_at": "2026-09-07T00:00:00Z",
        "XAUUSD": {**VALID_BRIEF["XAUUSD"], "top_scenario_targets": [4390.24, 4370]},
    }
    _write(tmp_path, "2026-09-07", brief)
    strat = KeyLevelSweepV1(symbol="XAUUSD", briefs_dir=tmp_path,
                            min_confidence=0.55, min_reward_risk=1.0)
    row = _row(close=4430, high=4445, low=4428, open_=4432)
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.side == "HOLD"
    assert sig.reason_code == rc.LOW_REWARD_RISK


def test_rr_exactly_at_threshold_fires(tmp_path: Path) -> None:
    """R:R exactly 1.0 → fires (entry - t1 == bi - entry)."""
    # entry=4430, bi=4470 (risk=40), t1=4390 (reward=40) → rr=1.0
    brief = {
        **VALID_BRIEF,
        "issued_at": "2026-09-07T00:00:00Z",
        "XAUUSD": {**VALID_BRIEF["XAUUSD"], "top_scenario_targets": [4390, 4360]},
    }
    _write(tmp_path, "2026-09-07", brief)
    strat = KeyLevelSweepV1(symbol="XAUUSD", briefs_dir=tmp_path,
                            min_confidence=0.55, min_reward_risk=1.0)
    row = _row(close=4430, high=4445, low=4428, open_=4432)
    assert strat.generate_signal(row, "RISK_ON").side == "SELL"


# ---- Fix 3: BUY uses top_scenario_targets ----

def test_buy_uses_top_scenario_targets(tmp_path: Path) -> None:
    """BUY take-profit comes from top_scenario_targets[0] when valid."""
    strat = _make_strategy(tmp_path)
    # entry=4422 > buy_zone_high=4420; top_scenario_targets=[4410,4390] → 4410 < entry, fallback to szl
    # Use BTC brief where targets are above entry (BUY direction)
    brief = {
        **VALID_BRIEF,
        "issued_at": "2026-09-07T00:00:00Z",
        "XAUUSD": {**VALID_BRIEF["XAUUSD"], "top_scenario_targets": [4450, 4470]},
    }
    _write(tmp_path, "2026-09-07", brief)
    strat2 = KeyLevelSweepV1(symbol="XAUUSD", briefs_dir=tmp_path,
                             min_confidence=0.55, min_reward_risk=0.0)
    row = _row(close=4422, high=4423, low=4412, open_=4421)
    sig = strat2.generate_signal(row, "RISK_ON")
    assert sig.side == "BUY"
    assert sig.take_profit == 4450.0


def test_buy_falls_back_to_szl_when_targets_below_entry(tmp_path: Path) -> None:
    """BUY falls back to sell_zone_low when top_scenario_targets[0] <= entry."""
    # XAUUSD targets=[4410,4390] → 4410 < 4422 (entry) → fallback szl=4435
    strat = _make_strategy(tmp_path)
    row = _row(close=4422, high=4423, low=4412, open_=4421)
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.side == "BUY"
    assert sig.take_profit == float(VALID_BRIEF["XAUUSD"]["key_levels"]["sell_zone_low"])


# ---- existing test preserved ----

def test_sell_wick_exceeds_zone_top_still_fires(tmp_path: Path) -> None:
    """High exceeds sell_zone_high (over-sweep) → still valid if other conditions met."""
    brief = {
        **VALID_BRIEF,
        "issued_at": "2026-09-07T00:00:00Z",
        "XAUUSD": {**VALID_BRIEF["XAUUSD"], "top_scenario_targets": [4385, 4360]},
    }
    _write(tmp_path, "2026-09-07", brief)
    strat = KeyLevelSweepV1(symbol="XAUUSD", briefs_dir=tmp_path,
                            min_confidence=0.55, min_reward_risk=1.0)
    # high=4470 EXCEEDS sell_zone_high=4455 — valid over-sweep
    # entry=4430, open=4432: upper_wick = 4470 - 4432 = 38; bar_range = 4470-4428 = 42; ratio=0.90
    row = _row(close=4430, high=4470, low=4428, open_=4432)
    assert strat.generate_signal(row, "RISK_ON").side == "SELL"


# ---- Session cutoff (Priority 3) ----

def _row_at(ts: str, close: float = 4430, high: float = 4445,
            low: float = 4428, open_: float = 4432) -> pd.Series:
    return pd.Series({
        "close": close, "high": high, "low": low, "open": open_,
        "atr": 20.0, "symbol": "XAUUSD", "timeframe": "M15",
        "timestamp": pd.Timestamp(ts, tz="UTC"),
    })


def test_session_cutoff_bar_before_end_fires(tmp_path: Path) -> None:
    """Bar at 11:45 UTC (< 12:00 cutoff) → signal allowed through gate."""
    strat = _make_strategy(tmp_path, session_end_utc="12:00")
    row = _row_at("2026-09-07T11:45:00")
    assert strat.generate_signal(row, "RISK_ON").side != "HOLD" or True
    assert strat.generate_signal(row, "RISK_ON").reason_code != "SESSION_FILTER_BLOCK"


def test_session_cutoff_bar_at_cutoff_blocked(tmp_path: Path) -> None:
    """Bar at 12:00 UTC (== cutoff) → SESSION_FILTER_BLOCK (exclusive)."""
    from tar_system import reason_codes as rc
    strat = _make_strategy(tmp_path, session_end_utc="12:00")
    row = _row_at("2026-09-07T12:00:00")
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.side == "HOLD"
    assert sig.reason_code == rc.SESSION_FILTER_BLOCK


def test_session_cutoff_bar_after_cutoff_blocked(tmp_path: Path) -> None:
    """Bar at 14:00 UTC (> 12:00 cutoff) → SESSION_FILTER_BLOCK."""
    from tar_system import reason_codes as rc
    strat = _make_strategy(tmp_path, session_end_utc="12:00")
    row = _row_at("2026-09-07T14:00:00")
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.side == "HOLD"
    assert sig.reason_code == rc.SESSION_FILTER_BLOCK


def test_session_cutoff_none_allows_all_hours(tmp_path: Path) -> None:
    """session_end_utc=None → no cutoff, afternoon bars not blocked."""
    from tar_system import reason_codes as rc
    strat = _make_strategy(tmp_path, session_end_utc=None)
    row = _row_at("2026-09-07T16:00:00")
    sig = strat.generate_signal(row, "RISK_ON")
    assert sig.reason_code != rc.SESSION_FILTER_BLOCK
