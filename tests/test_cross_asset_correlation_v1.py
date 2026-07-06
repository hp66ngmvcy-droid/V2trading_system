"""Tests for cross_asset_correlation_v1 strategy."""
from __future__ import annotations

import pandas as pd
import pytest

from tar_system.strategies.cross_asset_correlation_v1 import CrossAssetCorrelationV1


def _row(close: float, atr: float = 10.0, ts: str = "2024-01-15") -> pd.Series:
    return pd.Series(
        {"timestamp": pd.Timestamp(ts), "close": close, "atr": atr, "symbol": "XAUUSD", "timeframe": "D1"}
    )


def _make_strategy_no_ext(monkeypatch) -> CrossAssetCorrelationV1:
    """Strategy with no external data — tests internal logic only."""
    monkeypatch.setattr(
        "tar_system.strategies.cross_asset_correlation_v1._load_close",
        lambda _: None,
    )
    return CrossAssetCorrelationV1()


def test_default_dxy_slope_window_is_5() -> None:
    s = CrossAssetCorrelationV1.__dataclass_fields__["dxy_slope_window"]
    assert s.default == 5


def test_hold_when_no_external_data(monkeypatch) -> None:
    strat = _make_strategy_no_ext(monkeypatch)
    # With no VIX/NQ/DXY, should always HOLD (no stress gate, no correlation window)
    for i in range(30):
        sig = strat.generate_signal(_row(1900.0 + i, ts=f"2024-01-{i+1:02d}"), regime="TRENDING")
    assert sig.side == "HOLD"


def test_hold_before_window_full(monkeypatch) -> None:
    strat = _make_strategy_no_ext(monkeypatch)
    # Only 5 rows — correlation window (20) not full
    for i in range(5):
        sig = strat.generate_signal(_row(1900.0 + i, ts=f"2024-01-{i+1:02d}"), regime="TRENDING")
    assert sig.side == "HOLD"


def test_dxy_surge_suppresses_buy(monkeypatch) -> None:
    """Verify DXY slope gate fires: surging dollar → HOLD even if other conditions met."""
    gold_prices = [1900.0 - i * 0.5 for i in range(25)]  # falling gold (negative corr with NQ)
    nq_prices = [16000.0 + i * 10 for i in range(25)]    # rising NQ
    dxy_prices = [101.0 + i * 0.5 for i in range(25)]    # strongly rising DXY
    vix_prices = [30.0] * 25                              # elevated VIX

    dates = pd.date_range("2024-01-01", periods=25, freq="D")

    def mock_load(symbol_tf: str) -> pd.Series | None:
        idx = pd.DatetimeIndex(dates)
        if "VIX" in symbol_tf:
            return pd.Series(vix_prices, index=idx)
        if "NQ" in symbol_tf:
            return pd.Series(nq_prices, index=idx)
        if "DXY" in symbol_tf:
            return pd.Series(dxy_prices, index=idx)
        return None

    monkeypatch.setattr(
        "tar_system.strategies.cross_asset_correlation_v1._load_close",
        mock_load,
    )
    strat = CrossAssetCorrelationV1()

    sig = None
    for i in range(25):
        sig = strat.generate_signal(
            _row(gold_prices[i], ts=str(dates[i].date())), regime="TRENDING"
        )
    # DXY surge over 5-day window (~2.5% rise) should suppress the entry
    assert sig.side == "HOLD", f"Expected HOLD due to DXY surge, got {sig.side}"
