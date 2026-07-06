from __future__ import annotations

import pandas as pd

from tar_system.signals.clear_read import generate_clear_read


def _row(**updates: object) -> pd.Series:
    payload: dict[str, object] = {
        "timestamp": pd.Timestamp("2026-01-01 08:00:00", tz="UTC"),
        "symbol": "BTCUSD",
        "timeframe": "H1",
        "open": 100.0,
        "high": 102.0,
        "low": 95.0,
        "close": 100.6,
        "ema_fast": 101.0,
        "ema_slow": 99.0,
        "ema_fast_slope": 0.001,
        "rsi": 58.0,
        "atr": 2.0,
        "macd": 1.2,
        "macd_signal": 0.9,
        "volume": 150.0,
        "volume_sma": 100.0,
        "prior_rolling_high": 103.0,
        "prior_rolling_low": 98.0,
        "is_liquid_session": True,
    }
    payload.update(updates)
    return pd.Series(payload)


def test_clear_read_long_when_all_local_reads_align() -> None:
    read = generate_clear_read(_row(), "TRENDING", {"risk_approved": True, "risk_reason": "RISK_APPROVED"})

    assert read.side == "LONG"
    assert read.paper_only is True
    assert read.risk_approved is True
    assert read.entry_reference == 100.6
    assert "CLEAR_READ_MOMENTUM_BULLISH" in read.reasons
    assert "CLEAR_READ_PRESSURE_BULLISH" in read.reasons
    assert "CLEAR_READ_LIQUIDITY_BULLISH" in read.reasons


def test_clear_read_short_when_all_local_reads_align() -> None:
    read = generate_clear_read(
        _row(
            open=101.0,
            high=105.0,
            low=98.0,
            close=100.4,
            ema_fast=99.0,
            ema_slow=101.0,
            ema_fast_slope=-0.001,
            rsi=42.0,
            macd=-1.0,
            macd_signal=-0.5,
            prior_rolling_high=103.0,
            prior_rolling_low=97.0,
        ),
        "TRENDING",
        {"risk_approved": True, "risk_reason": "RISK_APPROVED"},
    )

    assert read.side == "SHORT"
    assert read.confidence >= 0.65
    assert "CLEAR_READ_LIQUIDITY_BEARISH" in read.reasons


def test_clear_read_waits_on_regime_block() -> None:
    read = generate_clear_read(_row(), "VOLATILE", {"risk_approved": True, "risk_reason": "RISK_APPROVED"})

    assert read.side == "WAIT"
    assert read.confidence == 0.0
    assert "CLEAR_READ_REGIME_BLOCK_VOLATILE" in read.reasons


def test_clear_read_waits_on_paper_risk_block() -> None:
    read = generate_clear_read(_row(), "TRENDING", {"risk_approved": False, "risk_reason": "DAILY_LOSS_LIMIT"})

    assert read.side == "WAIT"
    assert read.risk_reason == "DAILY_LOSS_LIMIT"
    assert "CLEAR_READ_RISK_BLOCK" in read.reasons


def test_clear_read_waits_when_required_column_missing() -> None:
    row = _row().drop(labels=["prior_rolling_low"])

    read = generate_clear_read(row, "TRENDING", {"risk_approved": True, "risk_reason": "RISK_APPROVED"})

    assert read.side == "WAIT"
    assert "CLEAR_READ_MISSING_COLUMNS" in read.reasons
    assert read.metadata["missing_columns"] == ["prior_rolling_low"]


def test_clear_read_caps_confidence_without_volume_confirmation() -> None:
    row = _row().drop(labels=["volume_sma"])

    read = generate_clear_read(row, "TRENDING", {"risk_approved": True, "risk_reason": "RISK_APPROVED"})

    assert read.side == "WAIT"
    assert read.confidence == 0.6
    assert "CLEAR_READ_CAP_VOLUME_UNAVAILABLE" in read.reasons


def test_clear_read_ranging_regime_stays_wait_even_when_aligned() -> None:
    read = generate_clear_read(_row(), "RANGING", {"risk_approved": True, "risk_reason": "RISK_APPROVED"})

    assert read.side == "WAIT"
    assert read.confidence == 0.6
    assert "CLEAR_READ_CAP_RANGING_REGIME" in read.reasons
