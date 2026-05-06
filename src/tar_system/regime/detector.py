"""Simple market regime detection."""

from __future__ import annotations

from enum import Enum

import pandas as pd


class Regime(str, Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"


def detect_regime(row: pd.Series) -> Regime:
    ema_fast = row.get("ema_fast")
    ema_slow = row.get("ema_slow")
    atr = row.get("atr")
    close = row.get("close")
    volatility = row.get("rolling_volatility")
    compression = row.get("range_compression")
    values = [ema_fast, ema_slow, atr, close, volatility, compression]
    if any(pd.isna(value) for value in values):
        return Regime.UNKNOWN
    atr_ratio = atr / close if close else 0
    if volatility > 0.025 or atr_ratio > 0.025:
        return Regime.VOLATILE
    ema_gap = abs(ema_fast - ema_slow) / close if close else 0
    if ema_gap > 0.0015 and compression < 0.55:
        return Regime.TRENDING
    if compression < 0.35 and volatility < 0.01:
        return Regime.RANGING
    return Regime.UNKNOWN
