"""Tests for arsb_v1 D1 trend alignment gate."""
from __future__ import annotations

import pandas as pd

from tar_system.strategies.arsb_v1 import ArsbV1


def _row(
    close: float,
    asian_high: float = 2400.0,
    asian_low: float = 2390.0,
    atr: float = 2.0,
    hour_utc: int = 9,
    ts: str = "2026-07-17 09:00:00",
) -> pd.Series:
    asian_range = asian_high - asian_low
    return pd.Series(
        {
            "timestamp": pd.Timestamp(ts),
            "close": close,
            "atr": atr,
            "asian_high": asian_high,
            "asian_low": asian_low,
            "asian_range": asian_range,
            "asian_mid": (asian_high + asian_low) / 2,
            "hour_utc": hour_utc,
            "symbol": "XAUUSD",
            "timeframe": "M15",
        }
    )


def _trend(ema20: float, ema50: float, slope: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "available_from": [pd.Timestamp("2026-07-17")],
            "ema20": [ema20],
            "ema50": [ema50],
            "close_slope_5": [slope],
        }
    )


def test_d1_uptrend_allows_buy_and_suppresses_sell(monkeypatch) -> None:
    monkeypatch.setattr("tar_system.strategies.arsb_v1._load_d1_trend", lambda _: _trend(2450.0, 2400.0, 12.0))
    strategy = ArsbV1()

    assert strategy.generate_signal(_row(2402.0), regime="TRENDING").side == "BUY"
    assert strategy.generate_signal(_row(2388.0), regime="TRENDING").side == "HOLD"


def test_d1_downtrend_allows_sell_and_suppresses_buy(monkeypatch) -> None:
    monkeypatch.setattr("tar_system.strategies.arsb_v1._load_d1_trend", lambda _: _trend(2400.0, 2450.0, -12.0))
    strategy = ArsbV1()

    assert strategy.generate_signal(_row(2388.0), regime="TRENDING").side == "SELL"
    assert strategy.generate_signal(_row(2402.0), regime="TRENDING").side == "HOLD"


def test_d1_choppy_state_suppresses_all_entries(monkeypatch) -> None:
    monkeypatch.setattr("tar_system.strategies.arsb_v1._load_d1_trend", lambda _: _trend(2450.0, 2400.0, -1.0))
    strategy = ArsbV1()

    assert strategy.generate_signal(_row(2402.0), regime="TRENDING").side == "HOLD"
    assert strategy.generate_signal(_row(2388.0), regime="TRENDING").side == "HOLD"


def test_d1_trend_filter_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setattr("tar_system.strategies.arsb_v1._load_d1_trend", lambda _: _trend(2450.0, 2400.0, -1.0))
    strategy = ArsbV1(d1_trend_filter=False)

    assert strategy.generate_signal(_row(2402.0), regime="TRENDING").side == "BUY"
    assert strategy.generate_signal(_row(2388.0), regime="TRENDING").side == "SELL"
