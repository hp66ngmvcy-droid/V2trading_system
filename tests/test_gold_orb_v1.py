"""Tests for gold_orb_v1 — Opening Range Breakout strategy."""
from __future__ import annotations

import pandas as pd
import pytest

from tar_system.strategies.gold_orb_v1 import GoldOrbV1


def _row(
    close: float,
    orb_high: float = 2400.0,
    orb_low: float = 2390.0,
    atr: float = 3.0,
    hour_utc: int = 10,
    ts: str = "2026-07-17 10:00:00",
) -> pd.Series:
    orb_range = orb_high - orb_low
    return pd.Series({
        "timestamp": pd.Timestamp(ts),
        "close": close,
        "atr": atr,
        "orb_high": orb_high,
        "orb_low": orb_low,
        "orb_range": orb_range,
        "hour_utc": hour_utc,
        "symbol": "XAUUSD",
        "timeframe": "M15",
    })


# ── Defaults ─────────────────────────────────────────────────────────────────

def test_default_params() -> None:
    s = GoldOrbV1()
    assert s.buffer_mult == 0.10
    assert s.reward_risk == 3.0
    assert s.entry_start_hour == 6
    assert s.entry_end_hour == 20
    assert s.range_min_pts == 4.0
    assert s.range_max_pts == 60.0


# ── HOLD cases ────────────────────────────────────────────────────────────────

def test_hold_inside_range() -> None:
    s = GoldOrbV1()
    sig = s.generate_signal(_row(2395.0), regime="TRENDING")
    assert sig.side == "HOLD"


def test_hold_outside_session() -> None:
    s = GoldOrbV1()
    sig = s.generate_signal(_row(2405.0, hour_utc=3), regime="TRENDING")
    assert sig.side == "HOLD"


def test_hold_atr_above_cap() -> None:
    s = GoldOrbV1()
    sig = s.generate_signal(_row(2405.0, atr=15.0), regime="TRENDING")
    assert sig.side == "HOLD"


def test_hold_range_too_small() -> None:
    s = GoldOrbV1()
    # orb_range = 1.0 < range_min_pts=4.0
    sig = s.generate_signal(_row(2401.5, orb_high=2401.0, orb_low=2400.0, atr=1.0), regime="TRENDING")
    assert sig.side == "HOLD"


def test_hold_range_too_large() -> None:
    s = GoldOrbV1()
    # orb_range = 80 > range_max_pts=60
    sig = s.generate_signal(_row(2481.0, orb_high=2480.0, orb_low=2400.0), regime="TRENDING")
    assert sig.side == "HOLD"


def test_hold_no_orb_data() -> None:
    s = GoldOrbV1()
    row = _row(2405.0)
    row["orb_high"] = float("nan")
    row["orb_low"] = float("nan")
    row["orb_range"] = float("nan")
    sig = s.generate_signal(row, regime="TRENDING")
    assert sig.side == "HOLD"


# ── BUY breakout ──────────────────────────────────────────────────────────────

def test_buy_above_orb_high_plus_buffer() -> None:
    s = GoldOrbV1()
    # orb_high=2400, range=10, buffer=10*0.10=1.0 → breakout_long=2401.0
    sig = s.generate_signal(_row(2402.0, orb_high=2400.0, orb_low=2390.0), regime="TRENDING")
    assert sig.side == "BUY"


def test_buy_stop_at_orb_low() -> None:
    s = GoldOrbV1()
    sig = s.generate_signal(_row(2402.0, orb_high=2400.0, orb_low=2390.0), regime="TRENDING")
    assert sig.stop_loss == pytest.approx(2390.0)


def test_buy_tp_3x_range() -> None:
    s = GoldOrbV1()
    # entry=2402, range=10, TP = 2402 + 10*3.0 = 2432
    sig = s.generate_signal(_row(2402.0, orb_high=2400.0, orb_low=2390.0), regime="TRENDING")
    assert sig.take_profit == pytest.approx(2402.0 + 10.0 * 3.0)


def test_buy_not_triggered_at_orb_high_exactly() -> None:
    s = GoldOrbV1()
    # close == orb_high, not above breakout_long (needs > orb_high + buffer)
    sig = s.generate_signal(_row(2400.0, orb_high=2400.0, orb_low=2390.0), regime="TRENDING")
    assert sig.side == "HOLD"


# ── SELL breakdown ────────────────────────────────────────────────────────────

def test_sell_below_orb_low_minus_buffer() -> None:
    s = GoldOrbV1()
    # orb_low=2390, buffer=1.0 → breakout_short=2389.0
    sig = s.generate_signal(_row(2388.0, orb_high=2400.0, orb_low=2390.0), regime="TRENDING")
    assert sig.side == "SELL"


def test_sell_stop_at_orb_high() -> None:
    s = GoldOrbV1()
    sig = s.generate_signal(_row(2388.0, orb_high=2400.0, orb_low=2390.0), regime="TRENDING")
    assert sig.stop_loss == pytest.approx(2400.0)


def test_sell_tp_3x_range_below_entry() -> None:
    s = GoldOrbV1()
    sig = s.generate_signal(_row(2388.0, orb_high=2400.0, orb_low=2390.0), regime="TRENDING")
    assert sig.take_profit == pytest.approx(2388.0 - 10.0 * 3.0)


def test_one_trade_per_day_blocks_second_same_day_signal() -> None:
    s = GoldOrbV1()
    first = s.generate_signal(
        _row(2402.0, orb_high=2400.0, orb_low=2390.0, ts="2026-07-17 10:00:00"),
        regime="TRENDING",
    )
    second = s.generate_signal(
        _row(2388.0, orb_high=2400.0, orb_low=2390.0, ts="2026-07-17 14:00:00"),
        regime="TRENDING",
    )
    third = s.generate_signal(
        _row(2388.0, orb_high=2400.0, orb_low=2390.0, ts="2026-07-18 10:00:00"),
        regime="TRENDING",
    )

    assert first.side == "BUY"
    assert second.side == "HOLD"
    assert third.side == "SELL"


def test_one_trade_per_day_can_be_disabled() -> None:
    s = GoldOrbV1(one_trade_per_day=False)
    first = s.generate_signal(
        _row(2402.0, orb_high=2400.0, orb_low=2390.0, ts="2026-07-17 10:00:00"),
        regime="TRENDING",
    )
    second = s.generate_signal(
        _row(2388.0, orb_high=2400.0, orb_low=2390.0, ts="2026-07-17 14:00:00"),
        regime="TRENDING",
    )

    assert first.side == "BUY"
    assert second.side == "SELL"


def test_reset_state_clears_one_trade_per_day_memory() -> None:
    s = GoldOrbV1()
    first = s.generate_signal(
        _row(2402.0, orb_high=2400.0, orb_low=2390.0, ts="2026-07-17 10:00:00"),
        regime="TRENDING",
    )
    blocked = s.generate_signal(
        _row(2388.0, orb_high=2400.0, orb_low=2390.0, ts="2026-07-17 14:00:00"),
        regime="TRENDING",
    )
    s.reset_state()
    after_reset = s.generate_signal(
        _row(2388.0, orb_high=2400.0, orb_low=2390.0, ts="2026-07-17 14:00:00"),
        regime="TRENDING",
    )

    assert first.side == "BUY"
    assert blocked.side == "HOLD"
    assert after_reset.side == "SELL"


# ── Registry ──────────────────────────────────────────────────────────────────

def test_registry_contains_gold_orb_v1() -> None:
    from tar_system.strategies.registry import REGISTRY
    assert "gold_orb_v1" in REGISTRY


def test_get_strategy_by_name() -> None:
    from tar_system.strategies.registry import get_strategy
    s = get_strategy("gold_orb_v1")
    assert isinstance(s, GoldOrbV1)


def test_get_strategy_with_custom_params() -> None:
    from tar_system.strategies.registry import get_strategy
    s = get_strategy("gold_orb_v1", reward_risk=2.0, buffer_mult=0.05)
    assert s.reward_risk == 2.0
    assert s.buffer_mult == 0.05
